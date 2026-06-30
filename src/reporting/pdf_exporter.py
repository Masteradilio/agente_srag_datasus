import re
from pathlib import Path

import markdown  # type: ignore[import-untyped]

from utils.paths import PROJECT_ROOT

FALLBACK_NOTE = "PDF gerado com fallback ReportLab porque WeasyPrint falhou localmente."


def export_report_pdf(markdown_path: Path, output_pdf_path: Path) -> Path:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    html = markdown.markdown(markdown_text, extensions=["tables"])
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from weasyprint import HTML  # type: ignore[import-untyped]

        HTML(string=html, base_url=str(PROJECT_ROOT.parent)).write_pdf(output_pdf_path)
    except Exception:
        fallback_html_path = output_pdf_path.with_suffix(".html")
        fallback_html_path.write_text(_html_document(html), encoding="utf-8")
        _write_reportlab_pdf(markdown_text, output_pdf_path)

    return output_pdf_path


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
            story.append(Paragraph(_clean_markdown(stripped[2:]), styles["Title"]))
            continue
        if stripped.startswith("## "):
            flush_list()
            story.append(Paragraph(_clean_markdown(stripped[3:]), styles["Heading2"]))
            continue
        if stripped.startswith("- "):
            image_path = _extract_image_path(stripped)
            if image_path and image_path.is_file():
                flush_list()
                story.append(Image(str(image_path), width=440, height=190))
                story.append(Spacer(1, 8))
                continue
            text = _clean_markdown(stripped[2:])
            pending_items.append(ListItem(Paragraph(text, styles["BodyText"])))
            continue
        flush_list()
        story.append(Paragraph(_clean_markdown(stripped), styles["BodyText"]))

    flush_list()
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(output_pdf_path), pagesize=A4).build(story)


def _clean_markdown(text: str) -> str:
    cleaned = re.sub(r"`([^`]+)`", r"\1", text)
    cleaned = cleaned.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return cleaned


def _extract_image_path(text: str) -> Path | None:
    match = re.search(r"(agente_srag_datasus/[^\s`]+\.png)", text)
    if not match:
        return None
    return PROJECT_ROOT.parent / Path(match.group(1))


def _minimal_pdf(text: str) -> bytes:
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 72 720 Td ({safe_text}) Tj ET"
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(content.encode('latin-1'))} >> stream\n"
        f"{content}\nendstream endobj\n".encode("latin-1"),
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)
