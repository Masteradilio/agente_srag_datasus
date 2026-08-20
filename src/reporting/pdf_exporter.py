import os
import re
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import markdown  # type: ignore[import-untyped]

from utils.paths import PROJECT_ROOT

FALLBACK_NOTE = "PDF gerado com fallback ReportLab porque WeasyPrint falhou localmente."


def export_report_pdf(markdown_path: Path, output_pdf_path: Path) -> Path:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    html = markdown.markdown(markdown_text, extensions=["tables"])
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    success = _try_weasyprint(html, output_pdf_path)
    if not success:
        fallback_html_path = output_pdf_path.with_suffix(".html")
        fallback_html_path.write_text(_html_document(html), encoding="utf-8")
        _write_reportlab_pdf(markdown_text, output_pdf_path)

    return output_pdf_path


def _try_weasyprint(html: str, output_pdf_path: Path) -> bool:
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            with redirect_stderr(devnull), redirect_stdout(devnull):
                from weasyprint import HTML  # type: ignore[import-untyped]

                HTML(string=html, base_url=str(PROJECT_ROOT.parent)).write_pdf(output_pdf_path)
                return True
    except Exception:
        return False


def _html_document(body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>Relatorio SRAG</title></head><body>"
        f"{body}"
        "</body></html>"
    )


def _write_reportlab_pdf(markdown_text: str, output_pdf_path: Path) -> None:
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import getSampleStyleSheet  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        Image,
        ListFlowable,
        ListItem,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )

    styles = getSampleStyleSheet()
    story = []
    pending_items: list[ListItem] = []

    def flush_list() -> None:
        nonlocal pending_items
        if pending_items:
            story.append(ListFlowable(pending_items, bulletType="bullet"))
            pending_items = []

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush_list()
            story.append(Spacer(1, 8))
            continue

        if stripped.startswith("# "):
            flush_list()
            story.append(Paragraph(stripped[2:], styles["Title"]))
            story.append(Spacer(1, 10))
            continue

        if stripped.startswith("## "):
            flush_list()
            story.append(Paragraph(stripped[3:], styles["Heading2"]))
            story.append(Spacer(1, 8))
            continue

        if stripped.startswith("### "):
            flush_list()
            story.append(Paragraph(stripped[4:], styles["Heading3"]))
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("- "):
            image_match = re.match(r"- !\[.*?\]\((.*?)\)", stripped)
            if image_match:
                flush_list()
                relative_path = image_match.group(1).replace("/", os.sep)
                image_path = (PROJECT_ROOT / relative_path).resolve()
                if not image_path.is_file():
                    alt_path = (output_pdf_path.parent / Path(relative_path).name).resolve()
                    if alt_path.is_file():
                        image_path = alt_path
                if image_path.is_file():
                    story.append(Image(str(image_path), width=460, height=220))
                    story.append(Spacer(1, 8))
                continue

            pending_items.append(ListItem(Paragraph(_escape_xml(stripped[2:]), styles["BodyText"])))
            continue

        flush_list()
        story.append(Paragraph(_escape_xml(stripped), styles["BodyText"]))
        story.append(Spacer(1, 4))

    flush_list()
    doc = SimpleDocTemplate(str(output_pdf_path), pagesize=A4)
    doc.build(story)


def _escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
