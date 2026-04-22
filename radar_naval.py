import asyncio
import websockets
import json
import datetime
import sys

async def capturar_navios():
    api_key = "19b79b667ee38f6aa3e13c5749c962d73fbe1348" # GARANTE QUE ESTÁ CERTA
    url = "wss://stream.aisstream.io/v0/stream"
    
    # Bounding box de Ormuz
    bbox = [[25.0, 54.0], [28.0, 57.5]]
    navios_detectados = {}

    print("Tentando ligar ao radar naval...")
    
    try:
        # TIMEOUT GLOBAL: Se em 40 segundos não acabar, o script fecha à força
        async with asyncio.timeout(40):
            async with websockets.connect(url) as websocket:
                subscribe_msg = {
                    "APIKey": api_key,
                    "BoundingBoxes": [bbox],
                    "FilterMessageTypes": ["PositionReport"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                print("Ligação estabelecida. Aguardando sinais...")

                start_time = datetime.datetime.now()
                # Tenta colher dados durante 20 segundos
                while (datetime.datetime.now() - start_time).seconds < 20:
                    try:
                        # Se não recebermos uma mensagem individual em 10s, saímos
                        message = await asyncio.wait_for(websocket.recv(), timeout=10)
                        data = json.loads(message)
                        
                        if "MetaData" in data:
                            mmsi = data["MetaData"]["MMSI"]
                            navios_detectados[mmsi] = {
                                "type": "Feature",
                                "geometry": {"type": "Point", "coordinates": [data["MetaData"]["Longitude"], data["MetaData"]["Latitude"]]},
                                "properties": {
                                    "nome": data["MetaData"].get("ShipName", "Desconhecido").strip(),
                                    "mmsi": mmsi,
                                    "ultima_actualizacao": datetime.datetime.now().strftime("%H:%M:%S")
                                }
                            }
                    except asyncio.TimeoutError:
                        print("Sem mensagens novas nos últimos 10s. A encerrar recolha...")
                        break
    except Exception as e:
        print(f"Aviso: O radar naval parou ou expirou: {e}")

    # Grava o ficheiro MESMO que esteja vazio (para o GitHub não dar erro no passo seguinte)
    geojson = {"type": "FeatureCollection", "features": list(navios_detectados.values())}
    with open("navios_ormuz.geojson", "w") as f:
        json.dump(geojson, f, indent=2)
    
    print(f"Processo terminado. Navios encontrados: {len(navios_detectados)}")

if __name__ == "__main__":
    asyncio.run(capturar_navios())
