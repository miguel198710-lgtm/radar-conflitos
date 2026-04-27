import urllib.request
import xml.etree.ElementTree as ET
import json
import re

print("A iniciar varrimento OSINT global com categorização inteligente...")

# 1. As Fontes (Agências Globais)
FONTES = [
    {"nome": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"nome": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"nome": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml"}
]

# 2. Dicionário de Categorização Inteligente
CATEGORIAS_MAP = {
    "war": "Defesa/Conflito", "conflict": "Defesa/Conflito", "strike": "Defesa/Conflito", 
    "military": "Defesa/Conflito", "defense": "Defesa/Conflito", "missile": "Defesa/Conflito", 
    "troops": "Defesa/Conflito", "navy": "Defesa/Conflito", "army": "Defesa/Conflito", 
    "nuclear": "Defesa/Conflito", "tensions": "Defesa/Conflito", "ceasefire": "Defesa/Conflito", 
    "rebel": "Defesa/Conflito",
    "election": "Política", "parliament": "Política", "president": "Política", 
    "summit": "Política", "protest": "Política",
    "economy": "Economia", "sanctions": "Economia", "inflation": "Economia", 
    "oil": "Economia", "trade": "Economia", "debt": "Economia"
}

# 3. Dicionário de Coordenadas (Zonas de Risco)
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
                
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    desc = item.find('description').text if item.find('description') is not None else ""
                    
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "Data Recente"
                    
                    texto_completo = (title + " " + desc).lower()
                    
                    # Identificar a categoria pela palavra-chave
                    categoria_final = None
                    for palavra, cat in CATEGORIAS_MAP.items():
                        if palavra in texto_completo:
                            categoria_final = cat
                            break
                    
                    # Se tiver categoria, tenta mapear as coordenadas
                    if categoria_final:
                        coords = None
                        for pais, coordenadas in ZONAS.items():
                            if re.search(r'\b' + pais + r'\b', title, re.IGNORECASE):
                                coords = coordenadas
                                break
                        
                        # Escrever os dados exatos que a tabela do ArcGIS pede
                        if coords:
                            feature = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": coords
                                },
                                "properties": {
                                    "titulo_evento": title,
                                    "data_noticia": pub_date,
                                    "descricao": desc[:200] + "..." if len(desc) > 200 else desc,
                                    "url_fonte": link,
                                    "categoria": f"{categoria_final} ({fonte['nome']})"
                                }
                            }
                            geojson["features"].append(feature)
                            noticias_processadas += 1

        except Exception as e:
            print(f"Erro ao ler {fonte['nome']}: {e}")

    # Guardar no formato GeoJSON
    with open("conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)
        
    print(f"Sucesso! {noticias_processadas} eventos registados.")

if __name__ == "__main__":
    extrair_noticias()
