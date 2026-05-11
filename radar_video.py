import urllib.request
import urllib.parse
import json
import os
import re
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
    print("[OSINT VÍDEO] A iniciar varrimento com Filtro de Inteligência Estruturada e AOIs...")
    
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
        "UC16niRr50-MSBwiO3YDb3RA", # BBC News
        "UChqUTb7kYRX8-EiaN3XFrSQ"  # Reuters
    ]

    # ==========================================
    # DEFINIÇÃO DAS ÁREAS DE INTERESSE (AOIs)
    # ==========================================
    TEATROS = {
        "Ucrânia e Leste": "Ukraine|Russia|Zelensky|Putin|Kyiv|Moscow|NATO|Donbas",
        "Irão e Médio Oriente": "Iran|Tehran|Israel|Gaza|Lebanon|Hezbollah|Houthi|Red Sea",
        "Venezuela e Cuba": "Venezuela|Maduro|Cuba|Havana|Guyana|Essequibo",
        "Global": "war|conflict|strike|missile|attack|nuclear"
    }

    for nome_teatro, query in TEATROS.items():
        print(f"\n[VARRENDO AOI] -> {nome_teatro}")
        query_formatada = urllib.parse.quote(query)
        videos_do_teatro = []

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
                        videos_do_teatro.append({"id": v_id, "data": v_data})

                        # 2. Guardar para o GeoJSON (Nova interface profissional)
                        feature = {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [0, 0]},
                            "properties": {
                                "titulo": v_titulo,
                                "canal": v_canal,
                                "url_video": f"https://www.youtube.com/embed/{v_id}?autoplay=1&mute=1",
                                "thumbnail": v_thumb,
                                "data": v_data,
                                "aoi": nome_teatro  # <--- O NOSSO NOVO SELO TÁTICO
                            }
                        }
                        dados_totais_geojson.append(feature)

            except Exception as e:
                print(f"  [ERRO] Canal {canal}: {e}")

        # Gerar os ficheiros HTML para manter as transmissões automáticas antigas a funcionar
        if videos_do_teatro:
            videos_do_teatro.sort(key=lambda x: x["data"], reverse=True)
            
            # Limpar o nome para o ficheiro HTML (ex: "Ucrânia e Leste" vira "ucrania_e_leste.html")
            nome_limpo = re.sub(r'[^a-z0-9]', '_', nome_teatro.lower().replace('ã', 'a').replace('á', 'a').replace('é', 'e').replace('í', 'i'))
            nome_arq = f"{nome_limpo}.html"
            
            gerar_html_playlist([v["id"] for v in videos_do_teatro], nome_arq)

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
        print(f"\n[SUCESSO] Base de dados 'videos_taticos.geojson' gerada com {len(dados_totais_geojson)} transmissões marcadas por AOI.")

if __name__ == "__main__":
    radar_video_hibrido()
