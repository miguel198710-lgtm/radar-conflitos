from flask import Flask, jsonify
import urllib.request
import json

app = Flask(__name__)
URL_API = "https://api.adsb.lol/v2/mil"

@app.route('/voos_militares.geojson')
def get_voos():
    req = urllib.request.Request(URL_API, headers={'User-Agent': 'Mozilla/5.0'})
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
                    "tipo": aviao.get("t", "N/A"),
                    "altitude_pes": aviao.get("alt_baro", 0),
                    "velocidade_nos": aviao.get("gs", 0)
                }
            })
    return jsonify(geojson)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
