# Cobertura dos Critérios de Avaliação

Este documento mapeia os critérios de avaliação do desafio para evidências
concretas no repositório. O critério de escolha da arquitetura é tratado em
`docs/architecture.md`; aqui o foco está em governança, transparência,
guardrails, tools, dados sensíveis e clean code. A matriz específica de
segurança e privacidade dos guardrails está em `docs/guardrails_security_matrix.md`.

## Matriz de cobertura

| Critério | Como o projeto cobre | Evidências no repositório |
|---|---|---|
| Governança e Transparência | Cada execução gera manifesto, hashes, relatório de qualidade, métricas, fontes, observabilidade e trace do agente por nó/tool. Isso permite revisar origem dos dados, decisões operacionais, status das tools e uso do LLM. | `src/audit/manifest.py`, `src/audit/run_context.py`, `artifacts/runs/<run_id>/manifest.json`, `agent_trace.jsonl`, `observability.json`, `news_sources.json` |
| Guardrails | Há guardrails de entrada, saída, fontes externas e contratos de relatório. Eles bloqueiam prompt injection, escopo indevido, acesso a segredos, recursos internos, comandos perigosos, recomendações clínicas individualizadas e URLs fora da allowlist. | `src/guardrails/input_guard.py`, `src/guardrails/output_guard.py`, `src/guardrails/domain_allowlist.py`, `src/agents/output_contracts.py`, `tests/test_input_guardrails.py`, `tests/test_output_guardrails.py`, `tests/test_news_allowlist.py` |
| Uso de Tools | O LLM não calcula métricas diretamente. O agente usa tools determinísticas para métricas, gráficos, notícias, RAG e validação de relatório. As chamadas são registradas no trace. | `src/agents/tools.py`, `src/agents/graph.py`, `tests/test_agent_tools.py`, `tests/test_agent_graph.py` |
| Tratamento de Dados Sensíveis | O projeto bloqueia campos individuais, identificadores em valores, granularidade excessiva e grupos abaixo do tamanho mínimo. O relatório final também bloqueia identificadores pessoais e caminhos locais. | `src/guardrails/privacy.py`, `src/guardrails/output_guard.py`, `tests/test_privacy_guardrails.py`, `tests/test_output_guardrails.py` |
| Clean Code | O código está separado por responsabilidades: ingestão, validação, pré-processamento, métricas, notícias, RAG, agente, guardrails, auditoria e reporting. Há schemas Pydantic, funções pequenas e testes por camada. | `src/data`, `src/metrics`, `src/news`, `src/rag`, `src/agents`, `src/guardrails`, `src/reporting`, `tests/` |

## Artefatos obrigatórios por execução

Uma execução completa do pipeline deve produzir:

- `manifest.json`: manifesto com origem, hash e metadados da execução.
- `data_quality_report.json` e `data_quality_report.md`: diagnóstico da base processada.
- `metrics.json`: métricas determinísticas calculadas por código.
- `chart_context.json`: dados usados para comentar os gráficos.
- `news_sources.json`: fontes externas consultadas e extraídas.
- `observability.json`: modelo, status da chamada LLM, tokens, latência e linhas processadas.
- `agent_trace.jsonl`: sequência de nós, tools chamadas, status e resumos sanitizados.
- `report.md` e `report.pdf`: relatório final.
- `charts/daily_cases_30d.png` e `charts/monthly_cases_12m.png`: gráficos obrigatórios.

Esses artefatos são verificados pelo smoke test em `tests/test_pipeline_smoke.py`,
que falha se qualquer entrega obrigatória do run deixar de ser gerada.

## Cobertura de guardrails

Os guardrails atuais cobrem:

- prompt injection e tentativas de ignorar regras;
- pedido fora do escopo SRAG/DataSUS;
- solicitação de dados linha a linha ou identificadores individuais;
- diagnóstico, tratamento ou recomendação clínica individualizada;
- exfiltração de segredos, API keys, tokens, senhas, credenciais e arquivos `.env`;
- acesso a recursos locais ou internos, como `file://`, `localhost`, `127.0.0.1` e endpoints de metadata;
- comandos destrutivos ou perigosos, incluindo shell, SQL destrutivo e execução dinâmica de código;
- vazamento de `system prompt`, developer message ou instruções internas;
- CPF, e-mail e telefone em valores de registros;
- campos sensíveis como `cpf`, `cns`, `cartao_sus`, `dt_nasc`, `nome_paciente`;
- granularidade excessiva como endereço, CEP, bairro, latitude e longitude;
- grupos com contagem abaixo do tamanho mínimo configurado;
- URLs fora da allowlist no relatório final;
- ausência de fontes, aviso de uso ou limitações metodológicas no relatório.

## Limites e transparência

Os controles são determinísticos e adequados a uma PoC técnica. Eles não
substituem uma plataforma completa de DLP, SIEM, moderação especializada ou
governança corporativa, mas tornam os riscos principais auditáveis por código,
testes e artefatos reproduzíveis.
