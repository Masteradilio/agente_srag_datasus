# Arquitetura Técnica do Sistema (v2.0.0)

## 1. Visão Geral da Arquitetura

O sistema implementa uma arquitetura orientada a agentes em grafos estritos (**LangGraph StateGraph**) que segrega rigorosamente:
1. **Cálculo Determinístico e Engenharia de Dados**: Executado em Python e Pandas com validação de schema e hashing criptográfico SHA-256.
2. **Subagentes Concorrentes de Pesquisa Multi-Canal (Agent Reach)**: Coleta assíncrona de inteligência oficial, sinais em redes sociais e transcrições de mídia.
3. **RAG Híbrido Avançado**: Combinação de embeddings densos locais do Hugging Face com busca esparsa BM25 através de Reciprocal Rank Fusion (RRF).
4. **Ciclo de Reflexão e Auto-Correção (Reflection Loop)**: Verificação formal de fidelidade numérica contra `metrics.json` antes da emissão.
5. **Observabilidade e Contabilidade Financeira**: Rastreamento de custos em USD/BRL e cascata de latência por nó (OpenInference).

```text
                               +----------------------------------------+
                               |     OpenDataSUS Data Pipeline (ETL)    |
                               +----------------------------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               |  Parquet Refinado + Métricas + Z-Score |
                               +----------------------------------------+
                                                   |
                   +-------------------------------+-------------------------------+
                   |                               |                               |
                   v                               v                               v
    +-----------------------------+ +-----------------------------+ +-----------------------------+
    |  🏛️ Subagente Portal Oficial | | 💬 Subagente Social/Reddit  | |  🎙️ Subagente Mídia/YouTube  |
    +-----------------------------+ +-----------------------------+ +-----------------------------+
                   |                               |                               |
                   +-------------------------------+-------------------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               |         Fan-In Reducer Node            |
                               +----------------------------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               |   RAG Híbrido: ChromaDB + BM25 (RRF)   |
                               +----------------------------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               |    Drafting da Suíte Multi-Artefato    |
                               +----------------------------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               |   Reflection & Groundedness Evaluator  |
                               +----------------------------------------+
                                                   |
                                                   v
                               +----------------------------------------+
                               | Output Guardrail & Persistência Final  |
                               +----------------------------------------+
```

---

## 2. Orquestração no LangGraph

O grafo do agente é construído em cima do `langgraph.graph.StateGraph` com estado tipado `AgentState`:
- `validate_user_request`: Validação do prompt contra injeção e jailbreak via `enforce_input_guard`.
- `load_run_context`: Inicialização de buffers e ponteiros da execução.
- `collect_metrics`: Execução determinística dos cálculos epidemiológicos e estatísticos.
- `collect_charts`: Geração dos 4 gráficos obrigatórios em Matplotlib.
- `subagent_official_search`: Coleta em portais de órgãos de saúde.
- `subagent_social_search`: Mineração de discurso comunitário em fóruns públicos.
- `subagent_media_search`: Extração de pontos-chave de coletivas de imprensa.
- `fan_in_research`: Deduplicação e filtragem por allowlist institucional.
- `retrieve_methodology_context`: Recuperação contextual via RAG Híbrido com RRF.
- `draft_multi_artifacts`: Construção da suíte de 5 artefatos analíticos.
- `evaluate_and_reflect`: Nó de auto-correção que audita o rascunho textual contra as métricas calculadas.
- `validate_report`: Validação de contratos tipados e barreiras de saída.
- `persist_report`: Gravação em disco e geração do PDF final.

---

## 3. RAG Híbrido (ChromaDB + BM25 via Reciprocal Rank Fusion)

A recuperação contextual combina duas abordagens complementares:
1. **Busca Vetorial Densa (ChromaDB / Hugging Face)**:
   - Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensões).
   - Captura proximidade semântica e intenção conceitual.
2. **Busca Léxica Esparsa (BM25Okapi)**:
   - Tokenização e ponderação IDF exata para termos técnicos, códigos de doença e acrônimos médicos.
3. **Fusão por RRF**:
   $$RRF(d) = \frac{1}{60 + rank_{dense}(d)} + \frac{1}{60 + rank_{sparse}(d)}$$

---

## 4. Suíte de 5 Artefatos Analíticos Especializados

Cada execução gera os seguintes documentos no diretório `artifacts/runs/<run_id>/`:
1. `executive_bulletin.md`: Síntese gerencial de alto nível para tomada de decisão.
2. `epidemiological_deepdive.md`: Parecer técnico detalhado com tabelas de patógenos, estratificação por idade e taxas de UTI.
3. `anomaly_alerts.md`: Alertas estatísticos baseados em Z-score para detecção precoce de surtos.
4. `media_and_social_signals.md`: Inteligência de mídia, notícias e relatos públicos minerados via Agent Reach.
5. `data_governance_report.md`: Linhagem, contagem de linhas e hashes criptográficos SHA-256.
6. `report.md` / `report.pdf`: Relatório consolidado oficial.
