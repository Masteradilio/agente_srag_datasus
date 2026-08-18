from pathlib import Path

from evals.agent_evals import evaluate_agent_guardrails_security, evaluate_tool_contracts
from evals.rag_evals import (
    evaluate_generation_groundedness,
    evaluate_retrieval_benchmark,
    run_full_rag_evals,
)


def test_rag_retrieval_and_generation_evals() -> None:
    bench = evaluate_retrieval_benchmark()
    assert "methods_benchmark" in bench
    assert "hybrid_rrf" in bench["methods_benchmark"]
    assert bench["methods_benchmark"]["hybrid_rrf"]["hit_rate"] >= 0.50

    sample_metrics = {"known_mortality_rate": {"value": 0.04}}
    gen_eval = evaluate_generation_groundedness("Texto descritivo de casos.", sample_metrics)
    assert gen_eval["faithfulness_score"] >= 0.90
    assert gen_eval["evaluation_verdict"] == "PASSED"


def test_agent_security_and_contract_evals() -> None:
    security_eval = evaluate_agent_guardrails_security()
    assert security_eval["adversarial_security_accuracy"] >= 0.85
    assert security_eval["passed_cases"] >= 5

    tool_eval = evaluate_tool_contracts(
        metric_summary={
            "reference_date": "2026-05-01",
            "total_cases": 100,
            "case_growth_rate_7d": {"value": 0.1},
            "known_mortality_rate": {"value": 0.05},
            "icu_case_rate": {"value": 0.2},
        },
        chart_paths=["charts/daily.png", "charts/monthly.png"],
    )
    assert tool_eval["verdict"] == "PASSED"


def test_run_full_rag_evals_generates_json_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "benchmarks" / "rag_evals.json"
    res = run_full_rag_evals(output_path=output_path)

    assert output_path.is_file()
    assert "rag_triad_summary" in res
    assert res["rag_triad_summary"]["generation_faithfulness"] >= 0.90
