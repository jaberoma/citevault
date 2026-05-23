"""Render Markdown to PDF via markdown-it-py → HTML → WeasyPrint."""

from __future__ import annotations

from markdown_it import MarkdownIt
from weasyprint import HTML

_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 11pt; line-height: 1.5; color: #1a1a1a; }
h1 { font-size: 17pt; margin-top: 0; margin-bottom: 0.2em; }
h2 { font-size: 12pt; margin-top: 1.4em; border-bottom: 1px solid #ccc; padding-bottom: 0.2em;
     color: #333; text-transform: uppercase; letter-spacing: 0.05em; }
ul { padding-left: 1.4em; margin-top: 0.4em; }
li { margin-bottom: 0.4em; }
ol { padding-left: 1.4em; }
ol li { margin-bottom: 0.6em; }
sup { font-size: 0.7em; color: #666; vertical-align: super; }
small { font-size: 9pt; color: #555; }
em { color: #555; }
"""


def html_to_pdf(body_html: str, out_path: str) -> None:
    full_html = (
        f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head>"
        f"<body>{body_html}</body></html>"
    )
    HTML(string=full_html).write_pdf(out_path)


def markdown_to_pdf(md_text: str, out_path: str) -> None:
    md = MarkdownIt("commonmark", {"breaks": True, "html": False})
    html = md.render(md_text)
    html_to_pdf(html, out_path)
