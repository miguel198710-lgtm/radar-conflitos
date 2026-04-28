import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import ssl
from email.utils import parsedate_to_datetime

print("A atualizar rede de sensores: Adicionando Eixo Europeu e corrigindo canais de Economia...")

# Ignorar erros de certificados SSL
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# --- 1. REDE DE INTELIGÊNCIA EXPANDIDA (RSS FEEDS) ---
FONTES_RSS = {
    # DEFESA E GEOPOLÍTICA
    "Defense News": "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "War on the Rocks": "https://warontherocks.com/feed/",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    
    # EIXO EUROPEU (Novas Fontes)
    "Euronews (Europa)": "https://www.euronews.com/rss?level=vertical&name=news",
    "France 24": "https://www.france24.com/en/rss",
    "DW (Alemanha/UE)": "https://rss.dw.com/xml/rss-en-all",
    "Politico Europe": "https://www.politico.eu/feed/",
    
    # ECONOMIA (Link Corrigido e mais estável)
    "CNBC World Economy": "https://www.cnbc.com/id/100727362/device/rss/rss.xml",
    
    # AGGREGATORS (Busca ativa por temas)
    "Google News Military": "https://news.google.com/rss/search?q=military+OR+war+OR+missile+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News Markets": "https://news.google.com/rss/search?q=global+economy+OR+markets+when:1d&hl=en-US&gl=US&ceid=US:en"
}

# --- 2. FILTRO DE PALAVRAS-CHAVE ---
KEYWORDS_DEFESA = ["war", "military", "missile", "strike", "troops", "navy", "drone", "attack", "defense", "nuclear", "nato", "guerra", "míssil", "ataque", "tropas"]
KEYWORDS_ECONOMIA = ["economy", "inflation", "markets", "stocks", "oil", "sanctions", "bank", "trade", "interest rates", "economia", "mercados", "petróleo", "sanções"]
KEYWORDS_POLITICA = ["diplomacy", "summit", "election", "treaty", "un ", "eu ", "brussels", "eleições", "diplomacia", "acordo", "bruxelas", "ue"]

# --- 3. MAPA INTERNO EXPANDIDO (COORDENADAS TÁTICAS) ---
MAPA_INTERNO = {
    # EUROPA
    "portugal": [-8.2245, 39.3999], "lisbon": [-9.1393, 38.7223],
    "spain": [-3.7038, 40.4168], "madrid": [-3.7038, 40.4168],
    "france": [2.2137, 46.2276], "paris": [2.3522, 48.8566],
    "germany": [10.4515, 51.1657], "berlin": [13.4050, 52.5200],
    "uk ": [-3.4360, 55.3781], "london": [-0.1278, 51.5074],
    "italy": [12.5674, 41.8719], "rome": [12.4964, 41.9028],
    "belgium": [4.4699, 50.5039], "brussels": [4.3517, 50.8503],
    "poland": [19.1451, 51.9194], "warsaw": [21.0122, 52.2297],
    "greece": [21.8243, 39.0742], "athens": [23.7275, 37.9838],
    # CONFLITOS E GLOBAL
    "ukraine": [31.1656, 48.3794], "kyiv": [30.5238, 50.4547],
    "russia": [105.3188, 61.5240], "moscow": [37.6173, 55.7558],
    "israel": [34.8516, 31.0461], "gaza": [34.4668, 31.5017],
    "iran": [53.6880, 32.4279], "tehran": [51.3890, 35.6892],
    "china": [104.1954, 35.8617], "usa": [-95.7129, 37.0902],
    "taiwan": [120.9605, 23.6978], "yemen": [47.5868, 15.5527],
    "red sea": [38.1157, 20.2802], "north korea": [127.0500, 40.0000]
}

def categorizar_e_filtrar(texto):
    texto = texto.lower()
    if any(kw in texto for kw in KEYWORDS_DEFESA): return "Defesa/Conflito"
    if any(kw in texto for kw in KEYWORDS_ECONOMIA): return "Economia"
    if any(kw in texto for kw in KEYWORDS_POLITICA): return "Política"
    return None

def localizar_alvo(texto):
    texto_limpo = texto.lower()
    for local, coords in MAPA_INTERNO.items():
        if re.search(r'\b' + local + r'\b', texto_limpo):
            return coords
    return None

features_geojson = []
processed_count = 0

for fonte_nome, url in FONTES_RSS.items():
    print(f"A ler: {fonte_nome}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Subimos para 20 notícias por fonte para aumentar o volume
            for item in root.findall('.//item')[:20]:
                titulo = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else "#"
                
                categoria = categorizar_e_filtrar(f"{titulo} {desc}")
                coordenadas = localizar_alvo(f"{titulo} {desc}")
                
                if categoria and coordenadas:
                    # Formatar Data
                    raw_date = item.find('pubDate').text if item.find('pubDate') is not None else None
                    pub_date = "Data Recente"
                    if raw_date:
                        try:
                            dt = parsedate_to_datetime(raw_date)
                            pub_date = dt.strftime("%d/%m/%Y %H:%M")
                        except: pass
                    
                    features_geojson.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": coordenadas},
                        "properties": {
                            "titulo_evento": titulo,
                            "descricao": desc[:250] + "..." if len(desc) > 250 else desc,
                            "url_fonte": link,
                            "categoria": f"{categoria} ({fonte_nome})",
                            "data_noticia": pub_date
                        }
                    })
                    processed_count += 1
    except Exception as e:
        print(f"Erro na fonte {fonte_nome}: {str(e)}")

# Gravar o ficheiro final
output = {"type": "FeatureCollection", "features": features_geojson}
with open('conflitos.geojson', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Varrimento concluído. {processed_count} notícias injetadas no sistema.")
