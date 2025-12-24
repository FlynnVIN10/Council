from types import SimpleNamespace

import pytest

from src import ollama_llm


def test_ollama_completion_wraps_errors(monkeypatch):
    def raise_error(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(
        ollama_llm, "litellm", SimpleNamespace(completion=raise_error)
    )

    with pytest.raises(RuntimeError, match="Ollama completion failed"):
        ollama_llm.ollama_completion([{"role": "user", "content": "ping"}])
