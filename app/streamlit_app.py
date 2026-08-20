import base64
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import requests  # type: ignore[import-untyped]
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Explicitly load environment variables from project root
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from agents.graph import run_agent_graph  # noqa: E402
from audit.manifest import build_execution_manifest, write_execution_manifest  # noqa: E402
from config import load_news_sources, load_settings  # noqa: E402
from data.ingestion import run_ingestion  # noqa: E402
from data.preprocessing import run_preprocessing  # noqa: E402
from guardrails.input_guard import validate_input_request  # noqa: E402
from guardrails.privacy import enforce_no_sensitive_values  # noqa: E402
from news.extract import extract_news_article  # noqa: E402
from news.search import search_srag_news  # noqa: E402
from pipeline import _allowlist_source_candidates, _ensure_historical_raw_files  # noqa: E402
from rag.retriever import index_project_context, retrieve_context  # noqa: E402
from reporting.pdf_exporter import export_report_pdf  # noqa: E402
from utils.hashing import calculate_sha256  # noqa: E402
from utils.paths import ensure_directory, resolve_project_path  # noqa: E402

RUN_STATE_KEY = "selected_run_id"


def list_run_ids(artifacts_dir: Path) -> list[str]:
    """Return list of run IDs ordered strictly by execution time, most recent first."""
    if not artifacts_dir.is_dir():
        return []
    runs = [path.name for path in artifacts_dir.iterdir() if path.is_dir()]
    timestamped = sorted(
        [r for r in runs if (r.startswith("20") and len(r) >= 15) or (r.startswith("run-20") and len(r) >= 19)],
        reverse=True,
    )
    others = sorted([r for r in runs if r not in timestamped], reverse=True)
    return timestamped + others


def read_json(path: Path) -> dict[str, Any] | list[Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def artifact_paths(run_id: str, artifacts_dir: Path) -> dict[str, Path]:
    run_dir = artifacts_dir / run_id
    return {
        "run_dir": run_dir,
        "manifest": run_dir / "manifest.json",
        "quality": run_dir / "data_quality_report.json",
        "metrics": run_dir / "metrics.json",
        "news": run_dir / "news_sources.json",
        "trace": run_dir / "agent_trace.jsonl",
        "observability": run_dir / "observability.json",
        "chart_context": run_dir / "chart_context.json",
        "report_md": run_dir / "report.md",
        "report_pdf": run_dir / "report.pdf",
        "charts_dir": run_dir / "charts",
        "executive_bulletin": run_dir / "executive_bulletin.md",
        "epidemiological_deepdive": run_dir / "epidemiological_deepdive.md",
        "anomaly_alerts": run_dir / "anomaly_alerts.md",
        "media_and_social_signals": run_dir / "media_and_social_signals.md",
        "data_governance_report": run_dir / "data_governance_report.md",
    }


def default_raw_file() -> Path | None:
    candidates = sorted((PROJECT_ROOT / "data" / "landing").glob("**/INFLUD26-*.csv"))
    return candidates[-1] if candidates else None


def render_pdf(path: Path, height: int = 800) -> None:
    if not path.is_file():
        st.info(f"Arquivo PDF não encontrado: {path.name}")
        return
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    st.markdown(
        (
            f'<iframe src="data:application/pdf;base64,{encoded}" '
            f'width="100%" height="{height}" type="application/pdf"></iframe>'
        ),
        unsafe_allow_html=True,
    )


def selected_run_id(artifacts_dir: Path) -> str | None:
    run_ids = list_run_ids(artifacts_dir)
    if not run_ids:
        return None
    current = st.session_state.get(RUN_STATE_KEY)
    index = run_ids.index(current) if current in run_ids else 0
    chosen = st.sidebar.selectbox(
        "⏱️ Selecionar Execução (Mais recentes primeiro)",
        run_ids,
        index=index,
        help="As execuções estão ordenadas cronologicamente da mais recente para a mais antiga.",
    )
    st.session_state[RUN_STATE_KEY] = chosen
    return chosen


def metric_value(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key, {}).get("value")
    return float(value) if isinstance(value, int | float) else None


def pct(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.2%}"


# ==============================================================================
# CHAT QUESTION ANSWERING & CONTEXT ASSEMBLY
# ==============================================================================

def answer_chat_question(question: str, run_id: str, paths: dict[str, Path]) -> str:
    guard = validate_input_request(question, allow_contextual_chat=True)
    if not guard.allowed:
        return "Pedido bloqueado pelos guardrails: " + "; ".join(guard.reasons)

    metrics = read_json(paths["metrics"])
    quality = read_json(paths["quality"])
    news = read_json(paths["news"])
    chart_context = read_json(paths["chart_context"])
    report_text = read_text(paths["report_md"])

    # Read all 5 specialized intelligence artifacts
    executive_bulletin = read_text(paths["executive_bulletin"])
    epidemiological_deepdive = read_text(paths["epidemiological_deepdive"])
    anomaly_alerts = read_text(paths["anomaly_alerts"])
    media_and_social_signals = read_text(paths["media_and_social_signals"])
    data_governance_report = read_text(paths["data_governance_report"])

    privacy_payloads = [
        metrics if isinstance(metrics, dict) else {},
        quality if isinstance(quality, dict) else {},
    ]
    for payload in privacy_payloads:
        enforce_no_sensitive_values(payload)

    # Perform Hybrid RAG Retrieval (ChromaDB + BM25)
    persist_dir = PROJECT_ROOT / "artifacts" / "vector_store" / run_id
    retrieved = retrieve_context(question, top_k=5, persist_dir=persist_dir)
    rag_context = "\n\n".join(
        [
            f"[{item.source_path} | relevância={item.score:.2f}]\n{item.content[:800]}"
            for item in retrieved
        ]
    )

    external_context = _search_external_context_if_requested(question)
    parquet_context = _summarize_refined_parquet_if_needed(question, run_id)

    system_prompt = (
        "Você é o assistente executivo e especialista em vigilância epidemiológica do Agente DataSUS. "
        "Todas as respostas devem ser geradas por você a partir dos artefatos e resultados de tools fornecidos no contexto. "
        "Responda somente o que foi perguntado, com alto groundedness, em ate 3 paragrafos curtos. "
        "Não crie tabelas, títulos ou seções desnecessárias, exceto se o usuário pedir explicitamente. "
        "Cite números, porcentagens, faixas etárias, Z-scores e datas quando disponíveis. "
        "Se a informação não estiver nos dados, diga isso objetivamente. "
        "Sempre que usar informações ou notícias na resposta, finalize com uma seção chamada exatamente 'Fontes Consultadas:' "
        "e liste as URLs das fontes usadas. Essa seção é obrigatória: nunca omita as fontes. "
        "Não exponha dados individuais e não recomende tratamento individual."
    )

    user_prompt = (
        f"PERGUNTA_DO_USUARIO={question}\n\n"
        f"=== CONTEXTO DA RUN ATUAL (ID: {run_id}) ===\n\n"
        f"--- 1. MÉTRICAS ESTRUTURADAS (metrics.json) ---\n"
        f"{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n"
        f"--- 2. PARECER EPIDEMIOLÓGICO DEEP-DIVE (epidemiological_deepdive.md) ---\n"
        f"{epidemiological_deepdive}\n\n"
        f"--- 3. ALERTAS DE ANOMALIA & Z-SCORE (anomaly_alerts.md) ---\n"
        f"{anomaly_alerts}\n\n"
        f"--- 4. BOLETIM EXECUTIVO (executive_bulletin.md) ---\n"
        f"{executive_bulletin}\n\n"
        f"--- 5. SINAIS DE MÍDIA E REDES SOCIAIS / AGENT REACH (media_and_social_signals.md) ---\n"
        f"{media_and_social_signals}\n\n"
        f"--- 6. GOVERNANÇA, LINHAGEM E QUALIDADE (data_governance_report.md) ---\n"
        f"{data_governance_report}\n\n"
        f"--- 7. FONTES CONSULTADAS (news_sources.json) ---\n"
        f"{json.dumps(news, ensure_ascii=False, indent=2)}\n\n"
        f"--- 8. HISTÓRICO E GRÁFICOS (chart_context.json) ---\n"
        f"{json.dumps(chart_context, ensure_ascii=False, indent=2)}\n\n"
        f"--- 9. QUALIDADE DOS DADOS (data_quality_report.json) ---\n"
        f"{json.dumps(quality, ensure_ascii=False, indent=2)}\n\n"
        f"--- 10. RESUMO DO PARQUET ---\n"
        f"{parquet_context}\n\n"
        f"--- 11. RESULTADO_TOOL_BUSCA_ALLOWLIST ---\n"
        f"{external_context}\n\n"
        f"--- 12. RELATORIO ---\n"
        f"{report_text[:1800]}\n\n"
        f"--- 13. CONTEXTO_RAG ---\n"
        f"{rag_context}"
    )

    answer = _call_chat_llm(system_prompt, user_prompt, observability_path=paths.get("observability"))
    return _guard_chat_answer(answer)


def _call_chat_llm(system_prompt: str, user_prompt: str, observability_path: Path | None = None) -> str:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    if os.getenv("DISABLE_LLM_API") == "1":
        return _generate_grounded_local_answer(user_prompt)

    nvidia_key = (os.getenv("NVIDIA_API_KEY") or "").strip().strip('"').strip("'")
    nvidia_model = (os.getenv("LLM_MODEL") or "").strip().strip('"').strip("'") or "meta/llama-3.1-70b-instruct"

    openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip().strip('"').strip("'")
    openrouter_model = (os.getenv("OPENROUTER_MODEL") or "").strip().strip('"').strip("'") or "deepseek/deepseek-chat"

    # Tentativa 1: NVIDIA Integrate (Meta Llama 3.1 70B - Alta Velocidade)
    if nvidia_key:
        for model_candidate in ["meta/llama-3.1-70b-instruct", nvidia_model, "mistralai/mixtral-8x7b-instruct-v0.1"]:
            try:
                response = requests.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"},
                    json={
                        "model": model_candidate,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500,
                    },
                    timeout=15,
                )
                if response.status_code == 200:
                    payload = response.json()
                    answer = str(payload["choices"][0]["message"]["content"]).strip()
                    if observability_path:
                        usage = payload.get("usage", {})
                        p_tokens = int(usage.get("prompt_tokens") or _approx_tokens(system_prompt + user_prompt))
                        c_tokens = int(usage.get("completion_tokens") or _approx_tokens(answer))
                        t_tokens = int(usage.get("total_tokens") or (p_tokens + c_tokens))
                        _update_observability_chat(observability_path, p_tokens, c_tokens, t_tokens)
                    return answer
            except Exception:
                pass

    # Tentativa 2: OpenRouter (DeepSeek Chat)
    if openrouter_key:
        for model_candidate in ["deepseek/deepseek-chat", openrouter_model]:
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/Masteradilio/agente_srag_datasus",
                        "X-Title": "Agente SRAG DataSUS",
                    },
                    json={
                        "model": model_candidate,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500,
                    },
                    timeout=15,
                )
                if response.status_code == 200:
                    payload = response.json()
                    answer = str(payload["choices"][0]["message"]["content"]).strip()
                    if observability_path:
                        usage = payload.get("usage", {})
                        p_tokens = int(usage.get("prompt_tokens") or _approx_tokens(system_prompt + user_prompt))
                        c_tokens = int(usage.get("completion_tokens") or _approx_tokens(answer))
                        t_tokens = int(usage.get("total_tokens") or (p_tokens + c_tokens))
                        _update_observability_chat(observability_path, p_tokens, c_tokens, t_tokens)
                    return answer
            except Exception:
                pass

    # Tentativa 3: Fallback Analítico Local Grounded
    return _generate_grounded_local_answer(user_prompt)


def _generate_grounded_local_answer(prompt: str) -> str:
    """Fallback determinístico analítico de alta fidelidade para ambientes sem conexão à internet."""
    return (
        "Não foi possível contactar o provedor de LLM nesta chamada (verifique sua conexão ou saldo de API). "
        "Todos os dados foram preservados e podem ser consultados diretamente na aba 'Suíte de Relatórios & Artefatos'."
    )


def _guard_chat_answer(answer: str) -> str:
    blocked_terms = ["nu_notific", "cpf", "dt_nasc", "nome do paciente", "chave secreta", "developer message"]
    normalized = answer.casefold()
    if any(term in normalized for term in blocked_terms):
        return (
            "Resposta bloqueada pelos guardrails de saída do chat por risco de "
            "exposição de dado sensível ou instrução interna."
        )
    return answer


def _summarize_refined_parquet_if_needed(question: str, run_id: str) -> str:
    normalized = question.casefold()
    parquet_terms = ["parquet", "base", "dados", "coluna", "estado", "cidade", "linhas"]
    if not any(term in normalized for term in parquet_terms):
        return "Consulta ao Parquet não necessária para esta pergunta."
    parquet_path = PROJECT_ROOT / "data" / "refined" / run_id / "srag_total.parquet"
    if not parquet_path.is_file():
        return "Parquet refinado do run não encontrado."
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as exc:
        return f"Parquet refinado indisponível: {type(exc).__name__}."
    summary: dict[str, Any] = {
        "linhas": int(len(df)),
        "colunas": list(df.columns[:30]),
    }
    if "canonical_case_date" in df.columns:
        dates = pd.to_datetime(df["canonical_case_date"], errors="coerce")
        summary["data_min"] = str(dates.min().date()) if dates.notna().any() else None
        summary["data_max"] = str(dates.max().date()) if dates.notna().any() else None
    return json.dumps(summary, ensure_ascii=False)


def _approx_tokens(text: str) -> int:
    return len(text) // 4


def _update_observability_chat(
    observability_path: Path,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> None:
    try:
        if not observability_path.is_file():
            return
        data = json.loads(observability_path.read_text(encoding="utf-8"))
        data["llm_call_count"] = data.get("llm_call_count", 0) + 1
        data["prompt_tokens"] = data.get("prompt_tokens", 0) + prompt_tokens
        data["completion_tokens"] = data.get("completion_tokens", 0) + completion_tokens
        data["total_tokens"] = data.get("total_tokens", 0) + total_tokens

        observability_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _search_external_context_if_requested(question: str) -> str:
    normalized = question.casefold()
    external_terms = [
        "notícia",
        "noticia",
        "notícias",
        "noticias",
        "internet",
        "web",
        "fonte externa",
        "fontes externas",
    ]
    if not any(term in normalized for term in external_terms):
        return json.dumps(
            {"tool": "news_allowlist_search", "executed": False, "reason": "not_requested"},
            ensure_ascii=False,
        )
    asks_oldest = any(term in normalized for term in ["antiga", "antigas", "mais antigo"])
    try:
        sources = load_news_sources()
        search_domains = _prioritize_chat_news_domains(sources.allowed_domains)
        search_query = _external_news_search_query(question)
        if asks_oldest:
            search_query = f"{search_query} histórico"
        results = search_srag_news(
            search_query,
            search_domains,
            max_results=10 if asks_oldest else 5,
            candidates=_chat_news_candidates(),
        )
        articles = [
            extract_news_article(result.url, sources.allowed_domains, timeout_seconds=8)
            for result in results[:8]
        ]
    except Exception as exc:
        return json.dumps(
            {
                "tool": "news_allowlist_search",
                "executed": True,
                "status": "error",
                "error_type": type(exc).__name__,
            },
            ensure_ascii=False,
        )
    articles = [article for article in articles if _is_news_like_article(article)]
    articles = _dedupe_articles_by_domain(articles)
    if asks_oldest:
        articles = sorted(articles, key=_article_sort_key)
    selected = articles[:3] if asks_oldest else articles[:5]
    payload = [
        {
            "titulo": article.title,
            "url": article.url,
            "data": article.published_at,
            "trecho": article.excerpt[:350],
            "status": article.extraction_status,
        }
        for article in selected
    ]
    return json.dumps(
        {
            "tool": "news_allowlist_search",
            "executed": True,
            "status": "success",
            "allowed_domains_count": len(sources.allowed_domains),
            "ordering": "oldest_first" if asks_oldest else "relevance",
            "query": search_query,
            "results": payload,
        },
        ensure_ascii=False,
    )


def _prioritize_chat_news_domains(allowed_domains: list[str]) -> list[str]:
    preferred = [
        "g1.globo.com",
        "cnnbrasil.com.br",
        "folha.uol.com.br",
        "estadao.com.br",
        "uol.com.br",
        "metropoles.com",
        "exame.com",
        "revistapesquisa.fapesp.br",
        "cienciahoje.org.br",
        "sbmt.org.br",
        "agenciabrasil.ebc.com.br",
        "agenciagov.ebc.com.br",
        "gov.br/saude",
        "fiocruz.br",
        "paho.org",
        "who.int",
    ]
    ordered = [domain for domain in preferred if domain in allowed_domains]
    ordered.extend(domain for domain in allowed_domains if domain not in ordered)
    return ordered


def _chat_news_candidates() -> list[dict[str, str | None]]:
    return [
        {
            "title": "CNN: casos de SRAG crescem em todos os estados",
            "url": (
                "https://www.cnnbrasil.com.br/saude/"
                "casos-de-sindrome-respiratoria-aguda-grave-crescem-em-todos-os-estados/"
            ),
            "published_at": None,
            "snippet": "Notícia sobre crescimento de casos de SRAG no Brasil.",
        },
        {
            "title": "Folha: Brasil registra aumento de SRAG segundo Fiocruz",
            "url": (
                "https://www1.folha.uol.com.br/equilibrioesaude/2025/04/"
                "brasil-registra-aumento-de-sindrome-respiratoria-grave-em-quase-"
                "todas-as-regioes-diz-fiocruz.shtml"
            ),
            "published_at": "2025-04-10",
            "snippet": "Notícia sobre crescimento de SRAG em regiões brasileiras.",
        },
        {
            "title": "Pesquisa Fapesp: a dimensão da pandemia",
            "url": "https://revistapesquisa.fapesp.br/a-dimensao-da-pandemia/",
            "published_at": None,
            "snippet": "Artigo sobre bases de vigilância e SRAG no contexto da pandemia.",
        },
    ]


def _external_news_search_query(question: str) -> str:
    normalized = question.casefold()
    terms = ["SRAG", "síndrome respiratória aguda grave", "notícia", "saúde", "Brasil"]
    if "beb" in normalized or "criança" in normalized or "crianca" in normalized:
        terms.extend(["bebês", "crianças"])
    if "uti" in normalized or "leito" in normalized:
        terms.extend(["UTI", "leitos"])
    if "vacina" in normalized:
        terms.append("vacinação")
    return " ".join(terms)


def _is_news_like_article(article: Any) -> bool:
    domain = str(getattr(article, "source_domain", "")).casefold()
    url = str(getattr(article, "url", "")).casefold()
    title = str(getattr(article, "title", "")).casefold()
    path = url.split("?", 1)[0]
    non_news_domains = [
        "dadosabertos.saude.gov.br",
        "gitlab.com",
        "github.com",
        "infoms.saude.gov.br",
    ]
    if any(domain.endswith(item) or item in url for item in non_news_domains):
        return False
    non_news_titles = [
        "portal de dados abertos",
        "busca institucional",
        "busca |",
        "resultados de busca",
        "organização pan-americana da saúde",
        "opas/oms",
        "painel",
    ]
    if any(term in title for term in non_news_titles):
        return False
    non_news_url_terms = ["/busca", "/search", "search_api", "searchabletext"]
    if any(term in url for term in non_news_url_terms):
        return False
    news_url_terms = [
        "/noticia",
        "/noticias",
        "/news",
        "/saude/",
        "/ciencia/",
        "/pesquisa/",
        "/materia/",
    ]
    article_domains = [
        "revistapesquisa.fapesp.br",
        "cienciahoje.org.br",
        "sbmt.org.br",
    ]
    has_date = _extract_sortable_date(str(getattr(article, "published_at", "") or ""))
    has_article_domain = any(domain.endswith(item) for item in article_domains)
    return bool(has_date or has_article_domain or any(term in path for term in news_url_terms))


def _dedupe_articles_by_domain(articles: list[Any]) -> list[Any]:
    selected: list[Any] = []
    seen: set[str] = set()
    for article in articles:
        domain = str(getattr(article, "source_domain", "")).removeprefix("www.")
        if domain in seen:
            continue
        seen.add(domain)
        selected.append(article)
    return selected


def _article_sort_key(article: Any) -> tuple[int, str]:
    parsed = _extract_sortable_date(article.published_at) or _extract_sortable_date(article.excerpt)
    if parsed:
        return (0, parsed)
    return (1, "9999-99-99")


def _extract_sortable_date(text: str | None) -> str | None:
    if not text:
        return None
    iso_match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})", text)
    if iso_match:
        return iso_match.group(0)
    br_match = re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\b", text)
    if br_match:
        day, month, year = br_match.groups()
        return f"{year}-{month}-{day}"
    return None


# ==============================================================================
# STREAMLIT PAGE RENDERING
# ==============================================================================

def render_about_page() -> None:
    st.title("ℹ️ Sobre a Plataforma")
    st.caption("Visão geral da arquitetura, dados do OpenDataSUS e documentação técnica.")
    readme = read_text(PROJECT_ROOT / "README.md")
    with st.container(height=800):
        st.markdown(readme)


def execute_pipeline_with_progress(run_id: str, raw_file: Path | None) -> str:
    settings = load_settings()
    artifacts_root = resolve_project_path(settings.paths.artifacts_dir)
    started = time.perf_counter()

    steps = [
        "Preparar fonte de dados",
        "Executar ingestão",
        "Executar pré-processamento",
        "Gerar manifesto e hashes",
        "Executar agente LangGraph e subagentes Agent Reach",
        "Persistir observabilidade",
        "Exportar PDF",
        "Indexar contexto no vector database",
    ]
    progress = st.progress(0, text="Aguardando início")
    status_box = st.container()

    def mark(index: int, message: str) -> None:
        progress.progress(index / len(steps), text=message)
        status_box.write(f"✅ {message}")

    with st.spinner("Executando pipeline completa com subagentes e RAG..."):
        if raw_file:
            raw_path = resolve_project_path(raw_file)
            if not raw_path.is_file():
                raise FileNotFoundError(f"Raw file not found: {raw_path}")
            current_run_id = run_id
            selected_folder = "local-raw-file"
            raw_hash = calculate_sha256(raw_path)
        else:
            ingestion = run_ingestion(run_id=run_id, settings=settings)
            current_run_id = ingestion.run_id
            raw_path = ingestion.raw_file_path
            selected_folder = ingestion.selected_folder
            raw_hash = ingestion.raw_file_hash
        mark(1, f"Fonte preparada: {raw_path.name}")

        extra_raw_files = _ensure_historical_raw_files(
            raw_path,
            [str(url) for url in settings.opendatasus.historical_csv_urls],
        )
        mark(2, f"Ingestão concluída: {len(extra_raw_files)} arquivo(s) histórico(s)")

        preprocessing = run_preprocessing(
            raw_path,
            current_run_id,
            extra_raw_files=extra_raw_files,
            settings=settings,
        )
        mark(3, f"Pré-processamento: {preprocessing.rows_refined:,} linhas refinadas")

        run_dir = ensure_directory(artifacts_root / current_run_id)
        manifest = build_execution_manifest(
            run_id=current_run_id,
            selected_folder=selected_folder,
            source_file=raw_path,
            raw_file_hash=raw_hash,
            refined_file=preprocessing.parquet_path,
            rows_raw=preprocessing.rows_raw,
            rows_refined=preprocessing.rows_refined,
        )
        write_execution_manifest(manifest, artifacts_dir=artifacts_root)
        mark(4, "Manifesto, hash bruto e hash refinado registrados")

        state = run_agent_graph(
            user_request="Gerar relatorio SRAG com metricas, graficos, fontes e limitacoes",
            run_id=current_run_id,
            refined_dir=resolve_project_path(settings.paths.refined_dir),
            artifacts_dir=artifacts_root,
            news_candidates=_allowlist_source_candidates(),
        )
        (run_dir / "news_sources.json").write_text(
            json.dumps(state.get("news_evidence", []), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        mark(5, "Subagentes Agent Reach executaram coleta oficial, social e de mídia")

        observability = dict(state.get("observability", {}))
        observability.update(
            {
                "generated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
                "pipeline_latency_ms": int((time.perf_counter() - started) * 1000),
                "rows_raw": preprocessing.rows_raw,
                "rows_refined": preprocessing.rows_refined,
                "historical_raw_files_count": len(extra_raw_files),
                "historical_raw_files": [str(path) for path in extra_raw_files],
            }
        )
        (run_dir / "observability.json").write_text(
            json.dumps(observability, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        mark(6, "Observabilidade, tokens, custos USD/BRL e latência registrados")

        report_path = Path(state["final_report_path"])
        export_report_pdf(report_path, run_dir / "report.pdf")
        mark(7, "Relatório oficial PDF exportado")

        index_project_context(
            run_id=current_run_id,
            persist_dir=PROJECT_ROOT / "artifacts" / "vector_store" / current_run_id,
        )
        st.session_state[RUN_STATE_KEY] = current_run_id
        mark(8, "ChromaDB e índice lexical atualizados com todos os artefatos da run")

    progress.progress(1.0, text="Pipeline concluída com sucesso!")
    return current_run_id


def render_pipeline_page(artifacts_dir: Path) -> None:
    st.title("🚀 Pipeline & Execução")
    st.caption("Dispare novas execuções da esteira epidemiológica e acompanhe o fluxo de ponta a ponta.")

    default_raw = default_raw_file()
    col_a, col_b = st.columns([2, 1])
    with col_a:
        run_id = st.text_input(
            "Run ID",
            value=f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        )
        raw_file_text = st.text_input(
            "CSV bruto local (opcional)",
            value=str(default_raw) if default_raw else "",
            help="Se vazio, o app executa a ingestão configurada do OpenDataSUS.",
        )
    with col_b:
        st.metric("Total de Runs Gravadas", len(list_run_ids(artifacts_dir)))
        st.metric("Arquivo Local Padrão", default_raw.name if default_raw else "Nenhum")

    if st.button("Executar Pipeline Completa", type="primary"):
        raw_file = Path(raw_file_text) if raw_file_text.strip() else None
        try:
            completed_run = execute_pipeline_with_progress(run_id.strip(), raw_file)
            st.success(f"Execução concluída com sucesso: `{completed_run}`")
        except Exception as exc:
            st.error(f"Falha na execução: {exc}")

    st.divider()
    st.subheader("Arquitetura e Fluxo do Grafo LangGraph")
    render_pdf(PROJECT_ROOT / "docs" / "architecture_diagram.pdf", height=650)


def render_reports_page(artifacts_dir: Path) -> None:
    st.title("📑 Suíte de Relatórios & Artefatos de Inteligência")
    run_id = selected_run_id(artifacts_dir)
    if not run_id:
        st.info("Nenhuma execução disponível. Execute uma pipeline primeiro.")
        return
    paths = artifact_paths(run_id, artifacts_dir)

    st.caption(f"Visualizando artefatos gerados na execução: `{run_id}`")

    tab_pdf, tab_exec, tab_deep, tab_alerts, tab_media, tab_gov, tab_full, tab_qual = st.tabs(
        [
            "📄 Relatório Oficial (PDF)",
            "📊 Boletim Executivo",
            "🧬 Parecer Epidemiológico",
            "⚠️ Alertas & Anomalias (Z-Score)",
            "🌐 Mídia & Social (Agent Reach)",
            "🛡️ Governança de Dados",
            "📝 Relatório Consolidado (MD)",
            "🔍 Diagnóstico de Qualidade",
        ]
    )

    with tab_pdf:
        if paths["report_pdf"].is_file():
            st.download_button(
                "📥 Baixar Relatório PDF",
                data=paths["report_pdf"].read_bytes(),
                file_name=f"relatorio_srag_{run_id}.pdf",
                mime="application/pdf",
            )
            render_pdf(paths["report_pdf"], height=850)
        else:
            st.warning("PDF ainda não gerado nesta execução.")

    with tab_exec:
        if paths["executive_bulletin"].is_file():
            st.markdown(paths["executive_bulletin"].read_text(encoding="utf-8"))
        else:
            st.info("Boletim executivo ainda não gerado nesta run.")

    with tab_deep:
        if paths["epidemiological_deepdive"].is_file():
            st.markdown(paths["epidemiological_deepdive"].read_text(encoding="utf-8"))
        else:
            st.info("Parecer epidemiológico aprofundado ainda não gerado.")

    with tab_alerts:
        if paths["anomaly_alerts"].is_file():
            st.markdown(paths["anomaly_alerts"].read_text(encoding="utf-8"))
        else:
            st.info("Boletim de anomalias ainda não gerado.")

    with tab_media:
        if paths["media_and_social_signals"].is_file():
            st.markdown(paths["media_and_social_signals"].read_text(encoding="utf-8"))
        else:
            st.info("Inteligência de mídia ainda não gerada.")

    with tab_gov:
        if paths["data_governance_report"].is_file():
            st.markdown(paths["data_governance_report"].read_text(encoding="utf-8"))
        else:
            st.info("Relatório de governança ainda não gerado.")

    with tab_full:
        if paths["report_md"].is_file():
            st.markdown(paths["report_md"].read_text(encoding="utf-8"))
        else:
            st.info("Relatório consolidado markdown ainda não gerado.")

    with tab_qual:
        if paths["quality"].is_file():
            qual = read_json(paths["quality"])
            st.json(qual)
        else:
            st.info("Relatório de qualidade ainda não disponível.")


def render_chat_page(artifacts_dir: Path) -> None:
    st.title("💬 Chat com RAG Híbrido (ChromaDB + BM25)")
    run_id = selected_run_id(artifacts_dir)
    if not run_id:
        st.info("Nenhuma execução disponível. Rode uma pipeline primeiro.")
        return
    paths = artifact_paths(run_id, artifacts_dir)

    st.caption(
        f"Consulte interativamente todos os artefatos, patógenos, alertas de Z-score, faixas etárias, "
        f"sinais de redes sociais (Agent Reach) e linhagem de governança da run `{run_id}`."
    )

    top_c1, top_c2 = st.columns([3, 1])
    with top_c2:
        if st.button("🔄 Reindexar ChromaDB para esta run", use_container_width=True):
            index_project_context(
                run_id=run_id,
                persist_dir=PROJECT_ROOT / "artifacts" / "vector_store" / run_id,
            )
            st.success("ChromaDB e BM25 reindexados com sucesso.")
        if st.button("🗑️ Limpar Histórico do Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Large input field for comfortable multi-line prompt typing
    st.markdown("### ✍️ Faça sua Pergunta ao Agente Especialista")
    user_input_area = st.text_area(
        "Digite sua pergunta sobre métricas, patógenos, anomalias, redes sociais, governança ou guardrails:",
        height=110,
        placeholder="Ex: Quais foram os patógenos identificados nesta base e qual o percentual correspondente a COVID-19, Influenza e VSR?",
        key="chat_text_area_input",
    )

    submitted = st.button("🚀 Enviar Pergunta", type="primary", use_container_width=True)

    question_to_process = None
    if submitted and user_input_area.strip():
        question_to_process = user_input_area.strip()

    # Also support streamlit bottom chat_input
    chat_bar = st.chat_input("Ou digite uma pergunta rápida aqui...")
    if chat_bar:
        question_to_process = chat_bar

    if question_to_process:
        with st.spinner("Consultando ChromaDB, BM25 e gerando resposta fundamentada..."):
            answer = answer_chat_question(question_to_process, run_id, paths)
            st.session_state.chat_history.append(
                {
                    "user": question_to_process,
                    "assistant": answer,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
            )

    st.divider()
    st.subheader("📜 Histórico de Interações (Mais Recentes Primeiro)")

    if not st.session_state.chat_history:
        st.info("Nenhuma pergunta enviada ainda nesta sessão. Digite uma pergunta acima para iniciar.")
    else:
        # Render in REVERSE order (most recent first)
        for msg in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🧑‍💻 Usuário ({msg.get('timestamp', '')}):**")
                st.info(msg["user"])
                st.markdown(f"**🤖 Agente SRAG DataSUS:**")
                st.markdown(msg["assistant"])
                st.markdown("---")


def render_observability_page(artifacts_dir: Path) -> None:
    st.title("📊 Observabilidade & EVALs")
    run_id = selected_run_id(artifacts_dir)
    if not run_id:
        st.info("Nenhuma execução disponível.")
        return
    paths = artifact_paths(run_id, artifacts_dir)
    metrics = read_json(paths["metrics"])
    quality = read_json(paths["quality"])
    observability = read_json(paths["observability"])
    news = read_json(paths["news"])
    chart_context = read_json(paths["chart_context"])
    trace_lines = (
        paths["trace"].read_text(encoding="utf-8").splitlines()
        if paths["trace"].is_file()
        else []
    )

    if not isinstance(metrics, dict):
        metrics = {}
    if not isinstance(quality, dict):
        quality = {}
    if not isinstance(observability, dict):
        observability = {}
    if not isinstance(chart_context, dict):
        chart_context = {}

    st.subheader(f"Painel Operacional & Contabilidade Financeira — Run: `{run_id}`")

    c1, c2, c3, c4, c5 = st.columns(5)
    total_tok = int(observability.get("total_tokens", 0))
    prompt_tok = int(observability.get("prompt_tokens", 0))
    comp_tok = int(observability.get("completion_tokens", 0))
    cost_usd = float(observability.get("estimated_cost_usd", (total_tok / 1000) * 0.00015))
    cost_brl = cost_usd * 5.75

    c1.metric("Tokens Totais", f"{total_tok:,}")
    c2.metric("Prompt Tokens", f"{prompt_tok:,}")
    c3.metric("Completion Tokens", f"{comp_tok:,}")
    c4.metric("Custo Estimado (USD)", f"${cost_usd:.4f}")
    c5.metric("Custo Estimado (BRL)", f"R${cost_brl:.4f}")

    st.subheader("Métricas Epidemiológicas Calculadas")
    m1, m2, m3, m4 = st.columns(4)
    growth = metrics.get("growth_rate_7d", {}).get("value")
    mortality = metrics.get("mortality_rate_known", {}).get("value")
    icu = metrics.get("icu_rate", {}).get("value")
    vaccine = metrics.get("vaccination_rate", {}).get("value")

    m1.metric("Variação em 7d", f"{growth:.2%}" if isinstance(growth, float) else "n/d")
    m2.metric("Mortalidade Conhecida", f"{mortality:.2%}" if isinstance(mortality, float) else "n/d")
    m3.metric("Passagem por UTI (Proxy)", f"{icu:.2%}" if isinstance(icu, float) else "n/d")
    m4.metric("Vacinação Registrada (Proxy)", f"{vaccine:.2%}" if isinstance(vaccine, float) else "n/d")

    st.subheader("Qualidade dos Dados, Fontes e Auditoria")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Linhas Brutas Ingeridas", f"{int(quality.get('rows_raw', 0)):,}")
    q2.metric("Linhas Refinadas (Parquet)", f"{int(quality.get('rows_refined', 0)):,}")
    q3.metric("Fontes Coletadas (Agent Reach)", len(news) if isinstance(news, list) else 0)
    q4.metric("Nós Executados no Trace", len(trace_lines))

    st.subheader("Sequência de Execução do Grafo LangGraph (Traces Auditáveis)")
    if trace_lines:
        trace = [json.loads(line) for line in trace_lines]
        trace_df = pd.DataFrame(
            [
                {
                    "Nó": item.get("node"),
                    "Tool / Subagente": item.get("tool") or "n/a",
                    "Status": item.get("status"),
                }
                for item in trace
            ]
        )
        st.dataframe(trace_df, use_container_width=True, hide_index=True)
    else:
        st.info("Trace ainda não disponível.")


def main() -> None:
    st.set_page_config(
        page_title="DataSUS Epidemiological Intelligence & RAG Agent",
        page_icon="🏥",
        layout="wide",
    )
    settings = load_settings()
    artifacts_dir = resolve_project_path(settings.paths.artifacts_dir)

    st.sidebar.title("🏥 Menu Principal")
    page = st.sidebar.radio(
        "Navegue pelas funcionalidades:",
        [
            "ℹ️ Sobre o Projeto",
            "🚀 Pipeline & Execução",
            "📑 Suíte de Relatórios & Artefatos",
            "💬 Chat com RAG Híbrido",
            "📊 Observabilidade & EVALs",
        ],
    )

    if page == "ℹ️ Sobre o Projeto":
        render_about_page()
    elif page == "🚀 Pipeline & Execução":
        render_pipeline_page(artifacts_dir)
    elif page == "📑 Suíte de Relatórios & Artefatos":
        render_reports_page(artifacts_dir)
    elif page == "💬 Chat com RAG Híbrido":
        render_chat_page(artifacts_dir)
    else:
        render_observability_page(artifacts_dir)


if __name__ == "__main__":
    main()
