import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import ssl
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

print("A iniciar varrimento OSINT global com FILTRO TEMPORAL...")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# --- 1. REDE DE INTELIGÊNCIA ---
FONTES_RSS = {
    "Defense News": "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "War on the Rocks": "https://warontherocks.com/feed/",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Euronews (Europa)": "https://www.euronews.com/rss?level=vertical&name=news",
    "France 24": "https://www.france24.com/en/rss",
    "DW (Alemanha/UE)": "https://rss.dw.com/xml/rss-en-all",
    "Politico Europe": "https://www.politico.eu/feed/",
    "Yahoo Finance (Global)": "https://finance.yahoo.com/news/rssindex",
    "NYT Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "Wall Street Journal": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "Google News Military": "https://news.google.com/rss/search?q=military+OR+war+OR+missile+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News Markets": "https://news.google.com/rss/search?q=global+economy+OR+markets+when:1d&hl=en-US&gl=US&ceid=US:en"
}

# --- 2. FILTRO DE PALAVRAS-CHAVE ---
KEYWORDS_DEFESA = ["war", "military", "missile", "strike", "troops", "navy", "drone", "attack", "defense", "nuclear", "nato", "guerra", "míssil", "ataque", "tropas"]
KEYWORDS_ECONOMIA = ["economy", "inflation", "markets", "stocks", "oil", "sanctions", "bank", "trade", "interest rates", "economia", "mercados", "petróleo", "sanções"]
KEYWORDS_POLITICA = ["diplomacy", "summit", "election", "treaty", "un ", "eu ", "brussels", "eleições", "diplomacia", "acordo", "bruxelas", "ue"]

# --- 3. MAPA INTERNO ---
MAPA_INTERNO = {
    "usa": [-95.7129, 37.0902], "washington": [-77.0369, 38.9072], "new york": [-74.0060, 40.7128],
    "canada": [-106.3468, 56.1304], "ottawa": [-75.6972, 45.4215],
    "mexico": [-102.5528, 23.6345], "mexico city": [-99.1332, 19.4326],
    "brazil": [-51.9253, -14.2350], "brasilia": [-47.9292, -15.7801],
    "argentina": [-63.6167, -38.4161], "buenos aires": [-58.3816, -34.6037],
    "venezuela": [-66.5897, 6.4238], "caracas": [-66.9036, 10.4806],
    "colombia": [-74.2973, 4.5709], "bogota": [-74.0721, 4.7110],
    "cuba": [-79.1834, 21.5218], "havana": [-82.3666, 23.1136],
    "chile": [-71.5429, -35.6751], "santiago": [-70.6693, -33.4489],
    "peru": [-75.0152, -9.1900], "lima": [-77.0428, -12.0464],
    "portugal": [-8.2245, 39.3999], "lisbon": [-9.1393, 38.7223],
    "spain": [-3.7038, 40.4168], "madrid": [-3.7038, 40.4168],
    "france": [2.2137, 46.2276], "paris": [2.3522, 48.8566],
    "germany": [10.4515, 51.1657], "berlin": [13.4050, 52.5200],
    "uk ": [-3.4360, 55.3781], "london": [-0.1278, 51.5074],
    "italy": [12.5674, 41.8719], "rome": [12.4964, 41.9028],
    "belgium": [4.4699, 50.5039], "brussels": [4.3517, 50.8503],
    "poland": [19.1451, 51.9194], "warsaw": [21.0122, 52.2297],
    "greece": [21.8243, 39.0742], "athens": [23.7275, 37.9838],
    "ukraine": [31.1656, 48.3794], "kyiv": [30.5238, 50.4547],
    "russia": [105.3188, 61.5240], "moscow": [37.6173, 55.7558],
    "israel": [34.8516, 31.0461], "gaza": [34.4668, 31.5017],
    "iran": [53.6880, 32.4279], "tehran": [51.3890, 35.6892],
    "china": [104.1954, 35.8617], "beijing": [116.4074, 39.9042],
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
noticias_processadas = 0

# --- CONFIGURAÇÃO TÁTICA: Janela de Tempo ---
# Qualquer notícia com mais destas horas será eliminada
HORAS_EXPIRACAO = 48 

for fonte_nome, url in FONTES_RSS.items():
    print(f"A ler: {fonte_nome}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('.//item')[:25]:
                titulo = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else "#"
                
                categoria = categorizar_e_filtrar(f"{titulo} {desc}")
                coordenadas = localizar_alvo(f"{titulo} {desc}")
                
                if categoria and coordenadas:
                    raw_date = item.find('pubDate').text if item.find('pubDate') is not None else None
                    noticia_valida = True
                    pub_date = "Recente"
                    
                    if raw_date:
                        try:
                            # Converte o texto da data para um objeto de "Tempo" real
                            dt = parsedate_to_datetime(raw_date)
                            
                            # Adiciona fuso horário UTC se a notícia não tiver um
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            
                            # Vê que horas são agora em UTC
                            agora = datetime.now(timezone.utc)
                            
                            # Subtrai o tempo: Agora menos a data da Notícia
                            diferenca = agora - dt
                            
                            # Se a diferença for MAIOR que o nosso limite (ex: 48h), DESCARTA!
                            if diferenca > timedelta(hours=HORAS_EXPIRACAO):
                                noticia_valida = False
                            else:
                                pub_date = dt.strftime("%d/%m/%Y %H:%M")
                        except Exception:
                            pass
                    
                    # Só avança se a notícia for recente e não tiver expirado
                    if noticia_valida:
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
                        noticias_processadas += 1
    except Exception as e:
        print(f"Erro na fonte {fonte_nome}: {str(e)}")

output = {"type": "FeatureCollection", "features": features_geojson}
with open('conflitos.geojson', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Varrimento concluído. {noticias_processadas} alertas ativos (Últimas {HORAS_EXPIRACAO} horas).")
