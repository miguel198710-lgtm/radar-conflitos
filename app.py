from flask import Flask, jsonify
import urllib.request
import json
import threading
import websocket

app = Flask(__name__)

# --- CONFIGURAÇÕES AÉREAS ---
URL_VOOS = "https://api.adsb.lol/v2/mil"

# --- CONFIGURAÇÕES MARÍTIMAS ---
API_KEY_AIS = "7c942600ec42daa2f56ccf5446026ef31e67dfbb" 

navios_militares_mmsi = set() 
navios_buffer = {} 

# Motor de Descodificação de Bandeiras (MIDs principais)
def identificar_pais(mmsi):
    if len(mmsi) < 3: return "Desconhecido"
    mid = mmsi[:3]
    paises = {
        "263": "Portugal", "204": "Portugal (Açores)", "255": "Portugal (Madeira)",
        "235": "Reino Unido", "232": "Reino Unido", "233": "Reino Unido", "234": "Reino Unido",
        "338": "EUA", "366": "EUA", "367": "EUA", "368": "EUA", "369": "EUA",
        "273": "Rússia", "272": "Ucrânia",
        "412": "China", "413": "China", "414": "China",
        "227": "França", "228": "França",
        "224": "Espanha", "247": "Itália", "211": "Alemanha", "218": "Alemanha",
        "316": "Canadá", "503": "Austrália", "431": "Japão",
        "419": "Índia", "422": "Irão", "428": "Israel", "455": "Maldivas"
    }
    return paises.get(mid, f"Outro (MID: {mid})")

def processar_stream_maritimo(ws, message):
    try:
        data = json.loads(message)
        msg_type = data.get("MessageType")

        # 1. Bilhetes de Identidade (Agora extrai Destino e Callsign)
        if msg_type == "ShipStaticData":
            msg = data.get("Message", {}).get("ShipStaticData", {})
            mmsi = str(msg.get("UserID"))
            ship_type = msg.get("Type", 0)
            nome = msg.get("Name", "").strip()
            
            # Novos Atributos
            destino = msg.get("Destination", "PATRULHA/DESCONHECIDO").strip()
            callsign = msg.get("CallSign", "N/A").strip()

            if ship_type in [35, 55] or nome.startswith(("USS ", "HMS ", "WARSHIP", "NRP ", "FGS ")):
                navios_militares_mmsi.add(mmsi)
                # Atualiza ou cria o registo
                if mmsi not in navios_buffer:
                    navios_buffer[mmsi] = {"lat": 0, "lon": 0, "velocidade": 0, "rumo": 0}
                
                navios_buffer[mmsi]["nome"] = nome
                navios_buffer[mmsi]["tipo_id"] = ship_type
                navios_buffer[mmsi]["destino"] = destino
                navios_buffer[mmsi]["callsign"] = callsign
                navios_buffer[mmsi]["pais"] = identificar_pais(mmsi)

        # 2. Posições GPS
        elif msg_type == "PositionReport":
            msg = data.get("Message", {}).get("PositionReport", {})
            mmsi = str(msg.get("UserID"))

            if mmsi in navios_militares_mmsi:
                lat = msg.get("Latitude")
                lon = msg.get("Longitude")
                if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                    # Garantir que a estrutura existe antes de atualizar
                    if mmsi not in navios_buffer:
                        navios_buffer[mmsi] = {"nome": "Desconhecido", "destino": "N/A", "callsign": "N/A", "pais": identificar_pais(mmsi)}
                    
                    navios_buffer[mmsi]["lat"] = lat
                    navios_buffer[mmsi]["lon"] = lon
                    navios_buffer[mmsi]["velocidade"] = msg.get("Sog", 0)
                    navios_buffer[mmsi]["rumo"] = msg.get("TrueHeading", 0)
    except Exception:
        pass

def iniciar_radar_naval():
    cobertura_global = [[[-90, -180], [90, 180]]]
    mensagem_subscricao = {
        "APIKey": API_KEY_AIS,
        "BoundingBoxes": cobertura_global,
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
    }
    
    def on_open(ws):
        print("Radar Naval Global Otimizado Ativado.")
        ws.send(json.dumps(mensagem_subscricao))
        
    while True:
        try:
            ws = websocket.WebSocketApp("wss://stream.aisstream.io/v0/stream",
                                        on_message=processar_stream_maritimo,
                                        on_open=on_open)
            ws.run_forever()
        except:
            pass

threading.Thread(target=iniciar_radar_naval, daemon=True).start()

# --- ROTAS DE SAÍDA ---
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
                "geometry": {"type": "Point", "coordinates": [aviao["lon"], aviao["lat"]]},
                "properties": {
                    "callsign": aviao.get("flight", "DESCONHECIDO").strip(),
                    "tipo": aviao.get("t", "N/A"),
                    "altitude_pes": aviao.get("alt_baro", 0),
                    "velocidade_nos": aviao.get("gs", 0)
                }
            })
    return jsonify(geojson)

@app.route('/navios.geojson')
def get_navios():
    features = []
    
    # 1. A Sonda de Calibração (Garante que o ArcGIS nunca vê um ficheiro vazio)
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
        "properties": {
            "Nome_Navio": "Sonda de Calibração C4ISR",
            "Pais": "Sistema",
            "Destino": "Ponto Zero",
            "Callsign_Radio": "PING",
            "MMSI": "000000000",
            "Velocidade_Nos": 0,
            "Rumo": 0
        }
    })

    # 2. A Frota Real (Abaixo da sonda)
    frota_atual = list(navios_buffer.items())
    for mmsi, dados in frota_atual:
        if dados.get("lat", 0) != 0 and dados.get("lon", 0) != 0:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [dados["lon"], dados["lat"]]},
                "properties": {
                    "Nome_Navio": dados.get("nome", "A aguardar identificação..."),
                    "Pais": dados.get("pais", "Desconhecido"),
                    "Destino": dados.get("destino", "N/A"),
                    "Callsign_Radio": dados.get("callsign", "N/A"),
                    "MMSI": mmsi,
                    "Velocidade_Nos": dados.get("velocidade", 0),
                    "Rumo": dados.get("rumo", 0)
                }
            })
            
    return jsonify({"type": "FeatureCollection", "features": features})
