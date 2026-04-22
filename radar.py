import urllib.request
import json
import ssl

print("A ignorar GDELT (Erro 404). A ligar ao radar do UCDP (Uppsala)...")

# API da Universidade de Uppsala (dados de conflitos e mortes)
url = "https://ucdpapi.pcr.uu.se/api/gedevents/22.1?pagesize=50"

contexto = ssl.create_default_context()
contexto.check_hostname = False
contexto.verify_mode = ssl.CERT_NONE

pedido = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    resposta = urllib.request.urlopen(pedido, context=contexto, timeout=30)
    dados = json.loads(resposta.read().decode('utf-8'))
    
    features_formatadas = []
    
    # Extrair os conflitos e converter as coordenadas
    for evento in dados.get('Result', []):
        lat = float(evento.get('latitude', 0))
        lon = float(evento.get('longitude', 0))
        
        if lat != 0 and lon != 0:
            nova_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "titulo_evento": evento.get('conflict_name', 'Conflito Registado'),
                    "descricao": "Forças: " + evento.get('dyad_name', 'Desconhecidas') + " | Baixas estimadas: " + str(evento.get('best', 0)),
                    "url_fonte": evento.get('source_article', ''),
                    "data_noticia": evento.get('date_start', '')[:10],
                    "categoria": "Conflito Ativo (UCDP)"
                }
            }
            features_formatadas.append(nova_feature)

    geojson_final = {
        "type": "FeatureCollection",
        "features": features_formatadas
    }

    # Gravar o ficheiro com a formatação final
    with open("conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson_final, f, ensure_ascii=False, indent=2)

    print("SUCESSO ABSOLUTO: Ficheiro conflitos.geojson criado com dados da UCDP!")

except Exception as e:
    print("Erro critico:", e)
