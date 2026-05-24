"""Composition root wires real adapters together."""

from pathlib import Path

from citevault.composition.container import Container, ContainerConfig


def test_container_wires_dependencies(tmp_path: Path) -> None:
    cfg = ContainerConfig(
        db_path=str(tmp_path / "t.db"),
        ollama_base_url="http://localhost:11434",
        ollama_model="gemma4:e4b",
    )
    c = Container(cfg)
    assert c.evidence_repo is not None
    assert c.trace_repo is not None
    assert c.llm is not None
    # Heavy models load in background — wait before checking them.
    c.wait_ready(timeout=120)
    assert c.embedder is not None
    assert c.retrieval is not None
    assert c.reranker is not None
