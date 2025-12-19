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

def commit_changes(message):
    """Commit all changes with the given message"""
    try:
        # Check if there are any changes to commit
        status_result = subprocess.run(["git", "status", "--porcelain"], 
                                     check=True, capture_output=True, text=True)
        if not status_result.stdout.strip():
            raise Exception("No actual changes detected — nothing to commit. The proposal may have contained placeholder or incomplete code.")
        
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
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

