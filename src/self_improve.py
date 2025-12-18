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
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to commit changes: {e.stderr.decode() if e.stderr else str(e)}")

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
    diffs = {}
    for file_path, new_content in file_changes.items():
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

