# Agente SRAG DataSUS

Agente de IA Generativa para geração automatizada de relatórios sobre Síndrome Respiratória Aguda Grave (SRAG), combinando dados estruturados do OpenDataSUS/DataSUS com notícias e fontes institucionais recentes.

Este projeto foi criado como uma Prova de Conceito técnica para demonstrar uma arquitetura de agente analítico com pipeline determinístico de dados, uso controlado de tools, RAG documental, guardrails, auditoria e interface demonstrável em Streamlit.

---

## 1. Objetivo

Construir uma solução capaz de:

- acessar automaticamente os dados públicos de SRAG;
- identificar a pasta mais recente no repositório de dados unificados;
- baixar e processar o arquivo `srag_total.xlsx`;
- calcular métricas epidemiológicas de forma determinística;
- gerar gráficos obrigatórios;
- consultar notícias e fontes oficiais em tempo real;
- produzir um relatório explicativo com apoio de LLM;
- registrar rastreabilidade, fontes, decisões e artefatos por execução;
- disponibilizar uma interface em Streamlit para demonstração.

---

## 2. Escopo da PoC

A solução deve gerar um relatório contendo, no mínimo:

- taxa de aumento de casos;
- taxa de mortalidade;
- proporção de casos de SRAG com passagem por UTI;
- proporção de casos de SRAG com vacinação registrada;
- gráfico diário de casos dos últimos 30 dias;
- gráfico mensal de casos dos últimos 12 meses;
- comentários explicativos baseados em fontes confiáveis;
- limitações metodológicas;
- fontes consultadas.

Observação: algumas métricas solicitadas no desafio são tratadas como proxies quando a base não possui o denominador necessário. Por exemplo, a base de SRAG permite calcular proporção de casos com UTI, mas não ocupação hospitalar real de leitos sem fonte complementar de leitos disponíveis.

---

## 3. Princípio Arquitetural

A arquitetura separa cálculo determinístico de geração textual.

O LLM não calcula métricas diretamente. Ele atua como orquestrador e redator analítico, chamando tools controladas que retornam métricas e evidências já calculadas por código.

```text
GitLab/OpenDataSUS
        |
        v
Landing Raw
        |
        v
Preprocessing + Data Quality
        |
        v
Refined Parquet
        |
        v
Metric Tools + Chart Tools
        |
        v
LangGraph Agent
        |
        +--> RAG Documental
        +--> News Tools com allowlist
        +--> Guardrails
        |
        v
Relatório + Streamlit + Auditoria
```

---

## 4. Fontes Permitidas

A aplicação deve consultar somente fontes explicitamente permitidas.

Allowlist inicial:

1. `gitlab.com/cgcovid/dados-abertos`
2. `dadosabertos.saude.gov.br`
3. `gov.br/saude`
4. `infoms.saude.gov.br`
5. `fiocruz.br`
6. `github.com/infogripe`
7. `agenciagov.ebc.com.br`
8. `agenciabrasil.ebc.com.br`
9. `paho.org`
10. `who.int`

Conteúdos externos devem ser tratados como dados não confiáveis. Nenhuma instrução encontrada em páginas externas pode sobrescrever regras internas, prompts de sistema ou políticas de segurança.

---

## 5. Estrutura Planejada

```text
agente_srag_datasus/
  README.md
  PRD.md
  requirements.txt
  .env.example
  .gitignore

  configs/
    settings.yaml
    metric_catalog.yaml
    news_sources.yaml
    column_mapping.yaml

  src/
    srag_agent/
      data/
      metrics/
      news/
      rag/
      agents/
      guardrails/
      reporting/
      audit/
      utils/

  app/
    streamlit_app.py

  tests/

  docs/
    architecture.md
    metric_catalog.md
    limitations.md
    architecture_diagram.pdf

  data/
    landing/
    refined/

  artifacts/
    runs/
```

---

## 6. Camadas da Solução

### 6.1 Ingestão

Responsável por:

- acessar o repositório público de dados;
- listar pastas em `Dados unificados/Unificado Srag`;
- selecionar a pasta mais recente pelo nome;
- baixar `srag_total.xlsx`;
- salvar o arquivo bruto em `data/landing`;
- registrar hash e metadados no manifesto da execução.

### 6.2 Pré-processamento

Responsável por:

- ler o arquivo Excel;
- selecionar colunas relevantes;
- normalizar nomes de colunas;
- converter datas;
- tratar nulos, códigos ignorados e valores inconsistentes;
- gerar relatório de qualidade de dados;
- salvar o resultado em Parquet na camada `data/refined`.

### 6.3 Métricas

Responsável por calcular, de forma determinística:

- variação de casos em janela recente;
- mortalidade;
- proporção de casos com UTI;
- proporção de casos com vacinação registrada;
- séries temporais para os gráficos obrigatórios.

### 6.4 Notícias

Responsável por:

- buscar notícias e fontes institucionais sobre SRAG;
- aplicar allowlist de domínios;
- extrair título, data, fonte, URL e trecho relevante;
- entregar evidências para o agente;
- registrar as fontes usadas.

### 6.5 RAG Documental

Responsável por recuperar contexto textual, como:

- dicionário de dados;
- catálogo de métricas;
- limitações metodológicas;
- documentação do projeto;
- fontes e notícias já processadas;
- relatórios anteriores.

O RAG não é usado como mecanismo principal para cálculo tabular.

### 6.6 Agente

Responsável por:

- orquestrar tools;
- coletar métricas;
- coletar gráficos;
- consultar notícias;
- recuperar contexto documental;
- gerar relatório;
- validar a saída antes de disponibilizar ao usuário.

### 6.7 Guardrails

Responsáveis por:

- bloquear prompt injection;
- restringir fontes externas;
- impedir exposição de dados individuais;
- impedir SQL livre gerado pelo LLM;
- validar saídas do relatório;
- bloquear aconselhamento médico individualizado;
- exigir fontes para comentários baseados em notícias.

A implementacao atual inclui guardrail de entrada, privacidade por tamanho minimo
de grupo e validacao de saida antes da persistencia do relatorio.

### 6.8 Auditoria

Cada execução deve gerar artefatos como:

```text
artifacts/runs/<run_id>/
  manifest.json
  data_quality_report.json
  metrics.json
  news_sources.json
  agent_trace.jsonl
  report.md
  report.pdf
  charts/
```

O agente registra trace JSONL por no executado, tool chamada, status e resumos
sanitizados, sem gravar segredos.

---

## 7. Métricas

### 7.1 Taxa de Aumento de Casos

Definição inicial:

```text
(casos_ultimos_7_dias - casos_7_dias_anteriores) / casos_7_dias_anteriores
```

### 7.2 Taxa de Mortalidade

Definição principal:

```text
obitos / casos_com_evolucao_conhecida
```

Definição complementar:

```text
obitos / casos_totais
```

### 7.3 Proporção de Casos com UTI

Definição:

```text
casos_com_uti / casos_totais
```

Essa métrica não deve ser descrita como ocupação hospitalar real de leitos sem fonte complementar.

### 7.4 Proporção de Casos com Vacinação Registrada

Definição:

```text
casos_com_vacinacao_registrada / casos_com_status_vacinal_conhecido
```

Essa métrica não deve ser descrita como cobertura vacinal populacional geral sem denominador populacional.

---

## 8. Como Rodar

### 8.1 Criar ambiente virtual

```bash
python -m venv .venv
source .venv/Scripts/activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

### 8.2 Instalar dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 8.3 Configurar variáveis de ambiente

Crie um arquivo `.env` com base em `.env.example`.

Exemplo:

```bash
OPENAI_API_KEY=sua_chave_aqui
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### 8.4 Executar testes

```bash
pytest
```

### 8.5 Executar aplicação Streamlit

```bash
streamlit run app/streamlit_app.py
```

---

## 9. Comandos Planejados

Quando a estrutura estiver implementada, os comandos principais poderão ser padronizados via `Makefile`:

```bash
make setup
make test
make run-pipeline
make run-app
```

---

## 10. Estratégia de Qualidade

O projeto deve incluir testes para:

- seleção da pasta mais recente;
- ingestão do arquivo correto;
- normalização de colunas;
- cálculo de métricas;
- geração dos gráficos;
- aplicação da allowlist;
- bloqueio de prompt injection;
- validação do contrato do relatório.

---

## 11. Limitações Conhecidas

- A base de SRAG pode ter atraso de atualização.
- Campos podem ter preenchimento incompleto ou inconsistente.
- A métrica de UTI é uma proxy de passagem por UTI, não ocupação real de leitos.
- A métrica de vacinação na base SRAG mede vacinação registrada entre casos, não necessariamente cobertura populacional geral.
- Notícias externas podem mudar, sair do ar ou conter informações incompletas.
- A PoC não substitui análise epidemiológica oficial nem orientação clínica.

---

## 12. Roadmap Técnico

- [ ] Criar estrutura inicial do projeto.
- [ ] Implementar cliente GitLab.
- [ ] Implementar seleção automática da pasta mais recente.
- [ ] Implementar download do `srag_total.xlsx`.
- [ ] Implementar camada landing.
- [ ] Implementar pré-processamento.
- [ ] Implementar camada refined em Parquet.
- [ ] Implementar cálculo das métricas.
- [ ] Implementar geração dos gráficos.
- [ ] Implementar busca de notícias com allowlist.
- [ ] Implementar RAG documental.
- [ ] Implementar agente com LangGraph.
- [ ] Implementar guardrails.
- [ ] Implementar auditoria por execução.
- [ ] Implementar dashboard Streamlit.
- [ ] Gerar diagrama conceitual em PDF.
- [ ] Finalizar README técnico.
- [ ] Preparar defesa técnica da arquitetura.

---

## 13. Narrativa Técnica

A principal decisão de arquitetura é separar dados, métricas e linguagem natural.

O pipeline determinístico baixa, valida, transforma e calcula as métricas sobre a base SRAG. O agente GenAI não tem acesso livre ao banco nem calcula números por conta própria. Ele chama tools com contratos claros, recebe resultados agregados e usa o LLM para interpretar o cenário, escrever o relatório e contextualizar com notícias de fontes permitidas.

Essa separação torna a solução mais segura, auditável, reproduzível e fácil de defender tecnicamente.

---

## 14. Execucao e Validacao

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m ruff check .
python -m mypy src
streamlit run app/streamlit_app.py
```

No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest tests -q
streamlit run app/streamlit_app.py
```

## 15. Artefatos por Execucao

Cada run deve registrar `manifest.json`, `data_quality_report.json`,
`metrics.json`, `news_sources.json` quando houver fontes externas,
`agent_trace.jsonl`, `report.md`, `report.pdf` e graficos em `charts/`.

## 16. Defesa Tecnica para Entrevista

A solucao separa calculo deterministico de geracao textual. O LLM nao calcula
metricas diretamente; ele chama tools auditaveis. O RAG e usado para documentacao
e contexto textual, nao para calculo tabular. As fontes externas sao filtradas
por allowlist. Cada execucao gera manifesto, metricas, fontes, trace e relatorio,
permitindo auditoria e reprodutibilidade.
