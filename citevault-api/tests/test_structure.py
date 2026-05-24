"""Hexagonal structure smoke test: domain must not import from adapters."""

import ast
from pathlib import Path

DOMAIN = Path(__file__).parent.parent / "src" / "citevault" / "domain"


def test_domain_does_not_import_from_adapters() -> None:
    for py_file in DOMAIN.rglob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(
                    "citevault.adapters"
                ), f"{py_file} imports from adapters layer"
                assert not (node.module or "").startswith(
                    "citevault.application"
                ), f"{py_file} imports from application layer"
