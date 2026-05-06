import requests
import json

def obter_risco_incendio():
    print("[IPMA RCM] A iniciar extração de Risco de Incêndio (Estrutura DICO)...")
    
    ESCALA_RISCO = {
        1: "Reduzido", 2: "Moderado", 3: "Elevado", 4: "Muito Elevado", 5: "Máximo"
    }
    concelhos = {}
    dias_api = {0: "hoje", 1: "amanha"} 

    try:
        for id_dia, nome_dia in dias_api.items():
            url = f"https://api.ipma.pt/open-data/forecast/meteorology/rcm/rcm-d{id_dia}.json"
            print(f"A varrer dados de incendio para: {nome_dia}...")
            
            resposta = requests.get(url)
            if resposta.status_code != 200:
                print(f"[AVISO] Sem dados para {nome_dia}.")
                continue
                
            dados = resposta.json()
            data_referencia = dados.get("fileDate", "Data Desconhecida")[:10] 
            
            # O SEGREDO 1: O IPMA guarda a info de incêndios na chave "local"
            dicionario_locais = dados.get("local", {})
            if not dicionario_locais:
                dicionario_locais = dados.get("data", dados) # Plano B
                
            # Converter os dicionários dos concelhos (ex: {"0101": {...}}) numa lista
            lista_locais = list(dicionario_locais.values()) if isinstance(dicionario_locais, dict) else dicionario_locais

            if not lista_locais:
                print(f"[AVISO] Ficheiro de {nome_dia} estruturalmente vazio!")
                continue

            for info_local in lista_locais:
                if not isinstance(info_local, dict): 
                    continue

                dico = str(info_local.get("dico", ""))
                if not dico: 
                    continue
                
                lat = info_local.get("latitude") or info_local.get("lat") or 0
                lon = info_local.get("longitude") or info_local.get("lon") or 0
                
                if dico not in concelhos:
                    concelhos[dico] = {
                        "lat": float(lat),
                        "lon": float(lon),
                        "previsoes": {}
                    }
                
                # O SEGREDO 2: O valor de RCM está noutro sub-bloco "data"
                nivel_risco = 1
                if "data" in info_local and isinstance(info_local["data"], dict):
                    nivel_risco = info_local["data"].get("rcm", 1)
                else:
                    nivel_risco = info_local.get("rcm", 1)
                    
                concelhos[dico]["previsoes"][nome_dia] = {
                    "nivel_numero": int(nivel_risco),
                    "descricao": ESCALA_RISCO.get(int(nivel_risco), "Desconhecido"),
                    "data": data_referencia
                }

        # Montar o GeoJSON Final
        funcionalidades = []
        for dico, info in concelhos.items():
            if info["lat"] == 0 and info["lon"] == 0:
                continue
                
            propriedades = {"dico": dico}
            for dia, prev in info["previsoes"].items():
                propriedades[f"data_{dia}"] = prev["data"]
                propriedades[f"risco_num_{dia}"] = prev["nivel_numero"]
                propriedades[f"risco_desc_{dia}"] = prev["descricao"]

            funcionalidades.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [info["lon"], info["lat"]]
                },
                "properties": propriedades
            })

        with open('risco_incendio.geojson', 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "features": funcionalidades}, f, ensure_ascii=False, indent=2)
            
        print(f"[SUCESSO] Mapa de Incêndios gerado! Foram mapeados {len(funcionalidades)} concelhos.")

    except Exception as e:
        print(f"[ERRO CRÍTICO no RCM]: {e}")

if __name__ == "__main__":
    obter_risco_incendio()
