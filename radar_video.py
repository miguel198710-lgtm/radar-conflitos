import urllib.request
import json
import os
from datetime import datetime, timedelta

# Função auxiliar que constrói as "televisões" para o ArcGIS
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
    print("[OSINT VÍDEO] A iniciar varrimento Tático Duplo...")
    
    # Extração segura da chave do cofre do GitHub
    API_KEY = os.environ.get("YOUTUBE_API_KEY")
    if not API_KEY:
        print("[ERRO FATAL] Chave de API não encontrada nas Secrets do GitHub!")
        return
        
    ontem = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"

    # ==========================================
    # FASE 1: O RADAR GLOBAL (Painel Principal)
    # ==========================================
    print("\n[FASE 1] A atualizar Radar Global (Canais de Confiança)...")
    CANAIS_GLOBAIS = ["UCknLrEdhRCp1aegoMqRaCZg", "UCCEJ6cN9IFZlmgjsVxphkuw", "UCoMdktPbSTixAyNG8-8RFmA"]
    QUERY_GLOBAL = "war|conflict|strike|missile|attack"
    videos_globais = []
    
    for canal in CANAIS_GLOBAIS:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={canal}&q={QUERY_GLOBAL}&publishedAfter={ontem}&type=video&order=date&maxResults=5&key={API_KEY}"
        try:
            resposta = urllib.request.urlopen(url)
            dados = json.loads(resposta.read())
            for item in dados.get("items", []):
                if "videoId" in item["id"]:
                    videos_globais.append(item["id"]["videoId"])
        except Exception as e:
            print(f"  [ERRO] Falha num canal global: {e}")
            
    # Gera o ficheiro original intacto para o ecrã principal (playlist.html)
    gerar_html_playlist(videos_globais, "playlist.html")


    # ==========================================
    # FASE 2: OS TEATROS DE OPERAÇÕES REGIONAIS
    # ==========================================
    print("\n[FASE 2] A focar antenas nos teatros regionais...")
    
    # Dicionário com os focos de conflito. Podes expandir isto no futuro!
    TEATROS = {
        "ucrania_e_vizinhos": "(Ukraine | Russia | Belarus | Poland | Moldova | Romania) (war | conflict | border tension | NATO)",
        
    }

    for nome_teatro, query in TEATROS.items():
        print(f"- A varrer: {nome_teatro.upper()}")
        query_formatada = urllib.parse.quote(query)
        # Categoria 25 é a "News & Politics" no YouTube
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query_formatada}&videoCategoryId=25&publishedAfter={ontem}&type=video&order=date&maxResults=10&key={API_KEY}"
        videos_teatro = []
        
        try:
            resposta = urllib.request.urlopen(url)
            dados = json.loads(resposta.read())
            for item in dados.get("items", []):
                if "videoId" in item["id"]:
                    videos_teatro.append(item["id"]["videoId"])
        except Exception as e:
            print(f"  [ERRO] Falha no teatro {nome_teatro}: {e}")
            
        # Gera os ficheiros secundários (ucrania_e_vizinhos.html, israel.html, etc)
        gerar_html_playlist(videos_teatro, f"{nome_teatro}.html")

if __name__ == "__main__":
    radar_video_hibrido()
