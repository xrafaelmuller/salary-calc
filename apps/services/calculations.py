# Tabelas de Cálculo (INSS e IRPF 2025)
INSS_TETO_2025 = 8157.41
INSS_MAX_DESCONTO_2025 = 951.62

IRPF_TABELA_2025 = [
    {"limite": 2428.80, "aliquota": 0.0, "deducao": 0.0},
    {"limite": 2826.65, "aliquota": 0.075, "deducao": 182.16},
    {"limite": 3751.05, "aliquota": 0.15, "deducao": 394.16},
    {"limite": 4664.68, "aliquota": 0.225, "deducao": 675.49},
    {"limite": float('inf'), "aliquota": 0.275, "deducao": 908.73}
]

def calcular_inss(base_calculo):
    """Calcula o desconto do INSS com base no teto e alíquota."""
    if base_calculo >= INSS_TETO_2025:
        return INSS_MAX_DESCONTO_2025
    
    return base_calculo * 0.14

def calcular_irpf(base_calculo):
    """Calcula o desconto do IRPF com base na tabela progressiva."""
    desconto_irpf = 0.0
    for faixa in IRPF_TABELA_2025:
        if base_calculo <= faixa["limite"] or faixa["limite"] == float('inf'):
            desconto_irpf = (base_calculo * faixa["aliquota"]) - faixa["deducao"]
            break
    return max(0.0, desconto_irpf)