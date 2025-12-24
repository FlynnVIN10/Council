import os
import subprocess
import datetime
import difflib

def create_proposal_branch():
    """Create a new branch for the self-improvement proposal"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = f"self-improve/proposal-{timestamp}"
    try:
        subprocess.run(["git", "checkout", "-b", branch], check=True, capture_output=True)
        return branch
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to create branch: {e.stderr.decode() if e.stderr else str(e)}")

def commit_changes(message, file_paths=None):
    """Commit changes with the given message (optionally limited to file_paths)."""
    try:
        status_cmd = ["git", "status", "--porcelain"]
        if file_paths:
            status_cmd.extend(["--"] + list(file_paths))
        status_result = subprocess.run(
            status_cmd, check=True, capture_output=True, text=True
        )
        if not status_result.stdout.strip():
            raise Exception(
                "No actual changes detected — nothing to commit. "
                "The proposal may have contained placeholder or incomplete code."
            )

        add_cmd = ["git", "add"]
        if file_paths:
            add_cmd.extend(["--"] + list(file_paths))
        else:
            add_cmd.append(".")
        subprocess.run(add_cmd, check=True, capture_output=True)
        
        # Run commit and capture output for better error reporting
        commit_result = subprocess.run(["git", "commit", "-m", message], 
                                     check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        stdout_msg = e.stdout.decode() if e.stdout else ""
        full_error = f"Git command failed.\nSTDERR: {error_msg}\nSTDOUT: {stdout_msg}\n\n"
        full_error += "Suggest manually reviewing the branch with: git status, git diff"
        raise Exception(full_error)

def summarize_diffs(diffs: dict):
    """Summarize unified diffs with added/removed line counts per file."""
    summary = {}
    for path, diff in diffs.items():
        added = 0
        removed = 0
        for line in diff.splitlines():
            if line.startswith("+++ ") or line.startswith("--- ") or line.startswith("@@"):
                continue
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1
        summary[path] = {"added": added, "removed": removed}
    return summary

def apply_proposal(file_changes: dict, commit_message: str, auto_commit: bool = True):
    """
    Apply a self-improvement proposal to a new branch and optionally commit.
    Returns metadata including branch name and diff summary.
    """
    if not file_changes:
        raise Exception("No file changes found in proposal.")

    branch = create_proposal_branch()
    diffs = apply_changes(file_changes)
    summary = summarize_diffs(diffs)

    committed = False
    if auto_commit:
        commit_changes(commit_message, file_paths=file_changes.keys())
        committed = True

    return {
        "branch": branch,
        "diffs": diffs,
        "summary": summary,
        "committed": committed
    }

def generate_diff(old_content, new_content):
    """Generate a unified diff between old and new content"""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, lineterm='', n=3)
    return ''.join(diff)

def apply_changes(file_changes: dict):
    """
    Apply file changes and return diffs.
    file_changes = {"path/to/file.py": "new full content"}
    """
    if not file_changes:
        print("\033[1;33mWarning: No changes proposed — nothing to apply\033[0m")
        return {}
    
    diffs = {}
    for file_path, new_content in file_changes.items():
        # Check for placeholder/incomplete content
        placeholder_indicators = [
            "not shown", "not shown here", "placeholder", "todo", "implementation omitted",
            "implementation here", "code here", "...", "etc."
        ]
        new_content_lower = new_content.lower()
        if any(indicator in new_content_lower for indicator in placeholder_indicators):
            print(f"\033[1;33mWarning: File {file_path} appears to contain placeholder/incomplete content\033[0m")
            print(f"Found placeholder indicators — content may be incomplete")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        
        old_content = ""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                old_content = f.read()
        
        # Write new content
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(new_content)
        
        # Generate diff
        diffs[file_path] = generate_diff(old_content, new_content)
    
    return diffs

def get_current_branch():
    """Get the current git branch name"""
    try:
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                              check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def cleanup_merged_proposal_branches(keep=3, base_branch="main"):
    """
    Delete older self-improve/proposal-* branches that are already merged into base_branch.
    Keeps the newest `keep` merged branches.
    """
    try:
        merged = subprocess.run(
            ["git", "branch", "--merged", base_branch],
            check=True,
            capture_output=True,
            text=True
        ).stdout.splitlines()
    except subprocess.CalledProcessError:
        return []

    merged = [line.strip().lstrip("* ").strip() for line in merged]
    merged = [b for b in merged if b.startswith("self-improve/proposal-")]
    if len(merged) <= keep:
        return []

    try:
        refs = subprocess.run(
            [
                "git", "for-each-ref",
                "--format=%(refname:short)|%(committerdate:iso8601)",
                "refs/heads/self-improve/proposal-*"
            ],
            check=True,
            capture_output=True,
            text=True
        ).stdout.splitlines()
    except subprocess.CalledProcessError:
        return []

    dates = {}
    for line in refs:
        if "|" not in line:
            continue
        name, date = line.split("|", 1)
        if name in merged:
            dates[name] = date

    merged_sorted = sorted(dates.items(), key=lambda item: item[1], reverse=True)
    to_keep = {name for name, _ in merged_sorted[:keep]}
    to_delete = [name for name, _ in merged_sorted[keep:] if name not in to_keep]

    deleted = []
    for branch in to_delete:
        try:
            subprocess.run(["git", "branch", "-d", branch], check=True, capture_output=True)
            deleted.append(branch)
        except subprocess.CalledProcessError:
            continue

    return deleted
