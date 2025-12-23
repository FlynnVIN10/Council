from src.self_healing import ErrorCapture, HealingOrchestrator


def _raise_error():
    raise ValueError("boom")


def test_error_capture_includes_trace_and_context(tmp_path):
    capture = ErrorCapture(project_root=tmp_path)
    try:
        _raise_error()
    except Exception as exc:
        payload = capture.capture_exception(exc, prompt="hello", agent_state={"mode": "test"})

    assert "ValueError" in payload["error_message"]
    assert "stack_trace" in payload
    assert payload["prompt"] == "hello"
    assert payload["agent_state"]["mode"] == "test"
    assert payload["system_metrics"]["rss_bytes"] > 0


def test_healing_orchestrator_parses_sections(tmp_path):
    def fake_council_runner(prompt, skip_curator=True, stream=False):
        return {
            "final_answer": (
                "ROOT_CAUSE:\nMissing key in dict.\n"
                "DIFF:\n--- a/file.py\n+++ b/file.py\n+print('fix')\n"
                "TESTS:\n- pytest -v\n- python scripts/smoke_test.py\n"
                "RISKS:\nMinor behavior change."
            ),
            "agents": [
                {"name": "Curator", "output": "Short"},
                {"name": "Researcher", "output": "Deep"},
            ],
        }

    orchestrator = HealingOrchestrator(
        fake_council_runner, log_path=tmp_path / "healing_log.json", project_root=tmp_path
    )
    proposal = orchestrator.generate_proposal({"error_message": "x"})

    assert proposal.root_cause == "Missing key in dict."
    assert "+++ b/file.py" in proposal.unified_diff
    assert proposal.tests == ["pytest -v", "python scripts/smoke_test.py"]
    assert proposal.risks == "Minor behavior change."
    assert proposal.agent_reasoning["Curator"] == "Short"


def test_healing_log_written(tmp_path):
    def fake_council_runner(prompt, skip_curator=True, stream=False):
        return {"final_answer": "ROOT_CAUSE:\nX\nDIFF:\nNO_DIFF\nTESTS:\n\nRISKS:\nNone"}

    log_path = tmp_path / "healing_log.json"
    orchestrator = HealingOrchestrator(
        fake_council_runner, log_path=log_path, project_root=tmp_path
    )
    orchestrator.generate_proposal({"error_message": "y"})

    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "proposal_generated" in content
