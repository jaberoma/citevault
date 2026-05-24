"""PDF rendering smoke test (output is a valid PDF file)."""

from pathlib import Path

from citevault.adapters.outbound.pdf_renderer import markdown_to_pdf


def test_markdown_renders_to_pdf(tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    markdown_to_pdf(
        "# Hello\n\n- Some bullet.\n[^a]: source text",
        out_path=str(out),
    )
    assert out.exists()
    with open(out, "rb") as f:
        header = f.read(4)
    assert header == b"%PDF"
