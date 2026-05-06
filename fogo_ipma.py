import requests
import json

def obter_risco_incendio():
    print("[IPMA RCM] A preparar extração tática de Risco de Incêndio...")
    
    ESCALA_RISCO = {
        1: "Reduzido", 2: "Moderado", 3: "Elevado", 4: "Muito Elevado", 5: "Máximo"
    }
    concelhos = {}
    
    # O Risco de Incêndio do IPMA costuma ter apenas Hoje (0) e Amanhã (1)
    dias_api = {0: "hoje", 1: "amanha"} 

    try:
        for id_dia, nome_dia in dias_api.items():
            url = f"https://api.ipma.pt/open-data/forecast/meteorology/rcm/rcm-d{id_dia}.json"
            print(f"A varrer dados de incendio para: {nome_dia}...")
            
            resposta = requests.get(url)
            if resposta.status_code != 200:
                print(f"[AVISO] Sem dados para {nome_dia} (Status {resposta.status_code}).")
                continue
                
            dados = resposta.json()
            data_referencia = dados.get("fileDate", "Data Desconhecida")[:10] 
            
            # TÁTICA DE ADAPTAÇÃO: O IPMA pode devolver uma lista ou um dicionário
            conteudo = dados.get("data", [])
            lista_locais = list(conteudo.values()) if isinstance(conteudo, dict) else conteudo

            if not lista_locais:
                print(f"[AVISO] O ficheiro de {nome_dia} veio vazio da parte do IPMA!")
                continue

            for local in lista_locais:
                # Procurar o código do concelho seja qual for o nome que o IPMA lhe deu hoje
                dico = str(local.get("dico", "") or local.get("idAreaAviso", ""))
                if not dico: 
                    continue
                
                # Caça às coordenadas: tenta "latitude", se não houver tenta "lat"
                lat = local.get("latitude") or local.get("lat") or 0
                lon = local.get("longitude") or local.get("lon") or 0
                
                if dico not in concelhos:
                    concelhos[dico] = {
                        "lat": float(lat),
                        "lon": float(lon),
                        "previsoes": {}
                    }
                
                # Caça ao nível de risco
                nivel_risco = local.get("rcm") or local.get("risco") or 1
                concelhos[dico]["previsoes"][nome_dia] = {
                    "nivel_numero": int(nivel_risco),
                    "descricao": ESCALA_RISCO.get(int(nivel_risco), "Desconhecido"),
                    "data": data_referencia
                }

        # Montar o GeoJSON Final
        funcionalidades = []
        for dico, info in concelhos.items():
            # Só ignoramos se as coordenadas vierem mesmo a Zeros
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
