import requests
import json

# O tradutor completo e definitivo (25 zonas oficiais do IPMA)
COORDENADAS_ZONAS = {
    # Portugal Continental
    "AVR": {"nome": "Aveiro", "lat": 40.6405, "lon": -8.6538},
    "BJA": {"nome": "Beja", "lat": 38.0151, "lon": -7.8632},
    "BRG": {"nome": "Braga", "lat": 41.5454, "lon": -8.4265},
    "BGC": {"nome": "Bragança", "lat": 41.8058, "lon": -6.7572},
    "CBO": {"nome": "Castelo Branco", "lat": 39.8222, "lon": -7.4909},
    "CBR": {"nome": "Coimbra", "lat": 40.2056, "lon": -8.4195},
    "EVR": {"nome": "Évora", "lat": 38.5667, "lon": -7.9000},
    "FAR": {"nome": "Faro", "lat": 37.0194, "lon": -7.9322},
    "GDA": {"nome": "Guarda", "lat": 40.5373, "lon": -7.2658},
    "LRA": {"nome": "Leiria", "lat": 39.7436, "lon": -8.8071},
    "LSB": {"nome": "Lisboa", "lat": 38.7223, "lon": -9.1393},
    "PTG": {"nome": "Portalegre", "lat": 39.2938, "lon": -7.4312},
    "PTO": {"nome": "Porto", "lat": 41.1579, "lon": -8.6291},
    "STM": {"nome": "Santarém", "lat": 39.2333, "lon": -8.6833},
    "STB": {"nome": "Setúbal", "lat": 38.5244, "lon": -8.8882},
    "VCT": {"nome": "Viana do Castelo", "lat": 41.6932, "lon": -8.8329},
    "VRL": {"nome": "Vila Real", "lat": 41.3006, "lon": -7.7441},
    "VIS": {"nome": "Viseu", "lat": 40.6566, "lon": -7.9125},
    
    # Arquipélago da Madeira
    "MRM": {"nome": "Madeira - Região Montanhosa", "lat": 32.7486, "lon": -16.9740},
    "MCN": {"nome": "Madeira - Costa Norte", "lat": 32.8164, "lon": -16.9859},
    "MCS": {"nome": "Madeira - Costa Sul", "lat": 32.6568, "lon": -16.9200},
    "MPS": {"nome": "Porto Santo", "lat": 33.0640, "lon": -16.3400},
    
    # Arquipélago dos Açores
    "AOC": {"nome": "Açores - Grupo Ocidental", "lat": 39.4449, "lon": -31.1969},
    "ACE": {"nome": "Açores - Grupo Central", "lat": 38.5830, "lon": -28.0315},
    "AOR": {"nome": "Açores - Grupo Oriental", "lat": 37.7799, "lon": -25.4332}
}

def obter_avisos():
    url = "https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json"
    print("[IPMA] A extrair os dados táticos de alertas...")
    
    try:
        resposta = requests.get(url)
        resposta.raise_for_status() # Garante que não há erros de ligação
        dados = resposta.json()
    except Exception as e:
        print(f"[ERRO] Falha ao ligar ao IPMA: {e}")
        return
    
    funcionalidades = []
    
    for aviso in dados:
        nivel = aviso.get("awarenessLevelID", "green")
        
        # Ignora tudo o que é verde! Só queremos as ameaças ativas (amarelo, laranja, vermelho).
        if nivel == "green":
            continue
            
        codigo_area = aviso.get("idAreaAviso")
        
        # Se encontrou um aviso e o código existe no nosso dicionário, mapeia-o.
        if codigo_area in COORDENADAS_ZONAS:
            local = COORDENADAS_ZONAS[codigo_area]
            
            funcionalidade = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [local["lon"], local["lat"]]
                },
                "properties": {
                    "zona": local["nome"],
                    "ameaca": aviso.get("awarenessTypeName", "Desconhecido"),
                    "gravidade": nivel,
                    "inicio": aviso.get("startTime", ""),
                    "fim": aviso.get("endTime", ""),
                    "detalhes": aviso.get("text", "Sem detalhes adicionais.")
                }
            }
            funcionalidades.append(funcionalidade)

    # Cria o pacote final GeoJSON para a ESRI
    geojson = {
        "type": "FeatureCollection",
        "features": funcionalidades
    }

    # Guarda o ficheiro no formato correto
    with open('avisos_ipma.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print(f"[IPMA] Operação concluída. {len(funcionalidades)} alertas perigosos ativos convertidos para mapa.")

if __name__ == "__main__":
    obter_avisos()
