# Catálogo de Métricas Epidemiológicas e Estatísticas (v2.0.0)

## 1. Métricas Epidemiológicas Primárias

### 1.1 Data de Referência
- **Definição:** Maior valor válido de `canonical_case_date` na base refinada.

### 1.2 Taxa de Variação de Casos (7 dias móveis)
- **Fórmula:**
  $$\text{Taxa de Aumento} = \frac{\text{casos}_{t-7..t} - \text{casos}_{t-14..t-8}}{\text{casos}_{t-14..t-8}}$$
- **Significado:** Mede a aceleração da transmissão na última semana em relação à semana imediatamente anterior.

### 1.3 Taxa de Mortalidade Conhecida
- **Fórmula:**
  $$\text{Taxa de Mortalidade} = \frac{\text{óbitos}}{\text{casos com desfecho conhecido (cura + óbito)}}$$
- **Significado:** Elimina o viés de subnotificação de casos ainda em acompanhamento hospitalar ativo.

### 1.4 Taxa de Passagem por UTI (Proxy de Gravidade)
- **Fórmula:**
  $$\text{Taxa UTI} = \frac{\text{casos de SRAG com internação em UTI}}{\text{casos com campo UTI preenchido (Sim/Não)}}$$
- **Nota Metodológica:** Representa a proporção de casos graves que necessitaram de cuidados intensivos, não a taxa de ocupação física de leitos do município.

### 1.5 Taxa de Vacinação Registrada (Proxy Vacinal)
- **Fórmula:**
  $$\text{Taxa de Vacinação} = \frac{\text{casos de SRAG com registro vacinal positivo}}{\text{casos com campo de vacinação preenchido}}$$

---

## 2. Distribuição Etiológica de Patógenos

Classificação derivada a partir dos campos `CLASSI_FIN`, `PCR_RESUL` e `OUTRO_VIR`:
1. **COVID-19:** Casos confirmados para SARS-CoV-2 por PCR ou classificação final `5`.
2. **Influenza:** Casos positivos para Influenza A/B por PCR ou classificação final `1`.
3. **Vírus Sincicial Respiratório (VSR):** Casos positivos para VSR ou classificação final `2`.
4. **Outros Vírus Respiratórios:** Adenovírus, Metapneumovírus, Rinovírus, etc. (classificação `3`).
5. **Outros Agentes Etiológicos:** Agentes bacterianos ou fúngicos (classificação `4`).
6. **Não Especificado:** Síndrome respiratória sem identificação do patógeno (classificação `9` ou ignorado).

---

## 3. Estratificação por Faixas Etárias

Derivação padronizada a partir da codificação do DataSUS:
- **0 a 4 anos:** Primeira infância (maior risco para VSR e bronquiolite).
- **5 a 19 anos:** Crianças em idade escolar e adolescentes.
- **20 a 59 anos:** Adultos e população economicamente ativa.
- **60+ anos:** População idosa (grupo de maior vulnerabilidade e mortalidade).
- **Não Informado:** Registros com idade nula ou códigos de exclusão (999).

---

## 4. Detecção Estatística de Anomalias (Z-Score)

- **Janela de Avaliação:** Comparação entre o período recente (últimos 14 dias) e o período de referência anterior (14 dias anteriores).
- **Fórmula do Z-Score:**
  $$Z = \frac{x_{\text{atual}} - \mu_{\text{anterior}}}{\sigma_{\text{anterior}}}$$
- **Níveis de Severidade:**
  - `info`: Variação positiva moderada ($Z \ge 1.0$ ou crescimento $\ge 30\%$).
  - `warning`: Aumento estatisticamente atípico ($Z \ge 2.0$ ou crescimento $\ge 50\%$).
  - `critical`: Surto epidemiológico severo ($Z \ge 3.0$ e crescimento $\ge 75\%$).
