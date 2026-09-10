"""
Teste exploratorio: mortalidade por sepse (CID-10 A40-A41) em criancas de
1 a 12 anos, por estado -- para avaliar se vale a pena migrar o artigo para
esse desfecho.

Reaproveita os arquivos .dbc de mortalidade ja baixados em data/raw_cache/
(nenhum download novo). Nao decide nada sozinho: so mede e reporta.
"""

import re
import sys
from pathlib import Path

import pandas as pd
from dbfread import DBF

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coletar_mortalidade_trauma as mort_mod  # noqa: E402  (reaproveita get_short_path, dbc2dbf etc.)

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw_cache"

IDADE_CODES_VALIDOS = {f"4{n:02d}" for n in range(1, 13)}  # 1 a 12 anos
SEPSE_CAUSABAS_REGEX = re.compile(r"^A4[01]")  # A40 e A41 = Septicemia (causa basica)

# Para medir o tamanho do "subregistro": sepse mencionada em qualquer linha
# da declaracao de obito (causa associada), mesmo quando NAO e a causa basica.
CAMPOS_CAUSA_ASSOCIADA = ["LINHAA", "LINHAB", "LINHAC", "LINHAD", "LINHAII"]
SEPSE_OU_CHOQUE_SEPTICO_REGEX = re.compile(r"A4[01]|R572")


def ler_dbf_bruto(dbc_path: Path) -> pd.DataFrame:
    short_dbc = mort_mod.get_short_path(dbc_path)
    dbf_path = dbc_path.with_suffix(".dbf")
    from pyreaddbc import dbc2dbf
    dbc2dbf(short_dbc, mort_mod.get_short_path(dbc_path.parent) + f"\\{dbf_path.name}")
    tabela = DBF(mort_mod.get_short_path(dbf_path), encoding="latin1")
    df = pd.DataFrame(iter(tabela))
    try:
        import os
        os.remove(dbf_path)
    except OSError:
        pass
    return df


def main():
    linhas = []
    for uf in sorted(mort_mod.REGIAO_POR_UF):
        candidatos = list(RAW_DIR.glob(f"DO{uf}2024.dbc")) + list(RAW_DIR.glob(f"DO{uf}2024.DBC"))
        if not candidatos:
            print(f"AVISO: sem arquivo em cache para {uf}")
            continue

        df = ler_dbf_bruto(candidatos[0])
        idade = df["IDADE"].astype(str).str.strip().str.zfill(3)
        idade_mask = idade.isin(IDADE_CODES_VALIDOS)

        causa = df["CAUSABAS"].astype(str).str.strip()
        sepse_basica_mask = causa.str.match(SEPSE_CAUSABAS_REGEX)

        criancas = df[idade_mask]
        obitos_1a12 = len(criancas)
        sepse_causa_basica = int((idade_mask & sepse_basica_mask).sum())

        # Sepse/choque septico mencionado em qualquer linha de causa associada,
        # entre os obitos de 1-12 anos (independente de qual foi a causa basica)
        sub = df[idade_mask].copy()
        texto_linhas = sub[CAMPOS_CAUSA_ASSOCIADA].astype(str).agg(" ".join, axis=1)
        sepse_mencionada = int(texto_linhas.str.contains(SEPSE_OU_CHOQUE_SEPTICO_REGEX, na=False).sum())

        linhas.append(
            {
                "uf": uf,
                "obitos_1a12_todas_causas": obitos_1a12,
                "sepse_causa_basica_A40_A41": sepse_causa_basica,
                "sepse_mencionada_qualquer_linha": sepse_mencionada,
            }
        )
        print(f"{uf}: obitos 1-12 (todas causas)={obitos_1a12}  "
              f"sepse (causa basica A40/A41)={sepse_causa_basica}  "
              f"sepse mencionada em qualquer linha={sepse_mencionada}")

    resultado = pd.DataFrame(linhas)
    print()
    print("Total Brasil - obitos 1-12 todas causas:", resultado["obitos_1a12_todas_causas"].sum())
    print("Total Brasil - sepse causa basica A40/A41:", resultado["sepse_causa_basica_A40_A41"].sum())
    print("Total Brasil - sepse mencionada em qualquer linha:", resultado["sepse_mencionada_qualquer_linha"].sum())
    print("Estados com ZERO obitos por sepse (causa basica):",
          (resultado["sepse_causa_basica_A40_A41"] == 0).sum(), "de", len(resultado))

    resultado.to_csv(PROJECT_DIR / "data" / "teste" / "teste_sepse_por_estado.csv", index=False)


if __name__ == "__main__":
    main()
