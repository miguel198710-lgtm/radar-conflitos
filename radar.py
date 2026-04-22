import urllib.request
import json
import datetime

print("A iniciar extração no GitHub...")

# O link corrigido (sem caracteres estranhos e com o modo PointData ativado)
url = "https://api.gdeltproject.org/api/v2/geo/geo?query=conflict&mode=PointData&format=geojson"

pedido = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

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

    # Formato exato para o ArcGIS
    geojson_final = {
        "type": "FeatureCollection",
        "features": features_formatadas
    }

    with open("conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson_final, f, ensure_ascii=False, indent=2)

    print("SUCESSO: Relatório conflitos.geojson gerado!")
except Exception as e:
    print("Ocorreu um erro na ligação:", e)
