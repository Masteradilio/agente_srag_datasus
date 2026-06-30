import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from langgraph.graph import END, StateGraph  # type: ignore[import-untyped]

from agents.llm_comments import generate_executive_report_sections
from agents.state import AgentState
from agents.tools import (
    generate_required_charts_tool,
    get_metric_summary_tool,
    retrieve_context_tool,
    search_srag_news_tool,
    validate_report_contract_tool,
)
from audit.run_context import AgentTraceLogger
from guardrails.input_guard import enforce_input_guard
from guardrails.output_guard import enforce_output_guard
from reporting.report_builder import ReportContext, build_report_markdown
from utils.paths import ensure_directory, resolve_project_path

MetricTool = Callable[[str, Path | None, Path | None], dict[str, Any]]
ChartTool = Callable[[str, Path | None, Path | None], list[str]]
NewsTool = Callable[
    [str, list[str] | None, int | None, list[dict[str, str | None]] | None],
    list[dict[str, Any]],
]
RagTool = Callable[[str, int, Path], list[dict[str, Any]]]
ValidationTool = Callable[
    [str, dict[str, Any] | None, list[str] | None, list[dict[str, Any]] | None],
    dict[str, Any],
]
AGENT_STEP_ORDER = [
    "validate_user_request",
    "load_run_context",
    "collect_metrics",
    "collect_charts",
    "search_news",
    "retrieve_methodology_context",
    "draft_report",
    "validate_report",
    "persist_report",
]
LANGGRAPH_NODE_ORDER = [f"node_{step}" for step in AGENT_STEP_ORDER]


@dataclass(frozen=True)
class AgentDependencies:
    metrics: MetricTool = get_metric_summary_tool
    charts: ChartTool = generate_required_charts_tool
    news: NewsTool = search_srag_news_tool
    rag: RagTool = retrieve_context_tool
    validate_report: ValidationTool = validate_report_contract_tool


def build_langgraph_workflow() -> Any:
    workflow = StateGraph(AgentState)
    for node_name in LANGGRAPH_NODE_ORDER:
        workflow.add_node(node_name, _passthrough_node)
    workflow.set_entry_point(LANGGRAPH_NODE_ORDER[0])
    for source, target in zip(LANGGRAPH_NODE_ORDER[:-1], LANGGRAPH_NODE_ORDER[1:], strict=True):
        workflow.add_edge(source, target)
    workflow.add_edge(LANGGRAPH_NODE_ORDER[-1], END)
    return workflow.compile()


def run_agent_graph(
    user_request: str,
    run_id: str,
    refined_dir: Path | None = None,
    artifacts_dir: Path | None = None,
    allowed_domains: list[str] | None = None,
    news_candidates: list[dict[str, str | None]] | None = None,
    rag_persist_dir: Path = Path("artifacts/vector_store"),
    dependencies: AgentDependencies | None = None,
) -> AgentState:
    deps = dependencies or AgentDependencies()
    state: AgentState = {"run_id": run_id, "user_request": user_request}
    trace_logger = AgentTraceLogger(
        run_id=run_id,
        artifacts_dir=artifacts_dir or Path("artifacts/runs"),
    )

    _run_traced_node(
        state,
        trace_logger,
        "validate_user_request",
        None,
        lambda: validate_user_request(state),
    )
    _run_traced_node(state, trace_logger, "load_run_context", None, lambda: load_run_context(state))
    _run_traced_node(
        state,
        trace_logger,
        "collect_metrics",
        "get_metric_summary_tool",
        lambda: collect_metrics(state, deps, refined_dir, artifacts_dir),
    )
    _run_traced_node(
        state,
        trace_logger,
        "collect_charts",
        "generate_required_charts_tool",
        lambda: collect_charts(state, deps, refined_dir, artifacts_dir),
    )
    _run_traced_node(
        state,
        trace_logger,
        "search_news",
        "search_srag_news_tool",
        lambda: search_news(state, deps, allowed_domains, news_candidates),
    )
    _run_traced_node(
        state,
        trace_logger,
        "retrieve_methodology_context",
        "retrieve_context_tool",
        lambda: retrieve_methodology_context(state, deps, rag_persist_dir),
    )
    _run_traced_node(state, trace_logger, "draft_report", None, lambda: draft_report(state))
    _run_traced_node(
        state,
        trace_logger,
        "validate_report",
        "validate_report_contract_tool",
        lambda: validate_report(state, deps),
    )
    _run_traced_node(
        state,
        trace_logger,
        "persist_report",
        None,
        lambda: persist_report(state, artifacts_dir),
    )
    return state


def validate_user_request(state: AgentState) -> AgentState:
    if not state.get("user_request", "").strip():
        raise ValueError("user_request nao pode ser vazio.")
    enforce_input_guard(state["user_request"])
    return state


def load_run_context(state: AgentState) -> AgentState:
    state.setdefault("validation_errors", [])
    return state


def collect_metrics(
    state: AgentState,
    dependencies: AgentDependencies,
    refined_dir: Path | None,
    artifacts_dir: Path | None,
) -> AgentState:
    state["metric_summary"] = dependencies.metrics(state["run_id"], refined_dir, artifacts_dir)
    return state


def collect_charts(
    state: AgentState,
    dependencies: AgentDependencies,
    refined_dir: Path | None,
    artifacts_dir: Path | None,
) -> AgentState:
    state["chart_paths"] = dependencies.charts(state["run_id"], refined_dir, artifacts_dir)
    state["chart_context"] = _read_chart_context(state["run_id"], artifacts_dir)
    return state


def search_news(
    state: AgentState,
    dependencies: AgentDependencies,
    allowed_domains: list[str] | None,
    news_candidates: list[dict[str, str | None]] | None,
) -> AgentState:
    state["news_evidence"] = dependencies.news(
        "SRAG Brasil DataSUS OpenDataSUS",
        allowed_domains,
        None,
        news_candidates,
    )
    return state


def retrieve_methodology_context(
    state: AgentState,
    dependencies: AgentDependencies,
    rag_persist_dir: Path,
) -> AgentState:
    state["rag_context"] = dependencies.rag(
        "metodologia metricas SRAG limitacoes DataSUS",
        5,
        rag_persist_dir,
    )
    return state


def draft_report(state: AgentState) -> AgentState:
    summary = state["metric_summary"]
    sources = state.get("news_evidence", [])
    executive_sections, observability = generate_executive_report_sections(
        metric_summary=summary,
        chart_context=state.get("chart_context", {}),
        news_evidence=sources,
    )
    used_sources = _select_used_news_sources(
        sources,
        executive_sections.get("used_source_urls", []),
    )
    state["executive_sections"] = executive_sections
    state["used_news_evidence"] = used_sources
    observability["generated_at"] = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
    state["observability"] = observability
    state["draft_report"] = build_report_markdown(
        ReportContext(
            run_id=state["run_id"],
            metric_summary=summary,
            chart_paths=state.get("chart_paths", []),
            news_evidence=used_sources,
            executive_sections=executive_sections,
            observability=observability,
        )
    )
    return state


def validate_report(state: AgentState, dependencies: AgentDependencies) -> AgentState:
    enforce_output_guard(state["draft_report"], requires_external_sources=True)
    result = dependencies.validate_report(
        state["draft_report"],
        state.get("metric_summary"),
        state.get("chart_paths"),
        state.get("used_news_evidence"),
    )
    state["validation_errors"] = list(result.get("errors", []))
    if state["validation_errors"]:
        raise ValueError("Report contract failed: " + "; ".join(state["validation_errors"]))
    return state


def persist_report(state: AgentState, artifacts_dir: Path | None = None) -> AgentState:
    base_dir = resolve_project_path(artifacts_dir or Path("artifacts/runs"))
    run_dir = ensure_directory(base_dir / state["run_id"])
    report_path = run_dir / "report.md"
    report_path.write_text(state["draft_report"], encoding="utf-8")
    state["final_report_path"] = str(report_path)
    return state


def _read_chart_context(run_id: str, artifacts_dir: Path | None = None) -> dict[str, Any]:
    base_dir = resolve_project_path(artifacts_dir or Path("artifacts/runs"))
    chart_context_path = base_dir / run_id / "chart_context.json"
    if not chart_context_path.is_file():
        return {}
    return json.loads(chart_context_path.read_text(encoding="utf-8"))


def _select_used_news_sources(
    sources: list[dict[str, Any]],
    used_source_urls: list[Any],
) -> list[dict[str, Any]]:
    used_urls = {str(url) for url in used_source_urls if url}
    selected = [source for source in sources if str(source.get("url")) in used_urls]
    if selected:
        return selected[:5]
    return sources[:5]


def _run_traced_node(
    state: AgentState,
    trace_logger: AgentTraceLogger,
    node: str,
    tool: str | None,
    action: Callable[[], AgentState],
) -> None:
    try:
        action()
    except Exception as exc:
        trace_logger.record(
            node=node,
            tool=tool,
            status="error",
            input_summary=_summarize_state(state),
            output_summary={"error": str(exc)},
        )
        raise

    trace_logger.record(
        node=node,
        tool=tool,
        status="success",
        input_summary={"run_id": state.get("run_id")},
        output_summary=_summarize_state(state),
    )


def _summarize_state(state: AgentState) -> dict[str, Any]:
    return {
        "run_id": state.get("run_id"),
        "has_metrics": bool(state.get("metric_summary")),
        "chart_count": len(state.get("chart_paths", [])),
        "has_chart_context": bool(state.get("chart_context")),
        "news_count": len(state.get("news_evidence", [])),
        "used_news_count": len(state.get("used_news_evidence", [])),
        "rag_count": len(state.get("rag_context", [])),
        "has_draft_report": bool(state.get("draft_report")),
        "validation_error_count": len(state.get("validation_errors", [])),
        "has_final_report": bool(state.get("final_report_path")),
    }


def _passthrough_node(state: AgentState) -> AgentState:
    return state
