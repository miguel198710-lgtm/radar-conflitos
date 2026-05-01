from flask import Flask, jsonify
import urllib.request
import json
import math # Precisamos da biblioteca de matemática

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
URL_VOOS = "https://api.adsb.lol/v2/mil"

# --- MEMÓRIA TÁTICA ---
historico_voos = {}

# --- FUNÇÃO PARA CALCULAR RUMO (AZIMUTE) ---
def calcular_rumo(lat1, lon1, lat2, lon2):
    """Calcula a direção em graus (0-360) entre duas coordenadas."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dLon = lon2 - lon1
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    brng = math.degrees(math.atan2(y, x))
    return (brng + 360) % 360

def atualizar_memoria_voos():
    req = urllib.request.Request(URL_VOOS, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            dados = json.loads(response.read().decode())
            for aviao in dados.get("ac", []):
                hex_id = aviao.get("hex", "000000")
                if "lat" in aviao and "lon" in aviao:
                    
                    if hex_id not in historico_voos:
                        historico_voos[hex_id] = {
                            "rasto": [], 
                            "callsign": aviao.get("flight", "DESCONHECIDO").strip(),
                            "tipo": aviao.get("t", "N/A"),
                            "hex": hex_id,
                            "rumo": 0 # Rumo inicial padrão
                        }
                    
                    # Guarda a posição anterior antes de adicionar a nova
                    posicoes_anteriores = len(historico_voos[hex_id]["rasto"])
                    if posicoes_anteriores > 0:
                        lon_ant, lat_ant = historico_voos[hex_id]["rasto"][-1]
                    
                    # Atualiza Rasto
                    historico_voos[hex_id]["rasto"].append([aviao["lon"], aviao["lat"]])
                    
                    # --- LÓGICA INFALÍVEL PARA O RUMO ---
                    # 1. Tenta ir buscar o rumo da API ("track", "true_heading" ou "mag_heading")
                    rumo_api = aviao.get("track") or aviao.get("true_heading") or aviao.get("mag_heading")
                    
                    if rumo_api is not None:
                        # Se a API der o rumo, usamos esse
                        historico_voos[hex_id]["rumo"] = float(rumo_api)
                    elif posicoes_anteriores > 0:
                        # Se a API falhar, MAS tivermos pelo menos a posição anterior, calculamos nós!
                        historico_voos[hex_id]["rumo"] = calcular_rumo(lat_ant, lon_ant, aviao["lat"], aviao["lon"])
                    
                    # Atualiza Identificação
                    historico_voos[hex_id]["callsign"] = aviao.get("flight", "DESCONHECIDO").strip()
                    historico_voos[hex_id]["tipo"] = aviao.get("t", "N/A")
                    
                    # DADOS TELEMÉTRICOS EXATOS
                    historico_voos[hex_id]["alt_pes"] = aviao.get("alt_baro", 0)
                    historico_voos[hex_id]["vel"] = aviao.get("gs", 0) 
                    historico_voos[hex_id]["squawk"] = str(aviao.get("squawk") or "NONE")
                    
                    if len(historico_voos[hex_id]["rasto"]) > 15:
                        historico_voos[hex_id]["rasto"].pop(0)
    except Exception as e:
        print(f"Erro de radar: {e}")


# --- ROTAS DA API ---
@app.route('/voos_militares.geojson')
def get_voos():
    atualizar_memoria_voos()
    features = []
    for hex_id, dados in historico_voos.items():
        if len(dados["rasto"]) > 0:
            pos_atual = dados["rasto"][-1]
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": pos_atual},
                "properties": {
                    "callsign": dados["callsign"],
                    "tipo": dados["tipo"],
                    "hex": dados["hex"],
                    "altitude_pes": dados["alt_pes"],
                    "velocidade_nos": dados["vel"],
                    "rumo": dados["rumo"]                    
                }
            })
    return jsonify({"type": "FeatureCollection", "features": features})

@app.route('/rastos_voos.geojson')
def get_rastos_voos():
    features = []
    for hex_id, dados in historico_voos.items():
        if len(dados["rasto"]) > 1:
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": dados["rasto"]},
                "properties": {"callsign": dados["callsign"]}
            })
    return jsonify({"type": "FeatureCollection", "features": features})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
