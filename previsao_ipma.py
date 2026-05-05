import requests
import json

def obter_previsao_3dias():
    print("[IPMA] A preparar cruzamento de dados para 3 dias...")
    
    # 1. Obter os nomes das cidades
    url_locais = "https://api.ipma.pt/open-data/distrits-islands.json"
    resp_locais = requests.get(url_locais).json()
    mapa_locais = {local["globalIdLocal"]: local["local"] for local in resp_locais["data"]}

    # Dicionário para guardar a info toda agrupada por cidade
    cidades = {}
    
    # Os 3 dias que a API permite
    dias_api = {
        0: "hoje",
        1: "amanha",
        2: "depois"
    }

    # 2. Vamos fazer 3 rondas (uma por cada dia)
    for id_dia, nome_dia in dias_api.items():
        url = f"https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/hp-daily-forecast-day{id_dia}.json"
        print(f"[IPMA] A extrair dados para: {nome_dia}...")
        
        dados = requests.get(url).json()
        
        for previsao in dados["data"]:
            id_local = previsao.get("globalIdLocal")
            
            # Se for a primeira vez que vemos esta cidade, criamos o registo com as coordenadas
            if id_local not in cidades:
                cidades[id_local] = {
                    "nome": mapa_locais.get(id_local, f"Zona {id_local}"),
                    "lat": float(previsao["latitude"]),
                    "lon": float(previsao["longitude"]),
                    "previsoes": {}
                }
            
            # Guardamos a previsão do dia específico dentro da cidade
            cidades[id_local]["previsoes"][nome_dia] = {
                "tMax": previsao.get("tMax"),
                "tMin": previsao.get("tMin"),
                "prob_chuva": previsao.get("precipitaProb"),
                "data": previsao.get("forecastDate")
            }

    # 3. Montar o GeoJSON final
    funcionalidades = []
    
    for id_local, dados_cidade in cidades.items():
        # Vamos criar as propriedades do ponto
        propriedades = {
            "local": dados_cidade["nome"]
        }
        
        # Despejar os 3 dias nas propriedades (ex: temp_max_hoje, temp_max_amanha...)
        for nome_dia, prev in dados_cidade["previsoes"].items():
            propriedades[f"data_{nome_dia}"] = prev.get("data")
            propriedades[f"temp_max_{nome_dia}"] = f"{prev.get('tMax')} °C"
            propriedades[f"temp_min_{nome_dia}"] = f"{prev.get('tMin')} °C"
            propriedades[f"prob_chuva_{nome_dia}"] = f"{prev.get('prob_chuva')} %"

        funcionalidade = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [dados_cidade["lon"], dados_cidade["lat"]]
            },
            "properties": propriedades
        }
        funcionalidades.append(funcionalidade)

    # 4. Gravar o ficheiro
    geojson = {
        "type": "FeatureCollection",
        "features": funcionalidades
    }

    with open('previsao_ipma.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print(f"[IPMA] Triplo sucesso! Previsão de 3 dias guardada para {len(funcionalidades)} locais.")

if __name__ == "__main__":
    obter_previsao_3dias()
