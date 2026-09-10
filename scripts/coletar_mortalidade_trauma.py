"""
Coleta de dados oficiais de mortalidade por trauma (causas externas) no SUS.

Fonte oficial: SIM - Sistema de Informacao sobre Mortalidade (Ministerio da
Saude / DATASUS), arquivos publicos de microdados disponibilizados em:
    ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/

O que este script faz, passo a passo:
    1. Conecta no FTP publico do DATASUS e baixa o arquivo de obitos (.dbc)
       de cada estado (UF) para o ano configurado.
    2. Converte cada arquivo .dbc (formato compactado do DATASUS) para .dbf
       usando a ferramenta oficial "pyreaddbc".
    3. Le os registros e filtra:
         - Idade entre 1 e 12 anos (campo IDADE, codigo "4" + 01 a 12)
         - Causa basica do obito (CAUSABAS) nos capitulos V, W, X ou Y do
           CID-10 (V01 a Y98) = "Causas externas de morbidade e mortalidade",
           que e a classificacao oficial de mortes por trauma/acidente/violencia.
    4. Agrupa o resultado por Regiao do Brasil e por sexo.
    5. Salva os resultados agregados em CSV e Excel dentro da pasta "saida".

Nao inventa nem preenche nenhum valor ausente: se um estado nao tiver arquivo
para o ano pedido, ele e reportado como ausente no log, e nao e substituido
por zero nem por estimativa.

Como atualizar no futuro (por exemplo, quando o ano de 2025 for publicado):
    - Basta mudar a variavel ANO abaixo para 2025 e rodar o script de novo.
"""

import ctypes
import ftplib
import os
import re
import sys
from pathlib import Path

import pandas as pd
from dbfread import DBF
from pyreaddbc import dbc2dbf

# ---------------------------------------------------------------------------
# CONFIGURACAO
# ---------------------------------------------------------------------------

ANO = 2024  # Ano dos dados. 2025 ainda nao estava disponivel na fonte oficial
            # na data da coleta (ver README.md). Troque aqui quando publicarem.

IDADE_MIN_ANOS = 1
IDADE_MAX_ANOS = 12

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIR = "/dissemin/publicos/SIM/CID10/DORES"

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw_cache"
SAIDA_DIR = PROJECT_DIR / "saida"

# Mapeamento oficial IBGE: Unidade da Federacao -> Regiao do Brasil
REGIAO_POR_UF = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
}

CID10_TRAUMA_REGEX = re.compile(r"^[VWXY]\d{2}")

# No campo IDADE do SIM, o primeiro digito "4" significa "idade em anos" e os
# dois digitos seguintes sao o valor. Ex.: "401" = 1 ano, "412" = 12 anos.
IDADE_CODES_VALIDOS = {
    f"4{n:02d}" for n in range(IDADE_MIN_ANOS, IDADE_MAX_ANOS + 1)
}


def get_short_path(path: Path) -> str:
    """Retorna um caminho equivalente sem acentos (nome curto do Windows).

    Necessario porque a biblioteca de conversao de arquivos do DATASUS
    (pyreaddbc, escrita em C) tem um bug conhecido com caracteres acentuados
    no caminho do arquivo. O nome curto aponta para a MESMA pasta -- nao
    move nem copia nada para fora do projeto.
    """
    buf = ctypes.create_unicode_buffer(260)
    ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, 260)
    return buf.value


def listar_arquivos_ano(ftp: ftplib.FTP, ano: int) -> dict:
    """Lista no FTP oficial os arquivos de obitos disponiveis para o ano.

    Retorna um dicionario {UF: nome_do_arquivo}.
    """
    todos = ftp.nlst()
    encontrados = {}
    for nome in todos:
        m = re.match(rf"^DO([A-Z]{{2}}){ano}\.dbc$", nome, re.IGNORECASE)
        if m:
            uf = m.group(1).upper()
            encontrados[uf] = nome
    return encontrados


def baixar_arquivo(ftp: ftplib.FTP, nome_remoto: str, destino: Path) -> None:
    with open(destino, "wb") as f:
        ftp.retrbinary(f"RETR {nome_remoto}", f.write)


def processar_uf(uf: str, dbc_path: Path) -> pd.DataFrame:
    """Converte o .dbc, le os obitos e devolve so os registros filtrados."""
    short_dbc = get_short_path(dbc_path)
    dbf_path = dbc_path.with_suffix(".dbf")

    dbc2dbf(short_dbc, get_short_path(dbc_path.parent) + f"\\{dbf_path.name}")

    tabela = DBF(get_short_path(dbf_path), encoding="latin1")
    linhas = []
    for registro in tabela:
        causa = str(registro.get("CAUSABAS") or "").strip()
        idade_raw = str(registro.get("IDADE") or "").strip().zfill(3)
        sexo_cod = str(registro.get("SEXO") or "").strip()

        if not CID10_TRAUMA_REGEX.match(causa):
            continue
        if idade_raw not in IDADE_CODES_VALIDOS:
            continue

        idade_anos = int(idade_raw[1:])
        sexo = {"1": "Masculino", "2": "Feminino"}.get(sexo_cod, "Ignorado")

        linhas.append(
            {
                "uf": uf,
                "idade_anos": idade_anos,
                "sexo": sexo,
                "causabas": causa,
            }
        )

    # Remove o .dbf intermediario (mantemos so o .dbc original como fonte bruta)
    try:
        os.remove(dbf_path)
    except OSError:
        pass

    return pd.DataFrame(linhas)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Conectando em ftp://{FTP_HOST}{FTP_DIR} ...")
    ftp = ftplib.FTP(FTP_HOST, timeout=60)
    ftp.login()
    ftp.cwd(FTP_DIR)

    arquivos_disponiveis = listar_arquivos_ano(ftp, ANO)
    print(f"Arquivos encontrados na fonte oficial para {ANO}: "
          f"{len(arquivos_disponiveis)} de {len(REGIAO_POR_UF)} UFs.")

    ausentes = sorted(set(REGIAO_POR_UF) - set(arquivos_disponiveis))
    if ausentes:
        print(f"AVISO: sem arquivo publicado para: {', '.join(ausentes)} "
              f"(nao serao inventados valores para essas UFs).")

    todos_registros = []
    for uf in sorted(REGIAO_POR_UF):
        if uf not in arquivos_disponiveis:
            continue
        nome_remoto = arquivos_disponiveis[uf]
        destino = RAW_DIR / nome_remoto
        if not destino.exists():
            print(f"  Baixando {nome_remoto} ...")
            baixar_arquivo(ftp, nome_remoto, destino)
        else:
            print(f"  {nome_remoto} ja baixado, reaproveitando.")

        print(f"  Processando {uf} ...")
        df_uf = processar_uf(uf, destino)
        todos_registros.append(df_uf)
        print(f"    -> {len(df_uf)} obitos por trauma (1-12 anos) em {uf}")

    ftp.quit()

    dados = pd.concat(todos_registros, ignore_index=True)
    dados["regiao"] = dados["uf"].map(REGIAO_POR_UF)

    # ---- Agregacao: Regiao x Sexo (+ Total) ----
    linhas_saida = []
    for regiao in sorted(set(REGIAO_POR_UF.values())):
        sub = dados[dados["regiao"] == regiao]
        total = len(sub)
        masc = len(sub[sub["sexo"] == "Masculino"])
        fem = len(sub[sub["sexo"] == "Feminino"])
        ignorado = len(sub[sub["sexo"] == "Ignorado"])

        for sexo_label, qtd in [
            ("Total", total),
            ("Masculino", masc),
            ("Feminino", fem),
        ]:
            linhas_saida.append(
                {
                    "periodo": ANO,
                    "regiao": regiao,
                    "indicador": "Mortalidade por trauma (causas externas)",
                    "faixa_etaria": f"{IDADE_MIN_ANOS} a {IDADE_MAX_ANOS} anos",
                    "sexo": sexo_label,
                    "quantidade_obitos": qtd,
                    "filtro_cid10": "V01-Y98 (Cap. XX CID-10 - Causas externas)",
                    "fonte": "SIM/DATASUS - ftp://ftp.datasus.gov.br"
                             "/dissemin/publicos/SIM/CID10/DORES/",
                }
            )
        if ignorado > 0:
            print(f"  Nota: {ignorado} registro(s) em {regiao} com sexo "
                  f"ignorado no campo original (incluidos no Total, nao "
                  f"somados em Masculino/Feminino).")

    resultado = pd.DataFrame(linhas_saida)

    csv_path = SAIDA_DIR / f"mortalidade_trauma_{ANO}_regioes.csv"
    xlsx_path = SAIDA_DIR / f"mortalidade_trauma_{ANO}_regioes.xlsx"
    resultado.to_csv(csv_path, index=False, encoding="utf-8-sig")
    resultado.to_excel(xlsx_path, index=False, sheet_name="mortalidade_trauma")

    print(f"\nConcluido. Arquivos gerados:\n  {csv_path}\n  {xlsx_path}")


if __name__ == "__main__":
    sys.exit(main())
