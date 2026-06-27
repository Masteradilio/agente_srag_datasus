# PRD.md — Agente GenAI para Relatório de SRAG com Dados OpenDataSUS

**Projeto:** SRAG GenAI Report Agent  
**Tipo:** Prova de Conceito técnica para desafio de Senior AI Engineer  
**Versão:** 1.0  
**Status:** Planejamento aprovado para implementação  
**Autor:** Adílio Farias  

---

## 1. Resumo Executivo

Este projeto tem como objetivo construir uma solução baseada em Inteligência Artificial Generativa capaz de gerar relatórios automatizados sobre Síndrome Respiratória Aguda Grave (SRAG), combinando dados estruturados do OpenDataSUS/DataSUS com notícias e fontes oficiais em tempo real.

A solução será composta por um pipeline determinístico de dados, uma camada analítica auditável, um agente GenAI orquestrado por tools controladas, uma camada de RAG documental, mecanismos de guardrails e uma interface em Streamlit para demonstração.

A decisão arquitetural principal é separar claramente:

1. **Cálculo determinístico:** ingestão, pré-processamento, validação, métricas e gráficos.
2. **Geração com LLM:** explicação, contextualização, redação do relatório e interação conversacional.
3. **Governança:** logs, rastreabilidade, versionamento, manifesto de execução, fontes consultadas e auditoria de decisões.

O LLM não deve calcular métricas diretamente a partir de linguagem natural. Ele deve chamar tools confiáveis que retornam métricas já calculadas por código. Isso reduz risco de alucinação, melhora reprodutibilidade e facilita a defesa técnica da arquitetura.

---

## 2. Contexto do Desafio

A Indicium HealthCare Inc. deseja avaliar uma PoC capaz de ajudar profissionais da área da saúde a entenderem, em tempo real, a severidade e o avanço de surtos de doenças.

Para a PoC, será usada a base real de internações por SRAG do OpenDataSUS/DataSUS. O agente deve consultar dados, buscar notícias em tempo real e gerar um relatório contendo métricas, gráficos e comentários explicativos sobre o cenário observado.

As métricas obrigatórias são:

- taxa de aumento de casos;
- taxa de mortalidade;
- taxa de ocupação de UTI;
- taxa de vacinação da população;
- gráfico de número diário de casos dos últimos 30 dias;
- gráfico de número mensal de casos dos últimos 12 meses.

O desafio também avalia:

- escolha de arquitetura;
- governança e transparência;
- mecanismos de auditoria e registro das decisões dos agentes;
- guardrails;
- uso de tools;
- tratamento de dados sensíveis;
- clean code.

---

## 3. Objetivos do Produto

### 3.1 Objetivo Principal

Construir uma aplicação demonstrável que gere um relatório automatizado sobre SRAG, combinando métricas calculadas sobre dados reais com explicações contextualizadas por notícias e fontes oficiais recentes.

### 3.2 Objetivos Técnicos

- Automatizar a descoberta da pasta mais recente no repositório GitLab de dados unificados.
- Baixar o arquivo `srag_total.xlsx` da pasta mais recente.
- Persistir o arquivo bruto em camada `landing`.
- Pré-processar os dados e salvar versão otimizada em camada `refined`.
- Calcular métricas epidemiológicas de forma determinística.
- Gerar os dois gráficos obrigatórios.
- Implementar um agente GenAI que use tools controladas para obter métricas, gráficos, contexto documental e notícias.
- Implementar RAG documental para apoiar explicações metodológicas e consulta ao dicionário de dados, sem usar o banco vetorial como motor principal de cálculo tabular.
- Registrar logs, fontes, decisões e artefatos por execução.
- Expor a solução em dashboard Streamlit.
- Criar documentação robusta no README e diagrama conceitual em PDF.

### 3.3 Objetivos de Defesa Técnica

A solução deve permitir defender claramente as seguintes decisões:

- Por que métricas são calculadas por código e não pelo LLM.
- Por que o agente usa tools com schemas e não acesso livre aos dados.
- Como a arquitetura reduz alucinação.
- Como as fontes externas são controladas por allowlist.
- Como os dados sensíveis são tratados.
- Como uma execução pode ser auditada e reproduzida.
- Como o projeto poderia evoluir para produção.

---

## 4. Não Objetivos

Este projeto não tem como objetivo:

- Substituir vigilância epidemiológica oficial.
- Fornecer diagnóstico médico individual.
- Recomendar tratamento clínico individualizado.
- Expor dados linha a linha de pacientes.
- Criar um modelo preditivo epidemiológico completo.
- Fazer fine-tuning de LLM.
- Construir infraestrutura cloud produtiva completa.
- Criar um data warehouse corporativo.
- Usar banco vetorial para cálculo numérico das métricas.

---

## 5. Personas e Usuários

### 5.1 Usuário Avaliador Técnico

Pessoa que avaliará arquitetura, código, clareza, governança, guardrails, uso de tools e capacidade de defesa técnica.

Necessidades:

- Rodar o projeto com comandos simples.
- Entender rapidamente a arquitetura.
- Ver evidências de senioridade técnica.
- Inspecionar logs, testes e decisões.

### 5.2 Profissional de Saúde / Analista Epidemiológico

Usuário final hipotético da PoC.

Necessidades:

- Visualizar métricas de SRAG de forma clara.
- Entender evolução recente dos casos.
- Obter comentários contextualizados com fontes confiáveis.
- Consultar limitações das métricas.

### 5.3 Engenheiro de IA / Mantenedor

Pessoa responsável por evoluir a solução.

Necessidades:

- Código modular.
- Configurações centralizadas.
- Testes automatizados.
- Contratos claros de tools.
- Facilidade para trocar LLM, vector store ou fonte de notícias.

---

## 6. Princípios de Arquitetura

### 6.1 Determinismo para Métricas

Todas as métricas devem ser calculadas por código testável. O LLM apenas interpreta os resultados retornados por tools.

### 6.2 Separação entre Dados Tabulares e Conhecimento Textual

Dados tabulares devem ser armazenados em Parquet e consultados por Polars, DuckDB ou Pandas.

O banco vetorial deve armazenar conteúdo textual, como:

- dicionário de dados;
- catálogo de métricas;
- documentação do projeto;
- notícias extraídas;
- relatórios gerados;
- limitações metodológicas;
- explicações de campos e fórmulas.

### 6.3 Tools Pequenas, Explícitas e Auditáveis

O agente deve acessar funcionalidades por meio de tools com entrada e saída bem definidas.

Exemplo:

```python
get_metric_summary(period: str, uf: str | None = None) -> MetricSummary
```

O agente não deve receber acesso livre ao banco nem executar SQL arbitrário.

### 6.4 Segurança e Privacidade por Design

O sistema deve bloquear perguntas fora do escopo, evitar exposição de registros individuais e aplicar regras de agregação mínima.

### 6.5 Reprodutibilidade

Cada execução deve gerar um diretório de artefatos com manifesto, hash do dado bruto, hash do dado refinado, métricas, relatório, gráficos, fontes e trace do agente.

### 6.6 Observabilidade

Todas as etapas relevantes devem gerar logs estruturados.

---

## 7. Arquitetura Conceitual

```text
[GitLab / OpenDataSUS]
        |
        v
[Data Ingestion]
- listar diretórios
- escolher pasta mais recente
- baixar srag_total.xlsx
- salvar landing/raw
- gerar manifest parcial
        |
        v
[Data Quality + Preprocessing]
- validação de schema mínimo
- normalização de colunas
- tratamento de datas
- tratamento de nulos e códigos
- geração de data_quality_report.json
- salvar refined/srag_total.parquet
        |
        v
[Analytical Layer]
- leitura Parquet
- cálculo de métricas
- agregações temporais
- geração de gráficos
        |
        v
[Agent Orchestrator]
- chama tools de métricas
- chama tools de notícias
- consulta RAG documental
- gera relatório
- passa por validação de saída
        |
        v
[Guardrails + Audit]
- valida entrada
- restringe tools
- aplica allowlist
- bloqueia dados sensíveis
- registra decisões
        |
        v
[Streamlit Dashboard]
- pipeline
- relatório
- qualidade dos dados
- chat analítico
```

---

## 8. Stack Técnica Recomendada

### 8.1 Linguagem e Empacotamento

- Python 3.11+
- `uv` ou `poetry` para gerenciamento de dependências
- `pyproject.toml`
- `ruff` para lint/format
- `pytest` para testes

### 8.2 Dados

- `requests` ou `httpx` para acesso HTTP
- `pandas` ou `polars` para leitura inicial de Excel
- `duckdb` para consultas analíticas locais
- `pyarrow` para Parquet
- `pandera` ou validações Pydantic para qualidade de dados

### 8.3 Agente e RAG

- LangGraph para orquestração controlada do agente
- LangChain apenas se facilitar integração com tools, retrievers e LLMs
- ChromaDB ou Qdrant como vector store open source
- Modelo de embedding multilíngue, preferencialmente com bom suporte a português
- LLM configurável por variável de ambiente

### 8.4 Interface

- Streamlit para dashboard e chat
- Plotly ou Matplotlib para gráficos

### 8.5 Exportação

- Markdown como formato primário do relatório
- PDF gerado a partir de Markdown/HTML
- PNG ou SVG para gráficos

---

## 9. Estrutura de Repositório

```text
srag-genai-agent/
  README.md
  PRD.md
  pyproject.toml
  .env.example
  Makefile
  Dockerfile
  .gitignore

  configs/
    settings.yaml
    metric_catalog.yaml
    news_sources.yaml
    column_mapping.yaml

  src/
    srag_agent/
      __init__.py

      data/
        gitlab_client.py
        ingestion.py
        preprocessing.py
        validation.py
        schema.py

      metrics/
        definitions.py
        calculators.py
        charts.py

      news/
        search.py
        extract.py
        rank.py
        summarize.py

      rag/
        loaders.py
        chunking.py
        vector_store.py
        retriever.py

      agents/
        graph.py
        state.py
        prompts.py
        tools.py
        output_contracts.py

      guardrails/
        input_guard.py
        output_guard.py
        privacy.py
        domain_allowlist.py

      reporting/
        report_builder.py
        pdf_exporter.py
        templates/
          report_template.md

      audit/
        manifest.py
        logger.py
        run_context.py

      utils/
        dates.py
        hashing.py
        paths.py

  app/
    streamlit_app.py

  tests/
    test_latest_folder_selection.py
    test_preprocessing.py
    test_metrics.py
    test_news_allowlist.py
    test_guardrails.py
    test_report_contract.py

  docs/
    architecture.md
    metric_catalog.md
    limitations.md
    architecture_diagram.pdf

  data/
    landing/.gitkeep
    refined/.gitkeep

  artifacts/
    runs/.gitkeep
```

---

## 10. Fontes e Allowlist

A aplicação deve consultar apenas fontes explicitamente permitidas. Isso reduz risco de baixa qualidade informacional, scraping indevido, prompt injection em páginas externas e uso de fontes não confiáveis.

### 10.1 Allowlist Máxima de Fontes

| Nº | Domínio/Fonte | Uso Permitido | Justificativa |
|---:|---|---|---|
| 1 | `gitlab.com/cgcovid/dados-abertos` | Download da base unificada SRAG | Fonte indicada no desafio para obter `srag_total.xlsx`. |
| 2 | `dadosabertos.saude.gov.br` | Dataset oficial, dicionário de dados e metadados | Portal oficial de dados abertos do SUS. |
| 3 | `gov.br/saude` | Notas técnicas, orientações e comunicados oficiais | Fonte institucional do Ministério da Saúde. |
| 4 | `infoms.saude.gov.br` | Painéis oficiais de saúde e vacinação, quando aplicável | Fonte oficial para indicadores complementares. |
| 5 | `fiocruz.br` | Boletins InfoGripe e notícias técnicas | Referência pública em vigilância e análise de SRAG. |
| 6 | `github.com/infogripe` | Repositórios públicos do InfoGripe, quando úteis | Suporte técnico e materiais públicos relacionados ao InfoGripe. |
| 7 | `agenciagov.ebc.com.br` | Notícias governamentais sobre saúde pública | Fonte pública de comunicação institucional. |
| 8 | `agenciabrasil.ebc.com.br` | Notícias públicas de saúde | Fonte jornalística pública brasileira. |
| 9 | `paho.org` | Contexto regional das Américas | Organização Pan-Americana da Saúde. |
| 10 | `who.int` | Contexto global e vigilância respiratória | Organização Mundial da Saúde. |

### 10.2 Regras de Uso da Allowlist

- O agente não deve buscar fontes fora da allowlist.
- Resultados de busca devem ser filtrados por domínio antes de qualquer extração.
- Cada notícia usada no relatório deve ser registrada em `news_sources.json`.
- Cada comentário baseado em notícia deve ser rastreável até pelo menos uma fonte.
- Conteúdo de páginas externas deve ser tratado como dado não confiável.
- Instruções encontradas em páginas externas nunca devem sobrescrever system prompt, developer prompt ou regras internas.

---

## 11. Pipeline de Dados

### 11.1 Ingestão

Responsabilidade: localizar e baixar automaticamente o arquivo mais recente.

Fluxo:

1. Acessar a árvore do repositório GitLab.
2. Navegar até `Dados unificados/Unificado Srag`.
3. Listar subpastas.
4. Identificar a pasta mais recente pelo nome.
5. Validar se existe `srag_total.xlsx`.
6. Baixar o arquivo.
7. Salvar em `data/landing/<run_id>/srag_total.xlsx`.
8. Calcular hash SHA-256 do arquivo.
9. Registrar metadados no manifesto.

Critério de seleção da pasta mais recente:

- O nome da pasta deve ser interpretado por uma função dedicada.
- A função deve aceitar formatos como `YYYY`, `YYYY_MM`, `YYYY_WW`, `YYYY_SE`, `YYYY_XX` ou equivalentes encontrados no repositório.
- Quando houver ambiguidade, ordenar primeiro por ano e depois pelo maior sufixo numérico.
- A função deve ser coberta por testes unitários.

### 11.2 Camada Landing

A camada `landing` deve armazenar o dado bruto sem alteração.

Regras:

- Nunca sobrescrever arquivo bruto sem registrar nova execução.
- Salvar hash do arquivo.
- Salvar caminho original e pasta selecionada.
- Salvar timestamp da coleta.

### 11.3 Pré-processamento

Responsabilidade: converter dados reais e imperfeitos em uma base analítica consistente.

Tratamentos esperados:

- normalizar nomes de colunas;
- mapear colunas para nomes canônicos internos;
- converter datas;
- remover linhas completamente vazias;
- tratar códigos ignorados ou desconhecidos;
- padronizar valores categóricos;
- gerar flags auxiliares;
- aplicar validações mínimas de consistência;
- preservar contagem de registros descartados ou inválidos;
- salvar a base refinada em Parquet.

### 11.4 Camada Refined

Arquivo principal:

```text
data/refined/<run_id>/srag_total.parquet
```

Essa camada será a fonte oficial para cálculo de métricas.

---

## 12. Colunas Relevantes e Mapeamento

Como bases públicas podem mudar de schema, o projeto deve usar um arquivo de mapeamento configurável.

Exemplo de colunas candidatas:

| Conceito | Colunas candidatas | Uso |
|---|---|---|
| Data de notificação | `DT_NOTIFIC` | Série temporal alternativa. |
| Data de início dos sintomas | `DT_SIN_PRI` | Série temporal preferencial para casos. |
| Unidade Federativa | `SG_UF_NOT`, `SG_UF` | Filtros geográficos. |
| Município | `ID_MUNICIP`, `CO_MUN_NOT` | Filtros agregados. |
| Evolução | `EVOLUCAO` | Mortalidade. |
| Data de evolução | `DT_EVOLUCA` | Recorte temporal de desfecho. |
| UTI | `UTI` | Proporção de casos com UTI. |
| Entrada em UTI | `DT_ENTUTI` | Estimativa temporal de UTI, se disponível. |
| Saída de UTI | `DT_SAIDUTI` | Estimativa temporal de UTI, se disponível. |
| Vacinação | `VACINA_COV`, `VACINA`, campos equivalentes | Proporção de casos com vacinação registrada. |
| Classificação final | `CLASSI_FIN` | Filtros de SRAG por etiologia, se aplicável. |
| Critério de encerramento | `CRITERIO` | Qualidade analítica. |

Regras:

- Se uma coluna obrigatória não existir, a aplicação deve falhar de forma explicável.
- Se uma coluna complementar não existir, a métrica associada deve registrar limitação.
- O mapeamento real deve ser validado contra o dicionário de dados.

---

## 13. Catálogo de Métricas

As fórmulas devem ser documentadas em `configs/metric_catalog.yaml` e `docs/metric_catalog.md`.

### 13.1 Data de Referência

A data de referência do relatório deve ser a maior data válida encontrada na base refinada, e não necessariamente a data atual do sistema.

Motivo: bases públicas podem ter atraso de atualização.

```text
data_referencia = max(data_evento_valida)
```

### 13.2 Taxa de Aumento de Casos

Definição principal:

```text
taxa_aumento_7d = (casos_ultimos_7_dias - casos_7_dias_anteriores) / casos_7_dias_anteriores
```

Janela:

- últimos 7 dias encerrados na data de referência;
- comparados com os 7 dias imediatamente anteriores.

Tratamento de divisão por zero:

- se o período anterior tiver zero casos, retornar `null` e explicar limitação.

Campos usados:

- data canônica de caso, preferencialmente início dos sintomas;
- fallback para data de notificação se necessário.

### 13.3 Taxa de Mortalidade

Definição principal:

```text
taxa_mortalidade_conhecida = obitos / casos_com_evolucao_conhecida
```

Definição complementar:

```text
taxa_mortalidade_bruta = obitos / casos_totais
```

Motivo:

A taxa sobre casos com evolução conhecida reduz distorção causada por registros ainda em aberto ou sem preenchimento.

O relatório deve apresentar a métrica principal e informar a limitação.

### 13.4 Taxa de Ocupação de UTI

A base de SRAG não necessariamente contém denominador de leitos disponíveis. Portanto, a métrica deve ser nomeada com precisão.

Definição principal para a PoC:

```text
proporcao_casos_com_uti = casos_com_uti / casos_totais
```

Nome recomendado no relatório:

```text
Proporção de casos de SRAG com passagem por UTI
```

Se houver datas de entrada e saída de UTI, pode ser criada uma métrica complementar:

```text
casos_estimados_em_uti_por_dia
```

Limitação obrigatória:

A métrica não representa ocupação hospitalar real de leitos sem uma base externa de leitos disponíveis.

### 13.5 Taxa de Vacinação da População

A base SRAG pode conter informação de vacinação dos casos notificados, mas isso não mede automaticamente cobertura vacinal da população geral.

Definição principal da PoC:

```text
proporcao_casos_com_vacinacao_registrada = casos_com_vacinacao_registrada / casos_com_status_vacinal_conhecido
```

Nome recomendado no relatório:

```text
Proporção de casos de SRAG com vacinação registrada
```

Extensão opcional:

- consultar fonte oficial complementar de cobertura vacinal populacional, caso disponível e estável;
- apresentar cobertura populacional separadamente da proporção entre casos.

Limitação obrigatória:

A métrica calculada na base de SRAG não deve ser descrita como cobertura vacinal populacional geral se o denominador populacional não estiver disponível.

### 13.6 Gráfico de Casos Diários — Últimos 30 Dias

Definição:

- eixo X: data;
- eixo Y: número de casos;
- janela: 30 dias encerrados na data de referência;
- agregação: contagem de casos por data canônica.

Arquivo esperado:

```text
artifacts/runs/<run_id>/charts/daily_cases_30d.png
```

### 13.7 Gráfico de Casos Mensais — Últimos 12 Meses

Definição:

- eixo X: mês;
- eixo Y: número de casos;
- janela: 12 meses encerrados no mês da data de referência;
- agregação: contagem de casos por mês.

Arquivo esperado:

```text
artifacts/runs/<run_id>/charts/monthly_cases_12m.png
```

---

## 14. Data Quality Report

Cada execução deve gerar:

```text
artifacts/runs/<run_id>/data_quality_report.json
```

Conteúdo mínimo:

```json
{
  "rows_raw": 0,
  "rows_refined": 0,
  "columns_raw": 0,
  "columns_selected": 0,
  "invalid_dates": {},
  "missing_required_columns": [],
  "missing_optional_columns": [],
  "null_rate_by_selected_column": {},
  "discarded_rows": 0,
  "warnings": []
}
```

O relatório final deve mencionar limitações relevantes encontradas na qualidade dos dados.

---

## 15. Camada de RAG

### 15.1 Objetivo

A camada RAG deve fornecer conhecimento textual ao agente, sem substituir a camada analítica.

### 15.2 Conteúdos Indexados

- dicionário de dados;
- catálogo de métricas;
- documentação de limitações;
- notícias extraídas e resumidas;
- relatório atual;
- relatórios anteriores, se houver;
- README e arquitetura do projeto.

### 15.3 Conteúdos Não Indexados como Fonte Primária

- registros linha a linha da base SRAG;
- dados pessoais ou quasi-identificadores;
- tabelas completas de pacientes;
- arquivos brutos sem curadoria.

### 15.4 Vector Store

Opções aceitáveis:

- ChromaDB para simplicidade local;
- Qdrant para defesa mais próxima de produção.

Critério de escolha para MVP:

- ChromaDB se o objetivo for velocidade de implementação;
- Qdrant se houver tempo para demonstrar maturidade maior.

---

## 16. Agente GenAI

### 16.1 Papel do Agente

O agente atua como orquestrador e redator analítico.

Ele deve:

- consultar métricas por tools;
- consultar gráficos gerados por tools;
- recuperar explicações metodológicas via RAG;
- buscar notícias em fontes permitidas;
- gerar relatório final;
- responder perguntas no chat com base no relatório e nos dados agregados.

Ele não deve:

- calcular métricas por conta própria;
- acessar dados linha a linha sem agregação;
- executar SQL livre;
- usar fontes fora da allowlist;
- dar diagnóstico médico individual;
- inventar fonte, número ou conclusão.

### 16.2 Orquestração com LangGraph

O fluxo do agente deve ser modelado como grafo controlado.

Nós sugeridos:

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

### 16.3 Estado do Agente

Exemplo de estado:

```python
class AgentState(TypedDict):
    run_id: str
    user_request: str
    metric_summary: dict
    chart_paths: dict
    news_evidence: list[dict]
    rag_context: list[dict]
    draft_report: str
    validation_errors: list[str]
    final_report_path: str
```

---

## 17. Tools do Agente

### 17.1 `get_metric_summary`

Retorna métricas obrigatórias e complementares.

Entrada:

```json
{
  "run_id": "string",
  "uf": "string|null",
  "period": "default|custom"
}
```

Saída:

```json
{
  "data_referencia": "YYYY-MM-DD",
  "taxa_aumento_7d": 0.0,
  "taxa_mortalidade_conhecida": 0.0,
  "taxa_mortalidade_bruta": 0.0,
  "proporcao_casos_com_uti": 0.0,
  "proporcao_casos_com_vacinacao_registrada": 0.0,
  "limitations": []
}
```

### 17.2 `generate_required_charts`

Gera os dois gráficos obrigatórios.

Saída:

```json
{
  "daily_cases_30d": "path/to/daily_cases_30d.png",
  "monthly_cases_12m": "path/to/monthly_cases_12m.png"
}
```

### 17.3 `search_srag_news`

Busca notícias e fontes recentes sobre SRAG.

Regras:

- aplicar allowlist antes de extrair conteúdo;
- priorizar fontes oficiais;
- registrar data, título, domínio e trecho relevante;
- limitar número de fontes por relatório.

### 17.4 `retrieve_context`

Busca no RAG documental informações sobre:

- definição das métricas;
- limitações;
- campos usados;
- metodologia;
- contexto das notícias já extraídas.

### 17.5 `validate_report_contract`

Confere se o relatório contém:

- as quatro métricas obrigatórias;
- os dois gráficos obrigatórios;
- seção de fontes;
- seção de limitações;
- aviso de uso analítico;
- ausência de dados sensíveis linha a linha.

---

## 18. Relatório Gerado

### 18.1 Formato

Formato primário:

```text
artifacts/runs/<run_id>/report.md
```

Formato complementar:

```text
artifacts/runs/<run_id>/report.pdf
```

### 18.2 Estrutura Mínima do Relatório

```markdown
# Relatório Automatizado de SRAG

## 1. Sumário Executivo

## 2. Dados Utilizados
- fonte
- pasta selecionada
- arquivo
- data de referência
- hash do arquivo bruto

## 3. Métricas Principais
- taxa de aumento de casos
- taxa de mortalidade
- proporção de casos com UTI
- proporção de casos com vacinação registrada

## 4. Evolução Temporal
- gráfico diário dos últimos 30 dias
- gráfico mensal dos últimos 12 meses

## 5. Contexto de Notícias e Fontes Oficiais
- principais fatos recentes
- relação entre notícias e métricas observadas

## 6. Comentários Analíticos do Agente
- interpretação do cenário
- hipóteses explicativas
- cautelas

## 7. Limitações Metodológicas

## 8. Fontes Consultadas

## 9. Aviso de Uso
```

### 18.3 Regras de Redação

O relatório deve:

- distinguir claramente dado calculado de comentário interpretativo;
- citar fontes consultadas;
- evitar tom alarmista;
- declarar limitações;
- não oferecer aconselhamento médico individual;
- indicar quando uma métrica é proxy e não medição direta.

---

## 19. Guardrails

### 19.1 Guardrails de Entrada

Devem bloquear ou redirecionar:

- pedidos fora do escopo de SRAG, relatório, metodologia ou dados agregados;
- tentativas de prompt injection;
- pedidos para ignorar regras do sistema;
- pedidos de dados pessoais ou registros individuais;
- pedidos de diagnóstico ou tratamento médico individualizado;
- pedidos de scraping fora da allowlist.

### 19.2 Guardrails de Tools

- O LLM só pode chamar tools registradas.
- Cada tool deve ter schema validado.
- Não permitir SQL livre vindo do LLM.
- Aplicar timeout.
- Registrar toda chamada de tool.
- Bloquear domínios fora da allowlist.
- Validar paths de arquivo para evitar path traversal.

### 19.3 Guardrails de Privacidade

- Não retornar linhas individuais.
- Não exibir recortes com contagem menor que limite configurável.
- Aplicar regra de agregação mínima, por exemplo `min_group_size = 10`.
- Remover ou não carregar campos que possam facilitar reidentificação.
- Evitar combinação excessivamente granular de filtros.

### 19.4 Guardrails de Saída

Antes de exibir resposta ou relatório:

- validar presença das métricas obrigatórias;
- validar presença dos gráficos obrigatórios;
- validar se afirmações de notícias possuem fonte;
- validar se não há dados sensíveis;
- validar se limitações estão declaradas;
- validar se não há recomendações clínicas individualizadas.

---

## 20. Governança, Auditoria e Transparência

Cada execução deve gerar uma pasta:

```text
artifacts/runs/<run_id>/
```

Conteúdo esperado:

```text
manifest.json
agent_trace.jsonl
data_quality_report.json
metrics.json
news_sources.json
report.md
report.pdf
charts/
  daily_cases_30d.png
  monthly_cases_12m.png
```

### 20.1 `manifest.json`

Conteúdo mínimo:

```json
{
  "run_id": "string",
  "created_at": "ISO-8601",
  "selected_folder": "string",
  "input_file": "srag_total.xlsx",
  "source_repository": "string",
  "source_path": "string",
  "raw_file_hash": "sha256",
  "refined_file_hash": "sha256",
  "rows_raw": 0,
  "rows_refined": 0,
  "model_name": "string",
  "embedding_model": "string",
  "prompt_version": "string",
  "metric_catalog_version": "string",
  "allowlist_version": "string"
}
```

### 20.2 `agent_trace.jsonl`

Cada linha deve registrar um evento:

```json
{
  "timestamp": "ISO-8601",
  "run_id": "string",
  "node": "collect_metrics",
  "tool": "get_metric_summary",
  "input_summary": {},
  "output_summary": {},
  "status": "success"
}
```

Não registrar prompts com segredos ou chaves de API.

---

## 21. Streamlit Dashboard

### 21.1 Aba Pipeline

Deve permitir:

- executar ingestão;
- ver pasta selecionada;
- ver status de download;
- ver hash do arquivo;
- ver status da camada refined;
- ver erros de validação.

### 21.2 Aba Relatório

Deve mostrar:

- métricas principais;
- gráficos obrigatórios;
- relatório gerado;
- fontes usadas;
- botão de download do Markdown/PDF.

### 21.3 Aba Qualidade dos Dados

Deve mostrar:

- número de linhas brutas e refinadas;
- colunas selecionadas;
- percentual de nulos;
- datas inválidas;
- avisos;
- limitações de interpretação.

### 21.4 Aba Chat

Deve permitir perguntas sobre:

- relatório gerado;
- métricas;
- metodologia;
- limitações;
- fontes usadas.

O chat deve recusar:

- diagnóstico individual;
- dados linha a linha;
- perguntas fora do escopo;
- pedidos para burlar regras.

---

## 22. Requisitos Funcionais

| ID | Requisito | Prioridade |
|---|---|---|
| RF-001 | Listar diretórios do GitLab e selecionar a pasta mais recente. | Alta |
| RF-002 | Baixar `srag_total.xlsx` da pasta selecionada. | Alta |
| RF-003 | Salvar dado bruto em camada landing. | Alta |
| RF-004 | Gerar hash e manifesto da execução. | Alta |
| RF-005 | Pré-processar base e salvar Parquet em refined. | Alta |
| RF-006 | Gerar data quality report. | Alta |
| RF-007 | Calcular as quatro métricas obrigatórias. | Alta |
| RF-008 | Gerar gráfico diário dos últimos 30 dias. | Alta |
| RF-009 | Gerar gráfico mensal dos últimos 12 meses. | Alta |
| RF-010 | Buscar notícias/fontes recentes sobre SRAG usando allowlist. | Alta |
| RF-011 | Implementar agente com tools controladas. | Alta |
| RF-012 | Gerar relatório em Markdown. | Alta |
| RF-013 | Exportar relatório para PDF. | Média |
| RF-014 | Disponibilizar dashboard Streamlit. | Alta |
| RF-015 | Disponibilizar chat sobre relatório e metodologia. | Média |
| RF-016 | Registrar trace do agente. | Alta |
| RF-017 | Implementar guardrails de entrada, tools e saída. | Alta |
| RF-018 | Criar README didático e diagrama PDF. | Alta |

---

## 23. Requisitos Não Funcionais

### 23.1 Segurança

- Chaves em `.env`, nunca commitadas.
- Allowlist para fontes externas.
- Sanitização de entrada.
- Sem exposição de dados individuais.

### 23.2 Confiabilidade

- Fallback para arquivo em cache se download falhar.
- Falhas explicáveis.
- Logs estruturados.

### 23.3 Reprodutibilidade

- Manifesto por execução.
- Hashes dos dados.
- Versão do catálogo de métricas.
- Versão dos prompts.

### 23.4 Manutenibilidade

- Código modular.
- Funções pequenas.
- Type hints.
- Testes unitários.
- Configuração centralizada.

### 23.5 Performance

- Salvar Parquet para leitura rápida.
- Evitar recarregar Excel em cada interação.
- Cache de notícias e embeddings.
- Limitar chamadas ao LLM.

---

## 24. Testes Automatizados

### 24.1 Testes de Dados

- seleção correta da pasta mais recente;
- download com mock de GitLab;
- validação de schema mínimo;
- conversão de datas;
- tratamento de nulos;
- geração de Parquet.

### 24.2 Testes de Métricas

- taxa de aumento com casos normais;
- taxa de aumento com denominador zero;
- mortalidade com evolução conhecida;
- mortalidade com dados ausentes;
- proporção de UTI;
- proporção de vacinação;
- janelas de 30 dias e 12 meses.

### 24.3 Testes de Guardrails

- bloqueio de prompt injection;
- bloqueio de domínio fora da allowlist;
- bloqueio de pedido de dados individuais;
- bloqueio de diagnóstico individual;
- validação de contagem mínima por grupo.

### 24.4 Testes do Relatório

- contém as quatro métricas;
- contém os dois gráficos;
- contém fontes;
- contém limitações;
- não contém dados sensíveis;
- separa métricas calculadas de comentários interpretativos.

---

## 25. Critérios de Aceite

A solução será considerada satisfatória quando:

1. O avaliador conseguir rodar o projeto com instruções claras no README.
2. A aplicação localizar automaticamente a pasta mais recente do repositório.
3. O arquivo `srag_total.xlsx` for baixado e salvo em landing.
4. O pipeline gerar Parquet refinado.
5. As quatro métricas obrigatórias forem calculadas por código.
6. Os dois gráficos obrigatórios forem gerados.
7. O agente gerar relatório com comentários e fontes.
8. O relatório declarar limitações metodológicas.
9. Houver guardrails implementados em código.
10. Houver logs e manifesto por execução.
11. A interface Streamlit demonstrar pipeline, relatório, qualidade dos dados e chat.
12. O repositório público conter README, PRD e diagrama conceitual em PDF.

---

## 26. README.md — Conteúdo Esperado

O README deve ser escrito como documento de defesa técnica.

Estrutura recomendada:

```markdown
# SRAG GenAI Report Agent

## 1. Visão Geral

## 2. Demonstração
- screenshots
- exemplo de relatório

## 3. Arquitetura
- diagrama
- explicação das camadas

## 4. Como Rodar
- pré-requisitos
- variáveis de ambiente
- comandos

## 5. Pipeline de Dados

## 6. Métricas e Fórmulas

## 7. Agente e Tools

## 8. RAG Documental

## 9. Guardrails e Privacidade

## 10. Governança e Auditoria

## 11. Testes

## 12. Limitações

## 13. Próximos Passos
```

Comandos esperados:

```bash
make setup
make test
make run-pipeline
make run-app
```

---

## 27. Diagrama Conceitual em PDF

O repositório deve incluir:

```text
docs/architecture_diagram.pdf
```

O diagrama deve mostrar:

- fonte GitLab/OpenDataSUS;
- camada landing;
- camada refined;
- camada analítica;
- vector store;
- agente principal;
- tools;
- LLM;
- fontes de notícias;
- guardrails;
- auditoria;
- Streamlit.

---

## 28. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Mudança no schema do arquivo | Métricas quebram | Mapeamento configurável e validação de schema. |
| Pasta mais recente com nome inesperado | Download falha | Parser testado e fallback explicável. |
| Arquivo muito grande/lento | Baixa usabilidade | Converter para Parquet e cachear. |
| LLM inventar números | Alto | Métricas apenas por tools determinísticas. |
| Notícias ruins ou irrelevantes | Médio | Allowlist, ranking e registro de fontes. |
| Prompt injection em conteúdo externo | Alto | Tratar páginas como dados não confiáveis e filtrar instruções. |
| Exposição de dados sensíveis | Alto | Agregação mínima e bloqueio de linha individual. |
| Métrica de UTI ser interpretada incorretamente | Alto | Nomear como proporção de casos com UTI e declarar limitação. |
| Métrica de vacinação ser interpretada como cobertura populacional | Alto | Separar vacinação em casos de cobertura populacional real. |

---

## 29. Evoluções Futuras

Após a PoC, a solução poderia evoluir para:

- ingestão incremental;
- orquestração com Airflow;
- armazenamento em data lake cloud;
- autenticação e controle de acesso;
- monitoramento de qualidade em produção;
- avaliação automática de respostas do agente;
- integração com APIs oficiais de vacinação e leitos;
- alertas automáticos por UF ou município;
- implantação em container cloud;
- LangSmith ou OpenTelemetry para tracing avançado;
- avaliação de custo, latência e qualidade do LLM.

---

## 30. Narrativa Técnica para Entrevista

A solução deve ser defendida com a seguinte linha de raciocínio:

> Eu separei a solução em uma camada determinística e uma camada GenAI. A camada determinística é responsável por baixar, validar, pré-processar e calcular métricas sobre a base SRAG. O LLM não calcula números diretamente; ele chama tools auditáveis que retornam métricas já calculadas. O agente usa LangGraph para seguir um fluxo controlado, consulta notícias apenas em fontes permitidas, recupera contexto metodológico via RAG e gera o relatório. Para governança, cada execução gera manifesto, hashes, data quality report, métricas, fontes e trace do agente. Para segurança, implementei guardrails de entrada, tools e saída, além de regras para não expor dados sensíveis ou registros individuais.

Pontos fortes a destacar:

- separação entre cálculo e linguagem natural;
- tool-calling controlado;
- RAG usado para documentação, não para métrica;
- allowlist de fontes;
- transparência de fórmulas;
- logs e auditoria;
- cuidado com limitações de UTI e vacinação;
- projeto demonstrável em Streamlit;
- estrutura de código compatível com evolução para produção.

---

## 31. Definição de Pronto

O projeto estará pronto para entrega quando houver:

- repositório público no GitHub;
- README completo;
- PRD.md versionado;
- aplicação Streamlit funcionando;
- pipeline executável;
- relatório gerado;
- gráficos gerados;
- agent trace;
- manifest;
- data quality report;
- testes passando;
- diagrama PDF em `docs/architecture_diagram.pdf`;
- `.env.example` sem segredos;
- instruções claras para reprodução.
