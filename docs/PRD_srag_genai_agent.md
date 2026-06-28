# PRD.md â€” Agente GenAI para RelatÃ³rio de SRAG com Dados OpenDataSUS

**Projeto:** SRAG GenAI Report Agent  
**Tipo:** Prova de Conceito tÃ©cnica para desafio de Senior AI Engineer  
**VersÃ£o:** 1.0  
**Status:** Planejamento aprovado para implementaÃ§Ã£o  
**Autor:** AdÃ­lio Farias  

---

## 1. Resumo Executivo

Este projeto tem como objetivo construir uma soluÃ§Ã£o baseada em InteligÃªncia Artificial Generativa capaz de gerar relatÃ³rios automatizados sobre SÃ­ndrome RespiratÃ³ria Aguda Grave (SRAG), combinando dados estruturados do OpenDataSUS/DataSUS com notÃ­cias e fontes oficiais em tempo real.

A soluÃ§Ã£o serÃ¡ composta por um pipeline determinÃ­stico de dados, uma camada analÃ­tica auditÃ¡vel, um agente GenAI orquestrado por tools controladas, uma camada de RAG documental, mecanismos de guardrails e uma interface em Streamlit para demonstraÃ§Ã£o.

A decisÃ£o arquitetural principal Ã© separar claramente:

1. **CÃ¡lculo determinÃ­stico:** ingestÃ£o, prÃ©-processamento, validaÃ§Ã£o, mÃ©tricas e grÃ¡ficos.
2. **GeraÃ§Ã£o com LLM:** explicaÃ§Ã£o, contextualizaÃ§Ã£o, redaÃ§Ã£o do relatÃ³rio e interaÃ§Ã£o conversacional.
3. **GovernanÃ§a:** logs, rastreabilidade, versionamento, manifesto de execuÃ§Ã£o, fontes consultadas e auditoria de decisÃµes.

O LLM nÃ£o deve calcular mÃ©tricas diretamente a partir de linguagem natural. Ele deve chamar tools confiÃ¡veis que retornam mÃ©tricas jÃ¡ calculadas por cÃ³digo. Isso reduz risco de alucinaÃ§Ã£o, melhora reprodutibilidade e facilita a defesa tÃ©cnica da arquitetura.

---

## 2. Contexto do Desafio

A Indicium HealthCare Inc. deseja avaliar uma PoC capaz de ajudar profissionais da Ã¡rea da saÃºde a entenderem, em tempo real, a severidade e o avanÃ§o de surtos de doenÃ§as.

Para a PoC, serÃ¡ usada a base real de internaÃ§Ãµes por SRAG do OpenDataSUS/DataSUS. O agente deve consultar dados, buscar notÃ­cias em tempo real e gerar um relatÃ³rio contendo mÃ©tricas, grÃ¡ficos e comentÃ¡rios explicativos sobre o cenÃ¡rio observado.

As mÃ©tricas obrigatÃ³rias sÃ£o:

- taxa de aumento de casos;
- taxa de mortalidade;
- taxa de ocupaÃ§Ã£o de UTI;
- taxa de vacinaÃ§Ã£o da populaÃ§Ã£o;
- grÃ¡fico de nÃºmero diÃ¡rio de casos dos Ãºltimos 30 dias;
- grÃ¡fico de nÃºmero mensal de casos dos Ãºltimos 12 meses.

O desafio tambÃ©m avalia:

- escolha de arquitetura;
- governanÃ§a e transparÃªncia;
- mecanismos de auditoria e registro das decisÃµes dos agentes;
- guardrails;
- uso de tools;
- tratamento de dados sensÃ­veis;
- clean code.

---

## 3. Objetivos do Produto

### 3.1 Objetivo Principal

Construir uma aplicaÃ§Ã£o demonstrÃ¡vel que gere um relatÃ³rio automatizado sobre SRAG, combinando mÃ©tricas calculadas sobre dados reais com explicaÃ§Ãµes contextualizadas por notÃ­cias e fontes oficiais recentes.

### 3.2 Objetivos TÃ©cnicos

- Automatizar a descoberta da pasta mais recente no repositÃ³rio GitLab de dados unificados.
- Baixar o arquivo `srag_total.xlsx` da pasta mais recente.
- Persistir o arquivo bruto em camada `landing`.
- PrÃ©-processar os dados e salvar versÃ£o otimizada em camada `refined`.
- Calcular mÃ©tricas epidemiolÃ³gicas de forma determinÃ­stica.
- Gerar os dois grÃ¡ficos obrigatÃ³rios.
- Implementar um agente GenAI que use tools controladas para obter mÃ©tricas, grÃ¡ficos, contexto documental e notÃ­cias.
- Implementar RAG documental para apoiar explicaÃ§Ãµes metodolÃ³gicas e consulta ao dicionÃ¡rio de dados, sem usar o banco vetorial como motor principal de cÃ¡lculo tabular.
- Registrar logs, fontes, decisÃµes e artefatos por execuÃ§Ã£o.
- Expor a soluÃ§Ã£o em dashboard Streamlit.
- Criar documentaÃ§Ã£o robusta no README e diagrama conceitual em PDF.

### 3.3 Objetivos de Defesa TÃ©cnica

A soluÃ§Ã£o deve permitir defender claramente as seguintes decisÃµes:

- Por que mÃ©tricas sÃ£o calculadas por cÃ³digo e nÃ£o pelo LLM.
- Por que o agente usa tools com schemas e nÃ£o acesso livre aos dados.
- Como a arquitetura reduz alucinaÃ§Ã£o.
- Como as fontes externas sÃ£o controladas por allowlist.
- Como os dados sensÃ­veis sÃ£o tratados.
- Como uma execuÃ§Ã£o pode ser auditada e reproduzida.
- Como o projeto poderia evoluir para produÃ§Ã£o.

---

## 4. NÃ£o Objetivos

Este projeto nÃ£o tem como objetivo:

- Substituir vigilÃ¢ncia epidemiolÃ³gica oficial.
- Fornecer diagnÃ³stico mÃ©dico individual.
- Recomendar tratamento clÃ­nico individualizado.
- Expor dados linha a linha de pacientes.
- Criar um modelo preditivo epidemiolÃ³gico completo.
- Fazer fine-tuning de LLM.
- Construir infraestrutura cloud produtiva completa.
- Criar um data warehouse corporativo.
- Usar banco vetorial para cÃ¡lculo numÃ©rico das mÃ©tricas.

---

## 5. Personas e UsuÃ¡rios

### 5.1 UsuÃ¡rio Avaliador TÃ©cnico

Pessoa que avaliarÃ¡ arquitetura, cÃ³digo, clareza, governanÃ§a, guardrails, uso de tools e capacidade de defesa tÃ©cnica.

Necessidades:

- Rodar o projeto com comandos simples.
- Entender rapidamente a arquitetura.
- Ver evidÃªncias de senioridade tÃ©cnica.
- Inspecionar logs, testes e decisÃµes.

### 5.2 Profissional de SaÃºde / Analista EpidemiolÃ³gico

UsuÃ¡rio final hipotÃ©tico da PoC.

Necessidades:

- Visualizar mÃ©tricas de SRAG de forma clara.
- Entender evoluÃ§Ã£o recente dos casos.
- Obter comentÃ¡rios contextualizados com fontes confiÃ¡veis.
- Consultar limitaÃ§Ãµes das mÃ©tricas.

### 5.3 Engenheiro de IA / Mantenedor

Pessoa responsÃ¡vel por evoluir a soluÃ§Ã£o.

Necessidades:

- CÃ³digo modular.
- ConfiguraÃ§Ãµes centralizadas.
- Testes automatizados.
- Contratos claros de tools.
- Facilidade para trocar LLM, vector store ou fonte de notÃ­cias.

---

## 6. PrincÃ­pios de Arquitetura

### 6.1 Determinismo para MÃ©tricas

Todas as mÃ©tricas devem ser calculadas por cÃ³digo testÃ¡vel. O LLM apenas interpreta os resultados retornados por tools.

### 6.2 SeparaÃ§Ã£o entre Dados Tabulares e Conhecimento Textual

Dados tabulares devem ser armazenados em Parquet e consultados por Polars, DuckDB ou Pandas.

O banco vetorial deve armazenar conteÃºdo textual, como:

- dicionÃ¡rio de dados;
- catÃ¡logo de mÃ©tricas;
- documentaÃ§Ã£o do projeto;
- notÃ­cias extraÃ­das;
- relatÃ³rios gerados;
- limitaÃ§Ãµes metodolÃ³gicas;
- explicaÃ§Ãµes de campos e fÃ³rmulas.

### 6.3 Tools Pequenas, ExplÃ­citas e AuditÃ¡veis

O agente deve acessar funcionalidades por meio de tools com entrada e saÃ­da bem definidas.

Exemplo:

```python
get_metric_summary(period: str, uf: str | None = None) -> MetricSummary
```

O agente nÃ£o deve receber acesso livre ao banco nem executar SQL arbitrÃ¡rio.

### 6.4 SeguranÃ§a e Privacidade por Design

O sistema deve bloquear perguntas fora do escopo, evitar exposiÃ§Ã£o de registros individuais e aplicar regras de agregaÃ§Ã£o mÃ­nima.

### 6.5 Reprodutibilidade

Cada execuÃ§Ã£o deve gerar um diretÃ³rio de artefatos com manifesto, hash do dado bruto, hash do dado refinado, mÃ©tricas, relatÃ³rio, grÃ¡ficos, fontes e trace do agente.

### 6.6 Observabilidade

Todas as etapas relevantes devem gerar logs estruturados.

---

## 7. Arquitetura Conceitual

```text
[GitLab / OpenDataSUS]
        |
        v
[Data Ingestion]
- listar diretÃ³rios
- escolher pasta mais recente
- baixar srag_total.xlsx
- salvar landing/raw
- gerar manifest parcial
        |
        v
[Data Quality + Preprocessing]
- validaÃ§Ã£o de schema mÃ­nimo
- normalizaÃ§Ã£o de colunas
- tratamento de datas
- tratamento de nulos e cÃ³digos
- geraÃ§Ã£o de data_quality_report.json
- salvar refined/srag_total.parquet
        |
        v
[Analytical Layer]
- leitura Parquet
- cÃ¡lculo de mÃ©tricas
- agregaÃ§Ãµes temporais
- geraÃ§Ã£o de grÃ¡ficos
        |
        v
[Agent Orchestrator]
- chama tools de mÃ©tricas
- chama tools de notÃ­cias
- consulta RAG documental
- gera relatÃ³rio
- passa por validaÃ§Ã£o de saÃ­da
        |
        v
[Guardrails + Audit]
- valida entrada
- restringe tools
- aplica allowlist
- bloqueia dados sensÃ­veis
- registra decisÃµes
        |
        v
[Streamlit Dashboard]
- pipeline
- relatÃ³rio
- qualidade dos dados
- chat analÃ­tico
```

---

## 8. Stack TÃ©cnica Recomendada

### 8.1 Linguagem e Empacotamento

- Python 3.11+
- `uv` ou `poetry` para gerenciamento de dependÃªncias
- `pyproject.toml`
- `ruff` para lint/format
- `pytest` para testes

### 8.2 Dados

- `requests` ou `httpx` para acesso HTTP
- `pandas` ou `polars` para leitura inicial de Excel
- `duckdb` para consultas analÃ­ticas locais
- `pyarrow` para Parquet
- `pandera` ou validaÃ§Ãµes Pydantic para qualidade de dados

### 8.3 Agente e RAG

- LangGraph para orquestraÃ§Ã£o controlada do agente
- LangChain apenas se facilitar integraÃ§Ã£o com tools, retrievers e LLMs
- ChromaDB ou Qdrant como vector store open source
- Modelo de embedding multilÃ­ngue, preferencialmente com bom suporte a portuguÃªs
- LLM configurÃ¡vel por variÃ¡vel de ambiente

### 8.4 Interface

- Streamlit para dashboard e chat
- Plotly ou Matplotlib para grÃ¡ficos

### 8.5 ExportaÃ§Ã£o

- Markdown como formato primÃ¡rio do relatÃ³rio
- PDF gerado a partir de Markdown/HTML
- PNG ou SVG para grÃ¡ficos

---

## 9. Estrutura de RepositÃ³rio

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

A aplicaÃ§Ã£o deve consultar apenas fontes explicitamente permitidas. Isso reduz risco de baixa qualidade informacional, scraping indevido, prompt injection em pÃ¡ginas externas e uso de fontes nÃ£o confiÃ¡veis.

### 10.1 Allowlist MÃ¡xima de Fontes

| NÂº | DomÃ­nio/Fonte | Uso Permitido | Justificativa |
|---:|---|---|---|
| 1 | `gitlab.com/cgcovid/dados-abertos` | Download da base unificada SRAG | Fonte indicada no desafio para obter `srag_total.xlsx`. |
| 2 | `dadosabertos.saude.gov.br` | Dataset oficial, dicionÃ¡rio de dados e metadados | Portal oficial de dados abertos do SUS. |
| 3 | `gov.br/saude` | Notas tÃ©cnicas, orientaÃ§Ãµes e comunicados oficiais | Fonte institucional do MinistÃ©rio da SaÃºde. |
| 4 | `infoms.saude.gov.br` | PainÃ©is oficiais de saÃºde e vacinaÃ§Ã£o, quando aplicÃ¡vel | Fonte oficial para indicadores complementares. |
| 5 | `fiocruz.br` | Boletins InfoGripe e notÃ­cias tÃ©cnicas | ReferÃªncia pÃºblica em vigilÃ¢ncia e anÃ¡lise de SRAG. |
| 6 | `github.com/infogripe` | RepositÃ³rios pÃºblicos do InfoGripe, quando Ãºteis | Suporte tÃ©cnico e materiais pÃºblicos relacionados ao InfoGripe. |
| 7 | `agenciagov.ebc.com.br` | NotÃ­cias governamentais sobre saÃºde pÃºblica | Fonte pÃºblica de comunicaÃ§Ã£o institucional. |
| 8 | `agenciabrasil.ebc.com.br` | NotÃ­cias pÃºblicas de saÃºde | Fonte jornalÃ­stica pÃºblica brasileira. |
| 9 | `paho.org` | Contexto regional das AmÃ©ricas | OrganizaÃ§Ã£o Pan-Americana da SaÃºde. |
| 10 | `who.int` | Contexto global e vigilÃ¢ncia respiratÃ³ria | OrganizaÃ§Ã£o Mundial da SaÃºde. |

### 10.2 Regras de Uso da Allowlist

- O agente nÃ£o deve buscar fontes fora da allowlist.
- Resultados de busca devem ser filtrados por domÃ­nio antes de qualquer extraÃ§Ã£o.
- Cada notÃ­cia usada no relatÃ³rio deve ser registrada em `news_sources.json`.
- Cada comentÃ¡rio baseado em notÃ­cia deve ser rastreÃ¡vel atÃ© pelo menos uma fonte.
- ConteÃºdo de pÃ¡ginas externas deve ser tratado como dado nÃ£o confiÃ¡vel.
- InstruÃ§Ãµes encontradas em pÃ¡ginas externas nunca devem sobrescrever system prompt, developer prompt ou regras internas.

---

## 11. Pipeline de Dados

### 11.1 IngestÃ£o

Responsabilidade: localizar e baixar automaticamente o arquivo mais recente.

Fluxo:

1. Acessar a Ã¡rvore do repositÃ³rio GitLab.
2. Navegar atÃ© `Dados unificados/Unificado Srag`.
3. Listar subpastas.
4. Identificar a pasta mais recente pelo nome.
5. Validar se existe `srag_total.xlsx`.
6. Baixar o arquivo.
7. Salvar em `data/landing/<run_id>/srag_total.xlsx`.
8. Calcular hash SHA-256 do arquivo.
9. Registrar metadados no manifesto.

CritÃ©rio de seleÃ§Ã£o da pasta mais recente:

- O nome da pasta deve ser interpretado por uma funÃ§Ã£o dedicada.
- A funÃ§Ã£o deve aceitar formatos como `YYYY`, `YYYY_MM`, `YYYY_WW`, `YYYY_SE`, `YYYY_XX` ou equivalentes encontrados no repositÃ³rio.
- Quando houver ambiguidade, ordenar primeiro por ano e depois pelo maior sufixo numÃ©rico.
- A funÃ§Ã£o deve ser coberta por testes unitÃ¡rios.

### 11.2 Camada Landing

A camada `landing` deve armazenar o dado bruto sem alteraÃ§Ã£o.

Regras:

- Nunca sobrescrever arquivo bruto sem registrar nova execuÃ§Ã£o.
- Salvar hash do arquivo.
- Salvar caminho original e pasta selecionada.
- Salvar timestamp da coleta.

### 11.3 PrÃ©-processamento

Responsabilidade: converter dados reais e imperfeitos em uma base analÃ­tica consistente.

Tratamentos esperados:

- normalizar nomes de colunas;
- mapear colunas para nomes canÃ´nicos internos;
- converter datas;
- remover linhas completamente vazias;
- tratar cÃ³digos ignorados ou desconhecidos;
- padronizar valores categÃ³ricos;
- gerar flags auxiliares;
- aplicar validaÃ§Ãµes mÃ­nimas de consistÃªncia;
- preservar contagem de registros descartados ou invÃ¡lidos;
- salvar a base refinada em Parquet.

### 11.4 Camada Refined

Arquivo principal:

```text
data/refined/<run_id>/srag_total.parquet
```

Essa camada serÃ¡ a fonte oficial para cÃ¡lculo de mÃ©tricas.

---

## 12. Colunas Relevantes e Mapeamento

Como bases pÃºblicas podem mudar de schema, o projeto deve usar um arquivo de mapeamento configurÃ¡vel.

Exemplo de colunas candidatas:

| Conceito | Colunas candidatas | Uso |
|---|---|---|
| Data de notificaÃ§Ã£o | `DT_NOTIFIC` | SÃ©rie temporal alternativa. |
| Data de inÃ­cio dos sintomas | `DT_SIN_PRI` | SÃ©rie temporal preferencial para casos. |
| Unidade Federativa | `SG_UF_NOT`, `SG_UF` | Filtros geogrÃ¡ficos. |
| MunicÃ­pio | `ID_MUNICIP`, `CO_MUN_NOT` | Filtros agregados. |
| EvoluÃ§Ã£o | `EVOLUCAO` | Mortalidade. |
| Data de evoluÃ§Ã£o | `DT_EVOLUCA` | Recorte temporal de desfecho. |
| UTI | `UTI` | ProporÃ§Ã£o de casos com UTI. |
| Entrada em UTI | `DT_ENTUTI` | Estimativa temporal de UTI, se disponÃ­vel. |
| SaÃ­da de UTI | `DT_SAIDUTI` | Estimativa temporal de UTI, se disponÃ­vel. |
| VacinaÃ§Ã£o | `VACINA_COV`, `VACINA`, campos equivalentes | ProporÃ§Ã£o de casos com vacinaÃ§Ã£o registrada. |
| ClassificaÃ§Ã£o final | `CLASSI_FIN` | Filtros de SRAG por etiologia, se aplicÃ¡vel. |
| CritÃ©rio de encerramento | `CRITERIO` | Qualidade analÃ­tica. |

Regras:

- Se uma coluna obrigatÃ³ria nÃ£o existir, a aplicaÃ§Ã£o deve falhar de forma explicÃ¡vel.
- Se uma coluna complementar nÃ£o existir, a mÃ©trica associada deve registrar limitaÃ§Ã£o.
- O mapeamento real deve ser validado contra o dicionÃ¡rio de dados.

---

## 13. CatÃ¡logo de MÃ©tricas

As fÃ³rmulas devem ser documentadas em `configs/metric_catalog.yaml` e `docs/metric_catalog.md`.

### 13.1 Data de ReferÃªncia

A data de referÃªncia do relatÃ³rio deve ser a maior data vÃ¡lida encontrada na base refinada, e nÃ£o necessariamente a data atual do sistema.

Motivo: bases pÃºblicas podem ter atraso de atualizaÃ§Ã£o.

```text
data_referencia = max(data_evento_valida)
```

### 13.2 Taxa de Aumento de Casos

DefiniÃ§Ã£o principal:

```text
taxa_aumento_7d = (casos_ultimos_7_dias - casos_7_dias_anteriores) / casos_7_dias_anteriores
```

Janela:

- Ãºltimos 7 dias encerrados na data de referÃªncia;
- comparados com os 7 dias imediatamente anteriores.

Tratamento de divisÃ£o por zero:

- se o perÃ­odo anterior tiver zero casos, retornar `null` e explicar limitaÃ§Ã£o.

Campos usados:

- data canÃ´nica de caso, preferencialmente inÃ­cio dos sintomas;
- fallback para data de notificaÃ§Ã£o se necessÃ¡rio.

### 13.3 Taxa de Mortalidade

DefiniÃ§Ã£o principal:

```text
taxa_mortalidade_conhecida = obitos / casos_com_evolucao_conhecida
```

DefiniÃ§Ã£o complementar:

```text
taxa_mortalidade_bruta = obitos / casos_totais
```

Motivo:

A taxa sobre casos com evoluÃ§Ã£o conhecida reduz distorÃ§Ã£o causada por registros ainda em aberto ou sem preenchimento.

O relatÃ³rio deve apresentar a mÃ©trica principal e informar a limitaÃ§Ã£o.

### 13.4 Taxa de OcupaÃ§Ã£o de UTI

A base de SRAG nÃ£o necessariamente contÃ©m denominador de leitos disponÃ­veis. Portanto, a mÃ©trica deve ser nomeada com precisÃ£o.

DefiniÃ§Ã£o principal para a PoC:

```text
proporcao_casos_com_uti = casos_com_uti / casos_totais
```

Nome recomendado no relatÃ³rio:

```text
ProporÃ§Ã£o de casos de SRAG com passagem por UTI
```

Se houver datas de entrada e saÃ­da de UTI, pode ser criada uma mÃ©trica complementar:

```text
casos_estimados_em_uti_por_dia
```

LimitaÃ§Ã£o obrigatÃ³ria:

A mÃ©trica nÃ£o representa ocupaÃ§Ã£o hospitalar real de leitos sem uma base externa de leitos disponÃ­veis.

### 13.5 Taxa de VacinaÃ§Ã£o da PopulaÃ§Ã£o

A base SRAG pode conter informaÃ§Ã£o de vacinaÃ§Ã£o dos casos notificados, mas isso nÃ£o mede automaticamente cobertura vacinal da populaÃ§Ã£o geral.

DefiniÃ§Ã£o principal da PoC:

```text
proporcao_casos_com_vacinacao_registrada = casos_com_vacinacao_registrada / casos_com_status_vacinal_conhecido
```

Nome recomendado no relatÃ³rio:

```text
ProporÃ§Ã£o de casos de SRAG com vacinaÃ§Ã£o registrada
```

ExtensÃ£o opcional:

- consultar fonte oficial complementar de cobertura vacinal populacional, caso disponÃ­vel e estÃ¡vel;
- apresentar cobertura populacional separadamente da proporÃ§Ã£o entre casos.

LimitaÃ§Ã£o obrigatÃ³ria:

A mÃ©trica calculada na base de SRAG nÃ£o deve ser descrita como cobertura vacinal populacional geral se o denominador populacional nÃ£o estiver disponÃ­vel.

### 13.6 GrÃ¡fico de Casos DiÃ¡rios â€” Ãšltimos 30 Dias

DefiniÃ§Ã£o:

- eixo X: data;
- eixo Y: nÃºmero de casos;
- janela: 30 dias encerrados na data de referÃªncia;
- agregaÃ§Ã£o: contagem de casos por data canÃ´nica.

Arquivo esperado:

```text
artifacts/runs/<run_id>/charts/daily_cases_30d.png
```

### 13.7 GrÃ¡fico de Casos Mensais â€” Ãšltimos 12 Meses

DefiniÃ§Ã£o:

- eixo X: mÃªs;
- eixo Y: nÃºmero de casos;
- janela: 12 meses encerrados no mÃªs da data de referÃªncia;
- agregaÃ§Ã£o: contagem de casos por mÃªs.

Arquivo esperado:

```text
artifacts/runs/<run_id>/charts/monthly_cases_12m.png
```

---

## 14. Data Quality Report

Cada execuÃ§Ã£o deve gerar:

```text
artifacts/runs/<run_id>/data_quality_report.json
```

ConteÃºdo mÃ­nimo:

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

O relatÃ³rio final deve mencionar limitaÃ§Ãµes relevantes encontradas na qualidade dos dados.

---

## 15. Camada de RAG

### 15.1 Objetivo

A camada RAG deve fornecer conhecimento textual ao agente, sem substituir a camada analÃ­tica.

### 15.2 ConteÃºdos Indexados

- dicionÃ¡rio de dados;
- catÃ¡logo de mÃ©tricas;
- documentaÃ§Ã£o de limitaÃ§Ãµes;
- notÃ­cias extraÃ­das e resumidas;
- relatÃ³rio atual;
- relatÃ³rios anteriores, se houver;
- README e arquitetura do projeto.

### 15.3 ConteÃºdos NÃ£o Indexados como Fonte PrimÃ¡ria

- registros linha a linha da base SRAG;
- dados pessoais ou quasi-identificadores;
- tabelas completas de pacientes;
- arquivos brutos sem curadoria.

### 15.4 Vector Store

OpÃ§Ãµes aceitÃ¡veis:

- ChromaDB para simplicidade local;
- Qdrant para defesa mais prÃ³xima de produÃ§Ã£o.

CritÃ©rio de escolha para MVP:

- ChromaDB se o objetivo for velocidade de implementaÃ§Ã£o;
- Qdrant se houver tempo para demonstrar maturidade maior.

---

## 16. Agente GenAI

### 16.1 Papel do Agente

O agente atua como orquestrador e redator analÃ­tico.

Ele deve:

- consultar mÃ©tricas por tools;
- consultar grÃ¡ficos gerados por tools;
- recuperar explicaÃ§Ãµes metodolÃ³gicas via RAG;
- buscar notÃ­cias em fontes permitidas;
- gerar relatÃ³rio final;
- responder perguntas no chat com base no relatÃ³rio e nos dados agregados.

Ele nÃ£o deve:

- calcular mÃ©tricas por conta prÃ³pria;
- acessar dados linha a linha sem agregaÃ§Ã£o;
- executar SQL livre;
- usar fontes fora da allowlist;
- dar diagnÃ³stico mÃ©dico individual;
- inventar fonte, nÃºmero ou conclusÃ£o.

### 16.2 OrquestraÃ§Ã£o com LangGraph

O fluxo do agente deve ser modelado como grafo controlado.

NÃ³s sugeridos:

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

Retorna mÃ©tricas obrigatÃ³rias e complementares.

Entrada:

```json
{
  "run_id": "string",
  "uf": "string|null",
  "period": "default|custom"
}
```

SaÃ­da:

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

Gera os dois grÃ¡ficos obrigatÃ³rios.

SaÃ­da:

```json
{
  "daily_cases_30d": "path/to/daily_cases_30d.png",
  "monthly_cases_12m": "path/to/monthly_cases_12m.png"
}
```

### 17.3 `search_srag_news`

Busca notÃ­cias e fontes recentes sobre SRAG.

Regras:

- aplicar allowlist antes de extrair conteÃºdo;
- priorizar fontes oficiais;
- registrar data, tÃ­tulo, domÃ­nio e trecho relevante;
- limitar nÃºmero de fontes por relatÃ³rio.

### 17.4 `retrieve_context`

Busca no RAG documental informaÃ§Ãµes sobre:

- definiÃ§Ã£o das mÃ©tricas;
- limitaÃ§Ãµes;
- campos usados;
- metodologia;
- contexto das notÃ­cias jÃ¡ extraÃ­das.

### 17.5 `validate_report_contract`

Confere se o relatÃ³rio contÃ©m:

- as quatro mÃ©tricas obrigatÃ³rias;
- os dois grÃ¡ficos obrigatÃ³rios;
- seÃ§Ã£o de fontes;
- seÃ§Ã£o de limitaÃ§Ãµes;
- aviso de uso analÃ­tico;
- ausÃªncia de dados sensÃ­veis linha a linha.

---

## 18. RelatÃ³rio Gerado

### 18.1 Formato

Formato primÃ¡rio:

```text
artifacts/runs/<run_id>/report.md
```

Formato complementar:

```text
artifacts/runs/<run_id>/report.pdf
```

### 18.2 Estrutura MÃ­nima do RelatÃ³rio

```markdown
# RelatÃ³rio Automatizado de SRAG

## 1. SumÃ¡rio Executivo

## 2. Dados Utilizados
- fonte
- pasta selecionada
- arquivo
- data de referÃªncia
- hash do arquivo bruto

## 3. MÃ©tricas Principais
- taxa de aumento de casos
- taxa de mortalidade
- proporÃ§Ã£o de casos com UTI
- proporÃ§Ã£o de casos com vacinaÃ§Ã£o registrada

## 4. EvoluÃ§Ã£o Temporal
- grÃ¡fico diÃ¡rio dos Ãºltimos 30 dias
- grÃ¡fico mensal dos Ãºltimos 12 meses

## 5. Contexto de NotÃ­cias e Fontes Oficiais
- principais fatos recentes
- relaÃ§Ã£o entre notÃ­cias e mÃ©tricas observadas

## 6. ComentÃ¡rios AnalÃ­ticos do Agente
- interpretaÃ§Ã£o do cenÃ¡rio
- hipÃ³teses explicativas
- cautelas

## 7. LimitaÃ§Ãµes MetodolÃ³gicas

## 8. Fontes Consultadas

## 9. Aviso de Uso
```

### 18.3 Regras de RedaÃ§Ã£o

O relatÃ³rio deve:

- distinguir claramente dado calculado de comentÃ¡rio interpretativo;
- citar fontes consultadas;
- evitar tom alarmista;
- declarar limitaÃ§Ãµes;
- nÃ£o oferecer aconselhamento mÃ©dico individual;
- indicar quando uma mÃ©trica Ã© proxy e nÃ£o mediÃ§Ã£o direta.

---

## 19. Guardrails

### 19.1 Guardrails de Entrada

Devem bloquear ou redirecionar:

- pedidos fora do escopo de SRAG, relatÃ³rio, metodologia ou dados agregados;
- tentativas de prompt injection;
- pedidos para ignorar regras do sistema;
- pedidos de dados pessoais ou registros individuais;
- pedidos de diagnÃ³stico ou tratamento mÃ©dico individualizado;
- pedidos de scraping fora da allowlist.

### 19.2 Guardrails de Tools

- O LLM sÃ³ pode chamar tools registradas.
- Cada tool deve ter schema validado.
- NÃ£o permitir SQL livre vindo do LLM.
- Aplicar timeout.
- Registrar toda chamada de tool.
- Bloquear domÃ­nios fora da allowlist.
- Validar paths de arquivo para evitar path traversal.

### 19.3 Guardrails de Privacidade

- NÃ£o retornar linhas individuais.
- NÃ£o exibir recortes com contagem menor que limite configurÃ¡vel.
- Aplicar regra de agregaÃ§Ã£o mÃ­nima, por exemplo `min_group_size = 10`.
- Remover ou nÃ£o carregar campos que possam facilitar reidentificaÃ§Ã£o.
- Evitar combinaÃ§Ã£o excessivamente granular de filtros.

### 19.4 Guardrails de SaÃ­da

Antes de exibir resposta ou relatÃ³rio:

- validar presenÃ§a das mÃ©tricas obrigatÃ³rias;
- validar presenÃ§a dos grÃ¡ficos obrigatÃ³rios;
- validar se afirmaÃ§Ãµes de notÃ­cias possuem fonte;
- validar se nÃ£o hÃ¡ dados sensÃ­veis;
- validar se limitaÃ§Ãµes estÃ£o declaradas;
- validar se nÃ£o hÃ¡ recomendaÃ§Ãµes clÃ­nicas individualizadas.

---

## 20. GovernanÃ§a, Auditoria e TransparÃªncia

Cada execuÃ§Ã£o deve gerar uma pasta:

```text
artifacts/runs/<run_id>/
```

ConteÃºdo esperado:

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

ConteÃºdo mÃ­nimo:

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

NÃ£o registrar prompts com segredos ou chaves de API.

---

## 21. Streamlit Dashboard

### 21.1 Aba Pipeline

Deve permitir:

- executar ingestÃ£o;
- ver pasta selecionada;
- ver status de download;
- ver hash do arquivo;
- ver status da camada refined;
- ver erros de validaÃ§Ã£o.

### 21.2 Aba RelatÃ³rio

Deve mostrar:

- mÃ©tricas principais;
- grÃ¡ficos obrigatÃ³rios;
- relatÃ³rio gerado;
- fontes usadas;
- botÃ£o de download do Markdown/PDF.

### 21.3 Aba Qualidade dos Dados

Deve mostrar:

- nÃºmero de linhas brutas e refinadas;
- colunas selecionadas;
- percentual de nulos;
- datas invÃ¡lidas;
- avisos;
- limitaÃ§Ãµes de interpretaÃ§Ã£o.

### 21.4 Aba Chat

Deve permitir perguntas sobre:

- relatÃ³rio gerado;
- mÃ©tricas;
- metodologia;
- limitaÃ§Ãµes;
- fontes usadas.

O chat deve recusar:

- diagnÃ³stico individual;
- dados linha a linha;
- perguntas fora do escopo;
- pedidos para burlar regras.

---

## 22. Requisitos Funcionais

| ID | Requisito | Prioridade |
|---|---|---|
| RF-001 | Listar diretÃ³rios do GitLab e selecionar a pasta mais recente. | Alta |
| RF-002 | Baixar `srag_total.xlsx` da pasta selecionada. | Alta |
| RF-003 | Salvar dado bruto em camada landing. | Alta |
| RF-004 | Gerar hash e manifesto da execuÃ§Ã£o. | Alta |
| RF-005 | PrÃ©-processar base e salvar Parquet em refined. | Alta |
| RF-006 | Gerar data quality report. | Alta |
| RF-007 | Calcular as quatro mÃ©tricas obrigatÃ³rias. | Alta |
| RF-008 | Gerar grÃ¡fico diÃ¡rio dos Ãºltimos 30 dias. | Alta |
| RF-009 | Gerar grÃ¡fico mensal dos Ãºltimos 12 meses. | Alta |
| RF-010 | Buscar notÃ­cias/fontes recentes sobre SRAG usando allowlist. | Alta |
| RF-011 | Implementar agente com tools controladas. | Alta |
| RF-012 | Gerar relatÃ³rio em Markdown. | Alta |
| RF-013 | Exportar relatÃ³rio para PDF. | MÃ©dia |
| RF-014 | Disponibilizar dashboard Streamlit. | Alta |
| RF-015 | Disponibilizar chat sobre relatÃ³rio e metodologia. | MÃ©dia |
| RF-016 | Registrar trace do agente. | Alta |
| RF-017 | Implementar guardrails de entrada, tools e saÃ­da. | Alta |
| RF-018 | Criar README didÃ¡tico e diagrama PDF. | Alta |

---

## 23. Requisitos NÃ£o Funcionais

### 23.1 SeguranÃ§a

- Chaves em `.env`, nunca commitadas.
- Allowlist para fontes externas.
- SanitizaÃ§Ã£o de entrada.
- Sem exposiÃ§Ã£o de dados individuais.

### 23.2 Confiabilidade

- Fallback para arquivo em cache se download falhar.
- Falhas explicÃ¡veis.
- Logs estruturados.

### 23.3 Reprodutibilidade

- Manifesto por execuÃ§Ã£o.
- Hashes dos dados.
- VersÃ£o do catÃ¡logo de mÃ©tricas.
- VersÃ£o dos prompts.

### 23.4 Manutenibilidade

- CÃ³digo modular.
- FunÃ§Ãµes pequenas.
- Type hints.
- Testes unitÃ¡rios.
- ConfiguraÃ§Ã£o centralizada.

### 23.5 Performance

- Salvar Parquet para leitura rÃ¡pida.
- Evitar recarregar Excel em cada interaÃ§Ã£o.
- Cache de notÃ­cias e embeddings.
- Limitar chamadas ao LLM.

---

## 24. Testes Automatizados

### 24.1 Testes de Dados

- seleÃ§Ã£o correta da pasta mais recente;
- download com mock de GitLab;
- validaÃ§Ã£o de schema mÃ­nimo;
- conversÃ£o de datas;
- tratamento de nulos;
- geraÃ§Ã£o de Parquet.

### 24.2 Testes de MÃ©tricas

- taxa de aumento com casos normais;
- taxa de aumento com denominador zero;
- mortalidade com evoluÃ§Ã£o conhecida;
- mortalidade com dados ausentes;
- proporÃ§Ã£o de UTI;
- proporÃ§Ã£o de vacinaÃ§Ã£o;
- janelas de 30 dias e 12 meses.

### 24.3 Testes de Guardrails

- bloqueio de prompt injection;
- bloqueio de domÃ­nio fora da allowlist;
- bloqueio de pedido de dados individuais;
- bloqueio de diagnÃ³stico individual;
- validaÃ§Ã£o de contagem mÃ­nima por grupo.

### 24.4 Testes do RelatÃ³rio

- contÃ©m as quatro mÃ©tricas;
- contÃ©m os dois grÃ¡ficos;
- contÃ©m fontes;
- contÃ©m limitaÃ§Ãµes;
- nÃ£o contÃ©m dados sensÃ­veis;
- separa mÃ©tricas calculadas de comentÃ¡rios interpretativos.

---

## 25. CritÃ©rios de Aceite

A soluÃ§Ã£o serÃ¡ considerada satisfatÃ³ria quando:

1. O avaliador conseguir rodar o projeto com instruÃ§Ãµes claras no README.
2. A aplicaÃ§Ã£o localizar automaticamente a pasta mais recente do repositÃ³rio.
3. O arquivo `srag_total.xlsx` for baixado e salvo em landing.
4. O pipeline gerar Parquet refinado.
5. As quatro mÃ©tricas obrigatÃ³rias forem calculadas por cÃ³digo.
6. Os dois grÃ¡ficos obrigatÃ³rios forem gerados.
7. O agente gerar relatÃ³rio com comentÃ¡rios e fontes.
8. O relatÃ³rio declarar limitaÃ§Ãµes metodolÃ³gicas.
9. Houver guardrails implementados em cÃ³digo.
10. Houver logs e manifesto por execuÃ§Ã£o.
11. A interface Streamlit demonstrar pipeline, relatÃ³rio, qualidade dos dados e chat.
12. O repositÃ³rio pÃºblico conter README, PRD e diagrama conceitual em PDF.

---

## 26. README.md â€” ConteÃºdo Esperado

O README deve ser escrito como documento de defesa tÃ©cnica.

Estrutura recomendada:

```markdown
# SRAG GenAI Report Agent

## 1. VisÃ£o Geral

## 2. DemonstraÃ§Ã£o
- screenshots
- exemplo de relatÃ³rio

## 3. Arquitetura
- diagrama
- explicaÃ§Ã£o das camadas

## 4. Como Rodar
- prÃ©-requisitos
- variÃ¡veis de ambiente
- comandos

## 5. Pipeline de Dados

## 6. MÃ©tricas e FÃ³rmulas

## 7. Agente e Tools

## 8. RAG Documental

## 9. Guardrails e Privacidade

## 10. GovernanÃ§a e Auditoria

## 11. Testes

## 12. LimitaÃ§Ãµes

## 13. PrÃ³ximos Passos
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

O repositÃ³rio deve incluir:

```text
docs/architecture_diagram.pdf
```

O diagrama deve mostrar:

- fonte GitLab/OpenDataSUS;
- camada landing;
- camada refined;
- camada analÃ­tica;
- vector store;
- agente principal;
- tools;
- LLM;
- fontes de notÃ­cias;
- guardrails;
- auditoria;
- Streamlit.

---

## 28. Riscos e MitigaÃ§Ãµes

| Risco | Impacto | MitigaÃ§Ã£o |
|---|---|---|
| MudanÃ§a no schema do arquivo | MÃ©tricas quebram | Mapeamento configurÃ¡vel e validaÃ§Ã£o de schema. |
| Pasta mais recente com nome inesperado | Download falha | Parser testado e fallback explicÃ¡vel. |
| Arquivo muito grande/lento | Baixa usabilidade | Converter para Parquet e cachear. |
| LLM inventar nÃºmeros | Alto | MÃ©tricas apenas por tools determinÃ­sticas. |
| NotÃ­cias ruins ou irrelevantes | MÃ©dio | Allowlist, ranking e registro de fontes. |
| Prompt injection em conteÃºdo externo | Alto | Tratar pÃ¡ginas como dados nÃ£o confiÃ¡veis e filtrar instruÃ§Ãµes. |
| ExposiÃ§Ã£o de dados sensÃ­veis | Alto | AgregaÃ§Ã£o mÃ­nima e bloqueio de linha individual. |
| MÃ©trica de UTI ser interpretada incorretamente | Alto | Nomear como proporÃ§Ã£o de casos com UTI e declarar limitaÃ§Ã£o. |
| MÃ©trica de vacinaÃ§Ã£o ser interpretada como cobertura populacional | Alto | Separar vacinaÃ§Ã£o em casos de cobertura populacional real. |

---

## 29. EvoluÃ§Ãµes Futuras

ApÃ³s a PoC, a soluÃ§Ã£o poderia evoluir para:

- ingestÃ£o incremental;
- orquestraÃ§Ã£o com Airflow;
- armazenamento em data lake cloud;
- autenticaÃ§Ã£o e controle de acesso;
- monitoramento de qualidade em produÃ§Ã£o;
- avaliaÃ§Ã£o automÃ¡tica de respostas do agente;
- integraÃ§Ã£o com APIs oficiais de vacinaÃ§Ã£o e leitos;
- alertas automÃ¡ticos por UF ou municÃ­pio;
- implantaÃ§Ã£o em container cloud;
- LangSmith ou OpenTelemetry para tracing avanÃ§ado;
- avaliaÃ§Ã£o de custo, latÃªncia e qualidade do LLM.

---

## 30. Narrativa TÃ©cnica para Entrevista

A soluÃ§Ã£o deve ser defendida com a seguinte linha de raciocÃ­nio:

> Eu separei a soluÃ§Ã£o em uma camada determinÃ­stica e uma camada GenAI. A camada determinÃ­stica Ã© responsÃ¡vel por baixar, validar, prÃ©-processar e calcular mÃ©tricas sobre a base SRAG. O LLM nÃ£o calcula nÃºmeros diretamente; ele chama tools auditÃ¡veis que retornam mÃ©tricas jÃ¡ calculadas. O agente usa LangGraph para seguir um fluxo controlado, consulta notÃ­cias apenas em fontes permitidas, recupera contexto metodolÃ³gico via RAG e gera o relatÃ³rio. Para governanÃ§a, cada execuÃ§Ã£o gera manifesto, hashes, data quality report, mÃ©tricas, fontes e trace do agente. Para seguranÃ§a, implementei guardrails de entrada, tools e saÃ­da, alÃ©m de regras para nÃ£o expor dados sensÃ­veis ou registros individuais.

Pontos fortes a destacar:

- separaÃ§Ã£o entre cÃ¡lculo e linguagem natural;
- tool-calling controlado;
- RAG usado para documentaÃ§Ã£o, nÃ£o para mÃ©trica;
- allowlist de fontes;
- transparÃªncia de fÃ³rmulas;
- logs e auditoria;
- cuidado com limitaÃ§Ãµes de UTI e vacinaÃ§Ã£o;
- projeto demonstrÃ¡vel em Streamlit;
- estrutura de cÃ³digo compatÃ­vel com evoluÃ§Ã£o para produÃ§Ã£o.

---

## 31. DefiniÃ§Ã£o de Pronto

O projeto estarÃ¡ pronto para entrega quando houver:

- repositÃ³rio pÃºblico no GitHub;
- README completo;
- PRD.md versionado;
- aplicaÃ§Ã£o Streamlit funcionando;
- pipeline executÃ¡vel;
- relatÃ³rio gerado;
- grÃ¡ficos gerados;
- agent trace;
- manifest;
- data quality report;
- testes passando;
- diagrama PDF em `docs/architecture_diagram.pdf`;
- `.env.example` sem segredos;
- instruÃ§Ãµes claras para reproduÃ§Ã£o.

