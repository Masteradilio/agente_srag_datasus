from reporting.pdf_exporter import export_report_pdf


def test_export_report_pdf_creates_file(tmp_path) -> None:
    markdown_path = tmp_path / "report.md"
    markdown_path.write_text("# Relatorio\n\nConteudo", encoding="utf-8")

    pdf_path = export_report_pdf(markdown_path, tmp_path / "report.pdf")

    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 0


def test_export_report_pdf_fallback_creates_html_and_pdf(monkeypatch, tmp_path) -> None:
    markdown_path = tmp_path / "report.md"
    markdown_path.write_text("# Relatorio\n\nConteudo", encoding="utf-8")

    monkeypatch.setitem(__import__("sys").modules, "weasyprint", None)

    pdf_path = export_report_pdf(markdown_path, tmp_path / "fallback.pdf")

    assert pdf_path.is_file()
    assert (tmp_path / "fallback.html").is_file()
    assert pdf_path.read_bytes().startswith(b"%PDF")

