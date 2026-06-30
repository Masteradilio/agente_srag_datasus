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
    if not artifacts_dir.is_dir():
        return []
    return sorted(
        [path.name for path in artifacts_dir.iterdir() if path.is_dir()],
        reverse=True,
    )


def read_json(path: Path) -> dict[str, Any] | list[Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


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
    }


def default_raw_file() -> Path | None:
    candidates = sorted((PROJECT_ROOT / "data" / "landing").glob("**/INFLUD26-*.csv"))
    return candidates[-1] if candidates else None


def render_pdf(path: Path, height: int = 780) -> None:
    if not path.is_file():
        st.info(f"Arquivo não encontrado: {path.name}")
        return
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    st.markdown(
        (
            f'<iframe src="data:application/pdf;base64,{encoded}" '
            f'width="100%" height="{height}" type="application/pdf"></iframe>'
        ),
        unsafe_allow_html=True,
    )


def render_about_page() -> None:
    st.title("Sobre")
    st.caption("README.md completo do projeto")
    readme = read_text(PROJECT_ROOT / "README.md")
    with st.container(height=760):
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
        "Executar agente LangGraph e tools",
        "Persistir observabilidade",
        "Exportar PDF",
        "Indexar contexto no vector database",
    ]
    progress = st.progress(0, text="Aguardando início")
    status_box = st.container()

    def mark(index: int, message: str) -> None:
        progress.progress(index / len(steps), text=message)
        status_box.write(f"✅ {message}")

    with st.spinner("Executando pipeline completo..."):
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
        mark(5, "Agente executou métricas, gráficos, notícias, RAG e validação")

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
        mark(6, "Observabilidade, tokens, latência e modelo registrados")

        report_path = Path(state["final_report_path"])
        export_report_pdf(report_path, run_dir / "report.pdf")
        mark(7, "PDF exportado")

        index_project_context(
            run_id=current_run_id,
            persist_dir=PROJECT_ROOT / "artifacts" / "vector_store" / current_run_id,
        )
        st.session_state[RUN_STATE_KEY] = current_run_id
        mark(8, "Vector database atualizado com relatório e fontes do run")

    progress.progress(1.0, text="Pipeline concluído")
    return current_run_id


def render_pipeline_page(artifacts_dir: Path) -> None:
    st.title("Pipeline e Arquitetura")
    st.caption("Execute a pipeline completa e acompanhe cada etapa do backend.")

    default_raw = default_raw_file()
    col_a, col_b = st.columns([2, 1])
    with col_a:
        run_id = st.text_input(
            "Run ID",
            value=f"streamlit-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        )
        raw_file_text = st.text_input(
            "CSV bruto local opcional",
            value=str(default_raw) if default_raw else "",
            help="Se vazio, o app executa a ingestão configurada.",
        )
    with col_b:
        st.metric("Runs disponíveis", len(list_run_ids(artifacts_dir)))
        st.metric("Fonte padrão", default_raw.name if default_raw else "ingestão remota")

    if st.button("Iniciar pipeline completa", type="primary"):
        raw_file = Path(raw_file_text) if raw_file_text.strip() else None
        try:
            completed_run = execute_pipeline_with_progress(run_id.strip(), raw_file)
            st.success(f"Pipeline concluída: {completed_run}")
        except Exception as exc:
            st.error(f"Falha na pipeline: {exc}")

    st.divider()
    st.subheader("Diagrama conceitual da arquitetura")
    render_pdf(PROJECT_ROOT / "docs" / "architecture_diagram.pdf", height=680)


def selected_run_id(artifacts_dir: Path) -> str | None:
    run_ids = list_run_ids(artifacts_dir)
    if not run_ids:
        return None
    current = st.session_state.get(RUN_STATE_KEY)
    index = run_ids.index(current) if current in run_ids else 0
    return st.sidebar.selectbox("Run para visualização", run_ids, index=index)


def answer_chat_question(question: str, run_id: str, paths: dict[str, Path]) -> str:
    guard = validate_input_request(question, allow_contextual_chat=True)
    if not guard.allowed:
        return "Pedido bloqueado pelos guardrails: " + "; ".join(guard.reasons)

    metrics = read_json(paths["metrics"])
    quality = read_json(paths["quality"])
    news = read_json(paths["news"])
    chart_context = read_json(paths["chart_context"])
    report_text = read_text(paths["report_md"])
    privacy_payloads = [
        metrics if isinstance(metrics, dict) else {},
        quality if isinstance(quality, dict) else {},
    ]
    for payload in privacy_payloads:
        enforce_no_sensitive_values(payload)

    persist_dir = PROJECT_ROOT / "artifacts" / "vector_store" / run_id
    retrieved = retrieve_context(question, top_k=3, persist_dir=persist_dir)
    context = "\n\n".join(
        [
            f"[{item.source_path} | score={item.score:.1f}]\n{item.content[:700]}"
            for item in retrieved
        ]
    )
    external_context = _search_external_context_if_requested(question)
    parquet_context = _summarize_refined_parquet_if_needed(question, run_id)

    system_prompt = (
        "Voce e o LLM do chat executivo do agente SRAG DataSUS. Todas as respostas "
        "devem ser geradas por voce a partir dos artefatos e resultados de tools "
        "fornecidos. Responda somente o que foi perguntado, com alto groundedness, "
        "em ate 3 paragrafos curtos. Nao crie tabelas, titulos, secoes, contexto de "
        "noticias, observacoes de qualidade ou limitacoes, exceto se o usuario pedir "
        "explicitamente. Cite numeros e datas quando disponiveis. Se a informacao nao "
        "estiver nos dados, diga isso objetivamente. Quando "
        "RESULTADO_TOOL_BUSCA_ALLOWLIST.executed=true, trate esse bloco como resultado "
        "de tool de pesquisa externa em fontes permitidas e use os links/datas dali "
        "para responder; nesse caso, nao diga que a busca externa nao foi executada. "
        "Se ordering=oldest_first, resuma os primeiros resultados como os mais antigos "
        "encontrados pela tool. Sempre que usar uma noticia na resposta, finalize com "
        "uma secao chamada exatamente 'Fontes Consultadas:' e liste as URLs das noticias "
        "usadas. Essa secao e obrigatoria: se o espaco parecer curto, reduza os "
        "comentarios, mas nunca omita as fontes. Nao exponha dados individuais e nao "
        "recomende tratamento individual."
    )
    user_prompt = (
        f"PERGUNTA_DO_USUARIO={question}\n\n"
        f"METRICAS={json.dumps(metrics, ensure_ascii=False)[:1600]}\n\n"
        f"CHART_CONTEXT={json.dumps(chart_context, ensure_ascii=False)[:1200]}\n\n"
        f"QUALIDADE={json.dumps(quality, ensure_ascii=False)[:700]}\n\n"
        f"NOTICIAS_DO_RELATORIO={json.dumps(news, ensure_ascii=False)[:1000]}\n\n"
        f"DADOS_PARQUET={parquet_context[:1000]}\n\n"
        f"RESULTADO_TOOL_BUSCA_ALLOWLIST={external_context[:1800]}\n\n"
        f"RELATORIO={report_text[:1800]}\n\n"
        f"CONTEXTO_RAG={context[:2200]}"
    )
    answer = _call_chat_llm(system_prompt, user_prompt)
    return _guard_chat_answer(answer)


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
        {
            "title": "CNN: SRAG cresce em bebês e acende alerta",
            "url": (
                "https://www.cnnbrasil.com.br/saude/"
                "casos-de-sindrome-respiratoria-crescem-em-bebes-e-acendem-alerta-no-brasil/"
            ),
            "published_at": None,
            "snippet": "Notícia sobre SRAG em crianças menores de dois anos.",
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
        return f"{iso_match.group(1)}-{iso_match.group(2)}-{iso_match.group(3)}"
    br_match = re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\b", text)
    if br_match:
        return f"{br_match.group(3)}-{br_match.group(2)}-{br_match.group(1)}"
    year_match = re.search(r"\b(20\d{2})\b", text)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return None


def _summarize_refined_parquet_if_needed(question: str, run_id: str) -> str:
    normalized = question.casefold()
    parquet_terms = ["parquet", "base", "dados", "coluna", "estado", "cidade"]
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
    for column in ["state", "city", "final_classification"]:
        asks_column = any(term in normalized for term in [column, "estado", "cidade"])
        if column in df.columns and asks_column:
            summary[f"top_{column}"] = df[column].value_counts(dropna=True).head(5).to_dict()
    return json.dumps(summary, ensure_ascii=False)


def _call_chat_llm(system_prompt: str, user_prompt: str) -> str:
    load_dotenv()
    if os.getenv("DISABLE_LLM_API") == "1":
        return _fallback_chat_answer(user_prompt)
    api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        return _fallback_chat_answer(user_prompt)
    endpoint = (
        "https://integrate.api.nvidia.com/v1/chat/completions"
        if os.getenv("NVIDIA_API_KEY")
        else "https://api.openai.com/v1/chat/completions"
    )
    model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    try:
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 1000,
            },
            timeout=45,
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]).strip()
    except Exception:
        return _fallback_chat_answer(user_prompt)


def _fallback_chat_answer(prompt: str) -> str:
    return (
        "Não consegui consultar o LLM nesta execução. Verifique a chave/API do modelo "
        "e tente novamente para que a resposta seja gerada pelo LLM com base nos "
        "artefatos e tools disponíveis."
    )


def _guard_chat_answer(answer: str) -> str:
    blocked_terms = ["cpf", "nu_notific", "dt_nasc", "nome do paciente", "api_key", "system prompt"]
    normalized = answer.casefold()
    if any(term in normalized for term in blocked_terms):
        return (
            "Resposta bloqueada pelos guardrails de saída do chat por risco de "
            "exposição de dado sensível ou instrução interna."
        )
    return answer


def render_report_chat_page(artifacts_dir: Path) -> None:
    st.title("Relatório e Chat")
    run_id = selected_run_id(artifacts_dir)
    if not run_id:
        st.info("Nenhuma execução disponível. Rode a pipeline primeiro.")
        return
    paths = artifact_paths(run_id, artifacts_dir)

    left, right = st.columns([1.05, 0.95])
    with left:
        st.subheader(f"Relatório PDF - {run_id}")
        render_pdf(paths["report_pdf"], height=760)
        if paths["report_pdf"].is_file():
            st.download_button(
                "Baixar PDF",
                data=paths["report_pdf"].read_bytes(),
                file_name=paths["report_pdf"].name,
                mime="application/pdf",
            )
    with right:
        st.subheader("Chat com RAG e guardrails")
        st.caption(
            "O chat usa relatório, fontes, métricas, qualidade dos dados e documentos "
            "indexados no vector database local."
        )
        if st.button("Reindexar contexto deste run"):
            index_project_context(
                run_id=run_id,
                persist_dir=PROJECT_ROOT / "artifacts" / "vector_store" / run_id,
            )
            st.success("Vector database atualizado.")

        question = st.chat_input("Pergunte sobre o relatório, dados, fontes ou metodologia")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if question:
            answer = answer_chat_question(question, run_id, paths)
            st.session_state.chat_history.append(("user", question))
            st.session_state.chat_history.append(("assistant", answer))
        for role, content in st.session_state.chat_history[-8:]:
            with st.chat_message(role):
                st.write(content)


def metric_value(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key, {}).get("value")
    return float(value) if isinstance(value, int | float) else None


def pct(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.2%}"


def render_observability_page(artifacts_dir: Path) -> None:
    st.title("Observbilidade")
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

    st.subheader(f"Run: {run_id}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Linhas refinadas", f"{int(observability.get('rows_refined', 0)):,}")
    c2.metric("Chamadas LLM", observability.get("llm_call_count", 0))
    c3.metric("Tokens totais", f"{int(observability.get('total_tokens', 0)):,}")
    pipeline_seconds = int(observability.get("pipeline_latency_ms", 0)) / 1000
    c4.metric("Latência pipeline", f"{pipeline_seconds:.1f}s")

    st.subheader("Métricas epidemiológicas")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Aumento de casos", pct(metric_value(metrics, "case_growth_rate_7d")))
    m2.metric("Mortalidade conhecida", pct(metric_value(metrics, "known_mortality_rate")))
    m3.metric("Uso de UTI", pct(metric_value(metrics, "icu_case_rate")))
    m4.metric(
        "Vacinação registrada",
        pct(metric_value(metrics, "registered_vaccination_case_rate")),
    )

    st.subheader("História dos dados")
    daily = chart_context.get("daily_cases_30d", {})
    monthly = chart_context.get("monthly_cases_12m", {})
    st.write(
        f"A janela diária analisada vai de {daily.get('start', 'n/d')} a "
        f"{daily.get('end', 'n/d')}, com pico de {daily.get('peak_value', 'n/d')} "
        f"casos em {daily.get('peak_date', 'n/d')}. No recorte mensal, o pico foi "
        f"em {monthly.get('peak_month', 'n/d')} com {monthly.get('peak_value', 'n/d')} casos."
    )
    series = monthly.get("series", {})
    if isinstance(series, dict) and series:
        df_monthly = pd.DataFrame(
            {"mes": list(series.keys()), "casos": list(series.values())}
        ).set_index("mes")
        st.bar_chart(df_monthly)

    st.subheader("Qualidade, fontes e auditoria")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Linhas brutas", f"{int(quality.get('rows_raw', 0)):,}")
    q2.metric("Linhas descartadas", f"{int(quality.get('discarded_rows', 0)):,}")
    q3.metric("Fontes coletadas", len(news) if isinstance(news, list) else 0)
    q4.metric("Eventos no trace", len(trace_lines))

    st.subheader("Execução do agente")
    if trace_lines:
        trace = [json.loads(line) for line in trace_lines]
        trace_df = pd.DataFrame(
            [
                {
                    "no": item.get("node"),
                    "tool": item.get("tool") or "n/a",
                    "status": item.get("status"),
                }
                for item in trace
            ]
        )
        st.dataframe(trace_df, use_container_width=True, hide_index=True)
    else:
        st.info("Trace ainda não disponível.")


def main() -> None:
    st.set_page_config(page_title="Agente SRAG DataSUS", layout="wide")
    settings = load_settings()
    artifacts_dir = resolve_project_path(settings.paths.artifacts_dir)

    page = st.sidebar.radio(
        "Navegação",
        ["Sobre", "Pipeline e Arquitetura", "Relatório e Chat", "Observbilidade"],
    )

    if page == "Sobre":
        render_about_page()
    elif page == "Pipeline e Arquitetura":
        render_pipeline_page(artifacts_dir)
    elif page == "Relatório e Chat":
        render_report_chat_page(artifacts_dir)
    else:
        render_observability_page(artifacts_dir)


if __name__ == "__main__":
    main()
