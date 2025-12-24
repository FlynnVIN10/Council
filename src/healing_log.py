import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def summarize_diff(diff_text: str) -> Dict[str, Any]:
    files: List[str] = []
    per_file: Dict[str, Dict[str, int]] = {}
    current_file: Optional[str] = None
    added = 0
    removed = 0

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            if path == "/dev/null":
                current_file = None
                continue
            current_file = path
            if current_file not in per_file:
                per_file[current_file] = {"added": 0, "removed": 0}
                files.append(current_file)
            continue
        if line.startswith("--- "):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
            if current_file and current_file in per_file:
                per_file[current_file]["added"] += 1
            continue
        if line.startswith("-") and not line.startswith("---"):
            removed += 1
            if current_file and current_file in per_file:
                per_file[current_file]["removed"] += 1
            continue

    return {
        "files": files,
        "loc_changed": added + removed,
        "per_file": per_file,
    }


def summarize_stack(error_context: Dict[str, Any]) -> List[str]:
    code_context = error_context.get("code_context") or []
    stack_trace = error_context.get("stack_trace") or ""

    if code_context:
        summary = []
        for frame in code_context[-3:]:
            file_name = frame.get("file", "")
            line = frame.get("line", "")
            func = frame.get("function", "")
            if file_name and line:
                summary.append(f"{file_name}:{line} in {func}".strip())
            elif file_name:
                summary.append(file_name)
        return summary

    summary = []
    for line in stack_trace.splitlines():
        line = line.strip()
        if not line.startswith("File \""):
            continue
        parts = line.split("\"")
        if len(parts) < 2:
            continue
        file_name = parts[1]
        line_no = ""
        if "line " in line:
            line_no = line.split("line ", 1)[1].split(",", 1)[0].strip()
        func = ""
        if " in " in line:
            func = line.split(" in ", 1)[1].strip()
        label = f"{file_name}:{line_no} in {func}".strip()
        summary.append(label)
        if len(summary) >= 3:
            break
    return summary


def one_sentence(text: str, fallback: str = "") -> str:
    if not text:
        return fallback
    trimmed = text.strip().splitlines()[0].strip()
    if not trimmed:
        return fallback
    for splitter in [". ", ".\n"]:
        if splitter in text:
            return text.split(splitter, 1)[0].strip() + "."
    return trimmed


def build_log_entry(
    *,
    error_context: Dict[str, Any],
    proposal_id: str,
    proposal_summary: str,
    files_changed: List[str],
    loc_changed_estimate: int,
    approval_status: str,
) -> Dict[str, Any]:
    error_message = error_context.get("error_message", "")
    error_type = error_message.split(":", 1)[0].strip() if error_message else "UnknownError"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error_type": error_type,
        "error_message": error_message,
        "stack_summary": summarize_stack(error_context),
        "proposal_id": proposal_id,
        "proposal_summary": proposal_summary,
        "files_changed": files_changed,
        "loc_changed_estimate": loc_changed_estimate,
        "approval_status": approval_status,
    }


def append_log_entry(log_path: Path, entry: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
