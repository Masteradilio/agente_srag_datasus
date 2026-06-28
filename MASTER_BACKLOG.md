# MASTER_BACKLOG.md — Agente SRAG DataSUS

**Projeto:** `agente_srag_datasus`  
**Repositório:** `https://github.com/Masteradilio/agente_srag_datasus`  
**Tipo:** PoC técnica para desafio de Senior AI Engineer  
**Objetivo:** implementar uma solução GenAI com pipeline determinístico, agente com tools controladas, RAG documental, notícias com allowlist, guardrails, auditoria e dashboard Streamlit para geração de relatórios sobre SRAG com dados DataSUS/OpenDataSUS.

---

## 1. Diretrizes Gerais de Implementação

### 1.1 Regra principal de arquitetura

O LLM **não deve calcular métricas diretamente**.

O pipeline determinístico deve baixar, validar, transformar e calcular as métricas. O agente GenAI deve orquestrar tools, consultar contexto, buscar notícias permitidas e redigir o relatório com base em resultados calculados por código.

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

### 1.3 Critérios de qualidade

Todo código deve seguir:

- funções pequenas e testáveis;
- type hints sempre que possível;
- configuração fora do código;
- logs claros;
- tratamento explícito de erro;
- nenhuma chave ou segredo versionado;
- testes unitários por fase;
- regressão completa ao final de cada fase;
- commits pequenos e descritivos.

### 1.4 Ambiente padrão de desenvolvimento

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

### 1.5 Comandos de regressão obrigatórios

Ao final de cada fase, executar dentro do ambiente `.venv`:

```bash
source .venv/Scripts/activate
python -m pytest tests -q
python -m ruff check .
```

Quando houver tipagem suficiente no módulo implementado:

```bash
python -m mypy src
```

Se ainda não houver testes implementados em uma fase inicial, criar pelo menos testes mínimos antes de encerrar a fase.

### 1.6 Política de commit

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

O projeto será considerado pronto quando:

- o pipeline identificar automaticamente a pasta mais recente do GitLab;
- o arquivo `srag_total.xlsx` for baixado para `data/landing`;
- a base for pré-processada e salva em Parquet em `data/refined`;
- as quatro métricas obrigatórias forem calculadas por código;
- os dois gráficos obrigatórios forem gerados;
- o agente gerar relatório com métricas, gráficos, notícias, fontes e limitações;
- houver allowlist de fontes externas;
- houver guardrails de entrada, tools, privacidade e saída;
- cada execução gerar `manifest.json`, `data_quality_report.json`, `metrics.json`, `news_sources.json`, `agent_trace.jsonl`, relatório e gráficos;
- o Streamlit demonstrar pipeline, relatório, qualidade de dados e chat;
- os testes passarem em ambiente `.venv`;
- o README explicar arquitetura, execução, métricas, guardrails, auditoria e limitações;
- o repositório incluir o PDF do diagrama conceitual em `docs/architecture_diagram.pdf`.

---

# Fase 0 — Bootstrap do Repositório

## Objetivo

Garantir que o repositório tenha uma base mínima organizada e pronta para desenvolvimento incremental.

## Tarefas

### F0.T1 — Conferir arquivos iniciais

Validar existência dos arquivos:

```text
README.md
.gitignore
requirements.txt
PRD.md
MASTER_BACKLOG.md
```

Se `PRD.md` ainda não estiver no repositório, adicioná-lo.

### F0.T2 — Criar estrutura inicial de diretórios

Criar:

```text
configs/
src/srag_agent/
src/srag_agent/data/
src/srag_agent/metrics/
src/srag_agent/news/
src/srag_agent/rag/
src/srag_agent/agents/
src/srag_agent/guardrails/
src/srag_agent/reporting/
src/srag_agent/audit/
src/srag_agent/utils/
app/
tests/
docs/
data/landing/
data/refined/
artifacts/runs/
```

Adicionar `.gitkeep` onde necessário.

### F0.T3 — Criar arquivos de pacote

Criar `__init__.py` em:

```text
src/srag_agent/
src/srag_agent/data/
src/srag_agent/metrics/
src/srag_agent/news/
src/srag_agent/rag/
src/srag_agent/agents/
src/srag_agent/guardrails/
src/srag_agent/reporting/
src/srag_agent/audit/
src/srag_agent/utils/
```

### F0.T4 — Criar `.env.example`

Criar:

```bash
OPENAI_API_KEY=
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
APP_ENV=local
```

Não versionar `.env`.

### F0.T5 — Criar teste mínimo de sanidade

Criar `tests/test_project_structure.py` validando que diretórios e arquivos principais existem.

## Critérios de aceite

- Estrutura inicial criada.
- `.env.example` criado.
- Teste de sanidade passando.
- Nenhum arquivo de dado bruto versionado.

## Regressão obrigatória da fase

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

# Fase 1 — Configurações, Schemas e Utilitários Base

## Objetivo

Criar a fundação configurável do projeto: settings, paths, hashing, datas, logs simples e arquivos YAML de configuração.

## Tarefas

### F1.T1 — Criar `configs/settings.yaml`

Conteúdo mínimo:

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

### F1.T2 — Criar `configs/news_sources.yaml`

Incluir allowlist máxima:

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

### F1.T3 — Criar `configs/metric_catalog.yaml`

Registrar fórmulas das métricas obrigatórias:

- taxa de aumento de casos;
- taxa de mortalidade conhecida;
- taxa de mortalidade bruta;
- proporção de casos com UTI;
- proporção de casos com vacinação registrada;
- gráficos obrigatórios.

### F1.T4 — Criar `configs/column_mapping.yaml`

Criar mapeamento inicial de colunas candidatas para conceitos canônicos:

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

### F1.T5 — Implementar utilitários

Arquivos:

```text
src/srag_agent/utils/paths.py
src/srag_agent/utils/hashing.py
src/srag_agent/utils/dates.py
src/srag_agent/audit/logger.py
```

Funções mínimas:

- criar diretórios;
- resolver paths;
- calcular SHA-256;
- gerar `run_id`;
- carregar YAML;
- logger básico estruturado.

### F1.T6 — Criar testes

Arquivos:

```text
tests/test_config_loading.py
tests/test_hashing.py
tests/test_dates.py
```

## Critérios de aceite

- Configurações carregam corretamente.
- Allowlist contém no máximo 10 fontes.
- Hash SHA-256 testado.
- `run_id` gerado de forma estável e segura.
- Testes passando.

## Regressão obrigatória da fase

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

# Fase 2 — Cliente GitLab e Ingestão da Camada Landing

## Objetivo

Implementar a ingestão automática do arquivo `srag_total.xlsx` a partir da pasta mais recente do repositório GitLab.

## Tarefas

### F2.T1 — Implementar `gitlab_client.py`

Arquivo:

```text
src/srag_agent/data/gitlab_client.py
```

Responsabilidades:

- montar URLs da API pública do GitLab;
- listar árvore do repositório;
- navegar no path configurado;
- listar pastas de `Dados unificados/Unificado Srag`;
- baixar arquivo bruto.

### F2.T2 — Implementar parser de pasta mais recente

Arquivo:

```text
src/srag_agent/data/ingestion.py
```

Funções:

```python
parse_folder_version(folder_name: str) -> tuple[int, ...]
select_latest_folder(folder_names: list[str]) -> str
```

Regras:

- ordenar por ano e sufixos numéricos;
- suportar formatos como `2026_24`, `2025`, `2024`;
- ignorar nomes inválidos com warning;
- falhar explicitamente se nenhuma pasta válida existir.

### F2.T3 — Implementar download para landing

Função:

```python
run_ingestion(run_id: str | None = None) -> IngestionResult
```

Deve:

- criar diretório `data/landing/<run_id>`;
- baixar `srag_total.xlsx`;
- salvar arquivo bruto;
- calcular hash;
- registrar metadados mínimos.

### F2.T4 — Criar modelos Pydantic

Arquivo:

```text
src/srag_agent/data/schema.py
```

Modelos:

```python
IngestionResult
GitLabTreeItem
```

### F2.T5 — Criar testes com mock

Arquivos:

```text
tests/test_latest_folder_selection.py
tests/test_gitlab_client.py
tests/test_ingestion.py
```

Testar:

- seleção de `2026_24` como mais recente quando existir;
- seleção de `2025` se só houver anos;
- erro quando não houver pasta válida;
- download mockado;
- criação de landing;
- hash calculado.

## Critérios de aceite

- A pasta mais recente é escolhida por código testado.
- O download é encapsulado.
- O resultado da ingestão é estruturado.
- A fase funciona com mock nos testes.

## Regressão obrigatória da fase

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

# Fase 3 — Pré-processamento, Validação e Camada Refined

## Objetivo

Transformar o Excel bruto em uma base Parquet refinada, validada e adequada para métricas.

## Tarefas

### F3.T1 — Implementar leitura do Excel

Arquivo:

```text
src/srag_agent/data/preprocessing.py
```

Função:

```python
load_raw_srag_excel(path: Path) -> pd.DataFrame
```

### F3.T2 — Implementar normalização de colunas

Funções:

```python
resolve_column_mapping(df: pd.DataFrame, mapping: dict) -> dict
normalize_selected_columns(df: pd.DataFrame, resolved_mapping: dict) -> pd.DataFrame
```

Criar colunas canônicas:

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

### F3.T3 — Implementar tratamento de datas e valores

Regras:

- converter datas com tolerância a erros;
- preservar contagem de datas inválidas;
- normalizar códigos de evolução, UTI e vacinação;
- remover linhas sem data de caso e sem data de notificação;
- criar `canonical_case_date`.

### F3.T4 — Implementar validação de dados

Arquivo:

```text
src/srag_agent/data/validation.py
```

Gerar relatório:

```text
artifacts/runs/<run_id>/data_quality_report.json
```

Conteúdo:

- linhas brutas;
- linhas refinadas;
- colunas encontradas;
- colunas ausentes;
- taxa de nulos;
- datas inválidas;
- registros descartados;
- warnings.

### F3.T5 — Salvar Parquet

Função:

```python
run_preprocessing(raw_file: Path, run_id: str) -> PreprocessingResult
```

Salvar:

```text
data/refined/<run_id>/srag_total.parquet
```

### F3.T6 — Criar fixture pequena para testes

Criar fixture sintética em teste, sem versionar dados reais grandes.

### F3.T7 — Criar testes

Arquivos:

```text
tests/test_preprocessing.py
tests/test_validation.py
```

Testar:

- resolução de colunas;
- fallback de data;
- datas inválidas;
- nulos;
- geração de Parquet;
- geração de data quality report.

### F3.T8 — Ajuste fino contra schema real do `srag_total.xlsx`

Status: DONE

Após executar a ingestão real do arquivo completo, validar o schema e os códigos
efetivos do `srag_total.xlsx` baixado e ajustar:

- `configs/column_mapping.yaml` com aliases reais adicionais, se aparecerem;
- normalização semântica dos códigos de `EVOLUCAO`, `UTI`, `VACINA_COV` e campos equivalentes;
- regras de obrigatoriedade entre colunas essenciais e complementares;
- warnings do `data_quality_report.json` para limitações observadas no arquivo real.

Esse ajuste deve preservar a estratégia configurável: adaptar o mapeamento em
`configs/` quando possível e só alterar código quando houver regra semântica
nova que precise ser testada.

Evidência executada:

- arquivo real baixado de `Dados unificados/Unificado Srag/2026_24/srag_total.xlsx`;
- schema real identificado como agregado por semana epidemiológica, UF, município,
  faixa etária, casos e óbitos;
- preprocessamento adaptado para schema agregado sem remover suporte ao schema
  linha a linha;
- métricas adaptadas para usar `casos` e `obitos` agregados quando presentes;
- smoke real gerou Parquet, `data_quality_report.json`, `metrics.json` e os dois
  gráficos obrigatórios para o run `20260627T212036-0300`.

## Critérios de aceite

- Excel bruto convertido para Parquet.
- Colunas canônicas criadas.
- Relatório de qualidade gerado.
- Testes com fixture sintética passando.

## Regressão obrigatória da fase

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

# Fase 4 — Métricas e Gráficos Obrigatórios

## Objetivo

Implementar o cálculo determinístico das métricas e a geração dos dois gráficos exigidos.

## Tarefas

### F4.T1 — Implementar definições de métricas

Arquivo:

```text
src/srag_agent/metrics/definitions.py
```

Criar documentação em código para:

- taxa de aumento 7d;
- mortalidade conhecida;
- mortalidade bruta;
- proporção de casos com UTI;
- proporção de casos com vacinação registrada.

### F4.T2 — Implementar calculadoras

Arquivo:

```text
src/srag_agent/metrics/calculators.py
```

Funções:

```python
calculate_reference_date(df: pd.DataFrame) -> date
calculate_case_growth_rate(df: pd.DataFrame, reference_date: date) -> MetricValue
calculate_mortality_rates(df: pd.DataFrame) -> dict
calculate_icu_rate(df: pd.DataFrame) -> MetricValue
calculate_vaccination_rate(df: pd.DataFrame) -> MetricValue
calculate_metric_summary(parquet_path: Path) -> MetricSummary
```

### F4.T3 — Implementar gráficos

Arquivo:

```text
src/srag_agent/metrics/charts.py
```

Funções:

```python
generate_daily_cases_30d_chart(df: pd.DataFrame, output_path: Path) -> Path
generate_monthly_cases_12m_chart(df: pd.DataFrame, output_path: Path) -> Path
```

Salvar em:

```text
artifacts/runs/<run_id>/charts/
```

### F4.T4 — Persistir `metrics.json`

Salvar:

```text
artifacts/runs/<run_id>/metrics.json
```

### F4.T5 — Criar testes

Arquivos:

```text
tests/test_metrics.py
tests/test_charts.py
```

Testar:

- cálculo com denominador zero;
- janelas de 7 dias;
- mortalidade conhecida;
- UTI;
- vacinação;
- geração dos gráficos;
- existência de arquivos de saída.

## Critérios de aceite

- As quatro métricas obrigatórias são calculadas por código.
- Os dois gráficos obrigatórios são gerados.
- Métricas têm limitações registradas quando necessário.
- `metrics.json` é produzido.
- Testes passam.

## Regressão obrigatória da fase

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

# Fase 5 — Notícias em Tempo Real com Allowlist

## Objetivo

Implementar busca e extração de notícias/fontes recentes sobre SRAG com domínio restrito por allowlist.

## Tarefas

### F5.T1 — Implementar validação de domínio

Arquivo:

```text
src/srag_agent/guardrails/domain_allowlist.py
```

Funções:

```python
is_allowed_url(url: str, allowed_domains: list[str]) -> bool
filter_allowed_urls(urls: list[str], allowed_domains: list[str]) -> list[str]
```

### F5.T2 — Implementar busca de notícias

Arquivo:

```text
src/srag_agent/news/search.py
```

Abordagem inicial aceitável:

- usar busca via API configurável, se disponível;
- ou preparar interface abstrata com implementação mock/local para testes;
- deixar clara a necessidade de chave externa, se usada.

A interface deve ser:

```python
search_srag_news(query: str, allowed_domains: list[str], max_results: int) -> list[NewsSearchResult]
```

### F5.T3 — Implementar extração de conteúdo

Arquivo:

```text
src/srag_agent/news/extract.py
```

Função:

```python
extract_news_article(url: str) -> NewsArticle
```

Regras:

- validar allowlist antes de extrair;
- timeout;
- user-agent claro;
- tratar erro sem quebrar todo o relatório.

### F5.T4 — Implementar ranking simples

Arquivo:

```text
src/srag_agent/news/rank.py
```

Critérios:

- fonte oficial primeiro;
- recência;
- presença de termos SRAG, síndrome respiratória, influenza, covid, VSR;
- diversidade de domínios.

### F5.T5 — Persistir `news_sources.json`

Salvar:

```text
artifacts/runs/<run_id>/news_sources.json
```

### F5.T6 — Criar testes

Arquivos:

```text
tests/test_news_allowlist.py
tests/test_news_ranking.py
tests/test_news_extraction.py
```

Testar:

- domínio permitido;
- domínio bloqueado;
- URL maliciosa;
- ranking;
- extração mockada;
- persistência de fontes.

## Critérios de aceite

- Nenhuma fonte fora da allowlist é aceita.
- Notícias são estruturadas.
- Falhas de notícia não quebram o pipeline completo.
- `news_sources.json` é produzido.
- Testes passam.

## Regressão obrigatória da fase

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

# Fase 6 — RAG Documental

## Objetivo

Implementar uma camada de RAG para recuperar contexto metodológico, dicionário de dados, limitações, documentação e notícias processadas.

## Tarefas

### F6.T1 — Implementar loaders

Arquivo:

```text
src/srag_agent/rag/loaders.py
```

Carregar:

- `README.md`;
- `PRD.md`;
- `MASTER_BACKLOG.md`;
- `configs/metric_catalog.yaml`;
- `docs/limitations.md`;
- `artifacts/runs/<run_id>/news_sources.json`;
- `artifacts/runs/<run_id>/report.md`, quando existir.

### F6.T2 — Implementar chunking

Arquivo:

```text
src/srag_agent/rag/chunking.py
```

Critérios:

- chunks moderados;
- metadados de origem;
- separação por seção quando possível.

### F6.T3 — Implementar vector store

Arquivo:

```text
src/srag_agent/rag/vector_store.py
```

Usar ChromaDB inicialmente.

Diretório local:

```text
artifacts/vector_store/
```

O `.gitignore` deve impedir versionamento desse diretório.

### F6.T4 — Implementar retriever

Arquivo:

```text
src/srag_agent/rag/retriever.py
```

Função:

```python
retrieve_context(query: str, top_k: int = 5) -> list[RetrievedDocument]
```

### F6.T5 — Criar testes

Arquivos:

```text
tests/test_rag_loaders.py
tests/test_rag_retriever.py
```

Testar:

- carregamento de documentos;
- metadados;
- chunking;
- recuperação com fixture pequena.

## Critérios de aceite

- RAG indexa documentação e contexto textual.
- RAG não é usado para cálculo de métricas.
- Recuperação retorna contexto com fonte.
- Testes passam.

## Regressão obrigatória da fase

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

# Fase 7 — Agente LangGraph e Tools Controladas

## Objetivo

Implementar o agente principal como grafo controlado, usando tools para métricas, gráficos, notícias, RAG e validação de relatório.

## Tarefas

### F7.T1 — Definir estado do agente

Arquivo:

```text
src/srag_agent/agents/state.py
```

Estado mínimo:

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

### F7.T2 — Implementar tools

Arquivo:

```text
src/srag_agent/agents/tools.py
```

Tools mínimas:

- `get_metric_summary_tool`;
- `generate_required_charts_tool`;
- `search_srag_news_tool`;
- `retrieve_context_tool`;
- `validate_report_contract_tool`.

### F7.T3 — Implementar prompts versionados

Arquivo:

```text
src/srag_agent/agents/prompts.py
```

Prompts devem instruir o agente a:

- não inventar métricas;
- usar apenas resultados das tools;
- diferenciar dado calculado de interpretação;
- citar fontes;
- declarar limitações;
- não dar recomendação médica individual.

### F7.T4 — Implementar grafo

Arquivo:

```text
src/srag_agent/agents/graph.py
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

### F7.T5 — Implementar contrato de saída

Arquivo:

```text
src/srag_agent/agents/output_contracts.py
```

Verificar que relatório tem:

- quatro métricas;
- dois gráficos;
- fontes;
- limitações;
- aviso de uso;
- ausência de dado individual.

### F7.T6 — Criar testes

Arquivos:

```text
tests/test_agent_tools.py
tests/test_agent_graph.py
tests/test_report_contract.py
```

Testar com mocks:

- tool de métricas chamada;
- tool de notícias chamada;
- relatório validado;
- falha quando métrica obrigatória faltar;
- falha quando fonte faltar.

## Critérios de aceite

- Agente orquestrado por LangGraph.
- Tools controladas.
- Relatório gerado em Markdown.
- Contrato de saída validado.
- Testes passam.

## Regressão obrigatória da fase

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

# Fase 8 — Guardrails e Auditoria Completa

## Objetivo

Fortalecer segurança, privacidade, rastreabilidade e governança da solução.

## Tarefas

### F8.T1 — Guardrail de entrada

Arquivo:

```text
src/srag_agent/guardrails/input_guard.py
```

Bloquear:

- prompt injection;
- pedido para ignorar regras;
- pedidos fora do escopo;
- dados linha a linha;
- diagnóstico individual;
- tratamento individual.

### F8.T2 — Guardrail de privacidade

Arquivo:

```text
src/srag_agent/guardrails/privacy.py
```

Implementar:

```python
enforce_min_group_size(records: list[dict], min_group_size: int) -> list[dict]
```

Regras:

- não exibir grupos com contagem menor que `min_group_size`;
- não retornar registros individuais;
- bloquear granularidade excessiva.

### F8.T3 — Guardrail de saída

Arquivo:

```text
src/srag_agent/guardrails/output_guard.py
```

Validar:

- ausência de dados individuais;
- presença de limitações;
- presença de aviso de uso analítico;
- ausência de recomendações clínicas individualizadas;
- fontes para comentários externos.

### F8.T4 — Manifesto de execução

Arquivo:

```text
src/srag_agent/audit/manifest.py
```

Gerar:

```text
artifacts/runs/<run_id>/manifest.json
```

Conteúdo mínimo:

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

### F8.T5 — Trace do agente

Arquivo:

```text
src/srag_agent/audit/run_context.py
```

Gerar:

```text
artifacts/runs/<run_id>/agent_trace.jsonl
```

Registrar:

- nó executado;
- tool chamada;
- status;
- resumo de entrada;
- resumo de saída;
- timestamp.

Não registrar segredos.

### F8.T6 — Criar testes

Arquivos:

```text
tests/test_input_guardrails.py
tests/test_privacy_guardrails.py
tests/test_output_guardrails.py
tests/test_manifest.py
tests/test_agent_trace.py
```

## Critérios de aceite

- Guardrails implementados em código.
- Manifesto gerado.
- Trace gerado.
- Testes passam.
- README menciona guardrails e auditoria.

## Regressão obrigatória da fase

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

# Fase 9 — Reporting e Exportação

## Objetivo

Criar geração de relatório consistente em Markdown e PDF, usando template versionado.

## Tarefas

### F9.T1 — Criar template Markdown

Arquivo:

```text
src/srag_agent/reporting/templates/report_template.md
```

Estrutura:

```markdown
# Relatório Automatizado de SRAG

## 1. Sumário Executivo
## 2. Dados Utilizados
## 3. Métricas Principais
## 4. Evolução Temporal
## 5. Contexto de Notícias e Fontes Oficiais
## 6. Comentários Analíticos do Agente
## 7. Limitações Metodológicas
## 8. Fontes Consultadas
## 9. Aviso de Uso
```

### F9.T2 — Implementar builder

Arquivo:

```text
src/srag_agent/reporting/report_builder.py
```

Função:

```python
build_report_markdown(context: ReportContext) -> str
```

### F9.T3 — Implementar exportador PDF

Arquivo:

```text
src/srag_agent/reporting/pdf_exporter.py
```

Função:

```python
export_report_pdf(markdown_path: Path, output_pdf_path: Path) -> Path
```

Se WeasyPrint apresentar problema local, criar fallback HTML e documentar.

### F9.T4 — Testes

Arquivos:

```text
tests/test_report_builder.py
tests/test_pdf_exporter.py
```

## Critérios de aceite

- Relatório Markdown gerado.
- PDF gerado ou fallback documentado.
- Template versionado.
- Testes passam.

## Regressão obrigatória da fase

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

# Fase 10 — Streamlit Dashboard

## Objetivo

Criar interface demonstrável para avaliadores técnicos e usuários finais.

## Tarefas

### F10.T1 — Criar `app/streamlit_app.py`

Abas obrigatórias:

1. Pipeline
2. Relatório
3. Qualidade dos Dados
4. Chat

### F10.T2 — Aba Pipeline

Exibir:

- botão para executar pipeline;
- pasta selecionada;
- arquivo baixado;
- hash;
- status de refined;
- links dos artefatos.

### F10.T3 — Aba Relatório

Exibir:

- métricas principais;
- gráficos;
- relatório Markdown;
- fontes consultadas;
- botão para baixar relatório.

### F10.T4 — Aba Qualidade dos Dados

Exibir:

- linhas brutas;
- linhas refinadas;
- colunas usadas;
- nulos;
- warnings;
- limitações.

### F10.T5 — Aba Chat

Permitir perguntas sobre:

- relatório;
- métricas;
- metodologia;
- limitações;
- fontes.

Bloquear:

- diagnóstico;
- dados individuais;
- perguntas fora de escopo.

### F10.T6 — Testes mínimos

Criar:

```text
tests/test_streamlit_smoke.py
```

Testar import da aplicação e funções auxiliares sem subir servidor.

## Critérios de aceite

- Dashboard executa com `streamlit run app/streamlit_app.py`.
- Interface mostra artefatos.
- Chat usa guardrails.
- Teste smoke passa.

## Regressão obrigatória da fase

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

# Fase 11 — Documentação, Diagrama e Preparação para Entrevista

## Objetivo

Finalizar a documentação técnica do repositório, criar diagrama conceitual em PDF e preparar a defesa técnica.

## Tarefas

### F11.T1 — Atualizar README.md

O README deve explicar:

- visão geral;
- arquitetura;
- como rodar;
- pipeline de dados;
- métricas e fórmulas;
- agente e tools;
- RAG documental;
- guardrails;
- auditoria;
- testes;
- limitações;
- próximos passos.

### F11.T2 — Criar `docs/architecture.md`

Explicar:

- camadas;
- fluxo de dados;
- fluxo do agente;
- decisões de arquitetura;
- trade-offs.

### F11.T3 — Criar `docs/metric_catalog.md`

Documentar:

- fórmulas;
- colunas usadas;
- limitações;
- proxies.

### F11.T4 — Criar `docs/limitations.md`

Documentar:

- atraso da base;
- nulos;
- proxy de UTI;
- proxy de vacinação;
- notícias externas;
- não substituição de análise oficial ou médica.

### F11.T5 — Criar diagrama conceitual PDF

Arquivo obrigatório:

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

### F11.T6 — Criar seção de defesa técnica

Adicionar ao README uma seção com a narrativa:

```text
A solução separa cálculo determinístico de geração textual. O LLM não calcula métricas diretamente; ele chama tools auditáveis. O RAG é usado para documentação e contexto textual, não para cálculo tabular. As fontes externas são filtradas por allowlist. Cada execução gera manifesto, métricas, fontes, trace e relatório, permitindo auditoria e reprodutibilidade.
```

## Critérios de aceite

- README completo.
- Documentação em `docs/`.
- PDF do diagrama presente.
- Limitações claramente documentadas.
- Projeto pronto para apresentação.

## Regressão obrigatória da fase

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

# Fase 12 — Validação Final de Entrega

## Objetivo

Executar uma validação final como se o avaliador técnico fosse clonar e rodar o projeto do zero.

## Tarefas

### F12.T1 — Rodar instalação limpa

Em nova pasta ou ambiente limpo:

```bash
git clone https://github.com/Masteradilio/agente_srag_datasus.git
cd agente_srag_datasus
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### F12.T2 — Rodar testes

```bash
python -m pytest tests -q
python -m ruff check .
python -m mypy src
```

### F12.T3 — Rodar pipeline

Executar comando definido pelo projeto, por exemplo:

```bash
python -m srag_agent.data.ingestion
python -m srag_agent.data.preprocessing
python -m srag_agent.metrics.calculators
```

Ou comando consolidado, se implementado:

```bash
python -m srag_agent.pipeline
```

### F12.T4 — Rodar Streamlit

```bash
streamlit run app/streamlit_app.py
```

### F12.T5 — Conferir artefatos finais

Validar existência de:

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

### F12.T6 — Revisar risco de arquivos indevidos

Garantir que não foram versionados:

- `.env`;
- chaves;
- dados brutos grandes;
- arquivos `.xlsx`;
- Parquet;
- vector store;
- artifacts de execução;
- logs locais.

### F12.T7 — Commit final

```bash
git status
git add .
git commit -m "chore: final delivery validation"
git push
```

## Critérios de aceite

- Repositório roda do zero.
- Testes passam.
- Streamlit abre.
- Relatório é gerado.
- Artefatos são criados.
- README é suficiente para avaliação.
- Nenhum segredo ou dado pesado foi versionado.

---

# Checklist Final para Entrevista Técnica

Use este checklist antes de apresentar:

- [ ] Sei explicar por que o LLM não calcula métricas.
- [ ] Sei explicar o papel do RAG documental.
- [ ] Sei explicar a allowlist de fontes.
- [ ] Sei explicar guardrails de entrada, tool e saída.
- [ ] Sei explicar como a solução trata dados sensíveis.
- [ ] Sei explicar a diferença entre proporção de UTI e ocupação real de leitos.
- [ ] Sei explicar a diferença entre vacinação entre casos e cobertura populacional.
- [ ] Sei mostrar o manifesto de execução.
- [ ] Sei mostrar o `agent_trace.jsonl`.
- [ ] Sei mostrar os testes automatizados.
- [ ] Sei rodar o Streamlit.
- [ ] Sei apontar próximos passos para produção.
