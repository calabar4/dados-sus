"""
Teste: correlacao entre mortalidade por sepse (1-12 anos) e leitos de UTI
Pediatrica, por estado (n=27). Compara com o resultado ja obtido para trauma.

Reaproveita:
- data/teste/teste_sepse_por_estado.csv (gerado por testar_sepse.py)
- saida/analise_correlacao_por_estado.csv (leitos e populacao, ja calculados)
"""

from pathlib import Path

import pandas as pd
from scipy import stats

PROJECT_DIR = Path(__file__).resolve().parent.parent

sepse = pd.read_csv(PROJECT_DIR / "data" / "teste" / "teste_sepse_por_estado.csv")
base = pd.read_csv(PROJECT_DIR / "saida" / "analise_correlacao_por_estado.csv")

df = base.merge(sepse, on="uf")
df["taxa_sepse_causabasica_por_100mil_hab"] = (
    df["sepse_causa_basica_A40_A41"] / df["populacao_2024_ibge"] * 100000
)
df["taxa_sepse_mencionada_por_100mil_hab"] = (
    df["sepse_mencionada_qualquer_linha"] / df["populacao_2024_ibge"] * 100000
)

csv_path = PROJECT_DIR / "saida" / "analise_correlacao_sepse_por_estado.csv"
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"Tabela salva em: {csv_path}\n")


def testar(nome, x, y):
    r, p = stats.pearsonr(x, y)
    sig = "SIGNIFICATIVA" if p < 0.05 else "nao significativa"
    print(f"{nome}: r={r:.3f}  p={p:.3f}  ({sig} a 5%)")
    return r, p


print("=== Sepse (causa basica A40/A41) x leitos, taxas /100mil hab, n=%d ===" % len(df))
testar("Sepse (causa basica) x Leitos existentes",
       df["taxa_sepse_causabasica_por_100mil_hab"], df["taxa_leitos_existentes_por_100mil_hab"])
testar("Sepse (causa basica) x Leitos SUS",
       df["taxa_sepse_causabasica_por_100mil_hab"], df["taxa_leitos_sus_por_100mil_hab"])

print()
print("=== Sepse (mencionada em qualquer linha) x leitos, taxas /100mil hab ===")
testar("Sepse (mencionada) x Leitos existentes",
       df["taxa_sepse_mencionada_por_100mil_hab"], df["taxa_leitos_existentes_por_100mil_hab"])
testar("Sepse (mencionada) x Leitos SUS",
       df["taxa_sepse_mencionada_por_100mil_hab"], df["taxa_leitos_sus_por_100mil_hab"])

print()
print("=== Para comparacao: resultado ja obtido para TRAUMA (mesmo n=27) ===")
testar("Trauma x Leitos existentes",
       df["taxa_mortalidade_por_100mil_hab"], df["taxa_leitos_existentes_por_100mil_hab"])
testar("Trauma x Leitos SUS",
       df["taxa_mortalidade_por_100mil_hab"], df["taxa_leitos_sus_por_100mil_hab"])

print()
print("Estados com ZERO obitos por sepse (causa basica):",
      (df["sepse_causa_basica_A40_A41"] == 0).sum(), "de", len(df))
print("Media de obitos por sepse (causa basica) por estado:",
      round(df["sepse_causa_basica_A40_A41"].mean(), 1))
print("Media de obitos por trauma por estado:",
      round(df["mortalidade_trauma_1a12anos"].mean(), 1))
