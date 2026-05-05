import json
import datetime
import os
# import earthkit.data as ek  # Ativaremos isto quando as credenciais estiverem no GitHub Secrets

def gerar_clima():
    print("[SATÉLITE] A iniciar varrimento meteorológico global...")

    # 1. Ler os países
    try:
        with open('paises.json', 'r', encoding='utf-8') as f:
            paises = json.load(f)
    except Exception as e:
        print(f"Erro ao ler paises.json: {e}")
        return

    features = []
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. Varrer cada país
    for pais in paises:
        # Quando tiveres a API Key ligada, a chamada real ao Copernicus entra aqui.
        # Exemplo: dados_clima = ek.from_source("cds", dataset="reanalysis-era5-single-levels", ...)
        
        # --- SIMULAÇÃO DE DADOS (Substituir pela leitura real do earthkit) ---
        temp_c = 15.0  
        vento_kts = 12 
        # -------------------------------------------------------------------
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [pais["lon"], pais["lat"]]
            },
            "properties": {
                "pais": pais["nome"],
                "estacao": pais["capital"],
                "temperatura_c": temp_c,
                "vento_kts": vento_kts,
                "atualizado_em": agora
            }
        }
        features.append(feature)

    # 3. Montar GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # 4. Guardar ficheiro
    with open('clima_global.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print("[SATÉLITE] Ficheiro clima_global.geojson gerado com sucesso!")

if __name__ == "__main__":
    gerar_clima()
