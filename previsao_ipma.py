import requests
import json

def obter_previsao_3dias():
    print("[IPMA] A gerar mapa com dicionário interno (Segurança Máxima)...")
    
    # 1. Dicionário Oficial do IPMA (Hardcoded para nunca falhar)
    DICIONARIO_TEMPO = {
        1: "Céu limpo", 2: "Céu parcialmente nublado", 3: "Céu pouco nublado",
        4: "Céu muito nublado ou encoberto", 5: "Céu nublado", 6: "Aguaceiros/chuva fraca",
        7: "Aguaceiros/chuva moderada", 8: "Aguaceiros/chuva forte", 9: "Chuva/aguaceiros",
        10: "Chuva moderada", 11: "Chuva forte", 12: "Períodos de chuva",
        13: "Períodos de chuva moderada", 14: "Períodos de chuva forte", 15: "Chuvisco",
        16: "Neblina", 17: "Nevoeiro", 18: "Neve", 19: "Trovoada",
        20: "Aguaceiros e trovoadas", 21: "Granizo", 22: "Geada",
        23: "Chuva e neve", 24: "Céu nublado por nuvens altas", 25: "Céu muito nublado",
        26: "Nevoeiro", 27: "Céu nublado", 28: "Céu encoberto"
    }

    try:
        # 2. Nomes das Cidades
        url_locais = "https://api.ipma.pt/open-data/distrits-islands.json"
        mapa_locais = {local["globalIdLocal"]: local["local"] for local in requests.get(url_locais).json()["data"]}

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
                
                id_tempo = int(previsao.get("idWeatherType", 0))
                cidades[id_local]["previsoes"][nome_dia] = {
                    "tMax": previsao.get("tMax"), 
                    "tMin": previsao.get("tMin"), 
                    "prob": previsao.get("precipitaProb"),
                    "desc": DICIONARIO_TEMPO.get(id_tempo, "Estado do tempo"),
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
        
        print("[IPMA] Sucesso total! Agora as descrições estão garantidas.")

    except Exception as e:
        print(f"[ERRO]: {e}")

if __name__ == "__main__":
    obter_previsao_3dias()
