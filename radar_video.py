import urllib.request
import json
import os
from datetime import datetime, timedelta

def radar_video_conflitos():
    print("[OSINT VÍDEO] A iniciar varrimento global de larga escala...")
    
    API_KEY = os.environ.get("YOUTUBE_API_KEY")
    
    if not API_KEY:
        print("[ERRO FATAL] Chave de API não encontrada! Verifica as GitHub Secrets.")
        return
    
    # ARSENAL EXPANDIDO DE CANAIS
    CANAIS = {
        "Al Jazeera (Médio Oriente)": "UCNye-wNBqNL5ZzHSJj3l8Bg",
        "DW News (Europa)": "UCknLrEdhRCp1aegoMqRaCZg",
        "France 24 (Europa/África)": "UCCEJ6cN9IFZlmgjsVxphkuw",
        "Sky News (Reino Unido)": "UCoMdktPbSTixAyNG8-8RFmA",
        "WION (Ásia/Índia)": "UC_gUM8rL-Lrg6O3adPWZqgg",
        "Reuters (Global)": "UChqUTb7kYRX8-EiaN3XFrSQ",
        "Global News (Américas)": "UChLsHIte9PPeN6trQlA7eHQ"
    }
    
    # PALAVRAS-CHAVE EXPANDIDAS
    QUERY = "war|conflict|strike|missile|attack|crisis|tension|military|drone|navy|geopolitics"
    
    # Apenas vídeos das últimas 24 horas
    ontem = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    
    videos_encontrados = []

    # O robô agora varre canal a canal e extrai a hora exata da notícia
    for nome_canal, canal_id in CANAIS.items():
        print(f"A intercetar sinal de: {nome_canal}...")
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={canal_id}&q={QUERY}&publishedAfter={ontem}&type=video&order=date&maxResults=5&key={API_KEY}"
        
        try:
            resposta = urllib.request.urlopen(url)
            dados = json.loads(resposta.read())
            
            for item in dados.get("items", []):
                if "videoId" in item["id"]:
                    video_id = item["id"]["videoId"]
                    titulo = item["snippet"]["title"]
                    data_pub = item["snippet"]["publishedAt"]
                    
                    # Guardamos a data para podermos organizar depois
                    videos_encontrados.append({
                        "id": video_id,
                        "titulo": titulo,
                        "data": data_pub
                    })
                    print(f"  -> Capturado: {titulo}")
                    
        except Exception as e:
            print(f"[ERRO] Falha na comunicação com {nome_canal}: {e}")

    if videos_encontrados:
        # A MAGIA ACONTECE AQUI: Ordena todos os vídeos do mais recente para o mais antigo
        videos_encontrados.sort(key=lambda x: x["data"], reverse=True)
        
        # Limita a 50 vídeos no máximo (o limite de uma playlist incorporada estável)
        lista_videos = [v["id"] for v in videos_encontrados][:50]
        
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
        
        with open("playlist.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print(f"\n[SUCESSO] Playlist global gerada com {len(lista_videos)} vídeos ordenados cronologicamente!")
    else:
        print("\n[STATUS] Nenhum vídeo detetado nas últimas 24 horas.")

if __name__ == "__main__":
    radar_video_conflitos()
