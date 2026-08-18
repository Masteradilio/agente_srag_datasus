# MASTER BACKLOG V2 — Plataforma de Inteligência e Vigilância Epidemiológica (DataSUS GenAI Agent & RAG)

## 1. Propósito e Posicionamento do Projeto

Este backlog definiu a evolução arquitetural e funcional da solução, transformando-a no **projeto definitivo de portfólio para posições de Senior AI Engineer e Lead Data Scientist**.

A solução posiciona-se como uma **Plataforma Autônoma e Auditável de Inteligência em Saúde Pública**, integrando:
1. **Engenharia de Dados e Estatística Determinística**: Ingestão de dados abertos do DataSUS/OpenDataSUS com cálculo matemático determinístico (taxas de crescimento, mortalidade, UTI, vacinação, distribuição etiológica e detecção estatística de anomalias/surtos por Z-score) e geração de 4 gráficos sem risco de alucinação numérica.
2. **Orquestração Hierárquica com LangGraph e Subagentes Concorrentes**: Grafo de estados com padrão *Supervisor / Fan-Out / Fan-In*, disparando subagentes especializados via **Agent Reach** para coletar sinais em fontes oficiais, redes sociais/comunidades (Reddit) e transcrições de mídia (YouTube/Podcasts), com ciclo de auto-correção (*Reflection / Self-Correction*).
3. **Ecossistema RAG Enterprise Multi-Artefato**: Geração de uma suíte de 5 artefatos especializados (*Boletim Executivo, Parecer Epidemiológico Técnico, Alertas de Anomalias, Síntese de Mídia e Governança de Dados*), indexados em um Banco Vetorial Open-Source local (**ChromaDB**) com embeddings gratuitos locais do **Hugging Face** (`sentence-transformers`), suportando busca híbrida (BM25 + Dense via Reciprocal Rank Fusion) e citação com proveniência estrita.
4. **Framework Rigoroso de EVALs e Observabilidade de Produção**: Matriz de avaliação cobrindo as 3 etapas do RAG (*Pré-recuperação, Na Recuperação e Pós-recuperação/Groundedness*) e métricas de agentes (latência em cascata, contabilidade de tokens, custo em USD/BRL e taxa de sucesso de tools).
5. **Governança, Guardrails Enterprise e Reprodutibilidade**: Proteção contra prompt injection, vazamento de PII/segredos, diagnósticos médicos não autorizados, com CI/CD (GitHub Actions), contêiner Docker e sincronização com o GitHub.

---

## 2. Visão Geral das Fases e Status de Conclusão

| Fase | Foco Arquitetural | Entregável Principal | Status |
|---|---|---|---|
| **0** | **Baseline & Fundamentação** | Congelamento de baseline, limpeza e setup | `[X] CONCLUÍDO` |
| **1** | **Multi-Doença & Anomalias** | Ingestão multi-etiologia e detecção estatística | `[X] CONCLUÍDO` |
| **2** | **Subagentes & Agent Reach** | LangGraph Fan-Out/Fan-In (Oficial, Redes, Mídia) | `[X] CONCLUÍDO` |
| **3** | **Suíte Multi-Artefato & Reflection** | Redação especializada e auto-correção no LangGraph | `[X] CONCLUÍDO` |
| **4** | **ChromaDB & HuggingFace RAG** | Vector Store local, embeddings e busca híbrida | `[X] CONCLUÍDO` |
| **5** | **Framework de EVALs** | Matriz de avaliação Pré, In e Pós-Recuperação + Agentes | `[X] CONCLUÍDO` |
| **6** | **Observabilidade & Streamlit UX** | Contabilidade de tokens, custo ($), traces e UI | `[X] CONCLUÍDO` |
| **7** | **Docs, Docker, CI/CD & Sync** | Documentação completa, containerização e GitHub Sync | `[X] CONCLUÍDO` |

---

## Fase 0 — Baseline, Arquitetura e Fundamentação

### SRAG-V2-000 — Congelar baseline técnico reproduzível
**Status:** `[X] CONCLUÍDO`
- [x] Ambiente virtual Python 3.12 validado com dependências atualizadas (`uv`).
- [x] Executada suíte de testes de regressão com 100% de aprovação.
- [x] Baseline registrado em `artifacts/benchmarks/v2_baseline_summary.json`.

---

## Fase 1 — Motor Multi-Doença, Multi-Etiologia e Detecção de Anomalias

### SRAG-V2-100 — Mapeamento e extração multi-etiologia na base OpenDataSUS
**Status:** `[X] CONCLUÍDO`
- [x] Mapeamento semântico no pré-processamento (`src/data/preprocessing.py`) para patógenos (`COVID-19`, `Influenza`, `VSR`, `Outros Vírus`, `Não Especificado`).
- [x] Estratificação etária (`0-4 anos`, `5-19 anos`, `20-59 anos`, `60+ anos`).
- [x] Testes unitários implementados em `tests/test_multi_disease_metrics.py`.

### SRAG-V2-101 — Cálculo determinístico de métricas segmentadas e detecção estatística de anomalias
**Status:** `[X] CONCLUÍDO`
- [x] Cálculo de distribuição etiológica e faixas etárias em `src/metrics/calculators.py`.
- [x] Algoritmo estatístico de detecção de anomalias por Z-score em janelas móveis de 14 dias.
- [x] Geração dos 4 gráficos padronizados (`daily_cases_30d.png`, `monthly_cases_12m.png`, `etiology_distribution.png`, `age_group_cases.png`).

---

## Fase 2 — Subagentes Concorrentes no LangGraph e Integração com Agent Reach

### SRAG-V2-200 — Integração da camada de pesquisa Agent Reach (`Panniantong/agent-reach`)
**Status:** `[X] CONCLUÍDO`
- [x] Módulo `src/news/agent_reach_client.py` com pesquisa em portais institucionais, discussões no Reddit e transcrições de mídia/coletivas.
- [x] Sanitização contra injeção de prompt e tagging de canal de origem.

### SRAG-V2-201 — Orquestração de subagentes concorrentes e Fan-In Reducer no LangGraph
**Status:** `[X] CONCLUÍDO`
- [x] Subagentes paralelos integrados no `src/agents/graph.py` com nó Fan-In Reducer e allowlist institucional.
- [x] Testes unitários em `tests/test_agent_reach_subagents.py`.

---

## Fase 3 — Suíte Multi-Artefato e Nó de Reflexão (Self-Correction Loop)

### SRAG-V2-300 — Geração especializada de múltiplos artefatos analíticos
**Status:** `[X] CONCLUÍDO`
- [x] `src/reporting/report_builder.py` gera 5 artefatos analíticos (`executive_bulletin.md`, `epidemiological_deepdive.md`, `anomaly_alerts.md`, `media_and_social_signals.md`, `data_governance_report.md` + `report.md` e `report.pdf`).

### SRAG-V2-301 — Implementação do nó de avaliação e reflexão no LangGraph
**Status:** `[X] CONCLUÍDO`
- [x] Nó `evaluate_and_reflect` no LangGraph comparando rascunhos contra `metrics.json` e emitindo score de fidelidade.
- [x] Testes unitários em `tests/test_multi_artifact_reflection.py`.

---

## Fase 4 — Banco Vetorial Open-Source (ChromaDB) e Embeddings Hugging Face

### SRAG-V2-400 — Integração do modelo de embeddings local Hugging Face
**Status:** `[X] CONCLUÍDO`
- [x] Módulo `src/rag/embeddings.py` utilizando `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` com execução offline e custo zero.

### SRAG-V2-401 — Implementação do ChromaVectorStore e Busca Híbrida (RRF)
**Status:** `[X] CONCLUÍDO`
- [x] `src/rag/vector_store.py` e `src/rag/retriever.py` com busca híbrida densa (ChromaDB) + esparsa (BM25) via Reciprocal Rank Fusion (RRF).
- [x] Testes em `tests/test_chroma_hybrid_rag.py`.

---

## Fase 5 — Framework de EVALs (RAG Triad e Segurança de Agentes)

### SRAG-V2-500 — Framework de avaliação do RAG Triad
**Status:** `[X] CONCLUÍDO`
- [x] Módulo `src/evals/rag_evals.py` com avaliação de Precision@3, Recall@3, MRR, Hit Rate, Faithfulness e benchmarking comparativo (BM25 vs. Dense vs. Hybrid).
- [x] Geração automática do artefato `artifacts/benchmarks/rag_eval_results.json`.

### SRAG-V2-501 — Framework de avaliação de resiliência e segurança dos agentes
**Status:** `[X] CONCLUÍDO`
- [x] Módulo `src/evals/agent_evals.py` com suíte adversarial (100% de acurácia defensiva) e validação de contratos de ferramentas.
- [x] Testes em `tests/test_evals_framework.py`.

---

## Fase 6 — Observabilidade Profunda, Contabilidade de Tokens e Streamlit UX

### SRAG-V2-600 — Contabilidade financeira de tokens e tracing em cascata
**Status:** `[X] CONCLUÍDO`
- [x] Módulo `src/audit/observability.py` com cálculo de tokens (Prompt/Completion) e custos em USD e BRL.
- [x] Geração do payload OpenInference com cascata de latência por nó/subagente.

### SRAG-V2-601 — Atualização do dashboard Streamlit
**Status:** `[X] CONCLUÍDO`
- [x] Visualizador interativo em abas para os 5 artefatos + PDF em `app/streamlit_app.py`.
- [x] Painel de Observabilidade & EVALs e Chat RAG com busca híbrida e citações de fontes.

---

## Fase 7 — Finalização, Documentação, Docker, CI/CD e Sincronização

### SRAG-V2-700 — Atualização documental completa
**Status:** `[X] CONCLUÍDO`
- [x] Atualizados `README.md`, `CHANGELOG.md`, `docs/architecture.md`, `docs/metric_catalog.md`, `docs/limitations.md`, `docs/guardrails_security_matrix.md` e `docs/cobertura_compliance.md`.

### SRAG-V2-701 — Containerização e automação CI/CD
**Status:** `[X] CONCLUÍDO`
- [x] Criados `Dockerfile`, `docker-compose.yml` e `.github/workflows/ci.yml`.

### SRAG-V2-702 — Validação final de regressão e sincronização com GitHub
**Status:** `[X] CONCLUÍDO`
- [x] 115 testes automatizados passando com 100% de sucesso.
