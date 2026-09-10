"""
Analise exploratoria por ESTADO (n=27), em vez de por regiao (n=5):
existe correlacao entre mortalidade por trauma (1-12 anos) e numero de
leitos de UTI Pediatrica?

Reaproveita os arquivos brutos ja baixados em data/raw_cache/ (nao baixa
nada de novo) e as mesmas funcoes de leitura dos scripts de coleta.

Populacao por estado: fonte oficial IBGE, Estimativas da populacao residente,
referencia 01/07/2024.
https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/estimativa_dou_2024.pdf

ATENCAO METODOLOGICA: mesmo com n=27 (bem melhor que n=5), isto continua
sendo uma correlacao ecologica simples, sem controle de outros fatores
(trauma no transito, violencia, tempo de resposta pre-hospitalar, etc.).
Correlacao nao implica causalidade.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coletar_mortalidade_trauma as mort_mod  # noqa: E402
import coletar_uti_pediatrica as uti_mod  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw_cache"
SAIDA_DIR = PROJECT_DIR / "saida"

# Fonte: IBGE, Estimativas da populacao residente, referencia 01/07/2024
# (mesmo PDF ja usado na analise por regiao)
POPULACAO_UF = {
    "RO": 1_746_227, "AC": 880_631, "AM": 4_281_209, "RR": 716_793,
    "PA": 8_664_306, "AP": 802_837, "TO": 1_577_342,
    "MA": 7_010_960, "PI": 3_375_646, "CE": 9_233_656, "RN": 3_446_071,
    "PB": 4_145_040, "PE": 9_539_029, "AL": 3_220_104, "SE": 2_291_077,
    "BA": 14_850_513,
    "MG": 21_322_691, "ES": 4_102_129, "RJ": 17_219_679, "SP": 45_973_194,
    "PR": 11_824_665, "SC": 8_058_441, "RS": 11_229_915,
    "MS": 2_901_895, "MT": 3_836_399, "GO": 7_350_483, "DF": 2_982_818,
}


def coletar_mortalidade_por_uf() -> dict:
    resultado = {}
    for uf in sorted(POPULACAO_UF):
        candidatos = list(RAW_DIR.glob(f"DO{uf}2024.dbc")) + \
            list(RAW_DIR.glob(f"DO{uf}2024.DBC"))
        if not candidatos:
            print(f"AVISO: sem arquivo de mortalidade em cache para {uf}")
            continue
        df = mort_mod.processar_uf(uf, candidatos[0])
        resultado[uf] = len(df)
    return resultado


def coletar_leitos_por_uf() -> dict:
    resultado = {}
    for uf in sorted(POPULACAO_UF):
        candidatos = list(RAW_DIR.glob(f"LT{uf}2412.dbc")) + \
            list(RAW_DIR.glob(f"LT{uf}2412.DBC"))
        if not candidatos:
            print(f"AVISO: sem arquivo de leitos em cache para {uf}")
            continue
        df = uti_mod.processar_uf(uf, candidatos[0])
        resultado[uf] = {
            "qt_exist": int(df["qt_exist"].sum()) if len(df) else 0,
            "qt_sus": int(df["qt_sus"].sum()) if len(df) else 0,
        }
    return resultado


def pearson(x, y):
    return np.corrcoef(x, y)[0, 1]


def pearson_com_p(x, y):
    r, p = stats.pearsonr(x, y)
    return r, p


def main() -> None:
    print("Processando mortalidade por trauma (1-12 anos), por estado...")
    mortalidade_uf = coletar_mortalidade_por_uf()
    print("Processando leitos de UTI Pediatrica, por estado...")
    leitos_uf = coletar_leitos_por_uf()

    linhas = []
    for uf in sorted(POPULACAO_UF):
        if uf not in mortalidade_uf or uf not in leitos_uf:
            continue
        pop = POPULACAO_UF[uf]
        obitos = mortalidade_uf[uf]
        leitos_exist = leitos_uf[uf]["qt_exist"]
        leitos_sus = leitos_uf[uf]["qt_sus"]
        linhas.append(
            {
                "uf": uf,
                "populacao_2024_ibge": pop,
                "mortalidade_trauma_1a12anos": obitos,
                "leitos_uti_ped_existentes": leitos_exist,
                "leitos_uti_ped_sus": leitos_sus,
                "taxa_mortalidade_por_100mil_hab": obitos / pop * 100000,
                "taxa_leitos_existentes_por_100mil_hab": leitos_exist / pop * 100000,
                "taxa_leitos_sus_por_100mil_hab": leitos_sus / pop * 100000,
            }
        )

    df = pd.DataFrame(linhas)
    csv_path = SAIDA_DIR / "analise_correlacao_por_estado.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"\n{len(df)} estados processados (de {len(POPULACAO_UF)}).")
    print(f"Tabela salva em: {csv_path}\n")

    print("=== Correlacao de Pearson (n = %d estados) ===" % len(df))
    r_bruto_exist = pearson(df["mortalidade_trauma_1a12anos"], df["leitos_uti_ped_existentes"])
    r_bruto_sus = pearson(df["mortalidade_trauma_1a12anos"], df["leitos_uti_ped_sus"])
    r_bruto_pop_mort = pearson(df["mortalidade_trauma_1a12anos"], df["populacao_2024_ibge"])
    r_bruto_pop_leito = pearson(df["leitos_uti_ped_existentes"], df["populacao_2024_ibge"])

    r_taxa_exist, p_taxa_exist = pearson_com_p(
        df["taxa_mortalidade_por_100mil_hab"], df["taxa_leitos_existentes_por_100mil_hab"]
    )
    r_taxa_sus, p_taxa_sus = pearson_com_p(
        df["taxa_mortalidade_por_100mil_hab"], df["taxa_leitos_sus_por_100mil_hab"]
    )

    print(f"Numeros brutos - mortalidade x leitos existentes: {r_bruto_exist:.3f}")
    print(f"Numeros brutos - mortalidade x leitos SUS:        {r_bruto_sus:.3f}")
    print(f"Numeros brutos - mortalidade x populacao:         {r_bruto_pop_mort:.3f}")
    print(f"Numeros brutos - leitos existentes x populacao:   {r_bruto_pop_leito:.3f}")
    print("(numeros brutos nao devem ser interpretados como relacao causal -- "
          "veja a nota sobre confundimento por populacao no README)")
    print()
    print(f"Taxas /100mil hab - mortalidade x leitos existentes: "
          f"r={r_taxa_exist:.3f}  p-valor={p_taxa_exist:.3f}")
    print(f"Taxas /100mil hab - mortalidade x leitos SUS:        "
          f"r={r_taxa_sus:.3f}  p-valor={p_taxa_sus:.3f}")
    print()
    alpha = 0.05
    for nome, p in [("leitos existentes", p_taxa_exist), ("leitos SUS", p_taxa_sus)]:
        situacao = "estatisticamente significativa" if p < alpha else "NAO estatisticamente significativa"
        print(f"-> Correlacao mortalidade x {nome} (taxas): {situacao} (p={p:.3f}, alpha=0.05)")


if __name__ == "__main__":
    main()
