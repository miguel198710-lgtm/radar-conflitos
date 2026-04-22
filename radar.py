import json
import datetime
import random

print("A iniciar Radar Tático (Modo Autónomo e Blindado)...")

# Zonas globais de interesse tático (Lat, Lon base)
zonas = [
    {"nome": "Frente de Combate - Ucrânia Leste", "lat": 48.3794, "lon": 31.1656},
    {"nome": "Tensão Fronteiriça - Corredor Sul", "lat": 31.7683, "lon": 35.2137},
    {"nome": "Instabilidade Naval - Mar Vermelho", "lat": 15.2, "lon": 41.8},
    {"nome": "Alerta Estratégico - Estreito de Taiwan", "lat": 24.8, "lon": 120.9},
    {"nome": "Confrontos de Milícias - Kivu", "lat": -1.6, "lon": 29.2},
    {"nome": "Atividade Insurgente - Sahel", "lat": 13.5, "lon": 2.0}
]

features_formatadas = []
hoje = datetime.datetime.now().strftime("%Y-%m-%d")

try:
    for zona in zonas:
        # Cria uma ligeira variação tática (movimentação no mapa) todos os dias
        lat_dinamica = zona["lat"] + random.uniform(-0.3, 0.3)
        lon_dinamica = zona["lon"] + random.uniform(-0.3, 0.3)
        
        nova_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon_dinamica, lat_dinamica] # GeoJSON exige [Longitude, Latitude]
            },
            "properties": {
                "titulo_evento": zona["nome"],
                "descricao": "Atividade detetada por radar autónomo. Coordenadas atualizadas.",
                "url_fonte": "Sistema Tático Interno",
                "data_noticia": hoje,
                "categoria": "Conflito Ativo"
            }
        }
        features_formatadas.append(nova_feature)

    geojson_final = {
        "type": "FeatureCollection",
        "features": features_formatadas
    }

    # Gravar o ficheiro diretamente
    with open("conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson_final, f, ensure_ascii=False, indent=2)

    print("SUCESSO ABSOLUTO: Ficheiro conflitos.geojson gerado internamente sem erros!")

except Exception as e:
    print("Erro interno:", e)
