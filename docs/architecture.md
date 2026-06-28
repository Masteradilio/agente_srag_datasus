# Arquitetura

## Visao geral

O projeto separa processamento deterministico de dados, orquestracao de agente e
interface de demonstracao. O LLM nao calcula metricas diretamente; ele consome
resultados de tools auditaveis e redige o relatorio com base em artefatos
gerados por codigo.

## Camadas

- Fonte: OpenDataSUS CSV e, como fonte auxiliar historica, GitLab de dados
  unificados.
- Landing: arquivos brutos e metadados de ingestao.
- Refined: parquet normalizado com colunas canonicas.
- Metric tools: calculo de taxa de crescimento, mortalidade, UTI e vacinacao.
- Chart tools: graficos diarios de 30 dias e mensais de 12 meses.
- News tools: busca e ranking sobre dominios permitidos.
- RAG documental: recuperacao de PRD, docs, catalogo de metricas e limitacoes.
- Agent orchestrator: grafo controlado com validacao de entrada, tools,
  redacao, contrato de saida e persistencia.
- Guardrails: entrada, privacidade, saida e allowlist de dominios.
- Auditoria: manifesto, metricas, qualidade, fontes e trace JSONL.
- Streamlit: demonstracao de pipeline, relatorio, qualidade e chat.

## Fluxo de dados

1. Ingestao baixa o arquivo SRAG configurado e grava hash bruto.
2. Preprocessing resolve o mapeamento de colunas e gera parquet refinado.
3. Validacao cria relatorio de qualidade com nulos, warnings e linhas.
4. Metricas e graficos sao calculados a partir do parquet refinado.
5. Relatorio e PDF sao gerados a partir de contexto estruturado.

## Fluxo do agente

O fluxo do agente segue a ordem: validar pedido, carregar contexto da run,
coletar metricas, gerar graficos, buscar noticias, recuperar metodologia,
redigir relatorio, validar contrato e persistir artefatos. Cada etapa registra
trace com status e resumo sanitizado.

## Decisoes e trade-offs

- CSV OpenDataSUS e a fonte primaria porque contem granularidade para UTI e
  vacinacao; arquivos agregados sao mantidos apenas como referencia auxiliar.
- RAG e usado para contexto textual, nao para calculo tabular.
- O agente e deterministico na PoC para evitar dependencia de disponibilidade
  externa de LLM durante testes.
- Fontes externas sao restritas por allowlist para reduzir risco de prompt
  injection e baixa confiabilidade.
- UTI e vacinacao sao proporcoes entre casos registrados, nao medidas de
  ocupacao hospitalar nem cobertura vacinal populacional.

