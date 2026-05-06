import requests
import json

def obter_risco_incendio():
    print("[IPMA RCM] A preparar extração tática de Risco de Incêndio...")
    
    # Escala Oficial de Risco de Incêndio do IPMA
    ESCALA_RISCO = {
        1: "Reduzido",
        2: "Moderado",
        3: "Elevado",
        4: "Muito Elevado",
        5: "Máximo"
    }

    # Dicionário para cruzar os dados por DICO (código do concelho)
    concelhos = {}
    dias_api = {0: "hoje", 1: "amanha", 2: "depois"}

    try:
        for id_dia, nome_dia in dias_api.items():
            # O IPMA guarda a info diária nestes ficheiros
            url = f"https://api.ipma.pt/open-data/forecast/meteorology/rcm-d{id_dia}.json"
            print(f"A varrer dados de incêndio para: {nome_dia}...")
            
            resposta = requests.get(url)
            if resposta.status_code != 200:
                print(f"[AVISO] Não foi possível obter dados para {nome_dia}.")
                continue
                
            dados = resposta.json()
            # Puxar apenas a data (YYYY-MM-DD) do ficheiro
            data_referencia = dados.get("fileDate", "Data Desconhecida")[:10] 
            
            for local in dados.get("data", []):
                dico = local.get("dico")
                
                # Se for a primeira vez que vemos este concelho, guardamos as coordenadas
                if dico not in concelhos:
                    concelhos[dico] = {
                        "lat": float(local.get("latitude", 0)),
                        "lon": float(local.get("longitude", 0)),
                        "previsoes": {}
                    }
                
                # Nível de risco vem como número (1 a 5)
                nivel_risco = local.get("rcm", 1) 
                
                concelhos[dico]["previsoes"][nome_dia] = {
                    "nivel_numero": nivel_risco,
                    "descricao": ESCALA_RISCO.get(nivel_risco, "Desconhecido"),
                    "data": data_referencia
                }

        # Montar o GeoJSON Final
        funcionalidades = []
        for dico, info in concelhos.items():
            # Prevenir erros se o IPMA não enviar coordenadas para algum ponto
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

        # Gravar o ficheiro GeoJSON no GitHub
        with open('risco_incendio.geojson', 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "features": funcionalidades}, f, ensure_ascii=False, indent=2)
            
        print(f"[SUCESSO] Mapa de Incêndios gerado! Foram mapeados {len(funcionalidades)} concelhos.")

    except Exception as e:
        print(f"[ERRO CRÍTICO no RCM]: {e}")

if __name__ == "__main__":
    obter_risco_incendio()
