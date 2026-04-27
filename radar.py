import urllib.request
import xml.etree.ElementTree as ET
import json
import re

print("A iniciar varrimento OSINT global (Conflitos, Defesa, Economia, Política)...")

# 1. As Fontes (Feeds RSS Globais)
FONTES = [
    {"nome": "Al Jazeera Global", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"nome": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"nome": "NY Times", "url": "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml"},
    {"nome": "The Guardian", "url": "https://www.theguardian.com/world/rss"},
    {"nome": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml"}
]

# 2. Filtro Tático (Palavras-chave em inglês)
KEYWORDS = [
    "war", "conflict", "strike", "military", "defense", "missile", "troops", 
    "navy", "army", "nuclear", "tensions", "ceasefire", "rebel", # Defesa/Conflitos
    "election", "parliament", "president", "summit", "protest", # Política
    "economy", "sanctions", "inflation", "oil", "trade", "debt" # Economia
]

# 3. Dicionário de Coordenadas (Zonas de Risco e Países Principais)
# Longitude, Latitude (Formato GeoJSON)
ZONAS = {
    "Ukraine": [31.16, 48.37], "Russia": [105.31, 61.52], "Gaza": [34.46, 31.50],
    "Israel": [34.85, 31.04], "Taiwan": [120.96, 23.69], "China": [104.19, 35.86],
    "Iran": [53.68, 32.42], "USA": [-95.71, 37.09], "United States": [-95.71, 37.09],
    "North Korea": [127.05, 40.33], "South Korea": [127.76, 35.90], 
    "Yemen": [47.58, 15.55], "Red Sea": [38.28, 20.28], "Syria": [38.99, 34.80],
    "Lebanon": [35.86, 33.85], "Sudan": [30.21, 12.86], "Somalia": [46.19, 5.15],
    "Niger": [8.08, 17.60], "Mali": [-3.99, 17.57], "UK": [-3.43, 55.37],
    "France": [2.21, 46.22], "Germany": [10.45, 51.16], "Poland": [19.14, 51.91],
    "NATO": [4.35, 50.85], "EU": [4.35, 50.85], "Portugal": [-8.22, 39.39]
}

def extrair_noticias():
    geojson = {"type": "FeatureCollection", "features": []}
    noticias_processadas = 0

    for fonte in FONTES:
        print(f"A varrer {fonte['nome']}...")
        req = urllib.request.Request(fonte['url'], headers={'User-Agent': 'Mozilla/5.0'})
        
        try:
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                # Procurar todos os items (notícias) no feed
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    desc = item.find('description').text if item.find('description') is not None else ""
                    
                    texto_completo = (title + " " + desc).lower()
                    
                    # Passo A: A notícia fala dos nossos temas?
                    if any(kw in texto_completo for kw in KEYWORDS):
                        
                        # Passo B: Conseguimos localizar a notícia?
                        # Procura o nome do país no Título (com maiúsculas para ser exato)
                        local_encontrado = None
                        coords = None
                        
                        for pais, coordenadas in ZONAS.items():
                            if re.search(r'\b' + pais + r'\b', title, re.IGNORECASE):
                                local_encontrado = pais
                                coords = coordenadas
                                break
                        
                        # Só adiciona ao mapa se conseguiu encontrar uma coordenada
                        if coords:
                            feature = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": coords
                                },
                                "properties": {
                                    "titulo": title,
                                    "descricao": desc[:200] + "..." if len(desc) > 200 else desc,
                                    "fonte": fonte['nome'],
                                    "link": link,
                                    "tema": "Operacional / Estratégico"
                                }
                            }
                            geojson["features"].append(feature)
                            noticias_processadas += 1

        except Exception as e:
            print(f"Erro ao ler {fonte['nome']}: {e}")

    # Guardar o ficheiro GeoJSON
    with open("conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)
        
    print(f"Missão concluída. {noticias_processadas} eventos globais mapeados.")

if __name__ == "__main__":
    extrair_noticias()

