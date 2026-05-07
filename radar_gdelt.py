import urllib.request
import zipfile
import io
import json

def radar_gdelt_raw():
    print("[INTELIGENCIA GDELT] A API publica rejeitou a ligacao (Erro 404).")
    print("[INTELIGENCIA GDELT] A iniciar plano de contingencia: Infiltracao direta no Mainframe Raw...")
    
    # 1. Encontrar o ficheiro de dados global mais recente (atualizado a cada 15 min)
    url_masterlist = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    try:
        req = urllib.request.Request(url_masterlist, headers={'User-Agent': 'Mozilla/5.0'})
        resposta = urllib.request.urlopen(req)
        linhas = resposta.read().decode('utf-8').splitlines()
        
        # A primeira linha contem a exportacao global de eventos
        url_zip = linhas[0].split(" ")[2]
        print(f"  -> Alvo localizado: {url_zip.split('/')[-1]}")
        
    except Exception as e:
        print(f"[ERRO FATAL] Falha ao aceder a masterlist do GDELT: {e}")
        return

    # 2. Descarregar e Descomprimir os dados na memoria (sem gravar lixo no disco)
    try:
        req_zip = urllib.request.Request(url_zip, headers={'User-Agent': 'Mozilla/5.0'})
        resposta_zip = urllib.request.urlopen(req_zip)
        pacote_zip = zipfile.ZipFile(io.BytesIO(resposta_zip.read()))
        
        # O GDELT envia um ficheiro comprimido. Lemos diretamente em RAM.
        nome_csv = pacote_zip.namelist()[0]
        dados_csv = pacote_zip.read(nome_csv).decode('utf-8')
        print("  -> Download e extracao concluidos. A processar telemetria...")
        
    except Exception as e:
        print(f"[ERRO FATAL] Falha ao processar o pacote de dados: {e}")
        return

    # 3. Filtrar os dados CSV e Converter manualmente para GeoJSON (O formato da ESRI)
    features = []
    
    # Codigos CAMEO (Dicionario Militar do GDELT) para eventos de alto risco:
    # 14 (Protestos/Motins), 17 (Coacao/Destruicao), 18 (Assalto Fisico), 19 (Combate Militar), 20 (Massacre/Armas nao convencionais)
    codigos_alvo = ['14', '17', '18', '19', '20']
    
    linhas_csv = dados_csv.splitlines()
    for linha in linhas_csv:
        colunas = linha.split('\t')
        
        # A Base de Dados GDELT 2.0 tem 61 colunas no total.
        if len(colunas) >= 60:
            root_code = colunas[28]  # Coluna do Codigo Macro do Evento
            
            if root_code in codigos_alvo:
                nome_local = colunas[52] # Coluna ActionGeo_FullName
                lat = colunas[56]        # Coluna ActionGeo_Lat
                lon = colunas[57]        # Coluna ActionGeo_Long
                url_fonte = colunas[60]  # Coluna SOURCEURL
                
                # Se o evento tiver coordenadas exatas, criamos um ponto de alvo
                if lat and lon:
                    try:
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [float(lon), float(lat)] # GeoJSON exige a ordem Longitude, Latitude
                            },
                            "properties": {
                                "local": nome_local,
                                "codigo_conflito": root_code,
                                "link_noticia": url_fonte
                            }
                        }
                        features.append(feature)
                    except ValueError:
                        continue # Ignora se os dados de GPS vierem corrompidos

    # Empacotamos todos os pontos da ultima hora
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open("gdelt_conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)
        
    print(f"[SUCESSO] Intercecao limpa! {len(features)} zonas ativas extraidas com sucesso.")

if __name__ == "__main__":
    radar_gdelt_raw()
