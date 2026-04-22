import asyncio
import websockets
import json

# Coordenadas do "Retângulo" de Ormuz (Bounding Box)
LAT_MIN, LAT_MAX = 25.8, 27.2
LON_MIN, LON_MAX = 54.5, 56.8

async def capturar_ormuz():
    url = "wss://stream.aisstream.io/v0/stream"
    # Nota: Precisas de uma API Key gratuita de aisstream.io para isto ser 100% estável
    async with websockets.connect(url) as websocket:
        subscribe_msg = {
            "APIKey": "19b79b667ee38f6aa3e13c5749c962d73fbe1348", # Obtém em aisstream.io
            "BoundingBoxes": [[[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]]]
        }
        await websocket.send(json.dumps(subscribe_msg))

        navios = {}
        try:
            # Captura dados por 30 segundos para encher o mapa
            async for message in websocket:
                data = json.loads(message)
                if "MetaData" in data:
                    mmsi = data["MetaData"]["MMSI"]
                    navios[mmsi] = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [data["MetaData"]["Longitude"], data["MetaData"]["Latitude"]]
                        },
                        "properties": {
                            "nome": data["MetaData"]["ShipName"].strip(),
                            "tipo": data["MessageType"],
                            "mmsi": mmsi,
                            "timestamp": data["MetaData"]["time_utc"]
                        }
                    }
                if len(navios) > 50: break # Limite de segurança
        except: pass

        geojson = {"type": "FeatureCollection", "features": list(navios.values())}
        with open("navios_ormuz.geojson", "w") as f:
            json.dump(geojson, f)

if __name__ == "__main__":
    asyncio.run(capturar_ormuz())
