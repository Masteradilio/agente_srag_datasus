from datetime import date
from pathlib import Path

import pandas as pd

from data.preprocessing import prepare_refined_dataframe
from metrics.calculators import (
    calculate_age_distribution,
    calculate_etiology_distribution,
    calculate_metric_summary,
    detect_statistical_anomalies,
)
from metrics.charts import (
    generate_age_group_cases_chart,
    generate_etiology_distribution_chart,
)


def test_etiology_and_age_group_derivation() -> None:
    raw_data = pd.DataFrame(
        {
            "DT_NOTIFIC": ["2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05"],
            "CLASSI_FIN": ["5", "1", "2", "3", "9"],
            "NU_IDADE_N": ["3", "12", "45", "72", "999"],
            "EVOLUCAO": ["1", "2", "1", "2", "1"],
            "UTI": ["1", "2", "1", "2", "2"],
            "VACINA_COV": ["1", "2", "1", "2", "9"],
        }
    )
    mapping = {
        "notification_date": "DT_NOTIFIC",
        "final_classification": "CLASSI_FIN",
        "age": "NU_IDADE_N",
        "evolution": "EVOLUCAO",
        "icu": "UTI",
        "vaccination": "VACINA_COV",
    }
    refined, _ = prepare_refined_dataframe(raw_data, mapping)

    assert "canonical_etiology" in refined.columns
    assert "canonical_age_group" in refined.columns
    assert refined["canonical_etiology"].tolist() == [
        "COVID-19",
        "Influenza",
        "VSR",
        "Outros Vírus",
        "Não Especificado",
    ]
    assert refined["canonical_age_group"].tolist() == [
        "0-4 anos",
        "5-19 anos",
        "20-59 anos",
        "60+ anos",
        "Não Informado",
    ]


def test_etiology_and_age_distribution_calculations() -> None:
    df = pd.DataFrame(
        {
            "canonical_case_date": pd.to_datetime(["2026-05-01"] * 5),
            "canonical_etiology": ["COVID-19", "COVID-19", "Influenza", "VSR", "VSR"],
            "canonical_age_group": ["0-4 anos", "0-4 anos", "20-59 anos", "60+ anos", "60+ anos"],
            "icu": ["1", "2", "1", "2", "1"],
            "evolution": ["1", "2", "1", "2", "1"],
        }
    )
    etio_dist = calculate_etiology_distribution(df)
    assert len(etio_dist) == 3
    assert etio_dist[0].etiology in {"COVID-19", "VSR"}
    assert sum(item.percentage for item in etio_dist) == 1.0

    age_dist = calculate_age_distribution(df)
    assert len(age_dist) == 3
    assert any(item.age_group == "0-4 anos" and item.cases == 2 for item in age_dist)


def test_statistical_anomaly_detection() -> None:
    # Simular aumento súbito de VSR em 0-4 anos nos últimos 14 dias
    dates_prev = pd.date_range(start="2026-05-01", end="2026-05-14", freq="D")
    dates_curr = pd.date_range(start="2026-05-15", end="2026-05-28", freq="D")

    # 1 caso por dia no periodo anterior
    df_prev = pd.DataFrame({
        "canonical_case_date": dates_prev,
        "canonical_etiology": ["VSR"] * len(dates_prev),
        "canonical_age_group": ["0-4 anos"] * len(dates_prev),
    })

    # 5 casos por dia no periodo recente (aumento brusco)
    df_curr = pd.DataFrame({
        "canonical_case_date": dates_curr.repeat(5),
        "canonical_etiology": ["VSR"] * (len(dates_curr) * 5),
        "canonical_age_group": ["0-4 anos"] * (len(dates_curr) * 5),
    })

    combined = pd.concat([df_prev, df_curr], ignore_index=True)
    anomalies = detect_statistical_anomalies(combined, reference_date=date(2026, 5, 28))

    assert anomalies.total_anomalies > 0
    assert any(a.category == "VSR" for a in anomalies.alerts)
    assert any(a.category == "0-4 anos" for a in anomalies.alerts)


def test_etiology_and_age_charts_generation(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "canonical_case_date": pd.to_datetime(["2026-05-01", "2026-05-02"]),
            "canonical_etiology": ["COVID-19", "Influenza"],
            "canonical_age_group": ["0-4 anos", "60+ anos"],
        }
    )
    etio_path = generate_etiology_distribution_chart(df, tmp_path / "etiology.png")
    age_path = generate_age_group_cases_chart(df, tmp_path / "age.png")

    assert etio_path.is_file()
    assert age_path.is_file()
