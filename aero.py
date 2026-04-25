import urllib.request
import json
import os

# URL da API para voos militares do adsb.lol
URL_API = "https://api.adsb.lol/v2/mil"

def rastrear_voos():
    print("A iniciar o rastreio de tráfego aéreo militar...")
    
    # 1. Fazer o pedido à API (Fingimos ser um browser normal)
    req = urllib.request.Request(URL_API, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            dados_brutos = json.loads(response.read().decode())
    except Exception as e:
        print(f"Erro ao ligar ao radar: {e}")
        return

    # Extrair a lista de aeronaves
    aeronaves = dados_brutos.get("ac", [])
    print(f"Radares detetaram {len(aeronaves)} aeronaves militares a transmitir sinal.")

    # 2. Estrutura base do GeoJSON (O formato que o ArcGIS entende)
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # 3. Filtrar e extrair as coordenadas
    voos_mapeados = 0
    for aviao in aeronaves:
        # Só nos interessam aviões com posição GPS conhecida (lat e lon)
        if "lat" in aviao and "lon" in aviao:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    # Atenção: GeoJSON exige sempre [Longitude, Latitude] nesta ordem!
                    "coordinates": [aviao["lon"], aviao["lat"]] 
                },
                "properties": {
                    "callsign": aviao.get("flight", "DESCONHECIDO").strip(),
                    "tipo": aviao.get("t", "N/A"),
                    "altitude_pes": aviao.get("alt_baro", "N/A"),
                    "velocidade_nos": aviao.get("gs", "N/A"),
                    "categoria": aviao.get("category", "N/A")
                }
            }
            geojson["features"].append(feature)
            voos_mapeados += 1

    print(f"Foram convertidos {voos_mapeados} voos com posição GPS válida.")

    # 4. Guardar o ficheiro pronto para o mapa
    with open("voos_militares.geojson", "w", encoding="utf-8") as ficheiro:
        json.dump(geojson, ficheiro, indent=4)
    
    print("Sucesso! Ficheiro 'voos_militares.geojson' criado e pronto a usar.")

if __name__ == "__main__":
    rastrear_voos()
