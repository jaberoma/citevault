"""TextChunker tests."""

from hypothesis import given, strategies as st

from citevault.domain.services.chunker import chunk_text


def test_short_text_produces_single_span() -> None:
    chunks = chunk_text("Hello world.", max_tokens=512, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world."
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == 12


def test_long_text_produces_multiple_overlapping_spans() -> None:
    text = "word " * 600  # ~600 tokens
    chunks = chunk_text(text, max_tokens=200, overlap=20)
    assert len(chunks) >= 3
    # Spans cover the entire text
    assert chunks[0].start_offset == 0
    assert chunks[-1].end_offset == len(text.rstrip())


def test_chunks_respect_paragraph_boundaries() -> None:
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunk_text(text, max_tokens=10, overlap=0)
    # Each paragraph should land in its own chunk given the tiny budget
    assert any("First paragraph" in c.text for c in chunks)
    assert any("Second paragraph" in c.text for c in chunks)


@given(st.text(min_size=10, max_size=2000))
def test_property_chunk_offsets_match_source(text: str) -> None:
    chunks = chunk_text(text, max_tokens=50, overlap=0)
    # Each span's offsets must index back to its exact text in the original
    for chunk in chunks:
        assert text[chunk.start_offset:chunk.end_offset] == chunk.text
