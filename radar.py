import urllib.request
import xml.etree.ElementTree as ET
import json
import datetime
import random
import ssl

print("A iniciar o Extrator RSS Nativo (Dados Reais)...")

# Dicionário Tático: Se a palavra-chave aparecer na notícia, ele sabe onde colocar no mapa
hotspots = {
    "Ucrânia": [31.16, 48.37], "Ukraine": [31.16, 48.37], "Kyiv": [30.52, 50.45],
    "Rússia": [37.61, 55.75], "Russia": [37.61, 55.75], "Moscow": [37.61, 55.75],
    "Gaza": [34.46, 31.50], "Israel": [34.85, 31.04], "Lebanon": [35.86, 33.85], "Líbano": [35.86, 33.85],
    "Sudão": [30.21, 12.86], "Sudan": [30.21, 12.86],
    "Iémen": [47.58, 15.55], "Yemen": [47.58, 15.55], "Houthi": [47.58, 15.55],
    "Síria": [38.99, 34.80], "Syria": [38.99, 34.80],
    "Myanmar": [95.95, 21.91],
    "Mali": [-3.99, 17.57],
    "Somália": [46.19, 5.15], "Somalia": [46.19, 5.15],
    "Taiwan": [120.96, 23.69],
    "Congo": [23.65, -2.88], "DRC": [23.65, -2.88]
}

# Fontes Oficiais de Notícias (Feeds RSS Abertos e Estáveis)
rss_urls = [
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml"
]

contexto = ssl.create_default_context()
contexto.check_hostname = False
contexto.verify_mode = ssl.CERT_NONE

features_formatadas = []

for feed_url in rss_urls:
    try:
        print(f"A varrer radar de notícias: {feed_url}...")
        pedido = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        resposta = urllib.request.urlopen(pedido, context=contexto, timeout=15)
        xml_data = resposta.read()
        root = ET.fromstring(xml_data)

        # Analisar as últimas 40 notícias de cada canal
        for item in root.findall('.//item')[:40]:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else datetime.datetime.now().strftime("%Y-%m-%d")

            # Procurar áreas de conflito no título da notícia
            for local, coords in hotspots.items():
                if local.lower() in title.lower():
                    # Adicionar uma dispersão tática (random) para as notícias não ficarem exatamente umas por cima das outras
                    lon = coords[0] + random.uniform(-0.15, 0.15)
                    lat = coords[1] + random.uniform(-0.15, 0.15)

                    nova_feature = {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "titulo_evento": title,
                            "descricao": f"Alvo detetado: {local.upper()}",
                            "url_fonte": link,
                            "data_noticia": pubDate[:16], # Fica só com a data e hora
                            "categoria": "Notícia Geolocalizada"
                        }
                    }
                    features_formatadas.append(nova_feature)
                    break # Se achou o local, guarda o ponto e passa para a próxima notícia
                    
    except Exception as e:
        print(f"Erro ao ler o feed {feed_url}: {e}")

geojson_final = {
    "type": "FeatureCollection",
    "features": features_formatadas
}

# Gravar o ficheiro com a formatação final
with open("conflitos.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson_final, f, ensure_ascii=False, indent=2)

print(f"SUCESSO ABSOLUTO: Ficheiro gerado com {len(features_formatadas)} notícias reais!")
