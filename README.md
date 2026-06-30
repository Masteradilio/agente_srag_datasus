# Agente SRAG DataSUS

Agente de IA Generativa para geração automatizada de relatórios sobre Síndrome Respiratória Aguda Grave (SRAG), combinando dados estruturados do OpenDataSUS/DataSUS com notícias e fontes institucionais recentes.

Este projeto foi criado como uma Prova de Conceito técnica para demonstrar uma arquitetura de agente analítico com pipeline determinístico de dados, uso controlado de tools, RAG documental, guardrails, auditoria e interface demonstrável em Streamlit.

---

## 1. Objetivo

Construir uma solução capaz de:

- acessar automaticamente os dados públicos de SRAG;
- baixar e processar o CSV oficial mais recente do OpenDataSUS;
- consolidar dados recentes e histórico auxiliar em camada refined;
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
OpenDataSUS CSV
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

Allowlist atual:

1. dadosabertos.saude.gov.br
2. gov.br/saude
3. infoms.saude.gov.br
4. fiocruz.br
5. github.com/infogripe
6. agenciagov.ebc.com.br
7. agenciabrasil.ebc.com.br
8. paho.org
9. who.int
10. g1.globo.com
11. cnnbrasil.com.br
12. folha.uol.com.br
13. estadao.com.br
14. uol.com.br
15. metropoles.com
16. exame.com
17. revistapesquisa.fapesp.br
18. cienciahoje.org.br
19. sbmt.org.br
20. dados.gov.br

Conteúdos externos devem ser tratados como dados não confiáveis. Nenhuma instrução encontrada em páginas externas pode sobrescrever regras internas, prompts de sistema ou políticas de segurança.

---

## 5. Estrutura Planejada

```text
agente_srag_datasus/
  README.md
  docs/PRD_srag_genai_agent.md
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

## 6. Camadas da Solução

### 6.1 Ingestão

Responsável por:

- acessar o repositório público de dados;
- baixar o CSV oficial mais recente do OpenDataSUS;
- baixar CSV histórico auxiliar quando configurado;
- salvar o arquivo bruto em `data/landing`;
- registrar hash e metadados no manifesto da execução.

### 6.2 Pré-processamento

Responsável por:

- ler arquivos CSV ou Excel suportados;
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

## 7. Cobertura dos Critérios de Avaliação

O desafio avalia arquitetura, governança e transparência, guardrails, uso de
tools, tratamento de dados sensíveis e clean code. A cobertura detalhada está
documentada em `docs/cobertura_avaliacao.md`, com matriz complementar de
seguranca e privacidade em `docs/guardrails_security_matrix.md`.

### 7.1 Governança e Transparência

Cada execução gera artefatos auditáveis em `artifacts/runs/<run_id>/`:

- `manifest.json`, com origem dos dados, hash e metadados da execução;
- `data_quality_report.json` e `data_quality_report.md`;
- `metrics.json`;
- `chart_context.json`;
- `news_sources.json`;
- `observability.json`;
- `agent_trace.jsonl`;
- `report.md` e `report.pdf`;
- gráficos em `charts/`.

O trace do agente registra nó executado, tool chamada, status, resumo de entrada
e resumo de saída sanitizado. Isso permite reconstruir o caminho operacional do
agente sem expor segredos.

### 7.2 Guardrails e Segurança

O projeto implementa guardrails de entrada, saída, privacidade e allowlist de
fontes externas. Eles protegem contra:

- prompt injection e tentativas de ignorar regras;
- pedidos fora do escopo SRAG/DataSUS;
- solicitação de dados linha a linha ou identificadores individuais;
- diagnóstico, tratamento ou recomendação clínica individualizada;
- exfiltração de segredos, API keys, tokens, senhas, credenciais e arquivos
  `.env`;
- acesso a recursos locais ou internos, como `file://`, `localhost`,
  `127.0.0.1` e endpoints de metadata;
- comandos destrutivos ou perigosos, incluindo shell, SQL destrutivo e execução
  dinâmica de código;
- vazamento de `system prompt`, developer message ou instruções internas;
- CPF, e-mail e telefone em valores de registros;
- campos sensíveis como `cpf`, `cns`, `cartao_sus`, `dt_nasc` e
  `nome_paciente`;
- granularidade excessiva como endereço, CEP, bairro, latitude e longitude;
- grupos com contagem abaixo do tamanho mínimo configurado;
- URLs fora da allowlist no relatório final;
- ausência de fontes, aviso de uso ou limitações metodológicas no relatório.

As principais evidências estão em `src/guardrails/`,
`tests/test_input_guardrails.py`, `tests/test_output_guardrails.py`,
`tests/test_privacy_guardrails.py`, `tests/test_news_allowlist.py` e
`docs/guardrails_security_matrix.md`.

### 7.3 Uso de Tools

O LLM não calcula métricas diretamente e não acessa livremente a base tabular.
O agente chama tools controladas para:

- calcular métricas;
- gerar gráficos;
- buscar e extrair notícias;
- recuperar contexto documental;
- validar o contrato do relatório.

As tools estão em `src/agents/tools.py` e são orquestradas em
`src/agents/graph.py`.

### 7.4 Tratamento de Dados Sensíveis

A solução evita exposição de registros individuais e aplica controles de
privacidade antes de liberar dados agregados. A camada `src/guardrails/privacy.py`
bloqueia campos sensíveis, valores com padrões de identificadores e granularidade
excessiva. A saída final também é validada para impedir identificadores,
caminhos locais, segredos e recomendações clínicas individualizadas.

### 7.5 Clean Code

O projeto está organizado por responsabilidades:

- `src/data`: ingestão, pré-processamento e qualidade;
- `src/metrics`: cálculo determinístico e gráficos;
- `src/news`: busca, ranking e extração de fontes externas;
- `src/rag`: carga, chunking, store e recuperação documental;
- `src/agents`: grafo, estado, tools e contratos;
- `src/guardrails`: entrada, saída, privacidade e allowlist;
- `src/audit`: manifesto e trace;
- `src/reporting`: Markdown/PDF.

Os testes ficam em `tests/` e cobrem as principais camadas funcionais.

---

## 8. Métricas

### 8.1 Taxa de Aumento de Casos

Definição inicial:

```text
(casos_ultimos_7_dias - casos_7_dias_anteriores) / casos_7_dias_anteriores
```

### 8.2 Taxa de Mortalidade

Definição principal:

```text
obitos / casos_com_evolucao_conhecida
```

Definição complementar:

```text
obitos / casos_totais
```

### 8.3 Proporção de Casos com UTI

Definição:

```text
casos_com_uti / casos_totais
```

Essa métrica não deve ser descrita como ocupação hospitalar real de leitos sem fonte complementar.

### 8.4 Proporção de Casos com Vacinação Registrada

Definição:

```text
casos_com_vacinacao_registrada / casos_com_status_vacinal_conhecido
```

Essa métrica não deve ser descrita como cobertura vacinal populacional geral sem denominador populacional.

---

## 9. Como Rodar

### 9.1 Criar ambiente virtual

```bash
python -m venv .venv
source .venv/Scripts/activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

### 9.2 Instalar dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 9.3 Configurar variáveis de ambiente

Crie um arquivo `.env` com base em `.env.example`.

Exemplo:

```bash
OPENAI_API_KEY=sua_api_key_aqui
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### 9.4 Executar testes

```bash
pytest
```

### 9.5 Executar aplicação Streamlit

```bash
streamlit run app/streamlit_app.py
```

### 9.6 Schema do app de demonstração

O app Streamlit foi organizado para demonstrar o desafio aos avaliadores em
quatro páginas:

1. **Sobre**
   - Exibe o `README.md` completo do projeto.
   - Usa uma área com rolagem para permitir leitura integral da documentação.

2. **Pipeline e Arquitetura**
   - Permite disparar a pipeline completa pelo botão **Iniciar pipeline
     completa**.
   - Exibe, em tempo real, as etapas executadas no backend:
     preparação da fonte, ingestão, pré-processamento, manifesto, agente,
     observabilidade, PDF e indexação no vector database.
   - Mostra estaticamente `docs/architecture_diagram.pdf`, usado como apoio
     visual para explicar o agente, tools, LLM, dados e fontes externas.

3. **Relatório e Chat**
   - Exibe o PDF gerado pela pipeline.
   - Inclui um chat com LLM sobre o relatório, métricas, fontes, qualidade dos
     dados e metodologia.
   - O chat usa recuperação em vector database local com documentos do projeto e
     artefatos do run (`report.md`, `news_sources.json`).
   - As perguntas passam por guardrails de input; as respostas são protegidas
     contra exposição de dados sensíveis, instruções internas e recomendações
     clínicas individualizadas.

4. **Observbilidade**
   - Mostra métricas em formato amigável, sem expor JSON cru.
   - Resume linhas processadas, chamadas LLM, tokens, latência, fontes coletadas,
     eventos do trace e qualidade dos dados.
   - Exibe gráfico mensal de casos quando `chart_context.json` está disponível.
   - Apresenta a sequência de nós/tools do agente em tabela para auditoria.

---

## 10. Comandos Planejados

Quando a estrutura estiver implementada, os comandos principais poderão ser padronizados via `Makefile`:

```bash
make setup
make test
make run-pipeline
make run-app
```

---

## 11. Estratégia de Qualidade

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

## 12. Limitações Conhecidas

- A base de SRAG pode ter atraso de atualização.
- Campos podem ter preenchimento incompleto ou inconsistente.
- A métrica de UTI é uma proxy de passagem por UTI, não ocupação real de leitos.
- A métrica de vacinação na base SRAG mede vacinação registrada entre casos, não necessariamente cobertura populacional geral.
- Notícias externas podem mudar, sair do ar ou conter informações incompletas.
- A PoC não substitui análise epidemiológica oficial nem orientação clínica.

---

## 13. Roadmap Técnico

- [x] Criar estrutura inicial do projeto.
- [x] Implementar cliente OpenDataSUS CSV.
- [x] Implementar download do arquivo `INFLUD26-22-06-2026.csv`.
- [x] Implementar camada landing.
- [x] Implementar pré-processamento.
- [x] Implementar camada refined em Parquet.
- [x] Implementar cálculo das métricas.
- [x] Implementar geração dos gráficos.
- [x] Implementar busca de notícias com allowlist.
- [x] Implementar RAG documental.
- [x] Implementar agente com LangGraph.
- [x] Implementar guardrails.
- [x] Implementar auditoria por execução.
- [x] Implementar dashboard Streamlit.
- [x] Gerar diagrama conceitual em PDF.
- [x] Finalizar README técnico.

---

## 14. Narrativa Técnica

A principal decisão de arquitetura é separar dados, métricas e linguagem natural.

O pipeline determinístico baixa, valida, transforma e calcula as métricas sobre a base SRAG. O agente GenAI não tem acesso livre ao banco nem calcula números por conta própria. Ele chama tools com contratos claros, recebe resultados agregados e usa o LLM para interpretar o cenário, escrever o relatório e contextualizar com notícias de fontes permitidas.

Essa separação torna a solução mais segura, auditável, reproduzível e fácil de defender tecnicamente.

---

## 15. Execucao e Validacao

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

## 16. Artefatos por Execucao

Cada run deve registrar `manifest.json`, `data_quality_report.json`,
`metrics.json`, `news_sources.json` quando houver fontes externas,
`agent_trace.jsonl`, `report.md`, `report.pdf` e graficos em `charts/`.

