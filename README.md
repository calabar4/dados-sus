# Dados Oficiais do SUS — Trauma Infantil (1 a 12 anos)

Dados públicos oficiais coletados do SUS para uso em artigo científico.
Este projeto reúne dois indicadores de coleta, duas análises de correlação
derivadas deles, e um conjunto de gráficos/tabelas comparativas, todos para
o ano de 2024:

1. **Mortalidade por trauma** em crianças/adolescentes de 1 a 12 anos (fonte: SIM), por região.
2. **Leitos de UTI Pediátrica** disponíveis no país (fonte: CNES), por região.
3. **Análise:** correlação entre mortalidade por trauma e leitos de UTI Pediátrica, por região e por estado.
4. **Análise:** o mesmo teste trocando o desfecho para mortalidade por sepse, por estado.
5. **Gráficos e tabelas comparativas** prontos para uso no artigo.

---

# Indicador 1 — Mortalidade por Trauma (Causas Externas)

## 1.1 Fonte oficial dos dados

- **Base:** SIM — Sistema de Informação sobre Mortalidade (Ministério da Saúde / DATASUS).
- **O que é:** o registro oficial de todos os óbitos ocorridos no Brasil, com causa (CID-10), idade, sexo e local de residência.
- **URL da fonte (arquivos públicos originais):**
  `ftp://ftp.datasus.gov.br/dissemin/publicos/SIM/CID10/DORES/`
- **Página oficial para conferência manual (TABNET):** http://tabnet.datasus.gov.br/
  (menu: Estatísticas Vitais → Mortalidade → Óbitos por Causas Externas desde 1996 pela CID-10)
- **Data da coleta:** 07/09/2026.

Não foi feito "scraping" de páginas web: os dados vieram diretamente dos arquivos brutos que o próprio Ministério da Saúde disponibiliza para download público (mesmo formato usado por pesquisadores e pelo próprio TABNET).

## 1.2 Ano dos dados: 2024 (não 2025)

O pedido original era para o ano de **2025**. Na data da coleta, **2025 ainda não estava publicado** na fonte oficial — a base de mortalidade (SIM) demora normalmente de 1 a 2 anos para fechar um ano, principalmente em óbitos por causas externas, que exigem investigação (IML, perícia) antes de fechar o CID-10.

Verificamos diretamente no servidor oficial e o **último ano disponível era 2024**. Por isso, seguindo a decisão combinada, os dados aqui são de **2024**, o ano mais recente já consolidado e publicado. O indicador de leitos (seção 2) usa o mesmo ano, para manter os dois indicadores comparáveis.

**Para atualizar quando 2025 for publicado:** abra `scripts/coletar_mortalidade_trauma.py`, troque o número na linha `ANO = 2024` para `ANO = 2025`, salve e rode o script de novo (veja seção 1.6).

## 1.3 Filtros aplicados

| Filtro | Valor usado | Observação |
|---|---|---|
| Idade | 1 a 12 anos | Campo `IDADE` do SIM, código "4" (anos) + valor de 01 a 12 |
| Sexo | Ambos | Reportado como Total, Masculino e Feminino separadamente |
| Local | Regiões do Brasil | Norte, Nordeste, Sudeste, Sul, Centro-Oeste (mapeamento oficial IBGE por estado) |
| Causa (CID-10) | **V01 a Y98** | Ver nota importante abaixo |

### Nota importante sobre o filtro de CID-10

O pedido original especificava os códigos **S00–S99 e T00–T98**. Testamos esse filtro nos dados reais e ele retornou **zero óbitos** — porque no atestado de óbito brasileiro, a "causa básica" de mortes por trauma/acidente/violência é sempre registrada com um código dos capítulos **V, W, X ou Y** do CID-10 (que descrevem a *circunstância* da morte, ex.: "V09.3 = pedestre atropelado"). Os códigos S00–T98 descrevem a *natureza da lesão* (ex.: "fratura de crânio") e são o padrão usado em **dados de internação hospitalar (SIH)**, não em óbitos (SIM).

Essa mudança foi **combinada e aprovada** antes de rodar a coleta final. É exatamente o filtro que a própria tabela oficial do TABNET usa em "Óbitos por Causas Externas".

## 1.4 Significado das colunas (arquivo de saída)

Arquivos: `saida/mortalidade_trauma_2024_regioes.csv` e `.xlsx`

| Coluna | Significado |
|---|---|
| `periodo` | Ano de referência dos óbitos (2024) |
| `regiao` | Região do Brasil (Norte, Nordeste, Sudeste, Sul, Centro-Oeste) |
| `indicador` | Nome do indicador: "Mortalidade por trauma (causas externas)" |
| `faixa_etaria` | Faixa etária filtrada: "1 a 12 anos" |
| `sexo` | "Total" (todos os óbitos), "Masculino" ou "Feminino" |
| `quantidade_obitos` | Número absoluto de óbitos (contagem, não taxa) |
| `filtro_cid10` | Faixa de código CID-10 usada para definir "trauma" |
| `fonte` | Endereço oficial de onde os dados foram baixados |

**Atenção:** `quantidade_obitos` é uma **contagem absoluta**, não uma taxa por habitante. Para calcular taxas de mortalidade (por 100 mil habitantes, por exemplo) seria necessário cruzar com dados populacionais do IBGE, o que não foi feito aqui.

Em uma região (Sul), houve 1 óbito com o campo "sexo" preenchido como ignorado na fonte original — esse caso está incluído em "Total" mas não em "Masculino" nem "Feminino" (por isso a soma de M+F pode ficar 1 a menos que o Total nessa região). Nenhum valor foi inventado ou estimado para substituir essa informação ausente.

## 1.5 Como conferir manualmente (auditoria)

1. Acesse http://tabnet.datasus.gov.br/
2. Vá em Estatísticas Vitais → Mortalidade → Óbitos por Causas Externas desde 1996 pela CID-10.
3. Selecione: Linha = Faixa Etária, Coluna = Sexo, Período = 2024, Abrangência = o estado ou região desejada.
4. Some manualmente as faixas etárias que cobrem 1 a 12 anos (o TABNET agrupa de 5 em 5 anos, não permite selecionar "1 a 12" diretamente — por isso este projeto usa os microdados brutos, que permitem esse recorte exato).
5. Compare com os números deste projeto: devem ficar bem próximos (pequenas diferenças de faixa etária são esperadas pela forma de agrupamento do TABNET).

## 1.6 Como atualizar os dados no futuro

1. Abra o arquivo `scripts/coletar_mortalidade_trauma.py` em um editor de texto simples (ex.: Bloco de Notas).
2. Se quiser outro ano, mude o número da linha `ANO = 2024`.
3. Abra o terminal PowerShell nesta pasta (`dados-sus`) e rode:
   ```
   .\venv\Scripts\python.exe .\scripts\coletar_mortalidade_trauma.py
   ```
4. Aguarde a mensagem "Concluido." — os arquivos novos aparecerão na pasta `saida/`.

O script não apaga nem sobrescreve arquivos `.dbc` já baixados (ele reaproveita o que já existir em `data/raw_cache/`), e nunca inventa ou completa dados que a fonte oficial não tiver disponível — estados sem arquivo publicado para o ano pedido aparecem como aviso no terminal, não como zero.

---

# Indicador 2 — Leitos de UTI Pediátrica

## 2.1 Fonte oficial dos dados

- **Base:** CNES — Cadastro Nacional de Estabelecimentos de Saúde (Ministério da Saúde / DATASUS), módulo de Leitos (LT).
- **Por que essa base e não o SIM:** o SIM (usado no Indicador 1) só tem dados de óbitos. O CNES é a única base do SUS que registra a capacidade instalada dos hospitais — quantos leitos de cada tipo existem, mês a mês, em cada estabelecimento de saúde do Brasil.
- **URL da fonte (arquivos públicos originais):**
  `ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/LT/`
- **Tabela oficial de códigos de tipo de leito (conferência dos códigos usados):**
  https://cnes2.datasus.gov.br/Mod_Ind_Tipo_Leito.asp?VEstado=00
- **Página oficial para conferência manual (TABNET):** http://tabnet.datasus.gov.br/ → CNES → Recursos Físicos → Leitos de Internação.
- **Data da coleta:** 07/09/2026.

## 2.2 Por que "dezembro/2024" e não "o ano de 2024"

Diferente de óbitos (que são eventos somados ao longo do ano), **leitos são um "estoque"**: o CNES publica uma fotografia da rede de saúde a cada mês. Não existe uma "soma anual de leitos" — o que se faz, inclusive no TABNET, é escolher um mês de referência. Usamos **dezembro de 2024** (competência `202412`), o retrato de fim de ano, mantendo o mesmo ano do Indicador 1.

**Para atualizar para outro ano/mês:** abra `scripts/coletar_uti_pediatrica.py` e troque `COMPETENCIA_ANO` e/ou `COMPETENCIA_MES`, depois rode o script de novo (veja seção 2.5).

## 2.3 Como "UTI Pediátrica" foi definida (importante)

O CNES classifica leitos por um código numérico (`CODLEITO`). Conferimos a tabela oficial vigente e usamos exclusivamente:

| Código | Descrição oficial |
|---|---|
| **78** | UTI Pediátrica — Tipo II |
| **79** | UTI Pediátrica — Tipo III |

**Códigos que ficaram de fora, de propósito:**
- **Código 77** ("UTI Pediátrica Tipo I" antigo): apareceu em pouquíssimos registros nos dados brutos, mas **não consta mais na tabela oficial vigente do CNES** — não é um código ativo, então não foi possível confirmar seu significado atual com uma fonte oficial. Para não incluir algo não confirmado, ele foi excluído.
- **Código 94** ("UCI-Ped" — Unidade de Cuidados Intermediários Pediátrica): é um nível de cuidado **abaixo** de UTI (cuidados intermediários, não intensivos). Inclusive, o antigo "UTI Pediátrica Tipo I" foi reclassificado para esse código por portaria do Ministério da Saúde em 2019. Como o pedido era especificamente por "UTI", esse código foi excluído.

Essa definição foi **combinada e aprovada** antes da coleta final.

## 2.4 Significado das colunas (arquivo de saída)

Arquivos: `saida/uti_pediatrica_2024_regioes.csv` e `.xlsx`

| Coluna | Significado |
|---|---|
| `periodo` | Ano de referência (2024) |
| `competencia` | Mês/ano exato dos dados no formato AAMM (2412 = dezembro/2024) |
| `regiao` | Região do Brasil |
| `indicador` | "Leitos de UTI Pediátrica" |
| `medida` | "Leitos existentes" (todos os leitos cadastrados, públicos e privados) ou "Leitos disponíveis ao SUS" (apenas os contratados/conveniados ao SUS) |
| `quantidade_leitos` | Número absoluto de leitos (soma de todos os estabelecimentos da região) |
| `filtro_codleito` | Quais códigos de tipo de leito foram somados |
| `fonte` | Endereço oficial de onde os dados foram baixados |

**Por que duas medidas (existentes x SUS)?** São dois números oficiais diferentes e igualmente válidos — "existentes" conta toda a capacidade instalada (incluindo leitos só de convênio/particular), "disponíveis ao SUS" conta só os que atendem pelo sistema público. Optamos por trazer os dois em vez de escolher um por você.

## 2.5 Como atualizar os dados no futuro

1. Abra `scripts/coletar_uti_pediatrica.py` em um editor de texto simples.
2. Mude `COMPETENCIA_ANO` e/ou `COMPETENCIA_MES` conforme desejado.
3. No PowerShell, nesta pasta (`dados-sus`), rode:
   ```
   .\venv\Scripts\python.exe .\scripts\coletar_uti_pediatrica.py
   ```
4. Aguarde "Concluido." — os arquivos novos aparecerão em `saida/`.

Assim como no Indicador 1, o script reaproveita arquivos `.dbc` já baixados e nunca inventa valores para estados sem arquivo publicado na competência pedida — eles aparecem como aviso no terminal.

## 2.6 Como conferir manualmente (auditoria)

1. Acesse http://tabnet.datasus.gov.br/
2. Vá em CNES → Recursos Físicos → Leitos de Internação (ou "Leitos Complementares", conforme o menu disponível).
3. Selecione Tipo de Leito = UTI Pediátrica (Tipo II e Tipo III), Competência = Dezembro/2024, Abrangência = o estado ou região desejada.
4. Compare o total com o número deste projeto. Pequenas diferenças podem ocorrer se o TABNET agrupar Tipo II e III de forma diferente da nossa soma manual — nesse caso, confira os dois tipos separadamente.

---

# Indicador 3 — Análise: correlação entre mortalidade por trauma e leitos de UTI Pediátrica

Pergunta original: existe correlação entre a mortalidade por trauma (1-12 anos) e o número de leitos de UTI Pediátrica, por localidade? Mais leitos parecem reduzir a mortalidade?

## 3.1 Método

- **Nível geográfico:** análise refeita por **estado (n=27)**, não por região (n=5), para ter poder estatístico suficiente para testar significância.
- **Dados reaproveitados** dos Indicadores 1 e 2 (nenhum download novo foi necessário — os arquivos brutos já estavam salvos em `data/raw_cache/`).
- **População por estado:** IBGE, Estimativas da população residente, referência 01/07/2024 (mesma fonte oficial): https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/estimativa_dou_2024.pdf
- **Por que taxas por 100 mil habitantes, e não números absolutos:** números absolutos de mortalidade e de leitos estão fortemente correlacionados com o tamanho da população do estado (r = 0,91 e r = 0,97, respectivamente) — isso por si só já cria uma correlação artificial forte entre os dois (r ≈ 0,85), mesmo sem nenhuma relação real entre eles. Por isso a análise correta usa **taxas por habitante**, não contagens brutas.
- **Script:** `scripts/analise_correlacao_por_estado.py` — Tabela completa: `saida/analise_correlacao_por_estado.csv`

## 3.2 Resultado

| Comparação (taxas por 100 mil hab.) | Correlação (r) | p-valor | Significativa a 5%? |
|---|---|---|---|
| Mortalidade × Leitos existentes | -0,19 | 0,35 | Não |
| Mortalidade × Leitos disponíveis ao SUS | +0,05 | 0,81 | Não |

## 3.3 Conclusão

**Não há evidência estatística de correlação entre o número de leitos de UTI Pediátrica e a mortalidade por trauma em crianças de 1 a 12 anos**, nem por região nem por estado. As correlações encontradas são fracas, mudam de sinal conforme a medida de leito usada, e não são estatisticamente significativas (p bem acima de 0,05) mesmo com as 27 unidades da federação.

Isso **não significa que UTIs não importem** — significa que, neste recorte (dados de um único ano, agregados por estado, sem controlar outros fatores), a capacidade de UTI Pediátrica não explica, sozinha, a variação da mortalidade por trauma entre estados. A mortalidade por trauma infantil provavelmente é determinada muito mais por fatores anteriores ao hospital (exposição a acidentes de trânsito e violência, tempo de resposta do socorro pré-hospitalar) do que pela quantidade de leitos de UTI disponíveis depois que o trauma já ocorreu.

## 3.4 Limitações (importantes para o artigo)

- Correlação ecológica simples (nível estado), sem controlar outras variáveis (trânsito, violência, renda, acesso a SAMU, distância a centros de trauma).
- Correlação não implica causalidade, em nenhuma direção — inclusive é plausível causalidade reversa (estados com histórico de mais trauma podem ter investido mais em UTI, o que tenderia a inflar uma correlação positiva, não negativa).
- Denominador populacional é a população **total** do estado, não a população de 1 a 12 anos especificamente (exigiria outra base do IBGE, não coletada neste projeto).
- Dado de leitos é uma fotografia de dezembro/2024; dado de óbitos é o ano inteiro de 2024.

---

# Indicador 4 — Análise: correlação entre mortalidade por sepse e leitos de UTI Pediátrica

Pergunta: se o artigo trocasse o desfecho de "trauma" para "sepse", a correlação com leitos de UTI Pediátrica ficaria estatisticamente mais forte? A hipótese fazia sentido em teoria (sepse depende mais diretamente de cuidado intensivo do que trauma, cuja mortalidade em boa parte acontece antes de qualquer UTI entrar em cena) — mas precisava ser testada com dados reais antes de mudar o artigo.

## 4.1 Método

- **Nível geográfico:** por estado (n=27), mesmo método do Indicador 3.
- **Dados reaproveitados:** os mesmos arquivos brutos de mortalidade (SIM, 2024) já baixados em `data/raw_cache/` para o Indicador 1 — nenhum download novo. Os leitos e a população são os mesmos do Indicador 3.
- **Duas definições de "morte por sepse" foram testadas**, porque a literatura de saúde pública aponta subregistro nessa causa:
  1. **Causa básica A40/A41** (Septicemia) — é o que aparece oficialmente no TABNET como "óbito por sepse".
  2. **Sepse mencionada em qualquer linha da declaração de óbito** (causa associada, campos `LINHAA`–`LINHAD`, `LINHAII`), mesmo quando a causa básica registrada foi outra doença (ex.: pneumonia, meningite) e a sepse foi só uma complicação. Essa definição mais ampla também inclui menção a choque séptico (CID R57.2).
- **Scripts:** `scripts/testar_sepse.py` (extrai as contagens) e `scripts/analise_correlacao_sepse.py` (calcula a correlação) — Tabela completa: `saida/analise_correlacao_sepse_por_estado.csv`

## 4.2 Resultado

| Comparação (taxas por 100 mil hab.) | r | p-valor | Significativa a 5%? |
|---|---|---|---|
| Sepse (causa básica A40/A41) × Leitos existentes | 0,07 | 0,74 | Não |
| Sepse (causa básica A40/A41) × Leitos SUS | -0,33 | 0,09 | Não (mas a mais próxima de todas) |
| Sepse (mencionada em qualquer linha) × Leitos existentes | -0,11 | 0,60 | Não |
| Sepse (mencionada em qualquer linha) × Leitos SUS | -0,20 | 0,32 | Não |
| *Trauma × Leitos existentes (Indicador 3, para comparação)* | -0,19 | 0,35 | Não |
| *Trauma × Leitos SUS (Indicador 3, para comparação)* | 0,05 | 0,81 | Não |

**Achado adicional sobre subregistro:** usando causa básica A40/A41, o Brasil teve **239 óbitos** de crianças de 1-12 anos por sepse em 2024. Usando a definição ampla (sepse mencionada em qualquer linha), esse número sobe para **3.037** — **12,7 vezes mais**. Isso indica que a estatística "oficial" de mortalidade por sepse (causa básica) provavelmente subestima bastante a mortalidade real associada à sepse nessa faixa etária.

## 4.3 Conclusão

**Trocar o desfecho para sepse não tornaria a correlação mais forte nem estatisticamente significativa** — nenhuma das quatro combinações testadas passa no corte de 5%. O resultado mais próximo da significância (sepse por causa básica × leitos SUS, p=0,09) vai na direção esperada pela teoria (mais leitos, menos mortalidade), mas não é conclusivo, e a definição mais ampla de sepse (que corrige o subregistro) enfraquece esse mesmo resultado (p=0,32) — sinal de que o p=0,09 provavelmente é ruído estatístico, não um efeito real.

**Por quê:** mortalidade por sepse (causa básica) teve média de **8,9 óbitos por estado**, com **3 estados em zero** (Acre, Roraima, Tocantins) — contra 93,5 óbitos por estado em média no trauma. Números tão baixos tornam a taxa por 100 mil habitantes extremamente instável (um único óbito a mais ou a menos muda bastante o resultado do estado), o que reduz — não aumenta — a confiabilidade estatística da análise.

## 4.4 Limitações (além das já listadas no Indicador 3)

- Contagens de sepse são pequenas o suficiente para sofrer forte influência de "números pequenos" (variância tipo Poisson): a taxa de um estado com 1 óbito pode dobrar ou zerar de um ano para o outro sem nenhuma mudança real no sistema de saúde.
- A definição ampla ("mencionada em qualquer linha") é mais sensível ao subregistro, mas também é uma escolha metodológica própria deste projeto — não é a definição usada oficialmente pelo TABNET, então merece essa ressalva explícita se for citada no artigo.
- Como no Indicador 3, esta é uma correlação ecológica simples de um único ano, sem controle de outros fatores clínicos ou epidemiológicos.

---

# Indicador 5 — Gráficos e tabelas comparativas

Reúne, em formato visual e tabular, os números já coletados e analisados nos Indicadores 1-4. Não baixa nem calcula nada novo — só organiza o que já existe para facilitar o uso direto no artigo.

- **Script:** `scripts/gerar_graficos_tabelas.py` (reutilizável — rode de novo sempre que atualizar algum dos indicadores anteriores)

## 5.1 Gráficos (`graficos/`, PNG prontos para colar no artigo)

| Arquivo | O que mostra |
|---|---|
| `01_mortalidade_trauma_por_regiao.png` | Taxa de mortalidade por trauma (1-12 anos) por região, ordenado do maior para o menor |
| `02_leitos_uti_ped_por_regiao.png` | Leitos existentes x leitos SUS de UTI Pediátrica, por região |
| `03_dispersao_trauma_x_leitos_existentes.png` | Dispersão trauma × leitos existentes, por estado (n=27), com linha de tendência e r/p |
| `04_dispersao_trauma_x_leitos_sus.png` | Dispersão trauma × leitos SUS, por estado |
| `05_dispersao_sepse_x_leitos_sus.png` | Dispersão sepse (causa básica) × leitos SUS, por estado — o resultado mais próximo de significância (Indicador 4) |
| `06_comparacao_trauma_sepse_por_estado.png` | Barras comparando trauma x sepse (causa básica) lado a lado, todos os 27 estados |

Todos os gráficos usam taxas por 100 mil habitantes (nunca números absolutos), pelo motivo explicado na seção 3.1 — comparar estados/regiões por número absoluto de óbitos ou leitos é enganoso porque ambos são dominados pelo tamanho da população.

## 5.2 Tabelas comparativas (`saida/`, Excel e CSV)

| Arquivo | Conteúdo |
|---|---|
| `tabela_comparativa_regioes.xlsx` / `.csv` | Uma linha por região: população, óbitos por trauma (absoluto e taxa), leitos existentes e SUS (absoluto e taxa) |
| `tabela_comparativa_estados.xlsx` / `.csv` | Uma linha por estado (n=27): população, óbitos por trauma, óbitos por sepse (causa básica e "mencionada"), leitos existentes e SUS — todos em absoluto e em taxa por 100 mil habitantes |
| `tabela_resumo_correlacoes.xlsx` / `.csv` | As 6 correlações testadas (trauma e as duas definições de sepse, contra leitos existentes e SUS): r, p-valor e se é significativa a 5% |

## 5.3 Como atualizar

Sempre que rodar de novo algum dos scripts dos Indicadores 1-4 (por exemplo, ao trocar para o ano de 2025), rode em seguida:
```
.\venv\Scripts\python.exe .\scripts\gerar_graficos_tabelas.py
```
Os gráficos e tabelas serão regravados com os dados mais recentes.

---

# Estrutura de pastas do projeto

```
dados-sus/
├── README.md                              este arquivo
├── venv/                                  ambiente Python isolado do projeto
├── scripts/
│   ├── coletar_mortalidade_trauma.py      script do Indicador 1 (reutilizável)
│   ├── coletar_uti_pediatrica.py          script do Indicador 2 (reutilizável)
│   ├── analise_correlacao_por_estado.py   script do Indicador 3 (análise de correlação, reutilizável)
│   ├── testar_sepse.py                    script do Indicador 4 (extrai contagens de sepse por estado)
│   ├── analise_correlacao_sepse.py        script do Indicador 4 (calcula a correlação com sepse)
│   └── gerar_graficos_tabelas.py          script do Indicador 5 (gráficos e tabelas comparativas, reutilizável)
├── data/
│   ├── raw_cache/                         arquivos originais baixados do DATASUS (.dbc), guardados como comprovação da fonte bruta
│   ├── teste/                             amostra do teste piloto (Sergipe/2024) e tabela de contagens de sepse por estado
│   ├── log_coleta.txt                     log da última execução do script do Indicador 1
│   └── log_coleta_uti.txt                 log da última execução do script do Indicador 2
├── graficos/
│   ├── 01_mortalidade_trauma_por_regiao.png
│   ├── 02_leitos_uti_ped_por_regiao.png
│   ├── 03_dispersao_trauma_x_leitos_existentes.png
│   ├── 04_dispersao_trauma_x_leitos_sus.png
│   ├── 05_dispersao_sepse_x_leitos_sus.png
│   └── 06_comparacao_trauma_sepse_por_estado.png
└── saida/
    ├── mortalidade_trauma_2024_regioes.csv / .xlsx
    ├── uti_pediatrica_2024_regioes.csv / .xlsx
    ├── analise_correlacao_mortalidade_leitos.csv   análise trauma x leitos por região (n=5)
    ├── analise_correlacao_por_estado.csv           análise trauma x leitos por estado (n=27)
    ├── analise_correlacao_sepse_por_estado.csv     análise sepse x leitos por estado (n=27)
    ├── tabela_comparativa_regioes.xlsx / .csv      Indicador 5
    ├── tabela_comparativa_estados.xlsx / .csv      Indicador 5
    └── tabela_resumo_correlacoes.xlsx / .csv       Indicador 5
```

# Privacidade

Todos os dados usados são públicos, oficiais e agregados (contagens por região, sem identificação de pacientes ou de profissionais). Nenhum dado pessoal ou identificável foi acessado — os microdados do SIM e do CNES já são divulgados de forma anonimizada/agregada pelo próprio Ministério da Saúde.
