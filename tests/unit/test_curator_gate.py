from src import council


def _stub_memory(monkeypatch):
    monkeypatch.setattr(council, "get_recent_messages", lambda *args, **kwargs: [])
    monkeypatch.setattr(council, "get_all_preferences", lambda *args, **kwargs: {})
    monkeypatch.setattr(council, "add_message", lambda *args, **kwargs: None)


def test_curator_confirmation_gate_true(monkeypatch):
    _stub_memory(monkeypatch)
    monkeypatch.setattr(
        council,
        "ollama_completion",
        lambda *args, **kwargs: (
            "I have a refined query ready: 'Test query'\n\n"
            "Ready for full council deliberation (~12 minutes)? (yes/no)"
        ),
    )
    response = council.run_curator_only(
        "Please help me design a multi-agent test suite.",
        conversation_history=[{"role": "user", "content": "Earlier input"}],
        stream=False,
    )

    assert response["asking_confirmation"] is True


def test_curator_confirmation_gate_false_on_first_message(monkeypatch):
    _stub_memory(monkeypatch)
    monkeypatch.setattr(
        council,
        "ollama_completion",
        lambda *args, **kwargs: (
            "I have a refined query ready: 'Test query'\n\n"
            "Ready for full council deliberation (~12 minutes)? (yes/no)"
        ),
    )
    response = council.run_curator_only(
        "Please help me design a multi-agent test suite.",
        conversation_history=[],
        stream=False,
    )

    assert response["asking_confirmation"] is False
