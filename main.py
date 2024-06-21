import requests
from bs4 import BeautifulSoup
import re
import nltk
import pymysql

# Função para abrir a conexão com o banco de dados
def abrirConexao():
    return pymysql.connect(host='localhost', user='root', passwd='root', db='indice', autocommit=True, use_unicode=True, charset="utf8mb4")

# Verifica se a página já existe no banco
def paginaIndexada(url):
    retorno = -1
    conexao = abrirConexao()
    cursorUrl = conexao.cursor()
    cursorUrl.execute('SELECT idurl FROM urls WHERE url = %s', url)
    if cursorUrl.rowcount > 0:
        idurl = cursorUrl.fetchone()[0]
        cursorPalavra = conexao.cursor()
        cursorPalavra.execute('SELECT idurl FROM palavra_localizacao WHERE idurl = %s', idurl)
        
        if cursorPalavra.rowcount > 0:
            retorno = -2
        else:
            retorno = idurl
        cursorPalavra.close()
    cursorUrl.close()
    conexao.close()
    
    return retorno

# Insere a página no banco
def insertPagina(url):
    conexao = abrirConexao()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO urls (url) VALUES (%s)", url)
    idpagina = cursor.lastrowid
    cursor.close()
    conexao.close()
    return idpagina

# Verifica se a palavra já existe no banco
def palavraIndexada(palavra):
    retorno = -1
    conexao = abrirConexao()
    cursor = conexao.cursor()
    cursor.execute('select idpalavra from palavras where palavra = %s', palavra)
    if cursor.rowcount > 0:
        retorno = cursor.fetchone()[0]

    cursor.close()
    conexao.close()
    return retorno

# Insere a palavra no banco
def insertPalavra(palavra):
    conexao = abrirConexao()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO palavras (palavra) VALUES (%s)", palavra)
    idpalavra = cursor.lastrowid
    cursor.close()
    conexao.close()
    return idpalavra

# Vincula a palavra na página e insere qual é a localização
def insertPalavraLocalizacao(idurl, idpalavra, localizacao):
    conexao = abrirConexao()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO palavra_localizacao (idurl, idpalavra, localizacao) VALUES (%s, %s, %s)", (idurl, idpalavra, localizacao))
    idpalavra_localizacao = cursor.lastrowid
    cursor.close()
    conexao.close()
    return idpalavra_localizacao

# Trata a sopa do html removendo tags de script e estilos
def getTexto(sopa):
    for tags in sopa(['script', 'style']):
        tags.decompose()
    return ' '.join(sopa.stripped_strings)

# Formata o texto para remover o que não é palavras, remover os stopwords e deixar apenas os radicais
def separaPalavras(texto):
    stop = nltk.corpus.stopwords.words('portuguese')
    stemmer = nltk.stem.RSLPStemmer()
    splitter = re.compile('\\W+')
    lista_palavras = []
    lista = [p for p in splitter.split(texto) if p != '']
    for p in lista:
        if stemmer.stem(p.lower()) not in stop:
            if len(p) > 1:
                lista_palavras.append(stemmer.stem(p.lower()))
    return lista_palavras

# Função que vai salvar novas páginas e palavras na localização correta
def indexador(url, sopa):
    indexada = paginaIndexada(url)
    if indexada == -2:
        print("Url já indexada: " + url)
        return 
    elif indexada == -1:
        idnova_pagina = insertPagina(url)
    elif indexada > 0:
        idnova_pagina = indexada
    
    print('Indexando: ' + url)
        
    texto = getTexto(sopa) 
    palavras = separaPalavras(texto)
    for i in range(len(palavras)):
        palavra = palavras[i]
        idpalavra = palavraIndexada(palavra) 
        if idpalavra == -1:
            idpalavra = insertPalavra(palavra)
        insertPalavraLocalizacao(idnova_pagina, idpalavra, i) 
    
# Função principal que recebe a url e qual a profundidade que vai rodar
def crawl(paginas, profundidade):
    print('Iniciando crawl para ' + str(len(paginas)) + ' paginas')
    
    novas_paginas = set()
    
    for pagina in paginas:
        try:
            dados_pagina = requests.get(pagina).text
        except:
            print('Erro ao abrir a pagina ' + pagina)
            continue
        
        sopa = BeautifulSoup(dados_pagina, "lxml")
        indexador(pagina, sopa)
        
        if profundidade > 0:
            links = sopa.find_all('a')
            for link in links:
                if 'href' in link.attrs:
                    url = link.get('href')
                    
                    if url.startswith('http'):
                        novas_paginas.add(url)
                       
                    if url.startswith('/'):
                        url = pagina + url
                        novas_paginas.add(url)
                    
            crawl(novas_paginas, profundidade - 1)

# Receber a entrada do usuário para a lista de páginas e a profundidade
lista_paginas = input('Digite a URL que deseja iniciar o crawling: ').strip()
profundidade = int(input('Digite a profundidade de crawling desejada: '))

# Iniciar o crawling
crawl([lista_paginas], profundidade)
print('Finalizado!!')
