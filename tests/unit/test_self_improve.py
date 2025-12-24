import datetime
import subprocess

import pytest

import src.self_improve as self_improve


class FixedDateTime(datetime.datetime):
    @classmethod
    def now(cls):
        return cls(2024, 1, 2, 3, 4, 5)


@pytest.fixture
def fixed_datetime(monkeypatch):
    monkeypatch.setattr(self_improve.datetime, "datetime", FixedDateTime)


def test_create_proposal_branch_success(monkeypatch, fixed_datetime):
    calls = []

    def fake_run(args, check, capture_output=True, text=False):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    branch = self_improve.create_proposal_branch()
    assert branch == "self-improve/proposal-20240102-030405"
    assert calls == [["git", "checkout", "-b", branch]]


def test_create_proposal_branch_git_error(monkeypatch, fixed_datetime):
    def fake_run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["git"], stderr=b"nope")

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    with pytest.raises(Exception, match="Failed to create branch: nope"):
        self_improve.create_proposal_branch()


def test_generate_diff_and_summarize():
    diff = self_improve.generate_diff("one\n", "one\ntwo\n")
    summary = self_improve.summarize_diffs({"file.txt": diff})
    assert summary["file.txt"]["added"] == 1
    assert summary["file.txt"]["removed"] == 0


def test_apply_changes_writes_and_diff(tmp_path):
    target = tmp_path / "notes.txt"
    diffs = self_improve.apply_changes({str(target): "new content\n"})
    assert target.read_text(encoding="utf-8") == "new content\n"
    assert str(target) in diffs
    assert diffs[str(target)].startswith("---")


def test_apply_changes_placeholder_warning(tmp_path, capsys):
    target = tmp_path / "todo.txt"
    self_improve.apply_changes({str(target): "TODO: placeholder"})
    output = capsys.readouterr().out
    assert "placeholder" in output.lower()


def test_apply_proposal_auto_commit(monkeypatch):
    monkeypatch.setattr(self_improve, "create_proposal_branch", lambda: "branch-x")
    monkeypatch.setattr(self_improve, "apply_changes", lambda changes: {"a.py": "+change"})
    committed = {}

    def fake_commit(message, file_paths=None):
        committed["message"] = message
        committed["paths"] = list(file_paths or [])
        return True

    monkeypatch.setattr(self_improve, "commit_changes", fake_commit)

    result = self_improve.apply_proposal({"a.py": "content"}, "commit msg", auto_commit=True)
    assert result["branch"] == "branch-x"
    assert result["committed"] is True
    assert committed["message"] == "commit msg"
    assert committed["paths"] == ["a.py"]


def test_apply_proposal_no_auto_commit(monkeypatch):
    monkeypatch.setattr(self_improve, "create_proposal_branch", lambda: "branch-y")
    monkeypatch.setattr(self_improve, "apply_changes", lambda changes: {"a.py": "+change"})
    monkeypatch.setattr(self_improve, "commit_changes", lambda *_args, **_kwargs: True)
    result = self_improve.apply_proposal({"a.py": "content"}, "msg", auto_commit=False)
    assert result["committed"] is False


def test_apply_proposal_empty_changes():
    with pytest.raises(Exception, match="No file changes found in proposal"):
        self_improve.apply_proposal({}, "msg")


def test_commit_changes_no_actual_changes(monkeypatch):
    def fake_run(args, check, capture_output=True, text=True):
        if args[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        raise AssertionError("Unexpected git command")

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    with pytest.raises(Exception, match="No actual changes detected"):
        self_improve.commit_changes("msg", ["file.py"])


def test_commit_changes_git_error(monkeypatch):
    def fake_run(args, check, capture_output=True, text=True):
        if args[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(args, 0, stdout=" M file.py\n", stderr="")
        if args[:2] == ["git", "add"]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        if args[:2] == ["git", "commit"]:
            raise subprocess.CalledProcessError(1, args, stderr=b"boom", output=b"")
        raise AssertionError("Unexpected git command")

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    with pytest.raises(Exception, match="Git command failed"):
        self_improve.commit_changes("msg")


def test_get_current_branch_success(monkeypatch):
    def fake_run(args, check, capture_output=True, text=True):
        return subprocess.CompletedProcess(args, 0, stdout="main\n", stderr="")

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    assert self_improve.get_current_branch() == "main"


def test_get_current_branch_failure(monkeypatch):
    def fake_run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["git"])

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    assert self_improve.get_current_branch() is None


def test_cleanup_merged_proposal_branches(monkeypatch):
    calls = []

    merged_output = "\n".join(
        [
            "  main",
            "  self-improve/proposal-1",
            "  self-improve/proposal-2",
            "  self-improve/proposal-3",
            "  self-improve/proposal-4",
        ]
    )
    refs_output = "\n".join(
        [
            "self-improve/proposal-1|2024-01-01T00:00:00+00:00",
            "self-improve/proposal-2|2024-01-02T00:00:00+00:00",
            "self-improve/proposal-3|2024-01-03T00:00:00+00:00",
            "self-improve/proposal-4|2024-01-04T00:00:00+00:00",
        ]
    )

    def fake_run(args, check, capture_output=True, text=True):
        calls.append(args)
        if args[:3] == ["git", "branch", "--merged"]:
            return subprocess.CompletedProcess(args, 0, stdout=merged_output, stderr="")
        if args[:2] == ["git", "for-each-ref"]:
            return subprocess.CompletedProcess(args, 0, stdout=refs_output, stderr="")
        if args[:2] == ["git", "branch"] and "-d" in args:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        raise AssertionError("Unexpected git command")

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    deleted = self_improve.cleanup_merged_proposal_branches(keep=2, base_branch="main")
    assert deleted == ["self-improve/proposal-2", "self-improve/proposal-1"]


def test_cleanup_merged_proposal_branches_git_error(monkeypatch):
    def fake_run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, ["git"])

    monkeypatch.setattr(self_improve.subprocess, "run", fake_run)
    assert self_improve.cleanup_merged_proposal_branches() == []


def test_apply_changes_empty_warns(capsys):
    assert self_improve.apply_changes({}) == {}
    assert "nothing to apply" in capsys.readouterr().out.lower()


def test_invalid_proposal_content(tmp_path):
    target = tmp_path / "bad.txt"
    diffs = self_improve.apply_changes({str(target): ""})
    assert diffs[str(target)] == ""
    assert target.read_text(encoding="utf-8") == ""
