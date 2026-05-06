import requests
import json
import os

def obter_risco_incendio_areas():
    print("[IPMA RCM] A iniciar Operação de Fusão Tática Blindada (CAOP 2025 + Dados IPMA)...")
    
    ESCALA_RISCO = {
        1: "Reduzido", 2: "Moderado", 3: "Elevado", 4: "Muito Elevado", 5: "Máximo"
    }
    
    print("[IPMA RCM] A ler ficheiro local da CAOP 2025...")
    try:
        with open('CAOP/caop2025_base.geojson', 'r', encoding='utf-8') as f:
            mapa_base = json.load(f)
    except Exception as e:
        print(f"[ERRO CRÍTICO] Não encontrei o ficheiro base: {e}")
        return

    dados_ipma = {}
    dias_api = {0: "hoje", 1: "amanha"} 

    for id_dia, nome_dia in dias_api.items():
        url = f"https://api.ipma.pt/open-data/forecast/meteorology/rcm/rcm-d{id_dia}.json"
        print(f"[IPMA RCM] A extrair dados para: {nome_dia}...")
        resposta = requests.get(url)
        
        if resposta.status_code != 200:
            print(f"[IPMA RCM] Aviso: Sem dados para {nome_dia}")
            continue
            
        dados = resposta.json()
        data_referencia = dados.get("fileDate", "Data Desconhecida")[:10] 
        
        conteudo = dados.get("local") or dados.get("data") or dados

        # A CORREÇÃO: Ler o DICO a partir do NOME da chave, e não de dentro do valor!
        if isinstance(conteudo, dict):
            for chave_dico, info_local in conteudo.items():
                if not isinstance(info_local, dict): continue

                # A chave do dicionário É o DICO
                dico_ipma = str(chave_dico).zfill(4) 
                if dico_ipma == "0000": continue
                
                nivel_risco = info_local.get("rcm", 1)
                # Proteção extra caso o RCM esteja dentro de outra sub-pasta
                if isinstance(nivel_risco, dict): 
                     nivel_risco = nivel_risco.get("rcm", 1)
                    
                if dico_ipma not in dados_ipma:
                    dados_ipma[dico_ipma] = {}
                    
                dados_ipma[dico_ipma][nome_dia] = {
                    "nivel_numero": int(nivel_risco),
                    "descricao": ESCALA_RISCO.get(int(nivel_risco), "Desconhecido"),
                    "data": data_referencia
                }
        
        elif isinstance(conteudo, list):
             for info_local in conteudo:
                if not isinstance(info_local, dict): continue

                dico_ipma = str(info_local.get("dico", info_local.get("idAreaAviso", ""))).zfill(4) 
                if dico_ipma == "0000": continue
                
                nivel_risco = info_local.get("rcm", 1)
                    
                if dico_ipma not in dados_ipma:
                    dados_ipma[dico_ipma] = {}
                    
                dados_ipma[dico_ipma][nome_dia] = {
                    "nivel_numero": int(nivel_risco),
                    "descricao": ESCALA_RISCO.get(int(nivel_risco), "Desconhecido"),
                    "data": data_referencia
                }

    print(f"[IPMA RCM] SUCESSO DE EXTRAÇÃO: {len(dados_ipma)} concelhos encontrados no IPMA!")
    print("[IPMA RCM] A fundir dados táticos com os polígonos da CAOP...")
    concelhos_fundidos = 0
    
    for feature in mapa_base["features"]:
        props = feature["properties"]
        
        props_lower = {str(k).lower(): v for k, v in props.items()}
        
        dico_bruto = props_lower.get("dico") or props_lower.get("dicofre")
        dico_mapa = str(dico_bruto).zfill(4)[:4] if dico_bruto else "0000"
        
        nome_concelho = props_lower.get("municipio") or props_lower.get("concelho") or "Desconhecido"
        
        feature["properties"] = {
            "dico": dico_mapa,
            "concelho": nome_concelho
        }
        
        if dico_mapa in dados_ipma:
            for dia, info in dados_ipma[dico_mapa].items():
                feature["properties"][f"data_{dia}"] = info["data"]
                feature["properties"][f"risco_num_{dia}"] = info["nivel_numero"]
                feature["properties"][f"risco_desc_{dia}"] = info["descricao"]
            concelhos_fundidos += 1
        else:
            feature["properties"]["risco_num_hoje"] = 0
            feature["properties"]["risco_desc_hoje"] = "Sem Dados"

    with open('risco_incendio.geojson', 'w', encoding='utf-8') as f:
        json.dump(mapa_base, f, ensure_ascii=False)
        
    print(f"[SUCESSO] Missão cumprida! {concelhos_fundidos} áreas ligadas aos dados do IPMA.")

if __name__ == "__main__":
    obter_risco_incendio_areas()
