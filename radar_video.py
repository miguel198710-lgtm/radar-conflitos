import urllib.request
import json
from datetime import datetime, timedelta

def radar_video_conflitos():
    print("[OSINT VÍDEO] A iniciar varrimento visual de conflitos...")
    
    # ---> É AQUI! COLA A TUA CHAVE DENTRO DAS ASPAS <---
    API_KEY = "AIzaSyCNLW1o-JNVhRTrhxZd0Japl2ae7kg0teE"
    
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
                # A API do YouTube por vezes devolve playlists no meio, isto garante que só apanhamos vídeos
                if "videoId" in item["id"]:
                    video_id = item["id"]["videoId"]
                    titulo = item["snippet"]["title"]
                    lista_videos.append(video_id)
                    print(f"[ALVO CAPTURADO] {titulo}")
                
        except Exception as e:
            print(f"[ERRO] Falha na comunicação: {e}")

    if lista_videos:
        # Gera o URL da Playlist para o teu Experience Builder
        video_principal = lista_videos[0]
        resto_playlist = ",".join(lista_videos[1:])
        
        url_embed = f"https://www.youtube.com/embed/{video_principal}?playlist={resto_playlist}&autoplay=1&mute=1"
        
        print("\n[SUCESSO] Missão cumprida. Copia este link para o Widget Embed do ArcGIS:")
        print(url_embed)
    else:
        print("\n[STATUS] Nenhum vídeo de conflito detetado nas últimas 24 horas.")

if __name__ == "__main__":
    radar_video_conflitos()
