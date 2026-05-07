import urllib.request
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
    print(f"  -> [SUCESSO] Emissão {nome_ficheiro} atualizada e pronta a transmitir!")

def radar_video_hibrido():
    print("[OSINT VÍDEO] A iniciar varrimento com Filtro de Propaganda...")
    
    API_KEY = os.environ.get("YOUTUBE_API_KEY")
    if not API_KEY:
        print("[ERRO FATAL] Chave de API não encontrada!")
        return
        
    ontem = (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z"

   # ==========================================
    # OS NOSSOS CANAIS DE CONFIANÇA (ARSENAL COMPLETO)
    # ==========================================
    CANAIS_CONFIANCA = [
        "UCknLrEdhRCp1aegoMqRaCZg", # DW News (Europa)
        "UCCEJ6cN9IFZlmgjsVxphkuw", # France 24 (Europa/África)
        "UCoMdktPbSTixAyNG8-8RFmA", # Sky News (Reino Unido)
        "UCNye-wNBqNL5ZzHSJj3l8Bg", # Al Jazeera (Médio Oriente)
        "UC_gUM8rL-Lrg6O3adPWZqgg", # WION (Ásia)
        "UChqUTb7kYRX8-EiaN3XFrSQ", # Reuters (Global)
        "UChLsHIte9PPeN6trQlA7eHQ"  # Global News (Américas)
    ]

    # ==========================================
    # FASE 1: O RADAR GLOBAL
    # ==========================================
    print("\n[FASE 1] A atualizar Radar Global...")
    QUERY_GLOBAL = "war|conflict|strike|missile|attack"
    videos_globais = []
    
    for canal in CANAIS_CONFIANCA:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={canal}&q={QUERY_GLOBAL}&publishedAfter={ontem}&type=video&maxResults=3&key={API_KEY}"
        try:
            resposta = urllib.request.urlopen(url)
            dados = json.loads(resposta.read())
            for item in dados.get("items", []):
                if "videoId" in item["id"]:
                    videos_globais.append({"id": item["id"]["videoId"], "data": item["snippet"]["publishedAt"]})
        except Exception as e:
            print(f"  [ERRO] Falha num canal global: {e}")
            
    if videos_globais:
        videos_globais.sort(key=lambda x: x["data"], reverse=True)
        gerar_html_playlist([v["id"] for v in videos_globais], "playlist.html")


    # ==========================================
    # FASE 2: TEATRO DE OPERAÇÕES DE LESTE
    # ==========================================
    print("\n[FASE 2] A focar antenas no Teatro de Leste (Fontes Seguras)...")
    
    # Tiro de caçadeira: Palavras-chave simples, separadas por |, SEM espaços.
    # Isto garante que a API entende que basta o vídeo ter UMA destas palavras para ser capturado.
    TEATROS = {
        "ucrania_e_vizinhos": "Ukraine|Russia|Putin|Zelensky|Kyiv|Moscow|NATO"
    }

    for nome_teatro, query in TEATROS.items():
        print(f"- A varrer: {nome_teatro.upper()}")
        query_formatada = urllib.parse.quote(query)
        videos_teatro = []
        
        for canal in CANAIS_CONFIANCA:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={canal}&q={query_formatada}&publishedAfter={ontem}&type=video&maxResults=3&key={API_KEY}"
            try:
                resposta = urllib.request.urlopen(url)
                dados = json.loads(resposta.read())
                for item in dados.get("items", []):
                    if "videoId" in item["id"]:
                        videos_teatro.append({"id": item["id"]["videoId"], "data": item["snippet"]["publishedAt"]})
            except Exception as e:
                print(f"  [ERRO] Falha no teatro {nome_teatro}: {e}")
                
        if videos_teatro:
            videos_teatro.sort(key=lambda x: x["data"], reverse=True)
            gerar_html_playlist([v["id"] for v in videos_teatro], f"{nome_teatro}.html")
        else:
            print(f"  -> Sem vídeos seguros hoje para {nome_teatro}.")

if __name__ == "__main__":
    radar_video_hibrido()
