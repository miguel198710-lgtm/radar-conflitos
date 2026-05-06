import requests
import json

def limpar_dico(valor):
    """Garante que o código fica sempre com 4 dígitos puros."""
    if not valor: return "0000"
    try:
        num = int(float(str(valor).strip()))
        return str(num).zfill(4)
    except:
        s = ''.join(filter(str.isdigit, str(valor)))
        return s.zfill(4)[:4] if s else "0000"

def extrair_risco(info_local):
    """Cão Farejador para o nível de Risco do IPMA (ignora maiúsculas/minúsculas)"""
    info_lower = {str(k).lower().strip(): v for k, v in info_local.items()}
    
    # Procura as chaves mais comuns de risco
    risco = info_lower.get("rcm") or info_lower.get("risco") or info_lower.get("classerisco")
    
    # Se o IPMA meteu o valor dentro de outra gaveta (ex: "rcm": {"rcm": 3})
    if isinstance(risco, dict):
        r_lower = {str(k).lower().strip(): v for k, v in risco.items()}
        risco = r_lower.get("rcm") or r_lower.get("risco")
        
    try:
        val = int(float(str(risco)))
        # Garante que devolve um número válido na escala de 1 a 5
        if 1 <= val <= 5: 
            return val
    except:
        pass
        
    # TÁTICA NUCLEAR: Se o nome da chave mudou completamente, procura qualquer valor solto (de 1 a 5)
    for k, v in info_lower.items():
        try:
            if 'id' in k or 'dico' in k: continue # ignora códigos de identificação
            val = int(float(str(v)))
            if 1 <= val <= 5: return val
        except:
            pass
            
    return 1 # Fallback de segurança se tudo falhar

def obter_risco_incendio_areas():
    print("[IPMA RCM] A iniciar Operação de Fusão Definitiva...")
    
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

        # Processar se a API devolver em formato Dicionário
        if isinstance(conteudo, dict):
            for chave_dico, info_local in conteudo.items():
                if not isinstance(info_local, dict): continue
                dico_ipma = limpar_dico(chave_dico)
                if dico_ipma == "0000": continue
                
                # A Nova Extração Blindada
                nivel_risco = extrair_risco(info_local)
                    
                if dico_ipma not in dados_ipma: dados_ipma[dico_ipma] = {}
                dados_ipma[dico_ipma][nome_dia] = {
                    "nivel_numero": nivel_risco,
                    "descricao": ESCALA_RISCO.get(nivel_risco, "Desconhecido"),
                    "data": data_referencia
                }
                
        # Processar se a API devolver em formato Lista
        elif isinstance(conteudo, list):
            for info_local in conteudo:
                if not isinstance(info_local, dict): continue
                
                info_lower = {str(k).lower().strip(): v for k, v in info_local.items()}
                dico_ipma = limpar_dico(info_lower.get("dico") or info_lower.get("idareaaviso"))
                if dico_ipma == "0000": continue
                
                # A Nova Extração Blindada
                nivel_risco = extrair_risco(info_local)
                
                if dico_ipma not in dados_ipma: dados_ipma[dico_ipma] = {}
                dados_ipma[dico_ipma][nome_dia] = {
                    "nivel_numero": nivel_risco,
                    "descricao": ESCALA_RISCO.get(nivel_risco, "Desconhecido"),
                    "data": data_referencia
                }

    print(f"[IPMA RCM] SUCESSO DE EXTRAÇÃO: {len(dados_ipma)} concelhos encontrados no IPMA!")

    concelhos_fundidos = 0
    
    for feature in mapa_base.get("features", []):
        props = feature.get("properties", {})
        props_lower = {str(k).lower().strip(): v for k, v in props.items()}
        
        # Lê a CAOP usando a tua descoberta do DTMN
        dico_bruto = props_lower.get("dtmn") or props_lower.get("dico")
        dico_mapa = limpar_dico(dico_bruto)
        
        nome_concelho = props_lower.get("municipio") or props_lower.get("concelho") or "Desconhecido"
        
        feature["properties"] = {"dico": dico_mapa, "concelho": nome_concelho}
        
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
        
    print(f"[SUCESSO] Missão cumprida! {concelhos_fundidos} áreas ligadas aos dados reais do IPMA.")

if __name__ == "__main__":
    obter_risco_incendio_areas()
