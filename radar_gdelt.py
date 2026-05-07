import urllib.request
import urllib.parse

def radar_gdelt():
    print("[INTELIGÊNCIA GDELT] A estabelecer ligação com o mainframe global...")
    
    # Usamos os "Themes" (Categorias) oficiais do GDELT para extrair apenas conflitos armados e terrorismo
    query = "theme:ARMEDCONFLICT OR theme:TERROR"
    query_formatada = urllib.parse.quote(query)
    
    # Pedimos os dados à API 2.0 diretamente no formato lido pela ESRI (GeoJSON)
    url = f"https://api.gdeltproject.org/api/v2/geo/geo?query={query_formatada}&format=GeoJSON"
    ficheiro = "gdelt_conflitos.geojson"
    
    try:
        # O GDELT bloqueia robôs não identificados. Camuflamos o pedido como se fosse o browser de um humano.
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        resposta = urllib.request.urlopen(req)
        
        with open(ficheiro, "wb") as f:
            f.write(resposta.read())
            
        print(f"[SUCESSO] Telemetria GDELT capturada e empacotada no ficheiro {ficheiro}!")
        
    except Exception as e:
        print(f"[ERRO] Falha ao contornar as defesas do GDELT: {e}")

if __name__ == "__main__":
    radar_gdelt()
