"""
Coleta de dados oficiais de leitos de UTI Pediatrica no SUS, por regiao do Brasil.

Fonte oficial: CNES - Cadastro Nacional de Estabelecimentos de Saude
(Ministerio da Saude / DATASUS), modulo de Leitos (LT), arquivos publicos em:
    ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/LT/

Por que o CNES (e nao o SIM usado no script de mortalidade):
    O CNES e o cadastro oficial de TODOS os estabelecimentos de saude do
    Brasil e de sua capacidade instalada (leitos, equipamentos, profissionais).
    E a unica base do SUS que registra QUANTOS leitos de UTI Pediatrica
    existem e estao disponiveis, mes a mes. O SIM (mortalidade) nao tem
    essa informacao.

Diferenca importante em relacao ao indicador de mortalidade:
    Leitos sao um "estoque" (retrato de um momento), nao um "evento" somado
    ao longo do ano como obitos. Por isso, para representar o ano de
    referencia, usamos a competencia de DEZEMBRO desse ano (ultimo mes),
    que e a pratica usual ao reportar leitos "do ano X".

Como este script define "UTI Pediatrica":
    Usa exclusivamente os codigos oficiais e ATIVOS da tabela "Tipo de Leito"
    do CNES:
        78 = UTI Pediatrica - Tipo II
        79 = UTI Pediatrica - Tipo III
    (O antigo codigo 77, referente a "UTI Pediatrica Tipo I", nao consta mais
    na tabela oficial vigente do CNES -- foi reclassificado por portaria do
    Ministerio da Saude em 2019 para "Unidade de Cuidados Intermediarios
    Pediatrica" (codigo 94), que e um nivel de cuidado diferente de UTI.
    Por isso os codigos 77 e 94 NAO entram nesta contagem.)

O que este script faz, passo a passo:
    1. Conecta no FTP publico do DATASUS e baixa o arquivo de leitos (.dbc)
       de cada estado (UF) para a competencia configurada.
    2. Converte cada arquivo .dbc para .dbf usando a ferramenta oficial
       "pyreaddbc".
    3. Filtra os registros com CODLEITO 78 ou 79.
    4. Agrupa (soma) por Regiao do Brasil, tanto os leitos "existentes"
       (QT_EXIST) quanto os leitos "disponiveis ao SUS" (QT_SUS) -- sao
       duas medidas oficiais diferentes, ambas incluidas para nao decidir
       por voce qual usar no artigo.
    5. Salva os resultados agregados em CSV e Excel dentro da pasta "saida".

Nao inventa nem preenche nenhum valor ausente: se um estado nao tiver
arquivo publicado para a competencia pedida, ele e reportado como ausente
no log, e nao e substituido por zero nem por estimativa.

Como atualizar no futuro (por exemplo, para o ano de 2025):
    - Basta mudar a variavel COMPETENCIA_ANO abaixo para 2025 e rodar de novo.
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

COMPETENCIA_ANO = 2024
COMPETENCIA_MES = 12  # Dezembro = retrato de fim de ano, mesma logica do TABNET

# Codigos oficiais e ATIVOS de "UTI Pediatrica" na tabela Tipo de Leito do CNES
# (fonte: https://cnes2.datasus.gov.br/Mod_Ind_Tipo_Leito.asp -- conferido em
# 07/09/2026). Ver docstring acima para o motivo de excluir os codigos 77 e 94.
CODIGOS_UTI_PEDIATRICA = {"78", "79"}

FTP_HOST = "ftp.datasus.gov.br"
FTP_DIR = "/dissemin/publicos/CNES/200508_/Dados/LT"

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


def competencia_aammdd() -> str:
    """Formato usado nos nomes de arquivo do CNES: AAMM (ano+mes, 2 digitos cada)."""
    return f"{COMPETENCIA_ANO % 100:02d}{COMPETENCIA_MES:02d}"


def listar_arquivos_competencia(ftp: ftplib.FTP) -> dict:
    """Lista no FTP oficial os arquivos de leitos disponiveis para a competencia.

    Retorna um dicionario {UF: nome_do_arquivo}.
    """
    todos = ftp.nlst()
    comp = competencia_aammdd()
    encontrados = {}
    for nome in todos:
        m = re.match(rf"^LT([A-Z]{{2}}){comp}\.dbc$", nome, re.IGNORECASE)
        if m:
            uf = m.group(1).upper()
            encontrados[uf] = nome
    return encontrados


def baixar_arquivo(ftp: ftplib.FTP, nome_remoto: str, destino: Path) -> None:
    with open(destino, "wb") as f:
        ftp.retrbinary(f"RETR {nome_remoto}", f.write)


def processar_uf(uf: str, dbc_path: Path) -> pd.DataFrame:
    """Converte o .dbc, le os leitos e devolve so os registros de UTI Pediatrica."""
    short_dbc = get_short_path(dbc_path)
    dbf_path = dbc_path.with_suffix(".dbf")

    dbc2dbf(short_dbc, get_short_path(dbc_path.parent) + f"\\{dbf_path.name}")

    tabela = DBF(get_short_path(dbf_path), encoding="latin1")
    linhas = []
    for registro in tabela:
        codleito = str(registro.get("CODLEITO") or "").strip()
        if codleito not in CODIGOS_UTI_PEDIATRICA:
            continue

        def _num(campo):
            try:
                return int(registro.get(campo) or 0)
            except (TypeError, ValueError):
                return 0

        linhas.append(
            {
                "uf": uf,
                "cnes": str(registro.get("CNES") or "").strip(),
                "codleito": codleito,
                "qt_exist": _num("QT_EXIST"),
                "qt_sus": _num("QT_SUS"),
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

    comp = competencia_aammdd()
    print(f"Conectando em ftp://{FTP_HOST}{FTP_DIR} (competencia {comp}) ...")
    ftp = ftplib.FTP(FTP_HOST, timeout=60)
    ftp.login()
    ftp.cwd(FTP_DIR)

    arquivos_disponiveis = listar_arquivos_competencia(ftp)
    print(f"Arquivos encontrados na fonte oficial para {comp}: "
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
        print(f"    -> {len(df_uf)} registro(s) de leito de UTI Pediatrica "
              f"em {uf} (soma QT_EXIST={df_uf['qt_exist'].sum() if len(df_uf) else 0})")

    ftp.quit()

    dados = pd.concat(todos_registros, ignore_index=True)
    dados["regiao"] = dados["uf"].map(REGIAO_POR_UF)

    # ---- Agregacao: Regiao (soma dos leitos existentes e dos leitos SUS) ----
    linhas_saida = []
    for regiao in sorted(set(REGIAO_POR_UF.values())):
        sub = dados[dados["regiao"] == regiao]
        qt_exist = int(sub["qt_exist"].sum())
        qt_sus = int(sub["qt_sus"].sum())

        for medida_label, qtd in [
            ("Leitos existentes", qt_exist),
            ("Leitos disponiveis ao SUS", qt_sus),
        ]:
            linhas_saida.append(
                {
                    "periodo": COMPETENCIA_ANO,
                    "competencia": comp,
                    "regiao": regiao,
                    "indicador": "Leitos de UTI Pediatrica",
                    "medida": medida_label,
                    "quantidade_leitos": qtd,
                    "filtro_codleito": "78 (UTI Pediatrica Tipo II) e "
                                        "79 (UTI Pediatrica Tipo III)",
                    "fonte": "CNES/DATASUS - ftp://ftp.datasus.gov.br"
                             "/dissemin/publicos/CNES/200508_/Dados/LT/",
                }
            )

    resultado = pd.DataFrame(linhas_saida)

    csv_path = SAIDA_DIR / f"uti_pediatrica_{COMPETENCIA_ANO}_regioes.csv"
    xlsx_path = SAIDA_DIR / f"uti_pediatrica_{COMPETENCIA_ANO}_regioes.xlsx"
    resultado.to_csv(csv_path, index=False, encoding="utf-8-sig")
    resultado.to_excel(xlsx_path, index=False, sheet_name="uti_pediatrica")

    print(f"\nConcluido. Arquivos gerados:\n  {csv_path}\n  {xlsx_path}")


if __name__ == "__main__":
    sys.exit(main())
