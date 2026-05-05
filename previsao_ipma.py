import requests
import json

def obter_previsao():
    print("[IPMA] A preparar cruzamento de dados...")
    
    # 1. Vamos buscar a lista oficial de IDs e Nomes de Cidades ao IPMA
    url_locais = "https://api.ipma.pt/open-data/distrits-islands.json"
    resp_locais = requests.get(url_locais).json()
    
    # Criar um dicionário automático (Ex: 1110600 -> "Lisboa")
    mapa_locais = {}
    for local in resp_locais["data"]:
        mapa_locais[local["globalIdLocal"]] = local["local"]

    # 2. Vamos buscar a Previsão para HOJE (idDay = 0, conforme a tua imagem)
    url_previsao = "https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/hp-daily-forecast-day0.json"
    print("[IPMA] A extrair previsão meteorológica de hoje...")
    
    resposta = requests.get(url_previsao)
    dados = resposta.json()
    
    funcionalidades = []
    
    # 3. Montar o mapa ponto a ponto
    for previsao in dados["data"]:
        id_local = previsao.get("globalIdLocal")
        nome_local = mapa_locais.get(id_local, f"Zona {id_local}")
        
        # Extrair as coordenadas que a API felizmente já nos dá
        lat = float(previsao["latitude"])
        lon = float(previsao["longitude"])
        
        funcionalidade = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "local": nome_local,
                "temperatura_max": f"{previsao.get('tMax')} °C",
                "temperatura_min": f"{previsao.get('tMin')} °C",
                "prob_chuva": f"{previsao.get('precipitaProb')} %",
                "direcao_vento": previsao.get("predWindDir"),
                "data": dados.get("forecastDate")
            }
        }
        funcionalidades.append(funcionalidade)

    # 4. Empacotar tudo para a ESRI
    geojson = {
        "type": "FeatureCollection",
        "features": funcionalidades
    }

    with open('previsao_ipma.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print(f"[IPMA] Sucesso! Previsão de hoje guardada para {len(funcionalidades)} distritos/ilhas.")

if __name__ == "__main__":
    obter_previsao()
