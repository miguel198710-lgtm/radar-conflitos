import requests
import json

def obter_previsao_3dias():
    print("[IPMA] A preparar dados com IDs para SVGs oficiais...")
    
    try:
        # 1. Nomes das Cidades
        url_locais = "https://api.ipma.pt/open-data/distrits-islands.json"
        mapa_locais = {local["globalIdLocal"]: local["local"] for local in requests.get(url_locais).json()["data"]}

        # 2. Descrições de Tempo (CORREÇÃO AQUI: Código mais robusto)
        url_tipos = "https://api.ipma.pt/open-data/weather-type-classe.json"
        tipos_data = requests.get(url_tipos).json()["data"]
        
        # Tentamos ler a descrição em PT, se falhar usamos um valor padrão
        mapa_tempo = {}
        for tipo in tipos_data:
            id_t = tipo.get("idWeatherType")
            # Procura por 'descIdWeatherTypePT' ou 'descIdWeatherTypeEN' ou deixa vazio
            desc = tipo.get("descIdWeatherTypePT") or tipo.get("descIdWeatherTypeEN") or "Estado do tempo"
            mapa_tempo[id_t] = desc

        cidades = {}
        dias_api = {0: "hoje", 1: "amanha", 2: "depois"}

        for id_dia, nome_dia in dias_api.items():
            url = f"https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/hp-daily-forecast-day{id_dia}.json"
            dados = requests.get(url).json()
            data_oficial = dados.get("forecastDate", "")
            
            for previsao in dados["data"]:
                id_local = previsao.get("globalIdLocal")
                if id_local not in cidades:
                    cidades[id_local] = {
                        "nome": mapa_locais.get(id_local, f"ID {id_local}"), 
                        "lat": float(previsao["latitude"]), 
                        "lon": float(previsao["longitude"]), 
                        "previsoes": {}
                    }
                
                id_tempo = previsao.get("idWeatherType")
                cidades[id_local]["previsoes"][nome_dia] = {
                    "tMax": previsao.get("tMax"), 
                    "tMin": previsao.get("tMin"), 
                    "prob": previsao.get("precipitaProb"),
                    "desc": mapa_tempo.get(id_tempo, "Informação indisponível"),
                    "icon_id": id_tempo,
                    "data": data_oficial
                }

        funcionalidades = []
        for id_local, d in cidades.items():
            props = {"local": d["nome"]}
            for dia, prev in d["previsoes"].items():
                props[f"data_{dia}"] = prev["data"]
                props[f"temp_max_{dia}"] = f"{prev['tMax']} °C"
                props[f"temp_min_{dia}"] = f"{prev['tMin']} °C"
                props[f"prob_chuva_{dia}"] = f"{prev['prob']} %"
                props[f"estado_{dia}"] = prev["desc"]
                props[f"icon_{dia}"] = prev["icon_id"]

            funcionalidades.append({
                "type": "Feature", 
                "geometry": {"type": "Point", "coordinates": [d["lon"], d["lat"]]}, 
                "properties": props
            })

        with open('previsao_ipma.geojson', 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "features": funcionalidades}, f, ensure_ascii=False, indent=2)
        
        print("[IPMA] Sucesso! Ficheiro GeoJSON gerado com as correções.")

    except Exception as e:
        print(f"[ERRO CRÍTICO]: {e}")

if __name__ == "__main__":
    obter_previsao_3dias()
