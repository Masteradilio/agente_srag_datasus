# Agente SRAG DataSUS

Agente de IA Generativa para geraÃ§Ã£o automatizada de relatÃ³rios sobre SÃ­ndrome RespiratÃ³ria Aguda Grave (SRAG), combinando dados estruturados do OpenDataSUS/DataSUS com notÃ­cias e fontes institucionais recentes.

Este projeto foi criado como uma Prova de Conceito tÃ©cnica para demonstrar uma arquitetura de agente analÃ­tico com pipeline determinÃ­stico de dados, uso controlado de tools, RAG documental, guardrails, auditoria e interface demonstrÃ¡vel em Streamlit.

---

## 1. Objetivo

Construir uma soluÃ§Ã£o capaz de:

- acessar automaticamente os dados pÃºblicos de SRAG;
- identificar a pasta mais recente no repositÃ³rio de dados unificados;
- baixar e processar o arquivo `srag_total.xlsx`;
- calcular mÃ©tricas epidemiolÃ³gicas de forma determinÃ­stica;
- gerar grÃ¡ficos obrigatÃ³rios;
- consultar notÃ­cias e fontes oficiais em tempo real;
- produzir um relatÃ³rio explicativo com apoio de LLM;
- registrar rastreabilidade, fontes, decisÃµes e artefatos por execuÃ§Ã£o;
- disponibilizar uma interface em Streamlit para demonstraÃ§Ã£o.

---

## 2. Escopo da PoC

A soluÃ§Ã£o deve gerar um relatÃ³rio contendo, no mÃ­nimo:

- taxa de aumento de casos;
- taxa de mortalidade;
- proporÃ§Ã£o de casos de SRAG com passagem por UTI;
- proporÃ§Ã£o de casos de SRAG com vacinaÃ§Ã£o registrada;
- grÃ¡fico diÃ¡rio de casos dos Ãºltimos 30 dias;
- grÃ¡fico mensal de casos dos Ãºltimos 12 meses;
- comentÃ¡rios explicativos baseados em fontes confiÃ¡veis;
- limitaÃ§Ãµes metodolÃ³gicas;
- fontes consultadas.

ObservaÃ§Ã£o: algumas mÃ©tricas solicitadas no desafio sÃ£o tratadas como proxies quando a base nÃ£o possui o denominador necessÃ¡rio. Por exemplo, a base de SRAG permite calcular proporÃ§Ã£o de casos com UTI, mas nÃ£o ocupaÃ§Ã£o hospitalar real de leitos sem fonte complementar de leitos disponÃ­veis.

---

## 3. PrincÃ­pio Arquitetural

A arquitetura separa cÃ¡lculo determinÃ­stico de geraÃ§Ã£o textual.

O LLM nÃ£o calcula mÃ©tricas diretamente. Ele atua como orquestrador e redator analÃ­tico, chamando tools controladas que retornam mÃ©tricas e evidÃªncias jÃ¡ calculadas por cÃ³digo.

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
RelatÃ³rio + Streamlit + Auditoria
```

---

## 4. Fontes Permitidas

A aplicaÃ§Ã£o deve consultar somente fontes explicitamente permitidas.

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

ConteÃºdos externos devem ser tratados como dados nÃ£o confiÃ¡veis. Nenhuma instruÃ§Ã£o encontrada em pÃ¡ginas externas pode sobrescrever regras internas, prompts de sistema ou polÃ­ticas de seguranÃ§a.

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

## 6. Camadas da SoluÃ§Ã£o

### 6.1 IngestÃ£o

ResponsÃ¡vel por:

- acessar o repositÃ³rio pÃºblico de dados;
- listar pastas em `Dados unificados/Unificado Srag`;
- selecionar a pasta mais recente pelo nome;
- baixar `srag_total.xlsx`;
- salvar o arquivo bruto em `data/landing`;
- registrar hash e metadados no manifesto da execuÃ§Ã£o.

### 6.2 PrÃ©-processamento

ResponsÃ¡vel por:

- ler o arquivo Excel;
- selecionar colunas relevantes;
- normalizar nomes de colunas;
- converter datas;
- tratar nulos, cÃ³digos ignorados e valores inconsistentes;
- gerar relatÃ³rio de qualidade de dados;
- salvar o resultado em Parquet na camada `data/refined`.

### 6.3 MÃ©tricas

ResponsÃ¡vel por calcular, de forma determinÃ­stica:

- variaÃ§Ã£o de casos em janela recente;
- mortalidade;
- proporÃ§Ã£o de casos com UTI;
- proporÃ§Ã£o de casos com vacinaÃ§Ã£o registrada;
- sÃ©ries temporais para os grÃ¡ficos obrigatÃ³rios.

### 6.4 NotÃ­cias

ResponsÃ¡vel por:

- buscar notÃ­cias e fontes institucionais sobre SRAG;
- aplicar allowlist de domÃ­nios;
- extrair tÃ­tulo, data, fonte, URL e trecho relevante;
- entregar evidÃªncias para o agente;
- registrar as fontes usadas.

### 6.5 RAG Documental

ResponsÃ¡vel por recuperar contexto textual, como:

- dicionÃ¡rio de dados;
- catÃ¡logo de mÃ©tricas;
- limitaÃ§Ãµes metodolÃ³gicas;
- documentaÃ§Ã£o do projeto;
- fontes e notÃ­cias jÃ¡ processadas;
- relatÃ³rios anteriores.

O RAG nÃ£o Ã© usado como mecanismo principal para cÃ¡lculo tabular.

### 6.6 Agente

ResponsÃ¡vel por:

- orquestrar tools;
- coletar mÃ©tricas;
- coletar grÃ¡ficos;
- consultar notÃ­cias;
- recuperar contexto documental;
- gerar relatÃ³rio;
- validar a saÃ­da antes de disponibilizar ao usuÃ¡rio.

### 6.7 Guardrails

ResponsÃ¡veis por:

- bloquear prompt injection;
- restringir fontes externas;
- impedir exposiÃ§Ã£o de dados individuais;
- impedir SQL livre gerado pelo LLM;
- validar saÃ­das do relatÃ³rio;
- bloquear aconselhamento mÃ©dico individualizado;
- exigir fontes para comentÃ¡rios baseados em notÃ­cias.

A implementacao atual inclui guardrail de entrada, privacidade por tamanho minimo
de grupo e validacao de saida antes da persistencia do relatorio.

### 6.8 Auditoria

Cada execuÃ§Ã£o deve gerar artefatos como:

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

## 7. MÃ©tricas

### 7.1 Taxa de Aumento de Casos

DefiniÃ§Ã£o inicial:

```text
(casos_ultimos_7_dias - casos_7_dias_anteriores) / casos_7_dias_anteriores
```

### 7.2 Taxa de Mortalidade

DefiniÃ§Ã£o principal:

```text
obitos / casos_com_evolucao_conhecida
```

DefiniÃ§Ã£o complementar:

```text
obitos / casos_totais
```

### 7.3 ProporÃ§Ã£o de Casos com UTI

DefiniÃ§Ã£o:

```text
casos_com_uti / casos_totais
```

Essa mÃ©trica nÃ£o deve ser descrita como ocupaÃ§Ã£o hospitalar real de leitos sem fonte complementar.

### 7.4 ProporÃ§Ã£o de Casos com VacinaÃ§Ã£o Registrada

DefiniÃ§Ã£o:

```text
casos_com_vacinacao_registrada / casos_com_status_vacinal_conhecido
```

Essa mÃ©trica nÃ£o deve ser descrita como cobertura vacinal populacional geral sem denominador populacional.

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

### 8.2 Instalar dependÃªncias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 8.3 Configurar variÃ¡veis de ambiente

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

### 8.5 Executar aplicaÃ§Ã£o Streamlit

```bash
streamlit run app/streamlit_app.py
```

---

## 9. Comandos Planejados

Quando a estrutura estiver implementada, os comandos principais poderÃ£o ser padronizados via `Makefile`:

```bash
make setup
make test
make run-pipeline
make run-app
```

---

## 10. EstratÃ©gia de Qualidade

O projeto deve incluir testes para:

- seleÃ§Ã£o da pasta mais recente;
- ingestÃ£o do arquivo correto;
- normalizaÃ§Ã£o de colunas;
- cÃ¡lculo de mÃ©tricas;
- geraÃ§Ã£o dos grÃ¡ficos;
- aplicaÃ§Ã£o da allowlist;
- bloqueio de prompt injection;
- validaÃ§Ã£o do contrato do relatÃ³rio.

---

## 11. LimitaÃ§Ãµes Conhecidas

- A base de SRAG pode ter atraso de atualizaÃ§Ã£o.
- Campos podem ter preenchimento incompleto ou inconsistente.
- A mÃ©trica de UTI Ã© uma proxy de passagem por UTI, nÃ£o ocupaÃ§Ã£o real de leitos.
- A mÃ©trica de vacinaÃ§Ã£o na base SRAG mede vacinaÃ§Ã£o registrada entre casos, nÃ£o necessariamente cobertura populacional geral.
- NotÃ­cias externas podem mudar, sair do ar ou conter informaÃ§Ãµes incompletas.
- A PoC nÃ£o substitui anÃ¡lise epidemiolÃ³gica oficial nem orientaÃ§Ã£o clÃ­nica.

---

## 12. Roadmap TÃ©cnico

- [ ] Criar estrutura inicial do projeto.
- [ ] Implementar cliente GitLab.
- [ ] Implementar seleÃ§Ã£o automÃ¡tica da pasta mais recente.
- [ ] Implementar download do `srag_total.xlsx`.
- [ ] Implementar camada landing.
- [ ] Implementar prÃ©-processamento.
- [ ] Implementar camada refined em Parquet.
- [ ] Implementar cÃ¡lculo das mÃ©tricas.
- [ ] Implementar geraÃ§Ã£o dos grÃ¡ficos.
- [ ] Implementar busca de notÃ­cias com allowlist.
- [ ] Implementar RAG documental.
- [ ] Implementar agente com LangGraph.
- [ ] Implementar guardrails.
- [ ] Implementar auditoria por execuÃ§Ã£o.
- [ ] Implementar dashboard Streamlit.
- [ ] Gerar diagrama conceitual em PDF.
- [ ] Finalizar README tÃ©cnico.
- [ ] Preparar defesa tÃ©cnica da arquitetura.

---

## 13. Narrativa TÃ©cnica

A principal decisÃ£o de arquitetura Ã© separar dados, mÃ©tricas e linguagem natural.

O pipeline determinÃ­stico baixa, valida, transforma e calcula as mÃ©tricas sobre a base SRAG. O agente GenAI nÃ£o tem acesso livre ao banco nem calcula nÃºmeros por conta prÃ³pria. Ele chama tools com contratos claros, recebe resultados agregados e usa o LLM para interpretar o cenÃ¡rio, escrever o relatÃ³rio e contextualizar com notÃ­cias de fontes permitidas.

Essa separaÃ§Ã£o torna a soluÃ§Ã£o mais segura, auditÃ¡vel, reproduzÃ­vel e fÃ¡cil de defender tecnicamente.

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

