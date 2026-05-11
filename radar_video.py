import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timedelta

def gerar_html_playlist(lista_videos, nome_ficheiro):
    if not lista_videos:
        print(f"[STATUS] Sem vídeos capturados para {nome_ficheiro}.")
        return
        
    video_principal = lista_videos[0]
    resto_playlist = ",".join(lista_videos[1:])
    url_embed = f"https://www.youtube.com/embed/{video_principal}?playlist={resto_playlist}&autoplay=1&mute=1"
    
    html = f"""<!DOCTYPE html>
    <html>
    <head>
        <style>
            body, html {{margin: 0; padding: 0; height: 100%; background-color: #000; overflow: hidden;}}
            iframe {{width: 100%; height: 100%; border: none;}}
        </style>
    </head>
    <body>
        <iframe src="{url_embed}" allow="autoplay; fullscreen"></iframe>
    </body>
    </html>"""
    
    with open(nome_ficheiro, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  -> [SUCESSO] Emissão {nome_ficheiro} atualizada!")

def radar_video_hibrido():
    print("[OSINT VÍDEO] A iniciar varrimento com Filtro de Inteligência Estruturada...")
    
    API_KEY = os.environ.get("YOUTUBE_API_KEY")
    if not API_KEY:
        print("[ERRO FATAL] Chave de API não encontrada!")
        return
        
    ontem = (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z"
    
    # Contentor para a base de dados GeoJSON
    dados_totais_geojson = []

    CANAIS_CONFIANCA = [
        "UCknLrEdhRCp1aegoMqRaCZg", # DW News
        "UCCEJ6cN9IFZlmgjsVxphkuw", # France 24
        "UCoMdktPbSTixAyNG8-8RFmA", # Sky News
        "UCNye-wNBqNL5ZzHSJj3l8Bg", # Al Jazeera
        "UC16niRr50-MSBwiO3YDb3RA", # BBC News (Atualizado conforme sua ordem anterior)
        "UChqUTb7kYRX8-EiaN3XFrSQ"  # Reuters
    ]

    # FASE 1 & 2 combinadas para recolha de dados
    QUERIES = {
        "Global": "war|conflict|strike|missile|attack",
        "Leste": "Ukraine|Russia|Putin|Zelensky|Kyiv|Moscow|NATO"
    }

    for nome_setor, query in QUERIES.items():
        print(f"\n[VARRENDO] Setor: {nome_setor}")
        query_formatada = urllib.parse.quote(query)
        videos_do_setor = []

        for canal in CANAIS_CONFIANCA:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={canal}&q={query_formatada}&publishedAfter={ontem}&type=video&maxResults=3&key={API_KEY}"
            try:
                resposta = urllib.request.urlopen(url)
                dados = json.loads(resposta.read())
                
                for item in dados.get("items", []):
                    if "videoId" in item["id"]:
                        v_id = item["id"]["videoId"]
                        v_titulo = item["snippet"]["title"]
                        v_canal = item["snippet"]["channelTitle"]
                        v_thumb = item["snippet"]["thumbnails"]["high"]["url"]
                        v_data = item["snippet"]["publishedAt"]

                        # 1. Guardar para o HTML (compatibilidade)
                        videos_do_setor.append({"id": v_id, "data": v_data})

                        # 2. Guardar para o GeoJSON (Nova interface profissional)
                        feature = {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [0, 0]},
                            "properties": {
                                "titulo": v_titulo,
                                "canal": v_canal,
                                "url_video": f"https://www.youtube.com/watch?v={v_id}",
                                "thumbnail": v_thumb,
                                "setor": nome_setor,
                                "data": v_data
                            }
                        }
                        dados_totais_geojson.append(feature)

            except Exception as e:
                print(f"  [ERRO] Canal {canal}: {e}")

        # Gerar os ficheiros HTML para manter as transmissões automáticas
        if videos_do_setor:
            videos_do_setor.sort(key=lambda x: x["data"], reverse=True)
            nome_arq = "playlist.html" if nome_setor == "Global" else "ucrania_e_vizinhos.html"
            gerar_html_playlist([v["id"] for v in videos_do_setor], nome_arq)

    # ==========================================
    # EXPORTAÇÃO FINAL DA BASE DE DADOS GEOJSON
    # ==========================================
    if dados_totais_geojson:
        geojson_final = {
            "type": "FeatureCollection",
            "features": dados_totais_geojson
        }
        with open("videos_taticos.geojson", "w", encoding="utf-8") as f:
            json.dump(geojson_final, f, ensure_ascii=False, indent=4)
        print(f"\n[SUCESSO] Base de dados 'videos_taticos.geojson' gerada com {len(dados_totais_geojson)} entradas.")

if __name__ == "__main__":
    radar_video_hibrido()
