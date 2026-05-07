import urllib.request
import json
import os
from datetime import datetime, timedelta

def radar_video_conflitos():
    print("[OSINT VÍDEO] A iniciar varrimento visual de conflitos...")
    
    # Extrai a chave de forma segura das GitHub Secrets
    API_KEY = os.environ.get("YOUTUBE_API_KEY")
    
    if not API_KEY:
        print("[ERRO FATAL] Chave de API não encontrada! Verifica as GitHub Secrets.")
        return
    
    # IDs de canais de confiança (Ex: DW News, France 24, Sky News)
    CANAIS = ["UCknLrEdhRCp1aegoMqRaCZg", "UCCEJ6cN9IFZlmgjsVxphkuw", "UCoMdktPbSTixAyNG8-8RFmA"]
    
    # Palavras-chave do filtro
    QUERY = "war|conflict|strike|missile|attack"
    
    # Apenas vídeos das últimas 24 horas
    ontem = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    
    lista_videos = []

    for canal in CANAIS:
        # Constrói o pedido à API do YouTube
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={canal}&q={QUERY}&publishedAfter={ontem}&type=video&order=date&maxResults=5&key={API_KEY}"
        
        try:
            resposta = urllib.request.urlopen(url)
            dados = json.loads(resposta.read())
            
            for item in dados.get("items", []):
                # Garante que só apanhamos vídeos e não playlists perdidas
                if "videoId" in item["id"]:
                    video_id = item["id"]["videoId"]
                    titulo = item["snippet"]["title"]
                    lista_videos.append(video_id)
                    print(f"[ALVO CAPTURADO] {titulo}")
                
        except Exception as e:
            print(f"[ERRO] Falha na comunicação com o canal {canal}: {e}")

    if lista_videos:
        # Pega no primeiro vídeo como principal e junta o resto como playlist
        video_principal = lista_videos[0]
        resto_playlist = ",".join(lista_videos[1:])
        
        url_embed = f"https://www.youtube.com/embed/{video_principal}?playlist={resto_playlist}&autoplay=1&mute=1"
        
        # Gera o ficheiro HTML para o ArcGIS ler a partir do GitHub Pages
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
            
        print("\n[SUCESSO] Ficheiro playlist.html gerado com sucesso!")
        print(f"URL Interno gerado: {url_embed}")
    else:
        print("\n[STATUS] Nenhum vídeo de conflito detetado nas últimas 24 horas.")

if __name__ == "__main__":
    radar_video_conflitos()
