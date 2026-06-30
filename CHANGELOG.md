# Changelog

## Unreleased

### Added

- Bootstrap do projeto com layout `src/`, diretorios `configs/`, `app/`, `tests/`,
  `data/landing`, `data/refined` e `artifacts/runs`.
- Configuracoes YAML para settings, fontes de noticia, catalogo de metricas e
  mapeamento de colunas.
- Utilitarios base para paths, YAML, hashes SHA-256, `run_id` e logging JSON.
- Ingestao por OpenDataSUS CSV como fonte primaria:
  `INFLUD26-22-06-2026.csv`.
- Cliente GitLab mantido como fonte auxiliar/contextual para arquivos agregados
  em `Dados unificados/Unificado Srag`.
- Pre-processamento de CSV linha a linha e XLSX agregado, com normalizacao para
  colunas canonicas e geracao de Parquet.
- Relatorio de qualidade de dados em `data_quality_report.json`.
- Calculo deterministico de metricas: aumento de casos em 7 dias, mortalidade
  conhecida, mortalidade bruta, proporcao de casos com UTI e proporcao de casos
  com vacinacao registrada.
- Graficos obrigatorios `daily_cases_30d.png` e `monthly_cases_12m.png`.
- Guardrails de entrada, privacidade, saida, allowlist de dominios e contrato de
  relatorio.
- Busca estruturada de noticias allowlisted, ranking simples, extracao de HTML e
  persistencia de `news_sources.json`.
- RAG documental local com loaders, chunking, indice lexical persistido em
  `artifacts/vector_store/` e retriever com metadados de fonte.
- Agente controlado com topologia LangGraph compilavel, tools deterministicas,
  contrato de saida e trace por no.
- Manifesto de execucao, `agent_trace.jsonl` e pipeline consolidado com
  `python -m pipeline`.
- Builder de relatorio Markdown, template versionado e exportador PDF com
  fallback HTML/PDF quando WeasyPrint nao possui dependencias nativas locais.
- Dashboard Streamlit com abas Pipeline, Relatorio, Qualidade dos Dados e Chat.
- Documentacao tecnica em `docs/architecture.md`, `docs/metric_catalog.md`,
  `docs/limitations.md` e `docs/architecture_diagram.pdf`.
- Smoke cumulativo de Fase 3 + Fase 4 cobrindo preprocessamento, metricas,
  graficos e artefatos.
- Relatorio executivo comentado por LLM, com secoes `Metricas Principais`,
  `Evolucao Historica`, `Noticias Recentes` e `Fontes Consultadas`.
- Modulo de comentarios LLM com fallback local auditavel e controle por
  `DISABLE_LLM_API`.
- Busca de noticias allowlisted ampliada, com extracao de URLs reais,
  ordenacao por data e persistencia das fontes usadas.
- Documentos de avaliacao em `docs/cobertura_avaliacao.md` e
  `docs/guardrails_security_matrix.md`.
- Guardrails enterprise adicionais para entrada, saida e privacidade,
  cobrindo escopo SRAG/DataSUS, prompt injection, jailbreak, exfiltracao,
  segredos, PII, caminhos locais, dados sensiveis e grupos pequenos.
- `.env.example` versionado com placeholders seguros para orientar quem clonar
  o repositorio sem expor chaves reais.

### Changed

- Fonte primaria do pipeline mudou dos XLSX agregados do GitLab para o CSV
  oficial do OpenDataSUS, pois o CSV contem as colunas necessarias de UTI,
  vacinacao, evolucao e datas.
- Arquivos XLSX agregados do GitLab passaram a ser tratados como fonte auxiliar
  contextual, sem soma automatica na camada refined para evitar duplicidade.
- `MASTER_BACKLOG.md` recebeu a tarefa `F3.T8`, executada para validar o schema
  real dos dados e adaptar o pipeline ao arquivo CSV oficial.
- Codigo reorganizado para remover o pacote intermediario `src/srag_agent`; os
  modulos agora ficam diretamente em `src/`.
- `.env` e dados locais continuam ignorados; `.env.example` passa a ser
  versionado com valores `sua_api_key_aqui`.
- `docs/descricao_vaga.md` e `MASTER_BACKLOG.md` passam a ser arquivos locais
  ignorados pelo Git.
- Dependencias foram reduzidas para as bibliotecas efetivamente usadas pela
  implementacao atual, mantendo instalacao limpa reproduzivel em Python
  `>=3.11,<3.13`.
- Smoke de pipeline passou a simular busca/extracao de noticias para nao
  depender de rede, LLM externo ou disponibilidade de portais durante testes.
- README foi atualizado para refletir OpenDataSUS CSV como fonte primaria,
  allowlist atual, cobertura dos criterios de avaliacao e instrucoes de
  ambiente com `.env.example`.
- Chat Streamlit, como demonstracao extra, passou a usar LLM com contexto
  grounded em artefatos, parquet e busca externa allowlisted, retornando fontes
  consultadas quando noticias entram na resposta.

### Verified

- Validacao limpa em clone temporario com `pip install -r requirements.txt`,
  `pytest`, `ruff` e `mypy`.
- Streamlit respondeu HTTP 200 em `localhost:8501`.
- Pipeline real gerou `manifest.json`, `data_quality_report.json`,
  `metrics.json`, `news_sources.json`, `agent_trace.jsonl`, `report.md`,
  `report.pdf` e os dois graficos obrigatorios.
- Smoke real com `data/landing/20260627T212036-0300/INFLUD26-22-06-2026.csv`:
  `rows_raw=137551`, `rows_refined=137551`, `reference_date=2026-06-21`,
  `known_mortality=0.05992052875135012`,
  `crude_mortality=0.043961875958735304`,
  `icu_value=0.24119054023598518` e
  `vaccination_value=0.4033807881628202`.
- Regressao completa anterior: `python -m pytest tests -q` com 48 testes,
  `python -m ruff check .` sem achados e `python -m mypy src` com sucesso.
- Validacao final de submissao, excluindo Streamlit/chat da conformidade:
  `python -m pytest tests -q --ignore=tests/test_streamlit_smoke.py` com
  94 testes, `python -m ruff check .` sem achados e `python -m mypy src`
  com sucesso em 47 arquivos.
- Varredura final de segredos sem chaves reais versionaveis; `.env`, dados,
  refined, artefatos de runtime e materiais locais permanecem ignorados.
