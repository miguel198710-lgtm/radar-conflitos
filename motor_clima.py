import json
import datetime
from datetime import timedelta
import earthkit.data as ek

def gerar_clima():
    print("[SATÉLITE] A iniciar ligação segura aos servidores do Copernicus (ECMWF)...")

    # 1. Ler os países
    try:
        with open('paises.json', 'r', encoding='utf-8') as f:
            paises = json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler paises.json: {e}")
        return

    # AVISO TÁTICO: O modelo ERA5 gratuito (Reanalysis) tem um atraso de segurança de 5 dias.
    # Para o código não falhar a pedir dados "do futuro", usamos a data de há 5 dias.
    # (Quando quiseres dados em tempo real puro, mudas o dataset para "forecasts")
    data_alvo = (datetime.datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

    # 2. Descarregar os dados globais do Copernicus
    print(f"[SATÉLITE] A pedir modelo atmosférico para {data_alvo}. Pode demorar uns minutos dependendo da fila de espera da Europa...")
    
    try:
        dados_clima = ek.from_source(
            "cds",
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": ["2m_temperature", "10m_u_component_of_wind", "10m_v_component_of_wind"],
                "date": data_alvo,
                "time": "12:00",
                "format": "grib"
            }
        )
        print("[SATÉLITE] GRIB Atmosférico descarregado com sucesso! A cruzar coordenadas...")
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha na comunicação com o Copernicus. Verifica os Secrets no GitHub. Erro: {e}")
        return

    features = []
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Varrer cada país e extrair o ponto exato do globo
    for pais in paises:
        try:
            # O earthkit espeta uma "agulha" no ficheiro global na coordenada exata
            pontos = dados_clima.to_points(latitudes=[pais["lat"]], longitudes=[pais["lon"]])
            
            # Extrair Temperatura (vem em Kelvin, subtraímos 273.15 para Celsius)
            temp_k = pontos["2m_temperature"][0] 
            temp_c = round(temp_k - 273.15, 1)

            # Extrair Vento (O Copernicus dá o vento em dois vetores, U e V. Usamos Pitágoras para a velocidade real)
            u_wind = pontos["10m_u_component_of_wind"][0]
            v_wind = pontos["10m_v_component_of_wind"][0]
            vento_ms = (u_wind**2 + v_wind**2) ** 0.5
            vento_kts = round(vento_ms * 1.94384, 1) # Converter metros/segundo para Nós (Knots)

            print(f"[OK] {pais['nome']}: {temp_c}ºC | {vento_kts} Nós")

        except Exception as e:
            print(f"[AVISO] Falha ao extrair telemetria para {pais['nome']}: {e}")
            temp_c = 0.0
            vento_kts = 0.0

        # Montar o ponto do mapa
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

    # 4. Montar e Guardar o GeoJSON final
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open('clima_global.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print("[SATÉLITE] Ficheiro clima_global.geojson atualizado com DADOS REAIS!")

if __name__ == "__main__":
    gerar_clima()
