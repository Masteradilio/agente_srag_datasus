# Cobertura de Testes, Qualidade e Compliance (v2.0.0)

Este documento mapeia os critérios de compliance, governança e conformidade técnica do projeto.

## 1. Cobertura de Testes Automatizados (115 Testes Passando)

A suíte de testes cobre todas as camadas do sistema com 100% de taxa de sucesso:
- `tests/test_preprocessing.py`: Ingestão, normalização de schemas, datas e tipos canônicos.
- `tests/test_multi_disease_metrics.py`: Classificação etiológica, faixas etárias e algoritmo de Z-score.
- `tests/test_agent_reach_subagents.py`: Subagentes concorrentes de pesquisa e filtragem de fontes.
- `tests/test_multi_artifact_reflection.py`: Geração da suíte de 5 artefatos e nó de avaliação de fidelidade (reflection).
- `tests/test_chroma_hybrid_rag.py`: ChromaDB, embeddings Hugging Face, BM25 e Hybrid Retriever (RRF).
- `tests/test_evals_framework.py`: Framework RAG Triad e avaliação adversarial de agentes.
- `tests/test_input_guardrails.py` & `tests/test_output_guardrails.py`: Defesas contra injeção e vazamentos.
- `tests/test_pipeline_smoke.py`: Teste ponta-a-ponta validando a geração de todos os artefatos obrigatórios.

---

## 2. Artefatos de Governança Produzidos por Execução

Cada execução gera os seguintes artefatos em `artifacts/runs/<run_id>/`:
1. `manifest.json`: Manifesto com hashes criptográficos SHA-256 e proveniência de dados.
2. `data_quality_report.json` & `data_governance_report.md`: Diagnóstico de completude e nulos.
3. `metrics.json`: Métricas determinísticas, distribuições etiológicas e anomalias.
4. `chart_context.json`: Contexto estruturado dos 4 gráficos gerados.
5. `news_sources.json`: Proveniência e timestamps de acesso das fontes consultadas.
6. `observability.json`: Contabilidade de tokens (Prompt/Completion), custos USD/BRL e latência waterfall.
7. `agent_trace.jsonl`: Traces detalhados de cada nó do LangGraph no padrão OpenInference.
8. `executive_bulletin.md`, `epidemiological_deepdive.md`, `anomaly_alerts.md`, `media_and_social_signals.md`, `report.md` e `report.pdf`.
