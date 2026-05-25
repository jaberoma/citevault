"""Test the Modelfile writer and the GGUF converter shell-out (mocked)."""

from pathlib import Path
from unittest.mock import patch

from citevault_finetune.adapter_exporter import (
    export_lora_to_gguf,
    write_ollama_modelfile,
)


def test_write_modelfile(tmp_path: Path) -> None:
    out = tmp_path / "Modelfile"
    write_ollama_modelfile(
        out_path=str(out), base_tag="gemma4:e4b", adapter_gguf="./voice.gguf",
    )
    text = out.read_text()
    assert "FROM gemma4:e4b" in text
    assert "ADAPTER ./voice.gguf" in text


def test_write_modelfile_includes_temperature(tmp_path: Path) -> None:
    out = tmp_path / "Modelfile"
    write_ollama_modelfile(out_path=str(out), base_tag="gemma4:e4b", adapter_gguf="./voice.gguf")
    assert "PARAMETER temperature" in out.read_text()


def test_export_calls_llama_cpp_converter(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LLAMA_CPP_DIR", "/fake/llama.cpp")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        export_lora_to_gguf(
            adapter_dir=str(tmp_path / "adapter"),
            out_gguf=str(tmp_path / "voice.gguf"),
        )
        cmd = mock_run.call_args.args[0]
        assert any("convert_lora_to_gguf.py" in str(c) for c in cmd)


def test_export_raises_without_llama_cpp_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("LLAMA_CPP_DIR", raising=False)
    try:
        export_lora_to_gguf(adapter_dir=str(tmp_path), out_gguf=str(tmp_path / "out.gguf"))
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "LLAMA_CPP_DIR" in str(e)
