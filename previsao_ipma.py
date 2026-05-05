import requests
import json

def obter_previsao_3dias():
    print("[IPMA] A preparar cruzamento de dados táticos (com iconografia)...")
    
    # 1. Nomes das Cidades
    url_locais = "https://api.ipma.pt/open-data/distrits-islands.json"
    resp_locais = requests.get(url_locais).json()
    mapa_locais = {local["globalIdLocal"]: local["local"] for local in resp_locais["data"]}

    # 2. O Dicionário de Tempo (Ex: 1 -> "Céu limpo")
    url_tipos = "https://api.ipma.pt/open-data/weather-type-classe.json"
    resp_tipos = requests.get(url_tipos).json()
    mapa_tempo = {tipo["idWeatherType"]: tipo["descIdWeatherTypePT"] for tipo in resp_tipos["data"]}

    cidades = {}
    dias_api = {0: "hoje", 1: "amanha", 2: "depois"}

    # 3. Fazer 3 rondas
    for id_dia, nome_dia in dias_api.items():
        url = f"https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/hp-daily-forecast-day{id_dia}.json"
        
        dados = requests.get(url).json()
        
        # AQUI ESTÁ A CORREÇÃO: Puxar a data do topo do ficheiro (cabeçalho geral)
        data_oficial = dados.get("forecastDate", "Data Desconhecida")
        
        for previsao in dados["data"]:
            id_local = previsao.get("globalIdLocal")
            
            if id_local not in cidades:
                cidades[id_local] = {
                    "nome": mapa_locais.get(id_local, f"Zona {id_local}"),
                    "lat": float(previsao["latitude"]),
                    "lon": float(previsao["longitude"]),
                    "previsoes": {}
                }
            
            # Cruzar o ID do tempo com a descrição em Português
            id_tempo = previsao.get("idWeatherType")
            desc_tempo = mapa_tempo.get(id_tempo, "Desconhecido")
            
            cidades[id_local]["previsoes"][nome_dia] = {
                "tMax": previsao.get("tMax"),
                "tMin": previsao.get("tMin"),
                "prob_chuva": previsao.get("precipitaProb"),
                "estado_tempo": desc_tempo,
                "data": data_oficial # Agora já vai injetar a data corretamente!
            }

    # 4. Montar o GeoJSON
    funcionalidades = []
    
    for id_local, dados_cidade in cidades.items():
        propriedades = {"local": dados_cidade["nome"]}
        
        for nome_dia, prev in dados_cidade["previsoes"].items():
            propriedades[f"data_{nome_dia}"] = prev.get("data")
            propriedades[f"temp_max_{nome_dia}"] = f"{prev.get('tMax')} °C"
            propriedades[f"temp_min_{nome_dia}"] = f"{prev.get('tMin')} °C"
            propriedades[f"prob_chuva_{nome_dia}"] = f"{prev.get('prob_chuva')} %"
            propriedades[f"estado_{nome_dia}"] = prev.get("estado_tempo")

        funcionalidade = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [dados_cidade["lon"], dados_cidade["lat"]]
            },
            "properties": propriedades
        }
        funcionalidades.append(funcionalidade)

    # 5. Gravar
    geojson = {
        "type": "FeatureCollection",
        "features": funcionalidades
    }

    with open('previsao_ipma.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print(f"[IPMA] Mapa atualizado! Datas corrigidas e propriedades visuais prontas.")

if __name__ == "__main__":
    obter_previsao_3dias()
