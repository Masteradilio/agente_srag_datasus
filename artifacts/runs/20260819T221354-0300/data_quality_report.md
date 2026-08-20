# Data Quality Report

## Linhas e Colunas
- Linhas brutas: 473791
- Linhas refinadas: 473791
- Colunas brutas: 194
- Colunas selecionadas: 20
- Linhas descartadas: 0

## Colunas Obrigatorias Ausentes
- `nenhuma`

## Colunas Opcionais Ausentes
- `epidemiological_week`
- `cases`
- `deaths`
- `age_group`
- `health_region`

## Datas Invalidas
- `case_date`: 0
- `evolution_date`: 0
- `icu_end_date`: 0
- `icu_start_date`: 1
- `notification_date`: 0

## Taxa de Nulos por Coluna Selecionada
- `age`: 0.00%
- `age_group`: 100.00%
- `case_date`: 0.00%
- `cases`: 100.00%
- `city`: 0.00%
- `city_code`: 0.00%
- `deaths`: 100.00%
- `epidemiological_week`: 100.00%
- `evolution`: 9.84%
- `evolution_date`: 19.00%
- `final_classification`: 5.94%
- `health_region`: 100.00%
- `icu`: 10.22%
- `icu_end_date`: 85.68%
- `icu_start_date`: 74.85%
- `notification_date`: 0.00%
- `other_virus`: 88.72%
- `pcr_result`: 8.77%
- `state`: 0.00%
- `vaccination`: 0.01%

## Avisos
- Missing optional columns: epidemiological_week, cases, deaths, age_group, health_region
- Invalid dates detected: icu_start_date=1
