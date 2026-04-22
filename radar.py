import urllib.request
import json
import datetime
import ssl

print("A iniciar extração no GitHub (Modo Sem Segurança SSL)...")

# O link para a API do GDELT
url = "https://api.gdeltproject.org/api/v2/geo/geo?query=conflict&mode=PointData&format=geojson"

# A MAGIA: Criar um passe livre que ignora falhas de certificados SSL
contexto_inseguro = ssl.create_default_context()
contexto_inseguro.check_hostname = False
contexto_inseguro.verify_mode = ssl.CERT_NONE

pedido = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

try:
    # Usamos o contexto_inseguro para furar o handshake
    resposta = urllib.request.urlopen(pedido, context=contexto_inseguro, timeout=30)
    dados = json.loads(resposta.read().decode('utf-8'))

    features_formatadas = []
    
    # Processar os 50 eventos mais recentes
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

    # Guarda o ficheiro no GitHub
    with open("conflitos.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson_final, f, ensure_ascii=False, indent=2)

    print("SUCESSO ABSOLUTO: Relatório conflitos.geojson gerado e guardado!")
except Exception as e:
    print("Erro critico de ligacao:", e)
