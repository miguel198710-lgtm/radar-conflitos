import json
import datetime
import requests

def gerar_clima():
    print("[SATÉLITE] A iniciar ligação em TEMPO REAL à rede meteorológica global...")

    # 1. Ler os países
    try:
        with open('paises.json', 'r', encoding='utf-8') as f:
            paises = json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler paises.json: {e}")
        return

    features = []
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. Pedir dados em tempo real para cada país
    for pais in paises:
        lat = pais["lat"]
        lon = pais["lon"]
        nome = pais["nome"]
        capital = pais["capital"]

        # Pedido "Sniper" à API pública Open-Meteo (dados instantâneos, unidade de vento já em Nós)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&wind_speed_unit=kn"
        
        try:
            resposta = requests.get(url, timeout=10)
            dados = resposta.json()
            
            # Extrair os dados exatos do momento atual
            temp_c = dados["current"]["temperature_2m"]
            vento_kts = dados["current"]["wind_speed_10m"]
            
            print(f"[OK] {nome} ({capital}): {temp_c}ºC | {vento_kts} Nós")
        except Exception as e:
            print(f"[AVISO] Falha ao extrair telemetria para {nome}: {e}")
            temp_c = 0.0
            vento_kts = 0.0

        # 3. Montar o ponto no mapa
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "pais": nome,
                "estacao": capital,
                "temperatura_c": temp_c,
                "vento_kts": vento_kts,
                "atualizado_em": agora
            }
        }
        features.append(feature)

    # 4. Guardar o mapa final
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open('clima_global.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print("[SATÉLITE] Ficheiro clima_global.geojson atualizado com DADOS EM TEMPO REAL!")

if __name__ == "__main__":
    gerar_clima()
