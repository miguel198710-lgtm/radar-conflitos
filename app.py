from flask import Flask, jsonify
import urllib.request
import json
import threading
import websocket

app = Flask(__name__)

# --- CONFIGURAÇÕES AÉREAS ---
URL_VOOS = "https://api.adsb.lol/v2/mil"

# --- CONFIGURAÇÕES MARÍTIMAS ---
# COLA A TUA CHAVE DENTRO DAS ASPAS ABAIXO:
API_KEY_AIS = "7c942600ec42daa2f56ccf5446026ef31e67dfbb" 
navios_buffer = {} # Memória do radar

def processar_stream_maritimo(ws, message):
    try:
        data = json.loads(message)
        if data.get("MessageType") == "PositionReport":
            report = data["Message"]["PositionReport"]
            mmsi = str(report["UserID"])
            lat = report["Latitude"]
            lon = report["Longitude"]
            
            # Filtro tático: só regista coordenadas GPS válidas
            if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                navios_buffer[mmsi] = {
                    "lat": lat,
                    "lon": lon,
                    "velocidade": report["Sog"],
                    "rumo": report["TrueHeading"]
                }
    except Exception:
        pass

def iniciar_radar_naval():
    # Zona de Operações (Europa e Atlântico). 
    # Global consome muita RAM, filtramos o Atlântico Norte e o Mediterrâneo.
    zona_operacoes = [[[20, -40], [75, 45]]] 
    
    mensagem_subscricao = {
        "APIKey": API_KEY_AIS,
        "BoundingBoxes": zona_operacoes,
        "FilterMessageTypes": ["PositionReport"]
    }
    
    def on_open(ws):
        ws.send(json.dumps(mensagem_subscricao))
        
    # Mantém o radar sempre a tentar reconectar se o sinal cair
    while True:
        try:
            ws = websocket.WebSocketApp("wss://stream.aisstream.io/v0/stream",
                                        on_message=processar_stream_maritimo,
                                        on_open=on_open)
            ws.run_forever()
        except:
            pass

# Ligar o radar marítimo nos bastidores
threading.Thread(target=iniciar_radar_naval, daemon=True).start()

# --- AS DUAS VIAS DE SAÍDA DE DADOS ---

# 1. Rota dos Aviões
@app.route('/voos_militares.geojson')
def get_voos():
    req = urllib.request.Request(URL_VOOS, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            dados = json.loads(response.read().decode())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    geojson = {"type": "FeatureCollection", "features": []}
    for aviao in dados.get("ac", []):
        if "lat" in aviao and "lon" in aviao:
            geojson["features"].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [aviao["lon"], aviao["lat"]]
                },
                "properties": {
                    "callsign": aviao.get("flight", "DESCONHECIDO").strip(),
                    "tipo": aviao.get("t", "N/A")
                }
            })
    return jsonify(geojson)

# 2. Rota dos Navios
@app.route('/navios.geojson')
def get_navios():
    features = []
    # Copiar a frota para não travar o fluxo de rádio em tempo real
    frota_atual = list(navios_buffer.items())
    
    for mmsi, dados in frota_atual:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [dados["lon"], dados["lat"]]
            },
            "properties": {
                "MMSI": mmsi,
                "Velocidade_Nos": dados["velocidade"],
                "Rumo": dados["rumo"]
            }
        })
    return jsonify({"type": "FeatureCollection", "features": features})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
