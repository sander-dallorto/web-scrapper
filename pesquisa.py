# -*- coding: utf-8 -*-
import pymysql

# Abre as conexões com o banco (alterar o usuário e senha)
def abrirConexao():
    return pymysql.connect(host='localhost', user='root', passwd='root', db='indice', use_unicode=True, charset="utf8mb4")

# Busca o ID de uma palavra
def getIdPalavra(palavra):
    retorno = -1 #não existe a palavra no índice
    conexao = abrirConexao()
    cursor = conexao.cursor()
    cursor.execute('select idpalavra from palavras where palavra = %s', palavra)
    if cursor.rowcount > 0:
        retorno = cursor.fetchone()[0]
    cursor.close()
    conexao.close()
    return retorno

# Busca apenas uma palavra no banco de dados com base no ID dela
def buscaUmaPalavra(palavra):
   idpalavra = getIdPalavra(palavra)
   conexao = abrirConexao()
   cursor = conexao.cursor()
   cursor.execute('SELECT urls.url FROM palavra_localizacao plc INNER JOIN urls ON plc.idurl = urls.idurl WHERE plc.idpalavra = %s', idpalavra)
   paginas = set()
   for url in cursor:
      paginas.add(url[0])
   print('Buscando palavra '+str(palavra)+ ': ', paginas)
   cursor.close()
   conexao.close()

# Busca mais de uma palavra no banco
def buscaMaisPalavras(consulta):
    listacampos = 'p1.idurl'
    listatabelas = ''
    listaclausulas = ''
    palavrasid = []
    
    palavras = consulta.split(' ')
    numerotabela = 1
    for palavra in palavras:
        idpalavra = getIdPalavra(palavra)
        if idpalavra > 0:
            palavrasid.append(idpalavra)
            if numerotabela > 1:
                listatabelas += ', '
                listaclausulas += ' and '
                listaclausulas += 'p%d.idurl = p%d.idurl and ' % (numerotabela - 1, numerotabela)
            listacampos += ', p%d.localizacao' % numerotabela
            listatabelas += ' palavra_localizacao p%d' % numerotabela
            listaclausulas += 'p%d.idpalavra = %d' % (numerotabela, idpalavra)
            numerotabela += 1
    consultacompleta = 'SELECT %s FROM %s WHERE %s' % (listacampos, listatabelas, listaclausulas)
    
    conexao = abrirConexao()
    cursor = conexao.cursor()
    cursor.execute(consultacompleta)
    linhas = [linha for linha in cursor]
    cursor.close()
    conexao.close()
    
    return linhas, palavrasid

# Busca URL
def getUrl(idurl):
    retorno = ''
    conexao = abrirConexao()
    cursor = conexao.cursor()
    cursor.execute('select url from urls where idurl = %s', idurl)
    if cursor.rowcount > 0:
        retorno = cursor.fetchone()[0]
    cursor.close()
    conexao.close()
    return retorno

# Calcula o score com base na frequencia que as palavras aparecem
def frequenciaScore(linhas):
    contagem = dict([(linha[0], 0) for linha in linhas])
    for linha in linhas:
        contagem[linha[0]] += 1
    return contagem

# Calcula o score com base na localização, quando mais em cima do texto melhor
def localizacaoScore(linhas):
    localizacoes = dict([linha[0], 1000000] for linha in linhas)
    for linha in linhas:
        soma = sum(linha[1:])
        if soma < localizacoes[linha[0]]:
            localizacoes[linha[0]] = soma
    return localizacoes

# Calcula o score com base na distancia entre as palavras
def distanciaScore(linhas):
    if len(linhas[0]) <= 2:
        return dict([(linha[0], 1.0) for linha in linhas]) 
    distancias = dict([(linha[0], 1000000) for linha in linhas])
    for linha in linhas:
        dist = sum([abs(linha[i] - linha[i - 1]) for i in range(2, len(linha))]) 
        if dist < distancias[linha[0]]: 
            distancias[linha[0]] = dist
    return distancias

#Inicia a pesquisa das palavras e lista as 10 melhores com base no score
def pesquisa(tipo_score='todos'):
    palavra1 = input("Digite a primeira palavra: ")
    palavra2 = input("Digite a segunda palavra: ")
    
    consulta = f"{palavra1} {palavra2}"
    
    linhas, palavrasid = buscaMaisPalavras(consulta)
    scores = {}
    
    if tipo_score == 'frequenciascore':
        scores = frequenciaScore(linhas)
    elif tipo_score == 'localizacaoscore':
        scores = localizacaoScore(linhas)
    elif tipo_score == 'distanciascore':
        scores = distanciaScore(linhas)
    elif tipo_score == 'todos':
        scores_freq = frequenciaScore(linhas)
        scores_loc = localizacaoScore(linhas)
        scores_dist = distanciaScore(linhas)
        
        for url in scores_freq.keys():
            scores[url] = scores_freq[url] + scores_loc[url] + scores_dist[url]
    else:
        print("Tipo de score inválido. Escolha entre 'frequenciaScore', 'localizacaoScore', 'distanciaScore' ou 'todos'.")
        return
    
    scoresordenado = sorted([(score, url) for (url, score) in scores.items()], reverse=1)
    for (score, idurl) in scoresordenado[:10]:
        print('%f\t%s' % (score, getUrl(idurl)))

tipo_score = input("Escolha o tipo de score (frequenciaScore, localizacaoScore, distanciaScore ou todos): ").lower()

pesquisa(tipo_score)





