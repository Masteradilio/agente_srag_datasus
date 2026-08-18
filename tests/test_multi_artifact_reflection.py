from pathlib import Path

from agents.graph import evaluate_and_reflect
from agents.state import AgentState
from reporting.report_builder import ReportContext, build_multi_artifacts


def test_build_multi_artifacts_generates_all_five_reports() -> None:
    context = ReportContext(
        run_id="run-2026-test",
        metric_summary={
            "reference_date": "2026-05-20",
            "total_cases": 1500,
            "case_growth_rate_7d": {"name": "Taxa de Aumento", "value": 0.12, "numerator": 12, "denominator": 100},
            "known_mortality_rate": {"name": "Taxa de Mortalidade", "value": 0.05, "numerator": 5, "denominator": 100},
            "icu_case_rate": {"name": "Taxa UTI", "value": 0.22, "numerator": 22, "denominator": 100},
            "registered_vaccination_case_rate": {"name": "Taxa Vacinação", "value": 0.45, "numerator": 45, "denominator": 100},
            "etiology_distribution": [{"etiology": "COVID-19", "cases": 800, "percentage": 0.53}],
            "age_distribution": [{"age_group": "60+ anos", "cases": 900, "percentage": 0.60, "icu_rate": 0.30, "mortality_rate": 0.08}],
            "anomalies": {"total_anomalies": 1, "alerts": [{"dimension": "Etiologia", "category": "COVID-19", "z_score": 2.5, "current_period_cases": 800, "previous_period_cases": 500, "growth_rate": 0.60, "severity": "critical", "description": "Alta de 60%"}]},
        },
        chart_paths=["charts/daily.png", "charts/monthly.png"],
        news_evidence=[{"title": "MS abre leitos", "url": "https://www.gov.br/saude/noticia", "snippet": "Leitos"}],
        executive_sections={"metrics_section": "Crescimento recente registrado nos casos."},
    )

    artifacts = build_multi_artifacts(context)

    expected_files = {
        "report.md",
        "executive_bulletin.md",
        "epidemiological_deepdive.md",
        "anomaly_alerts.md",
        "media_and_social_signals.md",
        "data_governance_report.md",
    }
    assert set(artifacts.keys()) == expected_files
    assert "# Boletim Executivo" in artifacts["executive_bulletin.md"]
    assert "Distribuição Etiológica" in artifacts["epidemiological_deepdive.md"]
    assert "Alerta de Anomalia" in artifacts["anomaly_alerts.md"]
    assert "Inteligência de Mídia" in artifacts["media_and_social_signals.md"]
    assert "Relatório de Governança" in artifacts["data_governance_report.md"]


def test_evaluate_and_reflect_computes_groundedness_score() -> None:
    state: AgentState = {
        "run_id": "run-test",
        "metric_summary": {
            "case_growth_rate_7d": {"value": 0.15},
            "known_mortality_rate": {"value": 0.04},
        },
        "draft_report": "O relatório apresenta um aumento de casos e mortalidade estável.",
    }
    updated_state = evaluate_and_reflect(state)

    assert "eval_scores" in updated_state
    assert updated_state["eval_scores"]["faithfulness"] >= 0.90
    assert updated_state.get("reflection_iteration", 0) == 1
