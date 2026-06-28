# Changelog

## Unreleased

### Added

- Bootstrap do projeto com layout `src/`, diretórios `configs/`, `app/`, `tests/`,
  `data/landing`, `data/refined` e `artifacts/runs`.
- Configurações YAML para settings, fontes de notícia, catálogo de métricas e
  mapeamento de colunas.
- Utilitários base para paths, YAML, hashes SHA-256, `run_id` e logging JSON.
- Ingestão por OpenDataSUS CSV como fonte primária:
  `INFLUD26-22-06-2026.csv`.
- Cliente GitLab mantido como fonte auxiliar/contextual para arquivos agregados
  em `Dados unificados/Unificado Srag`.
- Pré-processamento de CSV linha a linha e XLSX agregado, com normalização para
  colunas canônicas e geração de Parquet.
- Relatório de qualidade de dados em `data_quality_report.json`.
- Cálculo determinístico de métricas:
  - taxa de aumento de casos em 7 dias;
  - taxa de mortalidade conhecida;
  - taxa de mortalidade bruta;
  - proporção de casos com UTI;
  - proporção de casos com vacinação registrada.
- Geração dos gráficos obrigatórios:
  - `daily_cases_30d.png`;
  - `monthly_cases_12m.png`.
- Guardrail de allowlist de domínios para fontes externas.
- Busca estruturada de notícias allowlisted, ranking simples, extração de HTML e
  persistência de `news_sources.json`.
- RAG documental local com loaders, chunking, índice lexical persistido em
  `artifacts/vector_store/` e retriever com metadados de fonte.
- Teste smoke Fase 3 + Fase 4 cobrindo preprocessamento, métricas, gráficos e
  artefatos no formato agregado.

### Changed

- Fonte primária do pipeline mudou dos XLSX agregados do GitLab para o CSV
  oficial do OpenDataSUS, pois o CSV contém as colunas necessárias de UTI,
  vacinação, evolução e datas.
- Arquivos XLSX agregados do GitLab passaram a ser tratados como fonte auxiliar
  contextual, sem soma automática na camada refined para evitar duplicidade.
- `MASTER_BACKLOG.md` recebeu a tarefa `F3.T8`, executada para validar o schema
  real dos dados e adaptar o pipeline.
- `.gitignore` passou a ignorar `.env.example` porque o arquivo local contém
  chaves de API neste checkout.

### Verified

- Smoke real com `data/landing/20260627T212036-0300/INFLUD26-22-06-2026.csv`:
  - `rows_raw=137551`;
  - `rows_refined=137551`;
  - `reference_date=2026-06-21`;
  - `known_mortality=0.05992052875135012`;
  - `crude_mortality=0.043961875958735304`;
  - `icu_value=0.24119054023598518`;
  - `vaccination_value=0.4033807881628202`.
- Regressão completa:
  - `python -m pytest tests -q`: 48 passed;
  - `python -m ruff check .`: All checks passed;
  - `python -m mypy src`: Success.
