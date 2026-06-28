from pathlib import Path

import markdown  # type: ignore[import-untyped]

FALLBACK_NOTE = (
    "Fallback PDF gerado porque WeasyPrint nao estava disponivel ou falhou localmente."
)


def export_report_pdf(markdown_path: Path, output_pdf_path: Path) -> Path:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    html = markdown.markdown(markdown_text, extensions=["tables"])
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from weasyprint import HTML  # type: ignore[import-untyped]

        HTML(string=html).write_pdf(output_pdf_path)
    except Exception:
        fallback_html_path = output_pdf_path.with_suffix(".html")
        fallback_html_path.write_text(_html_document(html), encoding="utf-8")
        output_pdf_path.write_bytes(_minimal_pdf(FALLBACK_NOTE))

    return output_pdf_path


def _html_document(body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>Relatorio SRAG</title></head><body>"
        f"{body}<p><strong>{FALLBACK_NOTE}</strong></p>"
        "</body></html>"
    )


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
