from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langgraph.graph import END, StateGraph  # type: ignore[import-untyped]

from srag_agent.agents.prompts import SYSTEM_PROMPT
from srag_agent.agents.state import AgentState
from srag_agent.agents.tools import (
    generate_required_charts_tool,
    get_metric_summary_tool,
    retrieve_context_tool,
    search_srag_news_tool,
    validate_report_contract_tool,
)
from srag_agent.audit.run_context import AgentTraceLogger
from srag_agent.guardrails.input_guard import enforce_input_guard
from srag_agent.guardrails.output_guard import enforce_output_guard
from srag_agent.utils.paths import ensure_directory, resolve_project_path

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
    charts = state.get("chart_paths", [])
    sources = state.get("news_evidence", [])
    contexts = state.get("rag_context", [])

    state["draft_report"] = "\n".join(
        [
            "# Relatorio tecnico de SRAG",
            "",
            "## Escopo",
            (
                "Relatorio gerado com tools deterministicas. "
                "O agente nao calcula metricas diretamente."
            ),
            "",
            "## Metricas calculadas",
            f"- Data de referencia: {summary.get('reference_date')}",
            f"- Total de casos: {summary.get('total_cases')}",
            _format_metric("Taxa de aumento 7d", summary["case_growth_rate_7d"]),
            _format_metric("Taxa de mortalidade conhecida", summary["known_mortality_rate"]),
            _format_metric("Taxa de mortalidade bruta", summary["crude_mortality_rate"]),
            _format_metric("Proporcao de casos com UTI", summary["icu_case_rate"]),
            _format_metric(
                "Proporcao de casos com vacinacao registrada",
                summary["registered_vaccination_case_rate"],
            ),
            "",
            "## Graficos",
            *_format_charts(charts),
            "",
            "## Evidencias e interpretacao",
            _format_contexts(contexts),
            "",
            "## Fontes",
            *_format_sources(sources),
            "",
            "## Limitacoes",
            *_format_limitations(summary),
            "",
            "## Aviso de uso",
            (
                "Este relatorio e informativo, usa dados agregados e nao substitui "
                "avaliacao epidemiologica oficial ou aconselhamento medico individualizado."
            ),
            "",
            "<!-- prompt_rules -->",
            SYSTEM_PROMPT,
        ]
    )
    return state


def validate_report(state: AgentState, dependencies: AgentDependencies) -> AgentState:
    enforce_output_guard(state["draft_report"], requires_external_sources=True)
    result = dependencies.validate_report(
        state["draft_report"],
        state.get("metric_summary"),
        state.get("chart_paths"),
        state.get("news_evidence"),
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


def _format_metric(label: str, metric: dict[str, Any]) -> str:
    value = metric.get("value")
    formatted_value = "indisponivel" if value is None else f"{float(value):.4f}"
    return (
        f"- {label}: {formatted_value} "
        f"(numerador={metric.get('numerator')}, denominador={metric.get('denominator')})"
    )


def _format_charts(chart_paths: list[str]) -> list[str]:
    if not chart_paths:
        return ["- Nenhum grafico gerado."]
    return [f"- {Path(chart_path).name}: {chart_path}" for chart_path in chart_paths]


def _format_sources(sources: list[dict[str, Any]]) -> list[str]:
    if not sources:
        return ["- Nenhuma fonte externa recuperada."]
    return [
        f"- {source.get('title', 'Fonte')} ({source.get('source_domain', '')}): {source.get('url')}"
        for source in sources
    ]


def _format_contexts(contexts: list[dict[str, Any]]) -> str:
    if not contexts:
        return "Contexto metodologico documental nao recuperado nesta execucao."
    first = contexts[0]
    return (
        f"Contexto documental principal: {first.get('source_path')} "
        f"(score={first.get('score')})."
    )


def _format_limitations(summary: dict[str, Any]) -> list[str]:
    limitations = summary.get("limitations") or []
    if not limitations:
        return ["- Interpretacoes dependem da completude e atualizacao do banco SRAG."]
    return [f"- {limitation}" for limitation in limitations]


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
        "news_count": len(state.get("news_evidence", [])),
        "rag_count": len(state.get("rag_context", [])),
        "has_draft_report": bool(state.get("draft_report")),
        "validation_error_count": len(state.get("validation_errors", [])),
        "has_final_report": bool(state.get("final_report_path")),
    }


def _passthrough_node(state: AgentState) -> AgentState:
    return state
