from flask import Flask, jsonify
import urllib.request
import json

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
URL_VOOS = "https://api.adsb.lol/v2/mil"

# --- MEMÓRIA TÁTICA ---
historico_voos = {}

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
                            "hex": hex_id
                        }
                    
                    # Atualiza Rasto e Identificação
                    historico_voos[hex_id]["rasto"].append([aviao["lon"], aviao["lat"]])
                    historico_voos[hex_id]["callsign"] = aviao.get("flight", "DESCONHECIDO").strip()
                    historico_voos[hex_id]["tipo"] = aviao.get("t", "N/A")
                    
                    # DADOS TELEMÉTRICOS EXATOS
                    historico_voos[hex_id]["alt_pes"] = aviao.get("alt_baro", 0)
                    historico_voos[hex_id]["vel"] = aviao.get("gs", 0) # Ground Speed (Nós)
                    historico_voos[hex_id]["rumo"] = aviao.get("track", 0) # Heading (Graus)
                    historico_voos[hex_id]["squawk"] = str(aviao.get("squawk") or "NONE") # Transponder
                    
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
