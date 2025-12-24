import dataclasses
import json
import os
import resource
import subprocess
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclasses.dataclass
class HealingProposal:
    root_cause: str
    unified_diff: str
    tests: List[str]
    risks: str
    agent_reasoning: Dict[str, str]
    raw_response: str
    self_critique: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_cause": self.root_cause,
            "unified_diff": self.unified_diff,
            "tests": self.tests,
            "risks": self.risks,
            "agent_reasoning": self.agent_reasoning,
            "raw_response": self.raw_response,
            "self_critique": self.self_critique,
        }


class ErrorCapture:
    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path.cwd()

    def capture_exception(
        self,
        exc: BaseException,
        prompt: Optional[str] = None,
        agent_state: Optional[Dict[str, Any]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        stack_trace = traceback.format_exc()
        code_context = self._extract_code_context(exc)
        payload = {
            "error_message": f"{type(exc).__name__}: {exc}",
            "stack_trace": stack_trace,
            "prompt": prompt,
            "agent_state": agent_state or {},
            "system_metrics": self._system_metrics(),
            "git_context": self._git_context(),
            "code_context": code_context,
            "timestamp": time.time(),
        }
        if extra_context:
            payload["extra_context"] = extra_context
        return payload

    def capture_error_result(
        self,
        message: str,
        prompt: Optional[str] = None,
        agent_state: Optional[Dict[str, Any]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "error_message": message,
            "stack_trace": None,
            "prompt": prompt,
            "agent_state": agent_state or {},
            "system_metrics": self._system_metrics(),
            "git_context": self._git_context(),
            "code_context": [],
            "timestamp": time.time(),
        }
        if extra_context:
            payload["extra_context"] = extra_context
        return payload

    def _system_metrics(self) -> Dict[str, Any]:
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if rss < 100_000_000:
            rss_bytes = int(rss * 1024)
        else:
            rss_bytes = int(rss)
        return {"pid": os.getpid(), "rss_bytes": rss_bytes}

    def _git_context(self) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        commands = {
            "branch": ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            "status": ["git", "status", "--porcelain"],
            "diff_stat": ["git", "diff", "--stat"],
            "last_commit": ["git", "log", "-1", "--pretty=%h %s"],
        }
        for key, command in commands.items():
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root),
                    timeout=4,
                )
                if result.returncode == 0:
                    context[key] = result.stdout.strip()
                else:
                    context[key] = ""
            except (subprocess.SubprocessError, FileNotFoundError):
                context[key] = ""
        return context

    def _extract_code_context(self, exc: BaseException) -> List[Dict[str, Any]]:
        frames = traceback.extract_tb(exc.__traceback__)
        context = []
        for frame in frames[-5:]:
            snippet = self._read_snippet(frame.filename, frame.lineno, radius=3)
            context.append(
                {
                    "file": frame.filename,
                    "line": frame.lineno,
                    "function": frame.name,
                    "snippet": snippet,
                }
            )
        return context

    def _read_snippet(self, filename: str, lineno: int, radius: int = 3) -> str:
        try:
            path = Path(filename)
            lines = path.read_text(encoding="utf-8").splitlines()
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            return ""
        start = max(lineno - radius - 1, 0)
        end = min(lineno + radius, len(lines))
        snippet_lines = lines[start:end]
        return "\n".join(snippet_lines)


class HealingOrchestrator:
    def __init__(
        self,
        council_runner: Callable[..., Dict[str, Any]],
        log_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self.council_runner = council_runner
        self.project_root = project_root or Path.cwd()
        self.log_path = log_path or (self.project_root / "data" / "healing_log.json")

    def generate_proposal(self, error_context: Dict[str, Any]) -> HealingProposal:
        prompt = self._build_prompt(error_context)
        result = self.council_runner(prompt, skip_curator=True, stream=False)
        agent_reasoning = {
            agent.get("name", f"agent_{idx}"): agent.get("output", "")
            for idx, agent in enumerate(result.get("agents", []))
        }
        final_answer = result.get("final_answer") or result.get("message", "")
        proposal = self._parse_proposal(final_answer, agent_reasoning)
        proposal.self_critique = self._generate_self_critique(error_context, proposal)
        return proposal

    def apply_fix(
        self,
        proposal: HealingProposal,
        commit_message: str,
        run_tests: bool = True,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        if not proposal.unified_diff or "NO_DIFF" in proposal.unified_diff:
            return {"applied": False, "reason": "No diff supplied in proposal."}

        self._apply_unified_diff(proposal.unified_diff)
        test_results = []
        if run_tests:
            test_results = self._run_tests(proposal.tests)

        committed = False
        if auto_commit:
            committed = self._commit_changes(commit_message)

        result = {
            "applied": True,
            "tests": test_results,
            "committed": committed,
        }
        self._log_event("proposal_applied", {}, result)
        return result

    def _build_prompt(self, error_context: Dict[str, Any]) -> str:
        code_context = json.dumps(error_context.get("code_context", []), indent=2)
        git_context = json.dumps(error_context.get("git_context", {}), indent=2)
        system_metrics = json.dumps(error_context.get("system_metrics", {}), indent=2)
        return (
            "Self-healing mode: analyze the failure and propose a fix.\n"
            "Respond in the exact sections below:\n"
            "ROOT_CAUSE:\n"
            "DIFF:\n"
            "TESTS:\n"
            "RISKS:\n"
            "If no diff is possible, write NO_DIFF under DIFF.\n\n"
            f"ERROR_MESSAGE: {error_context.get('error_message')}\n"
            f"STACK_TRACE:\n{error_context.get('stack_trace')}\n"
            f"PROMPT: {error_context.get('prompt')}\n"
            f"AGENT_STATE: {json.dumps(error_context.get('agent_state', {}), indent=2)}\n"
            f"SYSTEM_METRICS:\n{system_metrics}\n"
            f"GIT_CONTEXT:\n{git_context}\n"
            f"CODE_CONTEXT:\n{code_context}\n"
        )

    def _parse_proposal(self, response: str, agent_reasoning: Dict[str, str]) -> HealingProposal:
        root_cause = self._extract_section(response, "ROOT_CAUSE")
        diff = self._extract_section(response, "DIFF")
        tests_raw = self._extract_section(response, "TESTS")
        risks = self._extract_section(response, "RISKS")
        tests = [line.strip("- ").strip() for line in tests_raw.splitlines() if line.strip()]
        if not tests:
            tests = ["pytest -v"]
        return HealingProposal(
            root_cause=root_cause.strip(),
            unified_diff=diff.strip(),
            tests=tests,
            risks=risks.strip(),
            agent_reasoning=agent_reasoning,
            raw_response=response,
            self_critique="",
        )

    def _extract_section(self, response: str, header: str) -> str:
        marker = f"{header}:"
        if marker not in response:
            return ""
        after = response.split(marker, 1)[1]
        for next_header in ["ROOT_CAUSE:", "DIFF:", "TESTS:", "RISKS:"]:
            if next_header == marker:
                continue
            if next_header in after:
                return after.split(next_header, 1)[0].strip()
        return after.strip()

    def _generate_self_critique(
        self,
        error_context: Dict[str, Any],
        proposal: HealingProposal,
    ) -> str:
        prompt = (
            "Review this self-healing proposal. "
            "List any parts of this proposal that might be incorrect, speculative, "
            "or based on missing context. Be brutally honest and concise.\n\n"
            f"ERROR_MESSAGE: {error_context.get('error_message')}\n"
            f"ROOT_CAUSE: {proposal.root_cause}\n"
            f"DIFF:\n{proposal.unified_diff}\n"
            f"TESTS: {', '.join(proposal.tests)}\n"
            f"RISKS: {proposal.risks}\n"
        )
        try:
            result = self.council_runner(prompt, skip_curator=True, stream=False)
        except Exception:
            return ""
        critique = result.get("final_answer") or result.get("message", "")
        return critique.strip()

    def _apply_unified_diff(self, diff_text: str) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(diff_text)
            patch_path = handle.name
        try:
            subprocess.run(
                ["git", "apply", patch_path],
                check=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
            )
        finally:
            try:
                os.unlink(patch_path)
            except OSError:
                pass

    def _run_tests(self, tests: List[str]) -> List[Dict[str, Any]]:
        results = []
        for command in tests:
            try:
                completed = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                )
                results.append(
                    {
                        "command": command,
                        "returncode": completed.returncode,
                        "stdout": completed.stdout.strip(),
                        "stderr": completed.stderr.strip(),
                    }
                )
                if completed.returncode != 0:
                    break
            except subprocess.SubprocessError as exc:
                results.append({"command": command, "error": str(exc)})
                break
        return results

    def _commit_changes(self, message: str) -> bool:
        try:
            subprocess.run(
                ["git", "add", "-A"],
                check=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
            )
        except subprocess.SubprocessError:
            return False
        return True

    def create_branch(self, branch_name: str) -> str:
        candidate = branch_name
        suffix = 1
        while self._branch_exists(candidate):
            suffix += 1
            candidate = f"{branch_name}-{suffix}"
        subprocess.run(
            ["git", "checkout", "-b", candidate],
            check=True,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
        )
        return candidate

    def _branch_exists(self, branch_name: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                check=False,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False
