"""
Analise exploratoria: existe correlacao entre mortalidade por trauma (1-12 anos)
e numero de leitos de UTI Pediatrica, por regiao do Brasil (2024)?

ATENCAO METODOLOGICA: com apenas 5 regioes (n=5), qualquer correlacao aqui
calculada tem pouquissima forca estatistica -- serve como exploracao inicial,
nao como prova de nada. Ver observacoes impressas ao final.
"""

import numpy as np

REGIOES = ["Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"]

# Fonte: saida/mortalidade_trauma_2024_regioes.csv (sexo = Total)
MORTALIDADE = np.array([269, 712, 448, 761, 335], dtype=float)

# Fonte: saida/uti_pediatrica_2024_regioes.csv
LEITOS_EXISTENTES = np.array([617, 1406, 485, 3024, 795], dtype=float)
LEITOS_SUS = np.array([328, 796, 331, 1454, 529], dtype=float)

# Fonte: IBGE, Estimativas da populacao residente, referencia 01/07/2024
# https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/estimativa_dou_2024.pdf
POPULACAO = np.array([17071595, 57112096, 18669345, 88617693, 31113021], dtype=float)


def pearson(x, y):
    return np.corrcoef(x, y)[0, 1]


mort_rate = MORTALIDADE / POPULACAO * 100000
leitos_exist_rate = LEITOS_EXISTENTES / POPULACAO * 100000
leitos_sus_rate = LEITOS_SUS / POPULACAO * 100000

print("=== Numeros absolutos, por regiao ===")
for r, m, le, ls, p in zip(REGIOES, MORTALIDADE, LEITOS_EXISTENTES, LEITOS_SUS, POPULACAO):
    print(f"{r:15s} mortalidade={m:5.0f}  leitos_exist={le:6.0f}  "
          f"leitos_sus={ls:6.0f}  populacao={p:>12,.0f}")

print()
print("Correlacao (numeros brutos) mortalidade x leitos_existentes:",
      round(pearson(MORTALIDADE, LEITOS_EXISTENTES), 3))
print("Correlacao (numeros brutos) mortalidade x leitos_sus:",
      round(pearson(MORTALIDADE, LEITOS_SUS), 3))
print("Correlacao (numeros brutos) mortalidade x populacao:",
      round(pearson(MORTALIDADE, POPULACAO), 3))
print("Correlacao (numeros brutos) leitos_existentes x populacao:",
      round(pearson(LEITOS_EXISTENTES, POPULACAO), 3))

print()
print("=== Taxas por 100 mil habitantes, por regiao ===")
for r, mr, ler, lsr in zip(REGIOES, mort_rate, leitos_exist_rate, leitos_sus_rate):
    print(f"{r:15s} taxa_mortalidade={mr:6.3f}  "
          f"taxa_leitos_exist={ler:6.3f}  taxa_leitos_sus={lsr:6.3f}")

print()
print("Correlacao (taxas por 100 mil hab.) mortalidade x leitos_existentes:",
      round(pearson(mort_rate, leitos_exist_rate), 3))
print("Correlacao (taxas por 100 mil hab.) mortalidade x leitos_sus:",
      round(pearson(mort_rate, leitos_sus_rate), 3))
