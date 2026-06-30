import json
import os
import re
import time
from typing import Any

import requests  # type: ignore[import-untyped]
from dotenv import load_dotenv


def generate_executive_report_sections(
    *,
    metric_summary: dict[str, Any],
    chart_context: dict[str, Any],
    news_evidence: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    load_dotenv()
    model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    disable_api = os.getenv("DISABLE_LLM_API") == "1"
    nvidia_key = None if disable_api else os.getenv("NVIDIA_API_KEY")
    openai_key = None if disable_api else os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    api_key = nvidia_key or openai_key
    provider = "nvidia_openai_compatible" if nvidia_key else "openai_chat_completions"
    if not api_key:
        provider = "local_deterministic"
    endpoint = (
        "https://integrate.api.nvidia.com/v1/chat/completions"
        if nvidia_key
        else "https://api.openai.com/v1/chat/completions"
    )

    prompt = _build_prompt(metric_summary, chart_context, news_evidence)
    observability = _base_observability(provider, model)

    if not api_key:
        sections = _fallback_sections(metric_summary, chart_context, news_evidence)
        return _finish_local(started, prompt, sections, observability, "local_no_api_key")

    try:
        response = _post_chat_completion(endpoint, api_key, model, prompt)
        response.raise_for_status()
        payload = response.json()
        content = str(payload["choices"][0]["message"]["content"]).strip()
        sections = _parse_sections(content, metric_summary, chart_context, news_evidence)
        usage = payload.get("usage", {})
        parse_status = "success" if sections.get("_generated_by_llm") else "parse_fallback"
        sections.pop("_generated_by_llm", None)
        observability.update(
            {
                "status": parse_status,
                "llm_call_count": 1,
                "prompt_tokens": int(usage.get("prompt_tokens", _approx_tokens(prompt))),
                "completion_tokens": int(
                    usage.get("completion_tokens", _approx_tokens(content))
                ),
                "total_tokens": int(usage.get("total_tokens", _approx_tokens(prompt + content))),
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }
        )
        return sections, observability
    except Exception as exc:
        sections = _fallback_sections(metric_summary, chart_context, news_evidence)
        sections, observability = _finish_local(
            started,
            prompt,
            sections,
            observability,
            "local_after_api_error",
        )
        observability["error_type"] = type(exc).__name__
        return sections, observability


def _build_prompt(
    metric_summary: dict[str, Any],
    chart_context: dict[str, Any],
    news_evidence: list[dict[str, Any]],
) -> str:
    compact_sources = [
        {
            "title": source.get("title"),
            "published_at": source.get("published_at"),
            "domain": source.get("source_domain"),
            "url": source.get("url"),
            "status": source.get("extraction_status"),
            "snippet": source.get("snippet"),
            "excerpt": str(source.get("excerpt", ""))[:700],
        }
        for source in _news_sources_for_prompt(news_evidence)
    ]
    compact_metrics = {
        "reference_date": metric_summary.get("reference_date"),
        "total_cases": metric_summary.get("total_cases"),
        "case_growth_rate_7d": _compact_metric(metric_summary, "case_growth_rate_7d"),
        "known_mortality_rate": _compact_metric(metric_summary, "known_mortality_rate"),
        "crude_mortality_rate": _compact_metric(metric_summary, "crude_mortality_rate"),
        "icu_case_rate": _compact_metric(metric_summary, "icu_case_rate"),
        "registered_vaccination_case_rate": _compact_metric(
            metric_summary,
            "registered_vaccination_case_rate",
        ),
    }
    chart_1 = json.dumps(chart_context.get("daily_cases_30d", {}), ensure_ascii=False)
    chart_2 = json.dumps(chart_context.get("monthly_cases_12m", {}), ensure_ascii=False)
    return (
        "Voce e um analista executivo de saude. Escreva um relatorio executivo "
        "sobre SRAG em portugues do Brasil, usando somente os dados abaixo. "
        "Retorne APENAS JSON valido com as chaves metrics_section, "
        "historical_chart_1_section, historical_chart_2_section, news_section e "
        "used_source_urls. Cada campo textual deve ter no maximo 900 caracteres. "
        "metrics_section: um paragrafo sobre taxa de aumento de casos, taxa de "
        "mortalidade, taxa de ocupacao de UTI e taxa de vacinacao. Esse paragrafo "
        "deve conter literalmente os termos taxa de aumento, crescimento, "
        "mortalidade conhecida, mortalidade bruta, UTI e vacinacao. Nao inclua "
        "calculos no formato numerador/denominador ou expressoes entre parenteses "
        "com numerador e denominador. "
        "historical_chart_1_section: um paragrafo comentando somente o grafico "
        "diario de 30 dias. historical_chart_2_section: um paragrafo comentando "
        "somente o grafico mensal de 12 meses. "
        "news_section: escolha as 3 fontes mais recentes entre as fontes extraidas "
        "e escreva exatamente 3 paragrafos em tom jornalistico de reportagem. "
        "Cada paragrafo deve trazer o titulo da noticia, a data publicada quando "
        "disponivel, um breve resumo do fato e um breve comentario analitico sobre "
        "impacto para a leitura de SRAG. Nao use numeracao, bullets, listas, nem "
        "prefixos como '1)' ou 'Fonte 1'. Nao faca descricao generica dos sites. "
        "used_source_urls: liste apenas as URLs "
        "efetivamente usadas no comentario de noticias, maximo 5. Nao invente "
        "numeros, datas, fontes, fatos ou URLs.\n"
        f"METRICAS={json.dumps(compact_metrics, ensure_ascii=False)}\n"
        f"GRAFICO_1_DIARIO={chart_1}\n"
        f"GRAFICO_2_MENSAL={chart_2}\n"
        f"FONTES_EXTRAIDAS={json.dumps(compact_sources, ensure_ascii=False)}"
    )


def _news_sources_for_prompt(news_evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    usable = [
        source
        for source in news_evidence
        if source.get("url")
        and source.get("extraction_status") in {"success", "metadata_only"}
        and (source.get("excerpt") or source.get("snippet"))
    ]
    return sorted(usable, key=_news_source_prompt_score, reverse=True)[:5]


def _news_source_prompt_score(source: dict[str, Any]) -> int:
    text = " ".join(
        str(source.get(key) or "")
        for key in ["title", "snippet", "excerpt", "source_domain"]
    ).casefold()
    url = str(source.get("url") or "").casefold()
    score = 0
    if source.get("published_at"):
        score += 80
    if "srag" in text or "síndrome respiratória" in text or "sindrome respiratoria" in text:
        score += 70
    if any(domain in url for domain in ["gov.br/saude", "agenciabrasil.ebc.com.br"]):
        score += 30
    if any(fragment in url for fragment in ["/noticia/", "/noticias/"]):
        score += 30
    if "search" in url or "busca" in url:
        score -= 80
    if url.rstrip("/").count("/") <= 2:
        score -= 60
    return score


def _post_chat_completion(
    endpoint: str,
    api_key: str,
    model: str,
    prompt: str,
) -> requests.Response:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Retorne somente JSON valido. Escreva em portugues do Brasil. "
                    "Nao use markdown fora dos campos JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1600,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_response: requests.Response | None = None
    for attempt in range(3):
        response = requests.post(endpoint, headers=headers, json=payload, timeout=180)
        last_response = response
        if response.status_code < 500:
            return response
        time.sleep(2**attempt)
    assert last_response is not None
    return last_response


def _parse_sections(
    content: str,
    metric_summary: dict[str, Any],
    chart_context: dict[str, Any],
    news_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        parsed = json.loads(_extract_json_object(_strip_json_fence(content)))
    except json.JSONDecodeError:
        return _fallback_sections(metric_summary, chart_context, news_evidence)
    required = [
        "metrics_section",
        "historical_chart_1_section",
        "historical_chart_2_section",
        "news_section",
        "used_source_urls",
    ]
    if not all(key in parsed for key in required):
        return _fallback_sections(metric_summary, chart_context, news_evidence)
    for text_key in required[:-1]:
        parsed[text_key] = _clean_model_text(str(parsed.get(text_key, "")))
    parsed["metrics_section"] = _remove_ratio_parentheticals(str(parsed["metrics_section"]))
    parsed["news_section"] = _normalize_news_paragraphs(str(parsed["news_section"]))
    parsed["used_source_urls"] = [
        str(url) for url in parsed.get("used_source_urls", []) if isinstance(url, str)
    ][:5]
    if not parsed["used_source_urls"]:
        parsed["used_source_urls"] = [str(source.get("url")) for source in news_evidence[:5]]
    parsed["_generated_by_llm"] = True
    return parsed


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.removeprefix("json").strip()
    return stripped


def _extract_json_object(content: str) -> str:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return content
    return content[start : end + 1]


def _clean_model_text(text: str) -> str:
    cleaned = (
        text.replace("comèµ·ç‚¹ de", "com valor inicial de")
        .replace("comèµ·ç‚¹", "com valor inicial")
        .strip()
    )
    return re.sub(r"(?m)^\s*(?:\d+[\).:-]\s*|[-*]\s+)", "", cleaned).strip()


def _remove_ratio_parentheticals(text: str) -> str:
    return re.sub(r"\s*\([^)]*\d[\d.]*\s*/\s*\d[\d.]*[^)]*\)", "", text).strip()


def _normalize_news_paragraphs(text: str) -> str:
    cleaned = _clean_model_text(text)
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n{2,}", cleaned)
        if paragraph.strip()
    ]
    if len(paragraphs) >= 3:
        return "\n\n".join(paragraphs[:3])
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", cleaned)
    grouped = [sentence.strip() for sentence in sentences if sentence.strip()]
    if len(grouped) >= 3:
        return "\n\n".join(grouped[:3])
    return cleaned


def _fallback_sections(
    metric_summary: dict[str, Any],
    chart_context: dict[str, Any],
    news_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    growth = _metric_value(metric_summary, "case_growth_rate_7d")
    known_mortality = _metric_value(metric_summary, "known_mortality_rate")
    crude_mortality = _metric_value(metric_summary, "crude_mortality_rate")
    icu = _metric_value(metric_summary, "icu_case_rate")
    vaccination = _metric_value(metric_summary, "registered_vaccination_case_rate")
    daily = chart_context.get("daily_cases_30d", {})
    monthly = chart_context.get("monthly_cases_12m", {})
    used_sources = _news_sources_for_prompt(news_evidence)
    return {
        "metrics_section": (
            "As metricas principais indicam taxa de aumento de casos e crescimento "
            f"recente de {_format_rate(growth)}, mortalidade conhecida de "
            f"{_format_rate(known_mortality)} e mortalidade bruta de "
            f"{_format_rate(crude_mortality)}. A taxa de ocupacao/uso de UTI "
            f"em casos de SRAG ficou em {_format_rate(icu)}, enquanto a taxa de "
            f"vacinacao registrada na populacao com SRAG ficou em {_format_rate(vaccination)}."
        ),
        "historical_chart_1_section": (
            "No grafico diario de 30 dias, a serie vai de "
            f"{daily.get('start')} a {daily.get('end')}, com pico de "
            f"{daily.get('peak_value')} casos em {daily.get('peak_date')} e "
            f"valor final de {daily.get('last_value')} casos."
        ),
        "historical_chart_2_section": (
            "No grafico mensal de 12 meses, a janela vai de "
            f"{monthly.get('start')} a {monthly.get('end')}, com pico em "
            f"{monthly.get('peak_month')} ({monthly.get('peak_value')} casos) "
            f"e fechamento em {monthly.get('last_value')} casos."
        ),
        "news_section": _fallback_news_section(used_sources),
        "used_source_urls": [str(source.get("url")) for source in used_sources[:5]],
    }


def _fallback_news_section(news_sources: list[dict[str, Any]]) -> str:
    if not news_sources:
        return (
            "Nao houve noticias recentes extraidas com conteudo suficiente nas fontes "
            "allowlisted para comentario executivo."
        )
    paragraphs = []
    for source in news_sources[:3]:
        title = source.get("title") or "Fonte consultada"
        date = _format_source_date(source.get("published_at"))
        snippet = source.get("snippet") or source.get("excerpt") or ""
        paragraphs.append(
            f"{title}, publicada em {date}, coloca a SRAG no centro da agenda "
            f"recente ao registrar que {str(snippet)[:220]}. A leitura executiva "
            "e que esse fato ajuda a dimensionar vigilancia, leitos e vacinacao "
            "com olhar de resposta publica."
        )
    return "\n\n".join(paragraphs)


def _base_observability(provider: str, model: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "llm_call_count": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "latency_ms": 0,
        "status": "not_started",
    }


def _compact_metric(metric_summary: dict[str, Any], key: str) -> dict[str, Any]:
    metric = metric_summary.get(key, {})
    value = metric.get("value")
    return {
        "name": metric.get("name"),
        "value": value,
        "formatted_percent": _format_rate(float(value)) if isinstance(value, int | float) else None,
        "numerator": metric.get("numerator"),
        "denominator": metric.get("denominator"),
        "limitations": metric.get("limitations", []),
    }


def _finish_local(
    started: float,
    prompt: str,
    sections: dict[str, Any],
    observability: dict[str, Any],
    status: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    completion_text = json.dumps(sections, ensure_ascii=False)
    prompt_tokens = _approx_tokens(prompt)
    completion_tokens = _approx_tokens(completion_text)
    observability.update(
        {
            "status": status,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }
    )
    return sections, observability


def _metric_value(metric_summary: dict[str, Any], key: str) -> float | None:
    value = metric_summary.get(key, {}).get("value")
    return float(value) if isinstance(value, int | float) else None


def _format_rate(value: float | None) -> str:
    return "indisponivel" if value is None else f"{value:.2%}"


def _format_source_date(value: Any) -> str:
    if not value:
        return "data nao informada"
    text = str(value)
    return text[:10] if len(text) >= 10 else text


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)
