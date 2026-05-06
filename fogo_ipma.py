import requests
import json
import os

def obter_risco_incendio_areas():
    print("[IPMA RCM] A iniciar Operação de Fusão Tática (CAOP 2025 + Dados IPMA)...")
    
    ESCALA_RISCO = {
        1: "Reduzido", 2: "Moderado", 3: "Elevado", 4: "Muito Elevado", 5: "Máximo"
    }
    
    # 1. Carregar a Base Geográfica Local (CAOP 2025 Comprimida)
    print("[IPMA RCM] A ler ficheiro local da CAOP 2025...")
    try:
        # Lê o ficheiro leve que acabaste de carregar no GitHub
        with open('caop2025_base.geojson', 'r', encoding='utf-8') as f:
            mapa_base = json.load(f)
    except Exception as e:
        print(f"[ERRO CRÍTICO] Não encontrei o ficheiro 'caop2025_base.geojson': {e}")
        return

    # 2. Obter Dados de Incêndio do IPMA
    dados_ipma = {}
    dias_api = {0: "hoje", 1: "amanha"} 

    for id_dia, nome_dia in dias_api.items():
        url = f"https://api.ipma.pt/open-data/forecast/meteorology/rcm/rcm-d{id_dia}.json"
        print(f"[IPMA RCM] A extrair níveis de risco para: {nome_dia}...")
        resposta = requests.get(url)
        
        if resposta.status_code != 200:
            print(f"[AVISO] Sem dados do IPMA para {nome_dia}.")
            continue
            
        dados = resposta.json()
        data_referencia = dados.get("fileDate", "Data Desconhecida")[:10] 
        
        dicionario_locais = dados.get("local", {})
        if not dicionario_locais:
            dicionario_locais = dados.get("data", dados)
            
        lista_locais = list(dicionario_locais.values()) if isinstance(dicionario_locais, dict) else dicionario_locais

        for info_local in lista_locais:
            if not isinstance(info_local, dict): continue

            dico = str(info_local.get("dico", "")).zfill(4) 
            if dico == "0000": continue
            
            nivel_risco = 1
            if "data" in info_local and isinstance(info_local["data"], dict):
                nivel_risco = info_local["data"].get("rcm", 1)
            else:
                nivel_risco = info_local.get("rcm", 1)
                
            if dico not in dados_ipma:
                dados_ipma[dico] = {}
                
            dados_ipma[dico][nome_dia] = {
                "nivel_numero": int(nivel_risco),
                "descricao": ESCALA_RISCO.get(int(nivel_risco), "Desconhecido"),
                "data": data_referencia
            }

    # 3. FUSÃO DE DADOS (Data Fusion)
    print("[IPMA RCM] A fundir dados táticos com os polígonos da CAOP...")
    concelhos_fundidos = 0
    
    for feature in mapa_base["features"]:
        props = feature["properties"]
        
        # Tática de caça ao DICO: Procura as variações mais comuns que a DGT usa
        dico_bruto = props.get("DICO") or props.get("Dicofre") or props.get("dico") or props.get("DICOFRE")
        # Garante que apanha apenas os primeiros 4 dígitos (concelho) caso o ficheiro traga 6 (freguesia)
        dico_mapa = str(dico_bruto).zfill(4)[:4] if dico_bruto else "0000"
        
        nome_concelho = props.get("Concelho") or props.get("CONCELHO") or props.get("Municipio") or "Desconhecido"
        
        # Limpar lixo do ficheiro base para manter a performance da ESRI no máximo
        feature["properties"] = {
            "dico": dico_mapa,
            "concelho": nome_concelho
        }
        
        # Injetar os dados de risco dentro do polígono
        if dico_mapa in dados_ipma:
            for dia, info in dados_ipma[dico_mapa].items():
                feature["properties"][f"data_{dia}"] = info["data"]
                feature["properties"][f"risco_num_{dia}"] = info["nivel_numero"]
                feature["properties"][f"risco_desc_{dia}"] = info["descricao"]
            concelhos_fundidos += 1
        else:
            feature["properties"]["risco_num_hoje"] = 0
            feature["properties"]["risco_desc_hoje"] = "Sem Dados"

    # 4. Gravar o Ficheiro Final
    with open('risco_incendio.geojson', 'w', encoding='utf-8') as f:
        json.dump(mapa_base, f, ensure_ascii=False)
        
    print(f"[SUCESSO] Missão cumprida! {concelhos_fundidos} áreas pintadas e gravadas no 'risco_incendio.geojson'.")

if __name__ == "__main__":
    obter_risco_incendio_areas()
