import json

from src.healing_log import append_log_entry, build_log_entry, summarize_diff
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
        if "Review this self-healing proposal" in prompt:
            return {"final_answer": "Potentially wrong assumption about dict keys."}
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
    assert proposal.self_critique == "Potentially wrong assumption about dict keys."


def test_healing_log_written(tmp_path):
    log_path = tmp_path / "healing_log.json"
    diff_summary = summarize_diff("+++ b/file.py\n+print('fix')\n")
    entry = build_log_entry(
        error_context={"error_message": "ValueError: boom", "stack_trace": "stack"},
        proposal_id="1",
        proposal_summary="Missing key in dict.",
        files_changed=diff_summary["files"],
        loc_changed_estimate=diff_summary["loc_changed"],
        approval_status="pending",
    )
    append_log_entry(log_path, entry)

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    assert payload["approval_status"] == "pending"
    assert payload["proposal_id"] == "1"
