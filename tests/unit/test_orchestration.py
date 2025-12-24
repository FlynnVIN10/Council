from src import council


def _stub_memory(monkeypatch):
    # Stub memory functions that are imported at module level
    monkeypatch.setattr(council, "get_latest_summary", lambda *args, **kwargs: "")
    monkeypatch.setattr(council, "get_relevant_facts", lambda *args, **kwargs: [])
    monkeypatch.setattr(council, "get_all_preferences", lambda *args, **kwargs: {})
    monkeypatch.setattr(council, "save_session", lambda *args, **kwargs: 1)
    monkeypatch.setattr(council, "add_message", lambda *args, **kwargs: None)
    monkeypatch.setattr(council, "save_summary", lambda *args, **kwargs: None)
    monkeypatch.setattr(council, "save_facts", lambda *args, **kwargs: None)
    monkeypatch.setattr(council, "build_session_summary", lambda *args, **kwargs: "summary")
    monkeypatch.setattr(council, "generate_memory_snapshot", lambda *args, **kwargs: ("", []))
    # Disable persistence so prune_messages/vacuum_db won't be called
    monkeypatch.setattr(council, "ENABLE_PERSISTENCE", False)


def test_run_council_sync_calls_agents_in_order(monkeypatch):
    _stub_memory(monkeypatch)
    calls = []
    responses = [
        "Curator response.",
        "Researcher response.",
        "Critic response.",
        "Planner response.",
        "Final Answer:\n1. One\n2. Two\n3. Three\n4. Four\nRationale: ok",
    ]

    def fake_completion(messages, *args, **kwargs):
        calls.append(messages[0]["content"])
        return responses[len(calls) - 1]

    monkeypatch.setattr(council, "ollama_completion", fake_completion)

    result = council.run_council_sync("Test prompt", skip_curator=False, stream=False)

    assert len(calls) == 5
    assert [agent["name"] for agent in result["agents"]] == [
        "Curator",
        "Researcher",
        "Critic",
        "Planner",
        "Judge",
    ]
    assert result["agents"][0]["output"] == "Curator response."
    assert result["agents"][1]["output"] == "Researcher response."
    assert result["agents"][2]["output"] == "Critic response."
    assert result["agents"][3]["output"] == "Planner response."
