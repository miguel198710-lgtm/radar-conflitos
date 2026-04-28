import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import ssl
from email.utils import parsedate_to_datetime

print("A iniciar varrimento OSINT global Nível 4 (Defesa, Economia, Política)...")

# Ignorar erros de certificados SSL de alguns sites de notícias
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# --- 1. REDE DE INTELIGÊNCIA (FONTES RSS) ---
FONTES_RSS = {
    "War on the Rocks": "https://warontherocks.com/feed/",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC Conflict": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Defense News": "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "CNBC Economy": "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=12000000&id=10000664",
    "Google News Defesa": "https://news.google.com/rss/search?q=military+OR+war+OR+missile+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News Economia": "https://news.google.com/rss/search?q=global+economy+OR+markets+OR+inflation+when:1d&hl=en-US&gl=US&ceid=US:en"
}

# --- 2. FILTRO DE AMEAÇAS (PALAVRAS-CHAVE TÁTICAS) ---
# A notícia tem de conter pelo menos uma destas palavras para ser validada
KEYWORDS_DEFESA = ["war", "military", "missile", "strike", "troops", "navy", "drone", "attack", "defense", "nuclear", "guerra", "míssil", "ataque", "tropas"]
KEYWORDS_ECONOMIA = ["economy", "inflation", "markets", "stocks", "oil", "sanctions", "bank", "trade", "economia", "mercados", "petróleo", "sanções", "inflação"]
KEYWORDS_POLITICA = ["diplomacy", "summit", "election", "treaty", "un ", "nato", "eleições", "diplomacia", "acordo", "nato", "onu"]

# --- 3. GEOCODIFICADOR TÁTICO INTERNO ---
# Se a notícia mencionar um destes países, o ponto vai direto para estas coordenadas
MAPA_INTERNO = {
    "ukraine": [31.1656, 48.3794], "kyiv": [30.5238, 50.4547],
    "russia": [105.3188, 61.5240], "moscow": [37.6173, 55.7558],
    "israel": [34.8516, 31.0461], "gaza": [34.4668, 31.5017],
    "iran": [53.6880, 32.4279], "tehran": [51.3890, 35.6892],
    "china": [104.1954, 35.8617], "taiwan": [120.9605, 23.6978],
    "usa": [-95.7129, 37.0902], "washington": [-77.0369, 38.9072],
    "uk ": [-3.4360, 55.3781], "london": [-0.1278, 51.5074],
    "france": [2.2137, 46.2276], "paris": [2.3522, 48.8566],
    "germany": [10.4515, 51.1657], "berlin": [13.4050, 52.5200],
    "portugal": [-8.2245, 39.3999], "lisbon": [-9.1393, 38.7223],
    "yemen": [47.5868, 15.5527], "red sea": [38.1157, 20.2802],
    "north korea": [127.0500, 40.0000], "south korea": [127.7669, 35.9078]
}

def categorizar_e_filtrar(texto):
    texto = texto.lower()
    
    if any(kw in texto for kw in KEYWORDS_DEFESA):
        return "Defesa/Conflito"
    elif any(kw in texto for kw in KEYWORDS_ECONOMIA):
        return "Economia"
    elif any(kw in texto for kw in KEYWORDS_POLITICA):
        return "Política"
    else:
        return None # A notícia não tem interesse tático, será descartada

def localizar_alvo(texto):
    texto_limpo = texto.lower()
    for local, coords in MAPA_INTERNO.items():
        # Usar regex para procurar a palavra exata e não partes de palavras
        if re.search(r'\b' + local + r'\b', texto_limpo):
            return coords
    return None # Não encontrou local militarmente relevante

features_geojson = []
noticias_processadas = 0
noticias_descartadas = 0

for fonte_nome, url in FONTES_RSS.items():
    print(f"A varrer radar: {fonte_nome}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Limitar a 15 notícias por fonte para evitar sobrecarga de dados
            for item in root.findall('.//item')[:15]:
                titulo = item.find('title').text if item.find('title') is not None else ""
                descricao = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else "#"
                
                # Juntar título e descrição para analisar
                texto_analise = f"{titulo} {descricao}"
                
                # 1. Filtro Tático (Saber o tema)
                categoria = categorizar_e_filtrar(texto_analise)
                if not categoria:
                    noticias_descartadas += 1
                    continue # Ignorar notícia se não for Defesa, Economia ou Política
                
                # 2. Localizador (Saber as coordenadas)
                coordenadas = localizar_alvo(texto_analise)
                if not coordenadas:
                    continue # Ignorar se não soubermos onde colocar no mapa
                
                # 3. Formatar Data
                raw_date = item.find('pubDate').text if item.find('pubDate') is not None else None
                pub_date = "Data Recente"
                if raw_date:
                    try:
                        dt = parsedate_to_datetime(raw_date)
                        pub_date = dt.strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        pub_date = raw_date
                
                # 4. Construir o Alvo para o Mapa e Rodapé
                features_geojson.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": coordenadas # [Longitude, Latitude]
                    },
                    "properties": {
                        "titulo_evento": titulo,
                        "descricao": descricao[:200] + "..." if len(descricao) > 200 else descricao, # Limitar texto longo
                        "url_fonte": link,
                        "categoria": f"{categoria} ({fonte_nome})",
                        "data_noticia": pub_date
                    }
                })
                noticias_processadas += 1

    except Exception as e:
        print(f"Falha de comunicações com a fonte {fonte_nome}: {str(e)}")

# Construir ficheiro final
geojson_output = {
    "type": "FeatureCollection",
    "features": features_geojson
}

# Gravar no repositório
with open('conflitos.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson_output, f, ensure_ascii=False, indent=2)

print("Varrimento concluído.")
print(f"Alvos confirmados no mapa: {noticias_processadas}")
print(f"Ruído bloqueado pelo filtro: {noticias_descartadas}")
