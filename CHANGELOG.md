# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-08-18

### Added
- **Multi-Disease / Multi-Etiology Epidemiological Surveillance**:
  - Semantic mapping and derivation of pathogens: COVID-19, Influenza A/B, Respiratory Syncytial Virus (VSR), Other Viruses, and Unspecified.
  - Stratification by age brackets (`0-4 anos`, `5-19 anos`, `20-59 anos`, `60+ anos`).
  - Automated statistical outbreak & surge detection using rolling 14-day window **Z-score** algorithm.
  - Generation of 4 standardized charts (`daily_cases_30d.png`, `monthly_cases_12m.png`, `etiology_distribution.png`, `age_group_cases.png`).
- **Concurrent Research Subagents & Agent Reach Integration**:
  - `AgentReachClient` multi-channel research module covering Institutional Portals, Reddit Social Discourse (`r/brasil`, `r/saude`), and Media/YouTube Press Briefing Transcripts.
  - LangGraph asynchronous multi-agent orchestration with Fan-In Reducer and institutional allowlist enforcement.
- **Specialized Multi-Artifact Suite & Self-Correction Reflection Loop**:
  - Generation of 5 discrete intelligence artifacts per execution (`executive_bulletin.md`, `epidemiological_deepdive.md`, `anomaly_alerts.md`, `media_and_social_signals.md`, `data_governance_report.md` + `report.md` and `report.pdf`).
  - LangGraph `evaluate_and_reflect` evaluator node verifying numerical groundedness against `metrics.json` to prevent hallucination.
- **ChromaDB Vector Store & Hugging Face Local Embeddings**:
  - Local, zero-cost semantic embedding model (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`).
  - Hybrid Retrieval engine combining Dense ChromaDB cosine vector search and Sparse BM25 via **Reciprocal Rank Fusion (RRF)**.
- **3-Tier Comprehensive EVALs Framework**:
  - Pre/In-Retrieval evaluation: Precision@3, Recall@3, MRR (0.75), Hit Rate (75%) comparing Dense, BM25, and Hybrid.
  - Post-Retrieval generation evaluation: 100% faithfulness score and zero hallucination rate.
  - Agent Security & Resilience evaluation: 100% defense against adversarial prompt injections and exfiltration attempts.
- **Deep Observability & Token Financial Accounting**:
  - Accurate token counting (Prompt, Completion, Total) and financial cost calculation in USD and BRL.
  - OpenInference-compliant Latency Waterfall tracing per node and subagent.
- **Modern Web Interface & Production DevOps**:
  - Streamlit dashboard overhaul with multi-artifact viewer, Observability & EVALs panel, and interactive RAG chat.
  - Multi-stage `Dockerfile`, `docker-compose.yml`, and GitHub Actions CI/CD automation workflow.

### Changed
- Expanded report contract validation and schema to accommodate multi-artifact suite and hybrid citations.
- Stabilized vector storage on Windows environments with high-performance NumPy cosine calculations and JSON index persistence.
- Refactored full pytest suite to 115 passing tests with 100% success rate.

---

## [1.0.0] - 2026-06-20

### Added
- Initial project bootstrap with DataSUS SRAG data pipeline.
- Deterministic calculation for case growth, mortality, ICU proxy, and vaccination proxy.
- Basic LangGraph pipeline, PDF export, and Streamlit dashboard.
- Domain allowlist and initial output guardrails.
