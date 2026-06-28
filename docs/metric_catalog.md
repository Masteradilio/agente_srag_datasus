# Catalogo de Metricas

## Data de referencia

Maior valor valido de `canonical_case_date` na base refinada.

## Taxa de aumento de casos em 7 dias

Formula:

```text
(casos_ultimos_7_dias - casos_7_dias_anteriores) / casos_7_dias_anteriores
```

Colunas usadas:

- `canonical_case_date`
- `cases`, quando a base estiver agregada

Limitacao: se a janela anterior nao tiver casos, a taxa fica indisponivel.

## Taxa de mortalidade conhecida

Formula em dados linha a linha:

```text
obitos / casos_com_evolucao_conhecida
```

Colunas usadas:

- `evolution`

Proxy em base agregada:

```text
deaths / cases
```

Limitacao: a taxa conhecida depende da completude de evolucao. Em base agregada,
usa casos totais porque o status individual nao esta disponivel.

## Taxa de mortalidade bruta

Formula:

```text
obitos / casos_totais
```

Colunas usadas:

- `evolution`, em dados linha a linha
- `deaths` e `cases`, em dados agregados

## Proporcao de casos com UTI

Formula:

```text
casos_com_uti / casos_totais
```

Colunas usadas:

- `icu`

Proxy: mede passagem por UTI registrada entre casos de SRAG, nao ocupacao de
leitos nem demanda hospitalar total.

## Proporcao de casos com vacinacao registrada

Formula:

```text
casos_com_vacinacao_sim / casos_com_status_vacinal_conhecido
```

Colunas usadas:

- `vaccination`

Proxy: mede registro vacinal entre casos de SRAG, nao cobertura vacinal da
populacao.

## Graficos

- `daily_cases_30d.png`: serie diaria dos ultimos 30 dias.
- `monthly_cases_12m.png`: serie mensal dos ultimos 12 meses.

