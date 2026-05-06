import requests
import json
import re

def limpar_dico(valor):
    """Opção Nuclear: Arranca qualquer lixo, espaços ou decimais e devolve 4 dígitos puros."""
    if not valor: return "0000"
    try:
        # Tenta lidar com números camuflados de decimais (ex: 1714.0 -> 1714)
        num = int(float(str(valor).strip()))
        return str(num).zfill(4)
    except:
        # Se falhar, arranca tudo o que não for número
        s = ''.join(filter(str.isdigit, str(valor)))
        return s.zfill(4)[:4] if s else "0000"

def obter_risco_incendio_areas():
    print("[IPMA RCM] A iniciar Operação de Fusão Tática Blindada (CAOP 2025 + Dados IPMA)...")
    
    ESCALA_RISCO = {
        1: "Reduzido", 2: "Moderado", 3: "Elevado", 4: "Muito Elevado", 5: "Máximo"
    }
    
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
        resposta = requests.get(url)
        if resposta.status_code != 200: continue
            
        dados = resposta.json()
        data_referencia = dados.get("fileDate", "Data Desconhecida")[:10] 
        
        conteudo = dados.get("local") or dados.get("data") or dados

        if isinstance(conteudo, dict):
            for chave_dico, info_local in conteudo.items():
                if not isinstance(info_local, dict): continue
                
                # LIMPEZA NUCLEAR DO DICO DO IPMA
                dico_ipma = limpar_dico(chave_dico)
                if dico_ipma == "0000": continue
                
                nivel_risco = info_local.get("rcm", 1)
                if isinstance(nivel_risco, dict): nivel_risco = nivel_risco.get("rcm", 1)
                    
                if dico_ipma not in dados_ipma: dados_ipma[dico_ipma] = {}
                dados_ipma[dico_ipma][nome_dia] = {
                    "nivel_numero": int(nivel_risco),
                    "descricao": ESCALA_RISCO.get(int(nivel_risco), "Desconhecido"),
                    "data": data_referencia
                }
        
        elif isinstance(conteudo, list):
             for info_local in conteudo:
                if not isinstance(info_local, dict): continue
                
                # LIMPEZA NUCLEAR DO DICO DO IPMA
                dico_ipma = limpar_dico(info_local.get("dico") or info_local.get("idAreaAviso"))
                if dico_ipma == "0000": continue
                
                nivel_risco = info_local.get("rcm", 1)
                if dico_ipma not in dados_ipma: dados_ipma[dico_ipma] = {}
                dados_ipma[dico_ipma][nome_dia] = {
                    "nivel_numero": int(nivel_risco),
                    "descricao": ESCALA_RISCO.get(int(nivel_risco), "Desconhecido"),
                    "data": data_referencia
                }

    print(f"[IPMA RCM] SUCESSO DE EXTRAÇÃO: {len(dados_ipma)} concelhos encontrados no IPMA!")
    
    # RADAR DE DIAGNÓSTICO: Mostra as 5 primeiras chaves limpas do IPMA
    amostra_ipma = list(dados_ipma.keys())[:5]
    print(f"[DIAGNÓSTICO] Amostra chaves IPMA: {amostra_ipma}")

    concelhos_fundidos = 0
    amostra_caop = []
    
    for feature in mapa_base["features"]:
        props = feature["properties"]
        props_lower = {str(k).lower(): v for k, v in props.items()}
        
        # LIMPEZA NUCLEAR DO DICO DA CAOP
        dico_bruto = props_lower.get("dico") or props_lower.get("dicofre")
        dico_mapa = limpar_dico(dico_bruto)
        
        # Guarda as 5 primeiras chaves para o Radar de Diagnóstico
        if len(amostra_caop) < 5: amostra_caop.append(dico_mapa)
        
        nome_concelho = props_lower.get("municipio") or props_lower.get("concelho") or "Desconhecido"
        
        feature["properties"] = {"dico": dico_mapa, "concelho": nome_concelho}
        
        # A HORA DA VERDADE (O MATCH)
        if dico_mapa in dados_ipma:
            for dia, info in dados_ipma[dico_mapa].items():
                feature["properties"][f"data_{dia}"] = info["data"]
                feature["properties"][f"risco_num_{dia}"] = info["nivel_numero"]
                feature["properties"][f"risco_desc_{dia}"] = info["descricao"]
            concelhos_fundidos += 1
        else:
            feature["properties"]["risco_num_hoje"] = 0
            feature["properties"]["risco_desc_hoje"] = "Sem Dados"

    # Mostra as 5 primeiras chaves limpas da CAOP
    print(f"[DIAGNÓSTICO] Amostra chaves CAOP: {amostra_caop}")

    with open('risco_incendio.geojson', 'w', encoding='utf-8') as f:
        json.dump(mapa_base, f, ensure_ascii=False)
        
    print(f"[SUCESSO] Missão cumprida! {concelhos_fundidos} áreas ligadas aos dados do IPMA.")

if __name__ == "__main__":
    obter_risco_incendio_areas()
