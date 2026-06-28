# MASTER_BACKLOG.md â€” Agente SRAG DataSUS

**Projeto:** `agente_srag_datasus`  
**RepositÃ³rio:** `https://github.com/Masteradilio/agente_srag_datasus`  
**Tipo:** PoC tÃ©cnica para desafio de Senior AI Engineer  
**Objetivo:** implementar uma soluÃ§Ã£o GenAI com pipeline determinÃ­stico, agente com tools controladas, RAG documental, notÃ­cias com allowlist, guardrails, auditoria e dashboard Streamlit para geraÃ§Ã£o de relatÃ³rios sobre SRAG com dados DataSUS/OpenDataSUS.

---

## Status de Execucao

- [x] Fase 0 - Preparacao, estrutura inicial, ambiente e documentacao base.
- [x] Fase 1 - Configuracoes, contratos, utilitarios e fundacao tecnica.
- [x] Fase 2 - Ingestao de dados e validacao de fonte.
- [x] Fase 3 - Pre-processamento, qualidade, schema real e tarefa F3.T8.
- [x] Fase 4 - Metricas deterministicas e graficos obrigatorios.
- [x] Fase 5 - RAG documental local.
- [x] Fase 6 - Noticias externas com allowlist.
- [x] Fase 7 - Agente controlado com tools e trace.
- [x] Fase 8 - Guardrails de entrada, privacidade e saida.
- [x] Fase 9 - Relatorio Markdown/PDF.
- [x] Fase 10 - Dashboard Streamlit.
- [x] Fase 11 - Documentacao, README, arquitetura e limitacoes.
- [x] Fase 12 - Validacao final, testes, smoke real e limpeza de arquivos indevidos.
- [x] Reorganizacao final - conteudo de `src/srag_agent` movido para `src/` e
  pacote intermediario removido.
- [x] Higiene de versionamento - `.env.example` e `docs/descricao_vaga.md`
  mantidos apenas localmente via `.gitignore`.

---

## 1. Diretrizes Gerais de ImplementaÃ§Ã£o

### 1.1 Regra principal de arquitetura

O LLM **nÃ£o deve calcular mÃ©tricas diretamente**.

O pipeline determinÃ­stico deve baixar, validar, transformar e calcular as mÃ©tricas. O agente GenAI deve orquestrar tools, consultar contexto, buscar notÃ­cias permitidas e redigir o relatÃ³rio com base em resultados calculados por cÃ³digo.

### 1.2 Camadas esperadas

```text
GitLab/OpenDataSUS
        |
        v
data/landing/
        |
        v
Preprocessing + Data Quality
        |
        v
data/refined/*.parquet
        |
        v
Metric Tools + Chart Tools
        |
        v
LangGraph Agent
        |
        +--> RAG Documental
        +--> News Tools com allowlist
        +--> Guardrails
        |
        v
artifacts/runs/<run_id>/
        |
        v
Streamlit Dashboard
```

### 1.3 CritÃ©rios de qualidade

Todo cÃ³digo deve seguir:

- funÃ§Ãµes pequenas e testÃ¡veis;
- type hints sempre que possÃ­vel;
- configuraÃ§Ã£o fora do cÃ³digo;
- logs claros;
- tratamento explÃ­cito de erro;
- nenhuma chave ou segredo versionado;
- testes unitÃ¡rios por fase;
- regressÃ£o completa ao final de cada fase;
- commits pequenos e descritivos.

### 1.4 Ambiente padrÃ£o de desenvolvimento

O projeto deve ser executado em ambiente virtual Python.

No Git Bash / Windows:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

No Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1.5 Comandos de regressÃ£o obrigatÃ³rios

Ao final de cada fase, executar dentro do ambiente `.venv`:

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
```

Quando houver tipagem suficiente no mÃ³dulo implementado:

```bash
python -m mypy src
```

Se ainda nÃ£o houver testes implementados em uma fase inicial, criar pelo menos testes mÃ­nimos antes de encerrar a fase.

### 1.6 PolÃ­tica de commit

Ao final de cada fase aprovada:

```bash
git status
git add .
git commit -m "feat: complete phase X - <short description>"
```

Exemplo:

```bash
git commit -m "feat: complete phase 2 - gitlab ingestion pipeline"
```

---

## 2. Definition of Done Global

O projeto serÃ¡ considerado pronto quando:

- o pipeline identificar automaticamente a pasta mais recente do GitLab;
- o arquivo `srag_total.xlsx` for baixado para `data/landing`;
- a base for prÃ©-processada e salva em Parquet em `data/refined`;
- as quatro mÃ©tricas obrigatÃ³rias forem calculadas por cÃ³digo;
- os dois grÃ¡ficos obrigatÃ³rios forem gerados;
- o agente gerar relatÃ³rio com mÃ©tricas, grÃ¡ficos, notÃ­cias, fontes e limitaÃ§Ãµes;
- houver allowlist de fontes externas;
- houver guardrails de entrada, tools, privacidade e saÃ­da;
- cada execuÃ§Ã£o gerar `manifest.json`, `data_quality_report.json`, `metrics.json`, `news_sources.json`, `agent_trace.jsonl`, relatÃ³rio e grÃ¡ficos;
- o Streamlit demonstrar pipeline, relatÃ³rio, qualidade de dados e chat;
- os testes passarem em ambiente `.venv`;
- o README explicar arquitetura, execuÃ§Ã£o, mÃ©tricas, guardrails, auditoria e limitaÃ§Ãµes;
- o repositÃ³rio incluir o PDF do diagrama conceitual em `docs/architecture_diagram.pdf`.

---

# Fase 0 â€” Bootstrap do RepositÃ³rio

## Objetivo

Garantir que o repositÃ³rio tenha uma base mÃ­nima organizada e pronta para desenvolvimento incremental.

## Tarefas

### F0.T1 â€” Conferir arquivos iniciais

Validar existÃªncia dos arquivos:

```text
README.md
.gitignore
requirements.txt
PRD.md
MASTER_BACKLOG.md
```

Se `PRD.md` ainda nÃ£o estiver no repositÃ³rio, adicionÃ¡-lo.

### F0.T2 â€” Criar estrutura inicial de diretÃ³rios

Criar:

```text
configs/
src/
src/data/
src/metrics/
src/news/
src/rag/
src/agents/
src/guardrails/
src/reporting/
src/audit/
src/utils/
app/
tests/
docs/
data/landing/
data/refined/
artifacts/runs/
```

Adicionar `.gitkeep` onde necessÃ¡rio.

### F0.T3 â€” Criar arquivos de pacote

Criar `__init__.py` em:

```text
src/
src/data/
src/metrics/
src/news/
src/rag/
src/agents/
src/guardrails/
src/reporting/
src/audit/
src/utils/
```

### F0.T4 â€” Criar `.env.example`

Criar:

```bash
OPENAI_API_KEY=
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
APP_ENV=local
```

NÃ£o versionar `.env`.

### F0.T5 â€” Criar teste mÃ­nimo de sanidade

Criar `tests/test_project_structure.py` validando que diretÃ³rios e arquivos principais existem.

## CritÃ©rios de aceite

- Estrutura inicial criada.
- `.env.example` criado.
- Teste de sanidade passando.
- Nenhum arquivo de dado bruto versionado.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
```

## Commit sugerido

```bash
git add .
git commit -m "chore: complete phase 0 - repository bootstrap"
```

---

# Fase 1 â€” ConfiguraÃ§Ãµes, Schemas e UtilitÃ¡rios Base

## Objetivo

Criar a fundaÃ§Ã£o configurÃ¡vel do projeto: settings, paths, hashing, datas, logs simples e arquivos YAML de configuraÃ§Ã£o.

## Tarefas

### F1.T1 â€” Criar `configs/settings.yaml`

ConteÃºdo mÃ­nimo:

```yaml
project:
  name: agente_srag_datasus
  default_run_timezone: America/Sao_Paulo

paths:
  landing_dir: data/landing
  refined_dir: data/refined
  artifacts_dir: artifacts/runs
  docs_dir: docs

gitlab:
  base_url: https://gitlab.com
  project_path: cgcovid/dados-abertos
  srag_tree_path: Dados unificados/Unificado Srag
  target_file: srag_total.xlsx

privacy:
  min_group_size: 10

news:
  max_sources_per_report: 6
  request_timeout_seconds: 20
```

### F1.T2 â€” Criar `configs/news_sources.yaml`

Incluir allowlist mÃ¡xima:

```yaml
allowed_domains:
  - gitlab.com/cgcovid/dados-abertos
  - dadosabertos.saude.gov.br
  - gov.br/saude
  - infoms.saude.gov.br
  - fiocruz.br
  - github.com/infogripe
  - agenciagov.ebc.com.br
  - agenciabrasil.ebc.com.br
  - paho.org
  - who.int
```

### F1.T3 â€” Criar `configs/metric_catalog.yaml`

Registrar fÃ³rmulas das mÃ©tricas obrigatÃ³rias:

- taxa de aumento de casos;
- taxa de mortalidade conhecida;
- taxa de mortalidade bruta;
- proporÃ§Ã£o de casos com UTI;
- proporÃ§Ã£o de casos com vacinaÃ§Ã£o registrada;
- grÃ¡ficos obrigatÃ³rios.

### F1.T4 â€” Criar `configs/column_mapping.yaml`

Criar mapeamento inicial de colunas candidatas para conceitos canÃ´nicos:

```yaml
case_date:
  candidates: [DT_SIN_PRI, DT_NOTIFIC]
notification_date:
  candidates: [DT_NOTIFIC]
evolution:
  candidates: [EVOLUCAO]
evolution_date:
  candidates: [DT_EVOLUCA]
icu:
  candidates: [UTI]
icu_start_date:
  candidates: [DT_ENTUTI]
icu_end_date:
  candidates: [DT_SAIDUTI]
vaccination:
  candidates: [VACINA_COV, VACINA]
state:
  candidates: [SG_UF_NOT, SG_UF]
city:
  candidates: [ID_MUNICIP, CO_MUN_NOT]
final_classification:
  candidates: [CLASSI_FIN]
```

### F1.T5 â€” Implementar utilitÃ¡rios

Arquivos:

```text
src/utils/paths.py
src/utils/hashing.py
src/utils/dates.py
src/audit/logger.py
```

FunÃ§Ãµes mÃ­nimas:

- criar diretÃ³rios;
- resolver paths;
- calcular SHA-256;
- gerar `run_id`;
- carregar YAML;
- logger bÃ¡sico estruturado.

### F1.T6 â€” Criar testes

Arquivos:

```text
tests/test_config_loading.py
tests/test_hashing.py
tests/test_dates.py
```

## CritÃ©rios de aceite

- ConfiguraÃ§Ãµes carregam corretamente.
- Allowlist contÃ©m no mÃ¡ximo 10 fontes.
- Hash SHA-256 testado.
- `run_id` gerado de forma estÃ¡vel e segura.
- Testes passando.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 1 - configuration and base utilities"
```

---

# Fase 2 â€” Cliente GitLab e IngestÃ£o da Camada Landing

## Objetivo

Implementar a ingestÃ£o automÃ¡tica do arquivo `srag_total.xlsx` a partir da pasta mais recente do repositÃ³rio GitLab.

## Tarefas

### F2.T1 â€” Implementar `gitlab_client.py`

Arquivo:

```text
src/data/gitlab_client.py
```

Responsabilidades:

- montar URLs da API pÃºblica do GitLab;
- listar Ã¡rvore do repositÃ³rio;
- navegar no path configurado;
- listar pastas de `Dados unificados/Unificado Srag`;
- baixar arquivo bruto.

### F2.T2 â€” Implementar parser de pasta mais recente

Arquivo:

```text
src/data/ingestion.py
```

FunÃ§Ãµes:

```python
parse_folder_version(folder_name: str) -> tuple[int, ...]
select_latest_folder(folder_names: list[str]) -> str
```

Regras:

- ordenar por ano e sufixos numÃ©ricos;
- suportar formatos como `2026_24`, `2025`, `2024`;
- ignorar nomes invÃ¡lidos com warning;
- falhar explicitamente se nenhuma pasta vÃ¡lida existir.

### F2.T3 â€” Implementar download para landing

FunÃ§Ã£o:

```python
run_ingestion(run_id: str | None = None) -> IngestionResult
```

Deve:

- criar diretÃ³rio `data/landing/<run_id>`;
- baixar `srag_total.xlsx`;
- salvar arquivo bruto;
- calcular hash;
- registrar metadados mÃ­nimos.

### F2.T4 â€” Criar modelos Pydantic

Arquivo:

```text
src/data/schema.py
```

Modelos:

```python
IngestionResult
GitLabTreeItem
```

### F2.T5 â€” Criar testes com mock

Arquivos:

```text
tests/test_latest_folder_selection.py
tests/test_gitlab_client.py
tests/test_ingestion.py
```

Testar:

- seleÃ§Ã£o de `2026_24` como mais recente quando existir;
- seleÃ§Ã£o de `2025` se sÃ³ houver anos;
- erro quando nÃ£o houver pasta vÃ¡lida;
- download mockado;
- criaÃ§Ã£o de landing;
- hash calculado.

## CritÃ©rios de aceite

- A pasta mais recente Ã© escolhida por cÃ³digo testado.
- O download Ã© encapsulado.
- O resultado da ingestÃ£o Ã© estruturado.
- A fase funciona com mock nos testes.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 2 - gitlab ingestion pipeline"
```

---

# Fase 3 â€” PrÃ©-processamento, ValidaÃ§Ã£o e Camada Refined

## Objetivo

Transformar o Excel bruto em uma base Parquet refinada, validada e adequada para mÃ©tricas.

## Tarefas

### F3.T1 â€” Implementar leitura do Excel

Arquivo:

```text
src/data/preprocessing.py
```

FunÃ§Ã£o:

```python
load_raw_srag_excel(path: Path) -> pd.DataFrame
```

### F3.T2 â€” Implementar normalizaÃ§Ã£o de colunas

FunÃ§Ãµes:

```python
resolve_column_mapping(df: pd.DataFrame, mapping: dict) -> dict
normalize_selected_columns(df: pd.DataFrame, resolved_mapping: dict) -> pd.DataFrame
```

Criar colunas canÃ´nicas:

```text
case_date
notification_date
evolution
evolution_date
icu
icu_start_date
icu_end_date
vaccination
state
city
final_classification
```

### F3.T3 â€” Implementar tratamento de datas e valores

Regras:

- converter datas com tolerÃ¢ncia a erros;
- preservar contagem de datas invÃ¡lidas;
- normalizar cÃ³digos de evoluÃ§Ã£o, UTI e vacinaÃ§Ã£o;
- remover linhas sem data de caso e sem data de notificaÃ§Ã£o;
- criar `canonical_case_date`.

### F3.T4 â€” Implementar validaÃ§Ã£o de dados

Arquivo:

```text
src/data/validation.py
```

Gerar relatÃ³rio:

```text
artifacts/runs/<run_id>/data_quality_report.json
```

ConteÃºdo:

- linhas brutas;
- linhas refinadas;
- colunas encontradas;
- colunas ausentes;
- taxa de nulos;
- datas invÃ¡lidas;
- registros descartados;
- warnings.

### F3.T5 â€” Salvar Parquet

FunÃ§Ã£o:

```python
run_preprocessing(raw_file: Path, run_id: str) -> PreprocessingResult
```

Salvar:

```text
data/refined/<run_id>/srag_total.parquet
```

### F3.T6 â€” Criar fixture pequena para testes

Criar fixture sintÃ©tica em teste, sem versionar dados reais grandes.

### F3.T7 â€” Criar testes

Arquivos:

```text
tests/test_preprocessing.py
tests/test_validation.py
```

Testar:

- resoluÃ§Ã£o de colunas;
- fallback de data;
- datas invÃ¡lidas;
- nulos;
- geraÃ§Ã£o de Parquet;
- geraÃ§Ã£o de data quality report.

### F3.T8 â€” Ajuste fino contra schema real do `srag_total.xlsx`

Status: DONE

ApÃ³s executar a ingestÃ£o real do arquivo completo, validar o schema e os cÃ³digos
efetivos do `srag_total.xlsx` baixado e ajustar:

- `configs/column_mapping.yaml` com aliases reais adicionais, se aparecerem;
- normalizaÃ§Ã£o semÃ¢ntica dos cÃ³digos de `EVOLUCAO`, `UTI`, `VACINA_COV` e campos equivalentes;
- regras de obrigatoriedade entre colunas essenciais e complementares;
- warnings do `data_quality_report.json` para limitaÃ§Ãµes observadas no arquivo real.

Esse ajuste deve preservar a estratÃ©gia configurÃ¡vel: adaptar o mapeamento em
`configs/` quando possÃ­vel e sÃ³ alterar cÃ³digo quando houver regra semÃ¢ntica
nova que precise ser testada.

EvidÃªncia executada:

- arquivo real baixado de `Dados unificados/Unificado Srag/2026_24/srag_total.xlsx`;
- schema real identificado como agregado por semana epidemiolÃ³gica, UF, municÃ­pio,
  faixa etÃ¡ria, casos e Ã³bitos;
- preprocessamento adaptado para schema agregado sem remover suporte ao schema
  linha a linha;
- mÃ©tricas adaptadas para usar `casos` e `obitos` agregados quando presentes;
- smoke real gerou Parquet, `data_quality_report.json`, `metrics.json` e os dois
  grÃ¡ficos obrigatÃ³rios para o run `20260627T212036-0300`.

## CritÃ©rios de aceite

- Excel bruto convertido para Parquet.
- Colunas canÃ´nicas criadas.
- RelatÃ³rio de qualidade gerado.
- Testes com fixture sintÃ©tica passando.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 3 - preprocessing and refined layer"
```

---

# Fase 4 â€” MÃ©tricas e GrÃ¡ficos ObrigatÃ³rios

## Objetivo

Implementar o cÃ¡lculo determinÃ­stico das mÃ©tricas e a geraÃ§Ã£o dos dois grÃ¡ficos exigidos.

## Tarefas

### F4.T1 â€” Implementar definiÃ§Ãµes de mÃ©tricas

Arquivo:

```text
src/metrics/definitions.py
```

Criar documentaÃ§Ã£o em cÃ³digo para:

- taxa de aumento 7d;
- mortalidade conhecida;
- mortalidade bruta;
- proporÃ§Ã£o de casos com UTI;
- proporÃ§Ã£o de casos com vacinaÃ§Ã£o registrada.

### F4.T2 â€” Implementar calculadoras

Arquivo:

```text
src/metrics/calculators.py
```

FunÃ§Ãµes:

```python
calculate_reference_date(df: pd.DataFrame) -> date
calculate_case_growth_rate(df: pd.DataFrame, reference_date: date) -> MetricValue
calculate_mortality_rates(df: pd.DataFrame) -> dict
calculate_icu_rate(df: pd.DataFrame) -> MetricValue
calculate_vaccination_rate(df: pd.DataFrame) -> MetricValue
calculate_metric_summary(parquet_path: Path) -> MetricSummary
```

### F4.T3 â€” Implementar grÃ¡ficos

Arquivo:

```text
src/metrics/charts.py
```

FunÃ§Ãµes:

```python
generate_daily_cases_30d_chart(df: pd.DataFrame, output_path: Path) -> Path
generate_monthly_cases_12m_chart(df: pd.DataFrame, output_path: Path) -> Path
```

Salvar em:

```text
artifacts/runs/<run_id>/charts/
```

### F4.T4 â€” Persistir `metrics.json`

Salvar:

```text
artifacts/runs/<run_id>/metrics.json
```

### F4.T5 â€” Criar testes

Arquivos:

```text
tests/test_metrics.py
tests/test_charts.py
```

Testar:

- cÃ¡lculo com denominador zero;
- janelas de 7 dias;
- mortalidade conhecida;
- UTI;
- vacinaÃ§Ã£o;
- geraÃ§Ã£o dos grÃ¡ficos;
- existÃªncia de arquivos de saÃ­da.

## CritÃ©rios de aceite

- As quatro mÃ©tricas obrigatÃ³rias sÃ£o calculadas por cÃ³digo.
- Os dois grÃ¡ficos obrigatÃ³rios sÃ£o gerados.
- MÃ©tricas tÃªm limitaÃ§Ãµes registradas quando necessÃ¡rio.
- `metrics.json` Ã© produzido.
- Testes passam.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 4 - deterministic metrics and charts"
```

---

# Fase 5 â€” NotÃ­cias em Tempo Real com Allowlist

## Objetivo

Implementar busca e extraÃ§Ã£o de notÃ­cias/fontes recentes sobre SRAG com domÃ­nio restrito por allowlist.

## Tarefas

### F5.T1 â€” Implementar validaÃ§Ã£o de domÃ­nio

Arquivo:

```text
src/guardrails/domain_allowlist.py
```

FunÃ§Ãµes:

```python
is_allowed_url(url: str, allowed_domains: list[str]) -> bool
filter_allowed_urls(urls: list[str], allowed_domains: list[str]) -> list[str]
```

### F5.T2 â€” Implementar busca de notÃ­cias

Arquivo:

```text
src/news/search.py
```

Abordagem inicial aceitÃ¡vel:

- usar busca via API configurÃ¡vel, se disponÃ­vel;
- ou preparar interface abstrata com implementaÃ§Ã£o mock/local para testes;
- deixar clara a necessidade de chave externa, se usada.

A interface deve ser:

```python
search_srag_news(query: str, allowed_domains: list[str], max_results: int) -> list[NewsSearchResult]
```

### F5.T3 â€” Implementar extraÃ§Ã£o de conteÃºdo

Arquivo:

```text
src/news/extract.py
```

FunÃ§Ã£o:

```python
extract_news_article(url: str) -> NewsArticle
```

Regras:

- validar allowlist antes de extrair;
- timeout;
- user-agent claro;
- tratar erro sem quebrar todo o relatÃ³rio.

### F5.T4 â€” Implementar ranking simples

Arquivo:

```text
src/news/rank.py
```

CritÃ©rios:

- fonte oficial primeiro;
- recÃªncia;
- presenÃ§a de termos SRAG, sÃ­ndrome respiratÃ³ria, influenza, covid, VSR;
- diversidade de domÃ­nios.

### F5.T5 â€” Persistir `news_sources.json`

Salvar:

```text
artifacts/runs/<run_id>/news_sources.json
```

### F5.T6 â€” Criar testes

Arquivos:

```text
tests/test_news_allowlist.py
tests/test_news_ranking.py
tests/test_news_extraction.py
```

Testar:

- domÃ­nio permitido;
- domÃ­nio bloqueado;
- URL maliciosa;
- ranking;
- extraÃ§Ã£o mockada;
- persistÃªncia de fontes.

## CritÃ©rios de aceite

- Nenhuma fonte fora da allowlist Ã© aceita.
- NotÃ­cias sÃ£o estruturadas.
- Falhas de notÃ­cia nÃ£o quebram o pipeline completo.
- `news_sources.json` Ã© produzido.
- Testes passam.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 5 - allowlisted news pipeline"
```

---

# Fase 6 â€” RAG Documental

## Objetivo

Implementar uma camada de RAG para recuperar contexto metodolÃ³gico, dicionÃ¡rio de dados, limitaÃ§Ãµes, documentaÃ§Ã£o e notÃ­cias processadas.

## Tarefas

### F6.T1 â€” Implementar loaders

Arquivo:

```text
src/rag/loaders.py
```

Carregar:

- `README.md`;
- `PRD.md`;
- `MASTER_BACKLOG.md`;
- `configs/metric_catalog.yaml`;
- `docs/limitations.md`;
- `artifacts/runs/<run_id>/news_sources.json`;
- `artifacts/runs/<run_id>/report.md`, quando existir.

### F6.T2 â€” Implementar chunking

Arquivo:

```text
src/rag/chunking.py
```

CritÃ©rios:

- chunks moderados;
- metadados de origem;
- separaÃ§Ã£o por seÃ§Ã£o quando possÃ­vel.

### F6.T3 â€” Implementar vector store

Arquivo:

```text
src/rag/vector_store.py
```

Usar ChromaDB inicialmente.

DiretÃ³rio local:

```text
artifacts/vector_store/
```

O `.gitignore` deve impedir versionamento desse diretÃ³rio.

### F6.T4 â€” Implementar retriever

Arquivo:

```text
src/rag/retriever.py
```

FunÃ§Ã£o:

```python
retrieve_context(query: str, top_k: int = 5) -> list[RetrievedDocument]
```

### F6.T5 â€” Criar testes

Arquivos:

```text
tests/test_rag_loaders.py
tests/test_rag_retriever.py
```

Testar:

- carregamento de documentos;
- metadados;
- chunking;
- recuperaÃ§Ã£o com fixture pequena.

## CritÃ©rios de aceite

- RAG indexa documentaÃ§Ã£o e contexto textual.
- RAG nÃ£o Ã© usado para cÃ¡lculo de mÃ©tricas.
- RecuperaÃ§Ã£o retorna contexto com fonte.
- Testes passam.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 6 - documental rag layer"
```

---

# Fase 7 â€” Agente LangGraph e Tools Controladas

## Objetivo

Implementar o agente principal como grafo controlado, usando tools para mÃ©tricas, grÃ¡ficos, notÃ­cias, RAG e validaÃ§Ã£o de relatÃ³rio.

## Tarefas

### F7.T1 â€” Definir estado do agente

Arquivo:

```text
src/agents/state.py
```

Estado mÃ­nimo:

```python
AgentState = TypedDict(
    "AgentState",
    {
        "run_id": str,
        "user_request": str,
        "metric_summary": dict,
        "chart_paths": dict,
        "news_evidence": list[dict],
        "rag_context": list[dict],
        "draft_report": str,
        "validation_errors": list[str],
        "final_report_path": str,
    },
)
```

### F7.T2 â€” Implementar tools

Arquivo:

```text
src/agents/tools.py
```

Tools mÃ­nimas:

- `get_metric_summary_tool`;
- `generate_required_charts_tool`;
- `search_srag_news_tool`;
- `retrieve_context_tool`;
- `validate_report_contract_tool`.

### F7.T3 â€” Implementar prompts versionados

Arquivo:

```text
src/agents/prompts.py
```

Prompts devem instruir o agente a:

- nÃ£o inventar mÃ©tricas;
- usar apenas resultados das tools;
- diferenciar dado calculado de interpretaÃ§Ã£o;
- citar fontes;
- declarar limitaÃ§Ãµes;
- nÃ£o dar recomendaÃ§Ã£o mÃ©dica individual.

### F7.T4 â€” Implementar grafo

Arquivo:

```text
src/agents/graph.py
```

Fluxo:

```text
START
  -> validate_user_request
  -> load_run_context
  -> collect_metrics
  -> collect_charts
  -> search_news
  -> retrieve_methodology_context
  -> draft_report
  -> validate_report
  -> persist_report
END
```

### F7.T5 â€” Implementar contrato de saÃ­da

Arquivo:

```text
src/agents/output_contracts.py
```

Verificar que relatÃ³rio tem:

- quatro mÃ©tricas;
- dois grÃ¡ficos;
- fontes;
- limitaÃ§Ãµes;
- aviso de uso;
- ausÃªncia de dado individual.

### F7.T6 â€” Criar testes

Arquivos:

```text
tests/test_agent_tools.py
tests/test_agent_graph.py
tests/test_report_contract.py
```

Testar com mocks:

- tool de mÃ©tricas chamada;
- tool de notÃ­cias chamada;
- relatÃ³rio validado;
- falha quando mÃ©trica obrigatÃ³ria faltar;
- falha quando fonte faltar.

## CritÃ©rios de aceite

- Agente orquestrado por LangGraph.
- Tools controladas.
- RelatÃ³rio gerado em Markdown.
- Contrato de saÃ­da validado.
- Testes passam.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 7 - langgraph agent and controlled tools"
```

---

# Fase 8 â€” Guardrails e Auditoria Completa

## Objetivo

Fortalecer seguranÃ§a, privacidade, rastreabilidade e governanÃ§a da soluÃ§Ã£o.

## Tarefas

### F8.T1 â€” Guardrail de entrada

Arquivo:

```text
src/guardrails/input_guard.py
```

Bloquear:

- prompt injection;
- pedido para ignorar regras;
- pedidos fora do escopo;
- dados linha a linha;
- diagnÃ³stico individual;
- tratamento individual.

### F8.T2 â€” Guardrail de privacidade

Arquivo:

```text
src/guardrails/privacy.py
```

Implementar:

```python
enforce_min_group_size(records: list[dict], min_group_size: int) -> list[dict]
```

Regras:

- nÃ£o exibir grupos com contagem menor que `min_group_size`;
- nÃ£o retornar registros individuais;
- bloquear granularidade excessiva.

### F8.T3 â€” Guardrail de saÃ­da

Arquivo:

```text
src/guardrails/output_guard.py
```

Validar:

- ausÃªncia de dados individuais;
- presenÃ§a de limitaÃ§Ãµes;
- presenÃ§a de aviso de uso analÃ­tico;
- ausÃªncia de recomendaÃ§Ãµes clÃ­nicas individualizadas;
- fontes para comentÃ¡rios externos.

### F8.T4 â€” Manifesto de execuÃ§Ã£o

Arquivo:

```text
src/audit/manifest.py
```

Gerar:

```text
artifacts/runs/<run_id>/manifest.json
```

ConteÃºdo mÃ­nimo:

- `run_id`;
- timestamp;
- pasta selecionada;
- arquivo;
- hash bruto;
- hash refinado;
- linhas brutas;
- linhas refinadas;
- modelo;
- embedding model;
- prompt version;
- metric catalog version;
- allowlist version.

### F8.T5 â€” Trace do agente

Arquivo:

```text
src/audit/run_context.py
```

Gerar:

```text
artifacts/runs/<run_id>/agent_trace.jsonl
```

Registrar:

- nÃ³ executado;
- tool chamada;
- status;
- resumo de entrada;
- resumo de saÃ­da;
- timestamp.

NÃ£o registrar segredos.

### F8.T6 â€” Criar testes

Arquivos:

```text
tests/test_input_guardrails.py
tests/test_privacy_guardrails.py
tests/test_output_guardrails.py
tests/test_manifest.py
tests/test_agent_trace.py
```

## CritÃ©rios de aceite

- Guardrails implementados em cÃ³digo.
- Manifesto gerado.
- Trace gerado.
- Testes passam.
- README menciona guardrails e auditoria.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 8 - guardrails and audit layer"
```

---

# Fase 9 â€” Reporting e ExportaÃ§Ã£o

## Objetivo

Criar geraÃ§Ã£o de relatÃ³rio consistente em Markdown e PDF, usando template versionado.

## Tarefas

### F9.T1 â€” Criar template Markdown

Arquivo:

```text
src/reporting/templates/report_template.md
```

Estrutura:

```markdown
# RelatÃ³rio Automatizado de SRAG

## 1. SumÃ¡rio Executivo
## 2. Dados Utilizados
## 3. MÃ©tricas Principais
## 4. EvoluÃ§Ã£o Temporal
## 5. Contexto de NotÃ­cias e Fontes Oficiais
## 6. ComentÃ¡rios AnalÃ­ticos do Agente
## 7. LimitaÃ§Ãµes MetodolÃ³gicas
## 8. Fontes Consultadas
## 9. Aviso de Uso
```

### F9.T2 â€” Implementar builder

Arquivo:

```text
src/reporting/report_builder.py
```

FunÃ§Ã£o:

```python
build_report_markdown(context: ReportContext) -> str
```

### F9.T3 â€” Implementar exportador PDF

Arquivo:

```text
src/reporting/pdf_exporter.py
```

FunÃ§Ã£o:

```python
export_report_pdf(markdown_path: Path, output_pdf_path: Path) -> Path
```

Se WeasyPrint apresentar problema local, criar fallback HTML e documentar.

### F9.T4 â€” Testes

Arquivos:

```text
tests/test_report_builder.py
tests/test_pdf_exporter.py
```

## CritÃ©rios de aceite

- RelatÃ³rio Markdown gerado.
- PDF gerado ou fallback documentado.
- Template versionado.
- Testes passam.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 9 - report generation and export"
```

---

# Fase 10 â€” Streamlit Dashboard

## Objetivo

Criar interface demonstrÃ¡vel para avaliadores tÃ©cnicos e usuÃ¡rios finais.

## Tarefas

### F10.T1 â€” Criar `app/streamlit_app.py`

Abas obrigatÃ³rias:

1. Pipeline
2. RelatÃ³rio
3. Qualidade dos Dados
4. Chat

### F10.T2 â€” Aba Pipeline

Exibir:

- botÃ£o para executar pipeline;
- pasta selecionada;
- arquivo baixado;
- hash;
- status de refined;
- links dos artefatos.

### F10.T3 â€” Aba RelatÃ³rio

Exibir:

- mÃ©tricas principais;
- grÃ¡ficos;
- relatÃ³rio Markdown;
- fontes consultadas;
- botÃ£o para baixar relatÃ³rio.

### F10.T4 â€” Aba Qualidade dos Dados

Exibir:

- linhas brutas;
- linhas refinadas;
- colunas usadas;
- nulos;
- warnings;
- limitaÃ§Ãµes.

### F10.T5 â€” Aba Chat

Permitir perguntas sobre:

- relatÃ³rio;
- mÃ©tricas;
- metodologia;
- limitaÃ§Ãµes;
- fontes.

Bloquear:

- diagnÃ³stico;
- dados individuais;
- perguntas fora de escopo.

### F10.T6 â€” Testes mÃ­nimos

Criar:

```text
tests/test_streamlit_smoke.py
```

Testar import da aplicaÃ§Ã£o e funÃ§Ãµes auxiliares sem subir servidor.

## CritÃ©rios de aceite

- Dashboard executa com `streamlit run app/streamlit_app.py`.
- Interface mostra artefatos.
- Chat usa guardrails.
- Teste smoke passa.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "feat: complete phase 10 - streamlit dashboard"
```

---

# Fase 11 â€” DocumentaÃ§Ã£o, Diagrama e PreparaÃ§Ã£o para Entrevista

## Objetivo

Finalizar a documentaÃ§Ã£o tÃ©cnica do repositÃ³rio, criar diagrama conceitual em PDF e preparar a defesa tÃ©cnica.

## Tarefas

### F11.T1 â€” Atualizar README.md

O README deve explicar:

- visÃ£o geral;
- arquitetura;
- como rodar;
- pipeline de dados;
- mÃ©tricas e fÃ³rmulas;
- agente e tools;
- RAG documental;
- guardrails;
- auditoria;
- testes;
- limitaÃ§Ãµes;
- prÃ³ximos passos.

### F11.T2 â€” Criar `docs/architecture.md`

Explicar:

- camadas;
- fluxo de dados;
- fluxo do agente;
- decisÃµes de arquitetura;
- trade-offs.

### F11.T3 â€” Criar `docs/metric_catalog.md`

Documentar:

- fÃ³rmulas;
- colunas usadas;
- limitaÃ§Ãµes;
- proxies.

### F11.T4 â€” Criar `docs/limitations.md`

Documentar:

- atraso da base;
- nulos;
- proxy de UTI;
- proxy de vacinaÃ§Ã£o;
- notÃ­cias externas;
- nÃ£o substituiÃ§Ã£o de anÃ¡lise oficial ou mÃ©dica.

### F11.T5 â€” Criar diagrama conceitual PDF

Arquivo obrigatÃ³rio:

```text
docs/architecture_diagram.pdf
```

Deve mostrar:

- GitLab/OpenDataSUS;
- landing;
- refined;
- metric tools;
- chart tools;
- RAG;
- news tools;
- agent orchestrator;
- LLM;
- guardrails;
- audit;
- Streamlit.

### F11.T6 â€” Criar seÃ§Ã£o de defesa tÃ©cnica

Adicionar ao README uma seÃ§Ã£o com a narrativa:

```text
A soluÃ§Ã£o separa cÃ¡lculo determinÃ­stico de geraÃ§Ã£o textual. O LLM nÃ£o calcula mÃ©tricas diretamente; ele chama tools auditÃ¡veis. O RAG Ã© usado para documentaÃ§Ã£o e contexto textual, nÃ£o para cÃ¡lculo tabular. As fontes externas sÃ£o filtradas por allowlist. Cada execuÃ§Ã£o gera manifesto, mÃ©tricas, fontes, trace e relatÃ³rio, permitindo auditoria e reprodutibilidade.
```

## CritÃ©rios de aceite

- README completo.
- DocumentaÃ§Ã£o em `docs/`.
- PDF do diagrama presente.
- LimitaÃ§Ãµes claramente documentadas.
- Projeto pronto para apresentaÃ§Ã£o.

## RegressÃ£o obrigatÃ³ria da fase

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

## Commit sugerido

```bash
git add .
git commit -m "docs: complete phase 11 - documentation and interview readiness"
```

---

# Fase 12 â€” ValidaÃ§Ã£o Final de Entrega

## Objetivo

Executar uma validaÃ§Ã£o final como se o avaliador tÃ©cnico fosse clonar e rodar o projeto do zero.

## Tarefas

### F12.T1 â€” Rodar instalaÃ§Ã£o limpa

Em nova pasta ou ambiente limpo:

```bash
git clone https://github.com/Masteradilio/agente_srag_datasus.git
cd agente_srag_datasus
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### F12.T2 â€” Rodar testes

```bash
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

### F12.T3 â€” Rodar pipeline

Executar comando definido pelo projeto, por exemplo:

```bash
python -m data.ingestion
python -m data.preprocessing
python -m metrics.calculators
```

Ou comando consolidado, se implementado:

```bash
python -m pipeline
```

### F12.T4 â€” Rodar Streamlit

```bash
streamlit run app/streamlit_app.py
```

### F12.T5 â€” Conferir artefatos finais

Validar existÃªncia de:

```text
artifacts/runs/<run_id>/manifest.json
artifacts/runs/<run_id>/data_quality_report.json
artifacts/runs/<run_id>/metrics.json
artifacts/runs/<run_id>/news_sources.json
artifacts/runs/<run_id>/agent_trace.jsonl
artifacts/runs/<run_id>/report.md
artifacts/runs/<run_id>/report.pdf
artifacts/runs/<run_id>/charts/daily_cases_30d.png
artifacts/runs/<run_id>/charts/monthly_cases_12m.png
```

### F12.T6 â€” Revisar risco de arquivos indevidos

Garantir que nÃ£o foram versionados:

- `.env`;
- chaves;
- dados brutos grandes;
- arquivos `.xlsx`;
- Parquet;
- vector store;
- artifacts de execuÃ§Ã£o;
- logs locais.

### F12.T7 â€” Commit final

```bash
git status
git add .
git commit -m "chore: final delivery validation"
git push
```

## CritÃ©rios de aceite

- RepositÃ³rio roda do zero.
- Testes passam.
- Streamlit abre.
- RelatÃ³rio Ã© gerado.
- Artefatos sÃ£o criados.
- README Ã© suficiente para avaliaÃ§Ã£o.
- Nenhum segredo ou dado pesado foi versionado.

---

# Checklist Final para Entrevista TÃ©cnica

Use este checklist antes de apresentar:

- [ ] Sei explicar por que o LLM nÃ£o calcula mÃ©tricas.
- [ ] Sei explicar o papel do RAG documental.
- [ ] Sei explicar a allowlist de fontes.
- [ ] Sei explicar guardrails de entrada, tool e saÃ­da.
- [ ] Sei explicar como a soluÃ§Ã£o trata dados sensÃ­veis.
- [ ] Sei explicar a diferenÃ§a entre proporÃ§Ã£o de UTI e ocupaÃ§Ã£o real de leitos.
- [ ] Sei explicar a diferenÃ§a entre vacinaÃ§Ã£o entre casos e cobertura populacional.
- [ ] Sei mostrar o manifesto de execuÃ§Ã£o.
- [ ] Sei mostrar o `agent_trace.jsonl`.
- [ ] Sei mostrar os testes automatizados.
- [ ] Sei rodar o Streamlit.
- [ ] Sei apontar prÃ³ximos passos para produÃ§Ã£o.

