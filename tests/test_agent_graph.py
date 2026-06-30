from pathlib import Path

import pandas as pd

from agents.graph import AgentDependencies, build_langgraph_workflow, run_agent_graph


def _metric_summary() -> dict:
    return {
        "reference_date": "2026-06-20",
        "total_cases": 20,
        "case_growth_rate_7d": {"value": 0.1, "numerator": 1, "denominator": 10},
        "known_mortality_rate": {"value": 0.2, "numerator": 4, "denominator": 20},
        "crude_mortality_rate": {"value": 0.2, "numerator": 4, "denominator": 20},
        "icu_case_rate": {"value": 0.5, "numerator": 10, "denominator": 20},
        "registered_vaccination_case_rate": {
            "value": 0.5,
            "numerator": 10,
            "denominator": 20,
        },
        "limitations": ["Dados sujeitos a revisao."],
    }


def test_agent_graph_calls_tools_and_persists_report(tmp_path) -> None:
    calls: list[str] = []

    def metrics(run_id: str, refined_dir: Path | None, artifacts_dir: Path | None) -> dict:
        calls.append(f"metrics:{run_id}")
        return _metric_summary()

    def charts(run_id: str, refined_dir: Path | None, artifacts_dir: Path | None) -> list[str]:
        calls.append(f"charts:{run_id}")
        return [
            str(tmp_path / "daily_cases_30d.png"),
            str(tmp_path / "monthly_cases_12m.png"),
        ]

    def news(query, allowed_domains, max_results, candidates) -> list[dict]:
        calls.append("news")
        return [
            {
                "title": "Boletim SRAG",
                "url": "https://www.who.int/news/srag",
                "source_domain": "www.who.int",
            }
        ]

    def rag(query: str, top_k: int, persist_dir: Path) -> list[dict]:
        calls.append("rag")
        return [{"source_path": "docs/PRD_srag_genai_agent.md", "score": 1.0}]

    state = run_agent_graph(
        user_request="Gerar relatorio SRAG",
        run_id="run-graph",
        artifacts_dir=tmp_path / "artifacts",
        dependencies=AgentDependencies(metrics=metrics, charts=charts, news=news, rag=rag),
    )

    assert calls == ["metrics:run-graph", "charts:run-graph", "news", "rag"]
    assert state["validation_errors"] == []
    assert Path(state["final_report_path"]).is_file()
    trace_path = tmp_path / "artifacts" / "run-graph" / "agent_trace.jsonl"
    assert trace_path.is_file()
    assert "validate_report" in trace_path.read_text(encoding="utf-8")


def test_langgraph_workflow_topology_compiles() -> None:
    workflow = build_langgraph_workflow()

    result = workflow.invoke({"run_id": "run-topology", "user_request": "Relatorio SRAG"})

    assert result["run_id"] == "run-topology"


def test_agent_graph_smoke_with_phase3_phase4_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DISABLE_LLM_API", "1")

    run_id = "run-smoke"
    refined_dir = tmp_path / "refined" / run_id
    refined_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "canonical_case_date": pd.date_range("2026-06-01", periods=40, freq="D"),
            "evolution": ["1", "2"] * 20,
            "icu": ["1", "2"] * 20,
            "vaccination": ["1", "2"] * 20,
        }
    ).to_parquet(refined_dir / "srag_total.parquet", index=False)

    def rag(query: str, top_k: int, persist_dir: Path) -> list[dict]:
        return [{"source_path": "docs/metric_catalog.md", "score": 1.0}]

    state = run_agent_graph(
        user_request="Gerar relatorio SRAG com metricas e graficos",
        run_id=run_id,
        refined_dir=tmp_path / "refined",
        artifacts_dir=tmp_path / "artifacts",
        allowed_domains=["who.int"],
        news_candidates=[
            {
                "title": "SRAG",
                "url": "https://www.who.int/news/srag",
                "snippet": "SRAG",
            }
        ],
        dependencies=AgentDependencies(rag=rag),
    )

    assert Path(state["final_report_path"]).is_file()
    assert (tmp_path / "artifacts" / run_id / "metrics.json").is_file()
    assert len(state["chart_paths"]) == 2

