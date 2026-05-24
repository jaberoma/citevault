"""Paragraph-aware text chunker producing offset-tracked spans.

"Tokens" are approximated by whitespace-split words — accurate tokenization can
be swapped in later (port: TokenizerPort) without changing the chunker's contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkSpan:
    text: str
    start_offset: int
    end_offset: int


_PARA_RE = re.compile(r"\n{2,}")


def _approx_token_count(text: str) -> int:
    return len(text.split())


def chunk_text(text: str, max_tokens: int, overlap: int) -> list[ChunkSpan]:
    """Chunk `text` into spans of at most `max_tokens` whitespace-tokens,
    with `overlap` token overlap between consecutive chunks. Respects
    paragraph boundaries (\\n\\n) so a span never crosses one.
    """
    if not text.strip():
        return []
    spans: list[ChunkSpan] = []
    for para_match in re.finditer(r"[^\n]+(?:\n[^\n]+)*", text):
        para = para_match.group(0)
        para_start = para_match.start()
        words = para.split()
        if not words:
            continue
        if _approx_token_count(para) <= max_tokens:
            spans.append(ChunkSpan(
                text=para, start_offset=para_start,
                end_offset=para_start + len(para),
            ))
            continue
        # Walk the paragraph in token windows
        i = 0
        offset_in_para = 0
        while i < len(words):
            window = words[i : i + max_tokens]
            chunk_text_val = " ".join(window)
            chunk_start = para_start + offset_in_para
            chunk_end = chunk_start + len(chunk_text_val)
            spans.append(ChunkSpan(
                text=chunk_text_val,
                start_offset=chunk_start, end_offset=chunk_end,
            ))
            if i + max_tokens >= len(words):
                break
            step = max(1, max_tokens - overlap)
            consumed = " ".join(words[i : i + step])
            offset_in_para += len(consumed) + 1
            i += step
    return spans
