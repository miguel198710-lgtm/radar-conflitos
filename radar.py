import urllib.request
import xml.etree.ElementTree as ET
import json
import datetime
import random
import ssl
from email.utils import parsedate_to_datetime

print("A iniciar radar tatico de alta frequencia...")

# Dicionario tatico expandido
hotspots = {
    "Ucrânia": [31.16, 48.37], "Ukraine": [31.16, 48.37], "Kyiv": [30.52, 50.45],
    "Rússia": [37.61, 55.75], "Russia": [37.61, 55.75], "Moscow": [37.61, 55.75],
    "Gaza": [34.46, 31.50], "Israel": [34.85, 31.04], "Rafah": [34.25, 31.28],
    "Líbano": [35.86, 33.85], "Lebanon": [35.86, 33.85], "Beirut": [35.50, 33.89],
    "Sudão": [30.21, 12.86], "Sudan": [30.21, 12.86],
    "Iémen": [47.58, 15.55], "Yemen": [47.58, 15.55], "Houthi": [47.58, 15.55],
    "Síria": [38.99, 34.80], "Syria": [38.99, 34.80],
    "Taiwan": [120.96, 23.69], "China": [116.40, 39.90],
    "Somália": [46.19, 5.15], "Iran": [51.38, 35.68], "Irão": [51.38, 35.68],
    "Venezuela": [-66.90, 10.48], "Guyana": [-58.15, 6.80]
}

# Lista de Feeds Expandida (Reuters, Al Jazeera, BBC, UN News)
rss_urls = [
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml",
    "https://feedx.net/rss/ap.xml",
    "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    "https://feeds.reuters.com/reuters/topnews",
    "https://www.france24.com/en/rss"
]

contexto = ssl.create_default_context()
contexto.check_hostname = False
contexto.verify_mode = ssl.CERT_NONE

features_formatadas = []
agora = datetime.datetime.now(datetime.timezone.utc)

for feed_url in rss_urls:
    try:
        print(f"A varrer: {feed_url}")
        pedido = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        resposta = urllib.request.urlopen(pedido, context=contexto, timeout=15)
        root = ET.fromstring(resposta.read())

        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            if not pub_date_str: continue
            
            # FILTRO DE 24 HORAS
            data_noticia = parsedate_to_datetime(pub_date_str)
            diferenca = agora - data_noticia
            
            if diferenca.total_seconds() > 86400: # 86400 segundos = 24 horas
                continue 

            for local, coords in hotspots.items():
                if local.lower() in title.lower():
                    # Dispersao tatica para evitar sobreposicao
                    lon = coords[0] + random.uniform(-0.18, 0.18)
                    lat = coords[1] + random.uniform(-0.18, 0.18)

                    features_formatadas.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "titulo_evento": title,
                            "descricao": f"Fonte: {local.upper()} (Ultimas 24h)",
                            "url_fonte": link,
                            "data_noticia": data_noticia.strftime("%Y-%m-%d %H:%M"),
                            "categoria": "Inteligencia Recente"
                        }
                    })
                    break
                    
    except Exception as e:
        print(f"Erro no feed: {e}")

# Exportacao Final
with open("conflitos.geojson", "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": features_formatadas}, f, ensure_ascii=False, indent=2)

print(f"SUCESSO: {len(features_formatadas)} eventos ativos nas ultimas 24h.")
