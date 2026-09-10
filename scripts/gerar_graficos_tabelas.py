"""
Gera graficos (PNG, prontos para colar no artigo) e tabelas comparativas
(Excel/CSV) a partir dos dados ja coletados e analisados nos Indicadores 1-4.

Nao baixa nada novo -- so le os arquivos ja salvos em saida/ e data/teste/.

Saidas:
    graficos/01_mortalidade_trauma_por_regiao.png
    graficos/02_leitos_uti_ped_por_regiao.png
    graficos/03_dispersao_trauma_x_leitos_existentes.png
    graficos/04_dispersao_trauma_x_leitos_sus.png
    graficos/05_dispersao_sepse_x_leitos_sus.png
    graficos/06_comparacao_trauma_sepse_por_estado.png
    saida/tabela_comparativa_regioes.xlsx / .csv
    saida/tabela_comparativa_estados.xlsx / .csv
    saida/tabela_resumo_correlacoes.xlsx / .csv
"""

import io
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = PROJECT_DIR / "saida"
GRAFICOS_DIR = PROJECT_DIR / "graficos"
GRAFICOS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Paleta validada (dataviz skill) -- modo claro, para figuras de artigo
# ---------------------------------------------------------------------------
AZUL = "#2a78d6"
LARANJA = "#eb6834"
TINTA_PRIMARIA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_MUTED = "#898781"
GRADE = "#e1e0d9"
BASELINE = "#c3c2b7"
SUPERFICIE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": TINTA_SECUNDARIA,
    "text.color": TINTA_PRIMARIA,
    "xtick.color": TINTA_MUTED,
    "ytick.color": TINTA_MUTED,
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "savefig.facecolor": SUPERFICIE,
})

REGIOES_ORDEM = ["Norte", "Nordeste", "Centro-Oeste", "Sul", "Sudeste"]


def salvar_fig(fig, caminho: Path) -> None:
    """Salva a figura em memoria e grava em disco com retry.

    Evita um erro intermitente do Windows (OSError Invalid argument) que
    acontece quando algo (ex.: antivirus) escaneia o arquivo PNG no exato
    momento em que o matplotlib/PIL tenta abri-lo para escrita.
    """
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    dados = buffer.getvalue()
    for tentativa in range(5):
        try:
            with open(caminho, "wb") as f:
                f.write(dados)
            return
        except OSError:
            if tentativa == 4:
                raise
            time.sleep(0.5)


def estilo_eixo(ax):
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.grid(axis="y", color=GRADE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# Carrega dados ja gerados pelos Indicadores 1-4
# ---------------------------------------------------------------------------
mort_regiao = pd.read_csv(SAIDA_DIR / "mortalidade_trauma_2024_regioes.csv")
leitos_regiao = pd.read_csv(SAIDA_DIR / "uti_pediatrica_2024_regioes.csv")
estado = pd.read_csv(SAIDA_DIR / "analise_correlacao_sepse_por_estado.csv")

POPULACAO_REGIAO = {
    "Centro-Oeste": 17_071_595, "Nordeste": 57_112_096, "Norte": 18_669_345,
    "Sudeste": 88_617_693, "Sul": 31_113_021,
}

# ---------------------------------------------------------------------------
# TABELA 1 - Comparativo por Regiao
# ---------------------------------------------------------------------------
tabela_regiao = []
for regiao in REGIOES_ORDEM:
    mort_total = mort_regiao[(mort_regiao["regiao"] == regiao) & (mort_regiao["sexo"] == "Total")]
    obitos = int(mort_total["quantidade_obitos"].iloc[0])
    leitos_exist = leitos_regiao[(leitos_regiao["regiao"] == regiao) & (leitos_regiao["medida"] == "Leitos existentes")]
    leitos_sus = leitos_regiao[(leitos_regiao["regiao"] == regiao) & (leitos_regiao["medida"] == "Leitos disponiveis ao SUS")]
    qt_exist = int(leitos_exist["quantidade_leitos"].iloc[0])
    qt_sus = int(leitos_sus["quantidade_leitos"].iloc[0])
    pop = POPULACAO_REGIAO[regiao]
    tabela_regiao.append({
        "regiao": regiao,
        "populacao_2024": pop,
        "obitos_trauma_1a12anos": obitos,
        "taxa_mortalidade_trauma_100mil": round(obitos / pop * 100000, 3),
        "leitos_uti_ped_existentes": qt_exist,
        "taxa_leitos_existentes_100mil": round(qt_exist / pop * 100000, 3),
        "leitos_uti_ped_sus": qt_sus,
        "taxa_leitos_sus_100mil": round(qt_sus / pop * 100000, 3),
    })
df_regiao = pd.DataFrame(tabela_regiao)

with pd.ExcelWriter(SAIDA_DIR / "tabela_comparativa_regioes.xlsx") as writer:
    df_regiao.to_excel(writer, index=False, sheet_name="por_regiao")
df_regiao.to_csv(SAIDA_DIR / "tabela_comparativa_regioes.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# TABELA 2 - Comparativo por Estado
# ---------------------------------------------------------------------------
df_estado = estado.rename(columns={
    "mortalidade_trauma_1a12anos": "obitos_trauma_1a12anos",
    "sepse_causa_basica_A40_A41": "obitos_sepse_causabasica_1a12anos",
    "sepse_mencionada_qualquer_linha": "obitos_sepse_mencionada_1a12anos",
})[[
    "uf", "populacao_2024_ibge",
    "obitos_trauma_1a12anos", "taxa_mortalidade_por_100mil_hab",
    "obitos_sepse_causabasica_1a12anos", "taxa_sepse_causabasica_por_100mil_hab",
    "obitos_sepse_mencionada_1a12anos", "taxa_sepse_mencionada_por_100mil_hab",
    "leitos_uti_ped_existentes", "taxa_leitos_existentes_por_100mil_hab",
    "leitos_uti_ped_sus", "taxa_leitos_sus_por_100mil_hab",
]].sort_values("uf").reset_index(drop=True)

with pd.ExcelWriter(SAIDA_DIR / "tabela_comparativa_estados.xlsx") as writer:
    df_estado.to_excel(writer, index=False, sheet_name="por_estado")
df_estado.to_csv(SAIDA_DIR / "tabela_comparativa_estados.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# TABELA 3 - Resumo das correlacoes ja calculadas (Indicadores 3 e 4)
# ---------------------------------------------------------------------------
def r_p(x, y):
    r, p = stats.pearsonr(x, y)
    return round(r, 3), round(p, 3)

r1, p1 = r_p(estado["taxa_mortalidade_por_100mil_hab"], estado["taxa_leitos_existentes_por_100mil_hab"])
r2, p2 = r_p(estado["taxa_mortalidade_por_100mil_hab"], estado["taxa_leitos_sus_por_100mil_hab"])
r3, p3 = r_p(estado["taxa_sepse_causabasica_por_100mil_hab"], estado["taxa_leitos_existentes_por_100mil_hab"])
r4, p4 = r_p(estado["taxa_sepse_causabasica_por_100mil_hab"], estado["taxa_leitos_sus_por_100mil_hab"])
r5, p5 = r_p(estado["taxa_sepse_mencionada_por_100mil_hab"], estado["taxa_leitos_existentes_por_100mil_hab"])
r6, p6 = r_p(estado["taxa_sepse_mencionada_por_100mil_hab"], estado["taxa_leitos_sus_por_100mil_hab"])

resumo_corr = pd.DataFrame([
    {"desfecho": "Trauma (1-12 anos)", "medida_leito": "Leitos existentes", "nivel": "Estado (n=27)", "r": r1, "p_valor": p1, "significativo_5pct": p1 < 0.05},
    {"desfecho": "Trauma (1-12 anos)", "medida_leito": "Leitos SUS", "nivel": "Estado (n=27)", "r": r2, "p_valor": p2, "significativo_5pct": p2 < 0.05},
    {"desfecho": "Sepse - causa basica A40/A41", "medida_leito": "Leitos existentes", "nivel": "Estado (n=27)", "r": r3, "p_valor": p3, "significativo_5pct": p3 < 0.05},
    {"desfecho": "Sepse - causa basica A40/A41", "medida_leito": "Leitos SUS", "nivel": "Estado (n=27)", "r": r4, "p_valor": p4, "significativo_5pct": p4 < 0.05},
    {"desfecho": "Sepse - mencionada em qualquer linha", "medida_leito": "Leitos existentes", "nivel": "Estado (n=27)", "r": r5, "p_valor": p5, "significativo_5pct": p5 < 0.05},
    {"desfecho": "Sepse - mencionada em qualquer linha", "medida_leito": "Leitos SUS", "nivel": "Estado (n=27)", "r": r6, "p_valor": p6, "significativo_5pct": p6 < 0.05},
])
with pd.ExcelWriter(SAIDA_DIR / "tabela_resumo_correlacoes.xlsx") as writer:
    resumo_corr.to_excel(writer, index=False, sheet_name="correlacoes")
resumo_corr.to_csv(SAIDA_DIR / "tabela_resumo_correlacoes.csv", index=False, encoding="utf-8-sig")

print("Tabelas salvas em saida/: tabela_comparativa_regioes, tabela_comparativa_estados, tabela_resumo_correlacoes")

# ---------------------------------------------------------------------------
# GRAFICO 1 - Mortalidade por trauma, taxa /100mil hab, por regiao
# ---------------------------------------------------------------------------
df1 = df_regiao.sort_values("taxa_mortalidade_trauma_100mil", ascending=True)
fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
barras = ax.barh(df1["regiao"], df1["taxa_mortalidade_trauma_100mil"], color=AZUL, height=0.6, zorder=3)
for barra, valor in zip(barras, df1["taxa_mortalidade_trauma_100mil"]):
    ax.text(valor + 0.03, barra.get_y() + barra.get_height() / 2, f"{valor:.2f}",
            va="center", ha="left", fontsize=10, color=TINTA_PRIMARIA)
estilo_eixo(ax)
ax.set_xlabel("Óbitos por trauma (1-12 anos) por 100 mil habitantes — 2024")
ax.set_title("Mortalidade por trauma em crianças (1-12 anos), por região", fontsize=12, pad=14, color=TINTA_PRIMARIA, loc="left")
fig.tight_layout()
salvar_fig(fig, GRAFICOS_DIR / "01_mortalidade_trauma_por_regiao.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# GRAFICO 2 - Leitos UTI Ped (existentes x SUS), taxa /100mil hab, por regiao
# ---------------------------------------------------------------------------
df2 = df_regiao.sort_values("taxa_leitos_existentes_100mil", ascending=True)
y = np.arange(len(df2))
altura = 0.35
fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
ax.barh(y + altura / 2, df2["taxa_leitos_existentes_100mil"], height=altura, color=AZUL, label="Leitos existentes", zorder=3)
ax.barh(y - altura / 2, df2["taxa_leitos_sus_100mil"], height=altura, color=LARANJA, label="Leitos disponíveis ao SUS", zorder=3)
ax.set_yticks(y)
ax.set_yticklabels(df2["regiao"])
estilo_eixo(ax)
ax.set_xlabel("Leitos de UTI Pediátrica por 100 mil habitantes — dez/2024")
ax.set_title("Leitos de UTI Pediátrica, por região", fontsize=12, pad=14, color=TINTA_PRIMARIA, loc="left")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
salvar_fig(fig, GRAFICOS_DIR / "02_leitos_uti_ped_por_regiao.png")
plt.close(fig)


# ---------------------------------------------------------------------------
# Graficos de dispersao (por estado, n=27) com linha de tendencia e r/p
# ---------------------------------------------------------------------------
def grafico_dispersao(x, y, rotulos, titulo, xlabel, ylabel, nome_arquivo, cor):
    r, p = stats.pearsonr(x, y)
    coef = np.polyfit(x, y, 1)
    linha_x = np.linspace(x.min(), x.max(), 100)
    linha_y = np.polyval(coef, linha_x)

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=150)
    ax.plot(linha_x, linha_y, color=TINTA_MUTED, linewidth=1.5, linestyle="--", zorder=2)
    ax.scatter(x, y, s=46, color=cor, edgecolor=SUPERFICIE, linewidth=0.8, zorder=3)
    for xi, yi, rot in zip(x, y, rotulos):
        ax.annotate(rot, (xi, yi), textcoords="offset points", xytext=(5, 4),
                    fontsize=8, color=TINTA_SECUNDARIA)
    estilo_eixo(ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo, fontsize=12, pad=14, color=TINTA_PRIMARIA, loc="left")
    sig = "significativo" if p < 0.05 else "não significativo"
    ax.text(0.98, 0.03, f"r = {r:.2f}   p = {p:.2f}  ({sig} a 5%)\nn = 27 estados",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=9, color=TINTA_SECUNDARIA)
    fig.tight_layout()
    salvar_fig(fig, GRAFICOS_DIR / nome_arquivo)
    plt.close(fig)


grafico_dispersao(
    estado["taxa_leitos_existentes_por_100mil_hab"], estado["taxa_mortalidade_por_100mil_hab"],
    estado["uf"],
    "Mortalidade por trauma × Leitos de UTI Ped. existentes (por estado)",
    "Leitos existentes por 100 mil hab.", "Óbitos por trauma (1-12 anos) por 100 mil hab.",
    "03_dispersao_trauma_x_leitos_existentes.png", AZUL,
)

grafico_dispersao(
    estado["taxa_leitos_sus_por_100mil_hab"], estado["taxa_mortalidade_por_100mil_hab"],
    estado["uf"],
    "Mortalidade por trauma × Leitos de UTI Ped. SUS (por estado)",
    "Leitos disponíveis ao SUS por 100 mil hab.", "Óbitos por trauma (1-12 anos) por 100 mil hab.",
    "04_dispersao_trauma_x_leitos_sus.png", AZUL,
)

grafico_dispersao(
    estado["taxa_leitos_sus_por_100mil_hab"], estado["taxa_sepse_causabasica_por_100mil_hab"],
    estado["uf"],
    "Mortalidade por sepse (causa básica) × Leitos de UTI Ped. SUS (por estado)",
    "Leitos disponíveis ao SUS por 100 mil hab.", "Óbitos por sepse (1-12 anos) por 100 mil hab.",
    "05_dispersao_sepse_x_leitos_sus.png", LARANJA,
)

# ---------------------------------------------------------------------------
# GRAFICO 6 - Comparacao trauma x sepse (causa basica), taxa por estado
# ---------------------------------------------------------------------------
df6 = estado.sort_values("taxa_mortalidade_por_100mil_hab", ascending=True)
y = np.arange(len(df6))
altura = 0.38
fig, ax = plt.subplots(figsize=(7.5, 9), dpi=150)
ax.barh(y + altura / 2, df6["taxa_mortalidade_por_100mil_hab"], height=altura, color=AZUL, label="Trauma", zorder=3)
ax.barh(y - altura / 2, df6["taxa_sepse_causabasica_por_100mil_hab"], height=altura, color=LARANJA, label="Sepse (causa básica)", zorder=3)
ax.set_yticks(y)
ax.set_yticklabels(df6["uf"])
estilo_eixo(ax)
ax.set_xlabel("Óbitos por 100 mil habitantes — 2024 (crianças de 1-12 anos)")
ax.set_title("Mortalidade por trauma x sepse, por estado", fontsize=12, pad=14, color=TINTA_PRIMARIA, loc="left")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
salvar_fig(fig, GRAFICOS_DIR / "06_comparacao_trauma_sepse_por_estado.png")
plt.close(fig)

print("Graficos salvos em graficos/: 01 a 06.")
