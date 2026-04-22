import urllib.request
import json
import datetime

print("A iniciar extração no GitHub...")
url = "https://api.gdeltproject.org/api/v2/geo/geo?query=(conflict%20OR%20military)&format=geojson"
pedido = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    resposta = urllib.request.urlopen(pedido, timeout=20)
    dados = json.loads(resposta.read().decode('utf-8'))

    features_formatadas = []
    # Vamos extrair os 50 conflitos mais recentes
    for evento in dados.get('features', [])[:50]:
        props = evento.get('properties', {})
        nova_feature = {
            "type": "Feature",
            "geometry": evento.get('geometry'),
            "properties": {
                "titulo_evento": props.get('name', 'Conflito Registado'),
                "descricao": "Fonte: Radar GDELT",
                "url_fonte": props.get('url', ''),
                "data_noticia": datetime.datetime.now().strftime("%Y-%m-%d"),
                "categoria": "Conflito Ativo"
            }
        }
        features_formatadas.append(nova_feature)

    # Prepara o formato exato que o ArcGIS Online exige
    geojson_final = {
        "type": "FeatureCollection",
        "features": features_formatadas
    }

    # Guarda o ficheiro no próprio GitHub
    with open("conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson_final, f, ensure_ascii=False, indent=2)

    print("Relatório conflitos.geojson gerado com sucesso!")
except Exception as e:
    print("Ocorreu um erro:", e)
