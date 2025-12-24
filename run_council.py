import os
import sys
import subprocess
from pathlib import Path
from src.council import run_council_sync, run_curator_only
from src.memory import get_recent_sessions
from src.self_improve import apply_proposal, commit_changes, cleanup_merged_proposal_branches
from src.self_healing import ErrorCapture, HealingOrchestrator, HealingProposal
from src.healing_log import (
    append_log_entry,
    build_log_entry,
    one_sentence,
    summarize_diff,
    summarize_stack,
)

def ensure_ollama_ready(retries=3, delay_seconds=3):
    """Ensure Ollama is reachable; attempt to start it if needed."""
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        if attempt == 1:
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except FileNotFoundError:
                print("Error: 'ollama' not found. Install Ollama and ensure it's on PATH.")
                return False

        if attempt < retries:
            print(f"Ollama not ready. Retrying ({attempt}/{retries})...")
            try:
                import time
                time.sleep(delay_seconds)
            except Exception:
                pass

    print("Error: Ollama is not reachable. Run 'ollama serve' in another terminal.")
    return False

def ensure_model():
    """Ensure the phi3 model is pulled and available"""
    try:
        if not ensure_ollama_ready():
            return
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and "phi3" not in result.stdout:
            print("Pulling phi3 model (first run, please wait)...")
            subprocess.run(["ollama", "pull", "phi3"], check=True)
            print("Model pull complete.\n")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError) as e:
        # If ollama command fails or times out, continue anyway (might be starting up)
        pass

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print("     THE COUNCIL — Bold & Deep Mode")
    print("     (phi3 @ 3700 tokens — visionary portfolios)")
    print("=" * 60)
    print("Type your message. 'exit' or 'quit' to end. Ctrl+C to interrupt.\n")

def _shorten_text(text: str, limit: int = 240) -> str:
    trimmed = text.strip()
    if len(trimmed) <= limit:
        return trimmed
    return trimmed[: limit - 3].rstrip() + "..."


def _display_healing_proposal(proposal: HealingProposal, proposal_id: int) -> None:
    print("\n" + "=" * 60)
    print("\033[1;33mSELF-HEALING PROPOSAL\033[0m")
    print("=" * 60)
    print(f"\n\033[1;36mProposal ID:\033[0m {proposal_id}")
    print("\n\033[1;33mType 'fix {proposal_id}' to review and approve.\033[0m".format(
        proposal_id=proposal_id
    ))


def _display_healing_review(
    proposal: HealingProposal,
    error_context: dict,
    diff_summary: dict,
    proposal_id: int,
) -> None:
    print("\n" + "=" * 60)
    print("\033[1;33mSELF-HEALING REVIEW\033[0m")
    print("=" * 60)
    print(f"\n\033[1;36mProposal ID:\033[0m {proposal_id}")
    print("\n\033[1;36mError:\033[0m")
    print(error_context.get("error_message", "(Unknown error)"))
    stack_summary = error_context.get("stack_summary")
    if stack_summary:
        print("\n\033[1;36mStack Summary:\033[0m")
        for frame in stack_summary:
            print(f"- {frame}")
    print("\n\033[1;36mRoot Cause:\033[0m")
    print(proposal.root_cause or "(No root cause provided)")
    print("\n\033[1;36mDiff Summary:\033[0m")
    if diff_summary.get("per_file"):
        for path, stats in diff_summary["per_file"].items():
            print(f"- {path}: +{stats.get('added', 0)} / -{stats.get('removed', 0)}")
        print(f"Total LOC changed: {diff_summary.get('loc_changed', 0)}")
    else:
        print("(No diff provided)")
    print("\n\033[1;36mRecommended Tests:\033[0m")
    for test_cmd in proposal.tests:
        print(f"- {test_cmd}")
    print("\n\033[1;36mRisks:\033[0m")
    print(proposal.risks or "(No risks provided)")
    if proposal.self_critique:
        print("\n\033[1;36mSelf-Critique:\033[0m")
        print(_shorten_text(proposal.self_critique))
    print("\n\033[1;33mApply this patch to a new branch and run tests? (yes/no)\033[0m")


def _register_healing_record(
    healing_result: dict,
    orchestrator: HealingOrchestrator,
    healing_records: dict,
    proposal_id: int,
) -> None:
    proposal = healing_result["proposal"]
    error_context = healing_result["error_context"]
    stack_summary = healing_result.get("stack_summary", [])
    diff_summary = summarize_diff(proposal.unified_diff)
    proposal_summary = one_sentence(
        proposal.root_cause,
        fallback=one_sentence(error_context.get("error_message", ""), fallback="Proposal generated."),
    )

    healing_records[proposal_id] = {
        "proposal": proposal,
        "error_context": error_context,
        "stack_summary": stack_summary,
        "diff_summary": diff_summary,
        "proposal_summary": proposal_summary,
    }

    log_entry = build_log_entry(
        error_context=error_context,
        proposal_id=str(proposal_id),
        proposal_summary=proposal_summary,
        files_changed=diff_summary["files"],
        loc_changed_estimate=diff_summary["loc_changed"],
        approval_status="pending",
    )
    append_log_entry(orchestrator.log_path, log_entry)
    _display_healing_proposal(proposal, proposal_id)

def _handle_self_healing(
    error_capture: ErrorCapture,
    orchestrator: HealingOrchestrator,
    prompt: str,
    agent_state: dict,
    error_message: str,
    exc: Exception | None = None,
) -> dict | None:
    try:
        if exc is None:
            error_context = error_capture.capture_error_result(
                error_message, prompt=prompt, agent_state=agent_state
            )
        else:
            error_context = error_capture.capture_exception(
                exc, prompt=prompt, agent_state=agent_state
            )
        proposal = orchestrator.generate_proposal(error_context)
        return {
            "error_context": error_context,
            "proposal": proposal,
            "stack_summary": summarize_stack(error_context),
        }
    except Exception as healing_error:
        print(f"\n\033[1;31mSelf-healing failed: {healing_error}\033[0m\n")
        return None

def interactive_mode():
    # Ensure model is available before starting
    ensure_model()
    
    print_header()
    
    # Show recent sessions if available
    try:
        recent = get_recent_sessions(3)
        if recent:
            print(f"\nWelcome back. {len(recent)} recent sessions remembered.")
            for row in recent:
                print(f"- {row[1][:19]}: {row[2][:80]}...")
            print()
    except Exception as e:
        # Don't fail if memory database isn't available
        pass
    
    print("\033[1;36mCurator:\033[0m Hello and welcome to The Council!\n")
    print("I'm the Curator — your fast assistant to help craft great queries for the full council's bold deliberation.\n")
    print("The council takes ~12 minutes for deep reasoning, so let's refine your idea first.\n")
    print("How can I help today?\n")

    curator_history = []  # Conversation history with Curator only
    last_proposal = None  # Store last self-improvement proposal
    last_healing_proposal = None  # Deprecated: kept for backward compatibility
    healing_records = {}
    next_healing_id = 1
    pending_healing_id = None
    pending_apply = None  # Track applied-but-uncommitted proposal
    waiting_for_confirmation = False  # Track if we're waiting for yes/no
    refined_query = None  # Store refined query when Curator asks for confirmation
    error_capture = ErrorCapture(project_root=Path(__file__).resolve().parent)
    orchestrator = HealingOrchestrator(run_council_sync, project_root=Path(__file__).resolve().parent)

    while True:
        try:
            # Standard input() handles multi-line paste correctly:
            # User can paste multi-line text, press Enter once, and input() returns the full text
            # Processing only happens after Enter is pressed - no auto-trigger on paste
            user_input = input("\033[1;34mYou:\033[0m ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in {"exit", "quit"}:
                print("\n\033[1;32mCouncil session ended. Goodbye!\033[0m")
                break

            fix_parts = user_input.lower().split()
            if len(fix_parts) == 2 and fix_parts[0] == "fix" and fix_parts[1].isdigit():
                proposal_id = int(fix_parts[1])
                record = healing_records.get(proposal_id)
                if not record:
                    print(f"\n\033[1;31mNo self-healing proposal found for ID {proposal_id}.\033[0m\n")
                    continue
                record["error_context"]["stack_summary"] = record["stack_summary"]
                _display_healing_review(
                    record["proposal"],
                    record["error_context"],
                    record["diff_summary"],
                    proposal_id,
                )
                pending_healing_id = proposal_id
                continue

            if pending_healing_id is not None:
                record = healing_records.get(pending_healing_id)
                if not record:
                    pending_healing_id = None
                    continue
                if user_input.lower() in {"yes", "y"}:
                    log_entry = build_log_entry(
                        error_context=record["error_context"],
                        proposal_id=str(pending_healing_id),
                        proposal_summary=record["proposal_summary"],
                        files_changed=record["diff_summary"]["files"],
                        loc_changed_estimate=record["diff_summary"]["loc_changed"],
                        approval_status="approved",
                    )
                    append_log_entry(orchestrator.log_path, log_entry)

                    branch_name = f"self-healing/{pending_healing_id}"
                    try:
                        branch_name = orchestrator.create_branch(branch_name)
                    except Exception as exc:
                        print(f"\n\033[1;31mFailed to create branch: {exc}\033[0m\n")
                        fail_entry = build_log_entry(
                            error_context=record["error_context"],
                            proposal_id=str(pending_healing_id),
                            proposal_summary=record["proposal_summary"],
                            files_changed=record["diff_summary"]["files"],
                            loc_changed_estimate=record["diff_summary"]["loc_changed"],
                            approval_status="failed_apply",
                        )
                        append_log_entry(orchestrator.log_path, fail_entry)
                        pending_healing_id = None
                        continue

                    commit_message = f"Self-heal: {record['proposal'].root_cause[:72]}".strip()
                    try:
                        result = orchestrator.apply_fix(
                            record["proposal"],
                            commit_message=commit_message,
                            run_tests=True,
                            auto_commit=True,
                        )
                    except Exception as exc:
                        print(f"\n\033[1;31mSelf-healing apply failed: {exc}\033[0m\n")
                        fail_entry = build_log_entry(
                            error_context=record["error_context"],
                            proposal_id=str(pending_healing_id),
                            proposal_summary=record["proposal_summary"],
                            files_changed=record["diff_summary"]["files"],
                            loc_changed_estimate=record["diff_summary"]["loc_changed"],
                            approval_status="failed_apply",
                        )
                        append_log_entry(orchestrator.log_path, fail_entry)
                        pending_healing_id = None
                        continue

                    if result.get("applied"):
                        print("\n\033[1;32mSelf-healing changes applied.\033[0m")
                        print(f"Branch: {branch_name}")
                        test_results = result.get("tests", [])
                        if test_results:
                            print("Test results:")
                            for test in test_results:
                                status = "ok" if test.get("returncode", 1) == 0 else "fail"
                                print(f"- {test.get('command')}: {status}")
                        if result.get("committed"):
                            print("Commit created for self-healing changes.")
                        applied_entry = build_log_entry(
                            error_context=record["error_context"],
                            proposal_id=str(pending_healing_id),
                            proposal_summary=record["proposal_summary"],
                            files_changed=record["diff_summary"]["files"],
                            loc_changed_estimate=record["diff_summary"]["loc_changed"],
                            approval_status="applied",
                        )
                        append_log_entry(orchestrator.log_path, applied_entry)
                    else:
                        print(f"\n\033[1;31mSelf-healing apply failed: {result.get('reason')} \033[0m")
                        fail_entry = build_log_entry(
                            error_context=record["error_context"],
                            proposal_id=str(pending_healing_id),
                            proposal_summary=record["proposal_summary"],
                            files_changed=record["diff_summary"]["files"],
                            loc_changed_estimate=record["diff_summary"]["loc_changed"],
                            approval_status="failed_apply",
                        )
                        append_log_entry(orchestrator.log_path, fail_entry)
                    pending_healing_id = None
                    continue
                if user_input.lower() in {"no", "n"}:
                    reject_entry = build_log_entry(
                        error_context=record["error_context"],
                        proposal_id=str(pending_healing_id),
                        proposal_summary=record["proposal_summary"],
                        files_changed=record["diff_summary"]["files"],
                        loc_changed_estimate=record["diff_summary"]["loc_changed"],
                        approval_status="rejected",
                    )
                    append_log_entry(orchestrator.log_path, reject_entry)
                    print("\n\033[1;33mSelf-healing proposal rejected.\033[0m\n")
                    pending_healing_id = None
                    continue

                print("\n\033[1;33mPlease answer 'yes' or 'no'.\033[0m\n")
                continue

            # If a proposal was applied and awaiting commit confirmation
            if pending_apply:
                if user_input.lower() in {"yes", "y"}:
                    try:
                        commit_changes(
                            pending_apply["commit_message"],
                            file_paths=pending_apply["file_paths"]
                        )
                        print("\n\033[1;32mCommit created on the proposal branch.\033[0m\n")
                        deleted = cleanup_merged_proposal_branches(keep=3, base_branch="main")
                        if deleted:
                            print("\033[1;33mCleaned up merged proposal branches:\033[0m")
                            for branch in deleted:
                                print(f"- {branch}")
                            print("")
                    except Exception as e:
                        print(f"\n\033[1;31mCommit failed: {e}\033[0m\n")
                    pending_apply = None
                    continue
                if user_input.lower() in {"no", "n"}:
                    print("\n\033[1;33mLeft changes uncommitted on the proposal branch.\033[0m")
                    print("Review with: git status, git diff\n")
                    pending_apply = None
                    continue

                print("\n\033[1;33mPlease answer 'yes' to commit or 'no' to leave uncommitted.\033[0m\n")
                continue

            # Check for Self-Improvement Mode trigger (only after Enter is pressed)
            is_self_improve_trigger = (
                "self-improvement mode" in user_input.lower() or 
                "self-improve" in user_input.lower()
            )
            
            # Handle Self-Improvement Mode - bypass Curator
            if is_self_improve_trigger:
                print("\n\033[1;36mCurator:\033[0m Entering Self-Improvement Mode — the full council will now deliberate on a self-evolution proposal (~12 minutes).\n")
                try:
                    result = run_council_sync(user_input, skip_curator=True, stream=True)
                except KeyboardInterrupt:
                    print("\n\n\033[1;31mDeliberation interrupted by user.\033[0m")
                    print("Returning to Curator...\n")
                    print_header()
                    continue
                
                if "error" in result:
                    print(f"\n\033[1;31mError: {result['error']}\033[0m")
                    healing_result = _handle_self_healing(
                        error_capture,
                        orchestrator,
                        user_input,
                        {"mode": "self-improve"},
                        result["error"],
                    )
                    if healing_result:
                        _register_healing_record(
                            healing_result,
                            orchestrator,
                            healing_records,
                            next_healing_id,
                        )
                        next_healing_id += 1
                    continue
                
                # Display final answer (streaming already printed agent outputs)
                print("\n" + "="*60)
                print("\033[1;37mFINAL COUNCIL ANSWER\033[0m")
                print("="*60)
                print(result['final_answer'])
                print("\n\033[1;37mREASONING SUMMARY\033[0m")
                print(result['reasoning_summary'])

                # Handle self-improvement proposal
                if result.get("is_self_improve") and "proposal" in result:
                    last_proposal = result["proposal"]
                    print("\n" + "="*60)
                    print("\033[1;33m🔧 SELF-IMPROVEMENT PROPOSAL GENERATED\033[0m")
                    print("="*60)
                    if "description" in last_proposal:
                        print(f"\n\033[1;36mProposal:\033[0m {last_proposal['description']}")
                    if "file_changes" in last_proposal:
                        print(f"\n\033[1;36mFiles to modify:\033[0m {', '.join(last_proposal['file_changes'].keys())}")
                    if "impact" in last_proposal:
                        print(f"\n\033[1;36mExpected Impact:\033[0m {last_proposal['impact']}")
                    print("\n\033[1;33mNote: Review the proposal above before applying changes.\033[0m")
                    print("\033[1;33mIf approved, type 'approved. proceed' to apply on a new branch.\033[0m")
                else:
                    last_proposal = None

                curator_history = []  # Reset after full council run
                waiting_for_confirmation = False
                refined_query = None

                # Clean return to prompt - user can scroll up for history
                continue

            # Handle approval for self-improvement (apply proposal to a new branch)
            if user_input.lower() == "approved. proceed" and last_proposal:
                file_changes = last_proposal.get("file_changes") if isinstance(last_proposal, dict) else None
                description = last_proposal.get("description", "Self-improvement proposal") if isinstance(last_proposal, dict) else ""
                if not file_changes:
                    print("\n\033[1;31mNo file changes found in the proposal.\033[0m\n")
                    last_proposal = None
                    curator_history = []
                    waiting_for_confirmation = False
                    continue

                commit_message = f"Self-improve: {description[:60]}".strip()
                try:
                    result = apply_proposal(file_changes, commit_message=commit_message, auto_commit=False)
                except Exception as e:
                    print(f"\n\033[1;31mSelf-improvement apply failed: {e}\033[0m\n")
                    last_proposal = None
                    curator_history = []
                    waiting_for_confirmation = False
                    continue

                print("\n\033[1;32mSelf-improvement applied.\033[0m")
                print(f"Branch: {result.get('branch', 'unknown')}")
                summary = result.get("summary", {})
                if summary:
                    print("Changes:")
                    for path, stats in summary.items():
                        print(f"- {path}: +{stats.get('added', 0)} / -{stats.get('removed', 0)}")
                print("\nCommit changes to this branch now? (yes/no)")

                pending_apply = {
                    "commit_message": commit_message,
                    "file_paths": list(file_changes.keys())
                }

                last_proposal = None
                curator_history = []
                waiting_for_confirmation = False
                continue

            # Handle confirmation response
            if waiting_for_confirmation:
                if user_input.lower() in {"yes", "y"}:
                    # Run full council with refined query
                    query_to_use = refined_query if refined_query else user_input
                    print("\n\033[1;33mThe Council is deliberating...\033[0m\n")
                    try:
                        result = run_council_sync(query_to_use, skip_curator=True, stream=True)
                    except KeyboardInterrupt:
                        print("\n\n\033[1;31mDeliberation interrupted by user.\033[0m")
                        print("Returning to Curator...\n")
                        waiting_for_confirmation = False
                        refined_query = None
                        print_header()
                        continue
                    waiting_for_confirmation = False
                    refined_query = None
                    curator_history = []  # Reset after full council run
                    
                    # Display final answer (streaming already printed agent outputs)
                if "error" in result:
                    print(f"\n\033[1;31mError: {result['error']}\033[0m")
                    healing_result = _handle_self_healing(
                        error_capture,
                        orchestrator,
                        query_to_use,
                        {"mode": "full_council"},
                        result["error"],
                    )
                    if healing_result:
                        _register_healing_record(
                            healing_result,
                            orchestrator,
                            healing_records,
                            next_healing_id,
                        )
                        next_healing_id += 1
                    continue

                    print("\n" + "="*60)
                    print("\033[1;37mFINAL COUNCIL ANSWER\033[0m")
                    print("="*60)
                    print(result['final_answer'])
                    print("\n\033[1;37mREASONING SUMMARY\033[0m")
                    print(result['reasoning_summary'])

                    # Handle self-improvement proposal
                    if result.get("is_self_improve") and "proposal" in result:
                        last_proposal = result["proposal"]
                        print("\n" + "="*60)
                        print("\033[1;33m🔧 SELF-IMPROVEMENT PROPOSAL GENERATED\033[0m")
                        print("="*60)
                        if "description" in last_proposal:
                            print(f"\n\033[1;36mProposal:\033[0m {last_proposal['description']}")
                        if "file_changes" in last_proposal:
                            print(f"\n\033[1;36mFiles to modify:\033[0m {', '.join(last_proposal['file_changes'].keys())}")
                        if "impact" in last_proposal:
                            print(f"\n\033[1;36mExpected Impact:\033[0m {last_proposal['impact']}")
                        print("\n\033[1;33mNote: Review the proposal above before applying changes.\033[0m")
                        print("\033[1;33mIf approved, type 'approved. proceed' to apply on a new branch.\033[0m")
                    else:
                        last_proposal = None

                    # Clean return to prompt - user can scroll up for history
                    continue
                else:
                    # Continue conversation with Curator
                    curator_history.append({"role": "user", "content": user_input})
                    try:
                        curator_result = run_curator_only(user_input, curator_history, stream=True)
                    except KeyboardInterrupt:
                        print("\n\n\033[1;31mCurator interrupted by user.\033[0m")
                        print("Returning to input...\n")
                        waiting_for_confirmation = False
                        print_header()
                        continue
                    if "error" in curator_result:
                        print(f"\n\033[1;31mError: {curator_result['error']}\033[0m")
                        healing_result = _handle_self_healing(
                            error_capture,
                            orchestrator,
                            user_input,
                            {"mode": "curator"},
                            curator_result["error"],
                        )
                        if healing_result:
                            _register_healing_record(
                                healing_result,
                                orchestrator,
                                healing_records,
                                next_healing_id,
                            )
                            next_healing_id += 1
                        continue
                    
                    # Output already streamed, no need to print again
                    print()  # Single blank line for separation
                    
                    curator_history.append({"role": "assistant", "content": curator_result['output']})
                    
                    if curator_result.get("asking_confirmation"):
                        waiting_for_confirmation = True
                        # Try to extract refined query from Curator output
                        output = curator_result['output']
                        if "refined query ready:" in output.lower():
                            parts = output.split("refined query ready:", 1)
                            if len(parts) > 1:
                                refined_query = parts[1].split("\n")[0].strip().strip('"').strip("'")
                        if not refined_query:
                            refined_query = user_input  # Fallback to original
                    else:
                        waiting_for_confirmation = False
                    
                    # Clean return to prompt - continue conversation
                    continue
            else:
                # Normal flow: Run Curator first
                curator_history.append({"role": "user", "content": user_input})
                try:
                    curator_result = run_curator_only(user_input, curator_history, stream=True)
                except KeyboardInterrupt:
                    print("\n\n\033[1;31mCurator interrupted by user.\033[0m")
                    print("Returning to input...\n")
                    print_header()
                    continue
                
                if "error" in curator_result:
                    print(f"\n\033[1;31mError: {curator_result['error']}\033[0m")
                    healing_result = _handle_self_healing(
                        error_capture,
                        orchestrator,
                        user_input,
                        {"mode": "curator"},
                        curator_result["error"],
                    )
                    if healing_result:
                        _register_healing_record(
                            healing_result,
                            orchestrator,
                            healing_records,
                            next_healing_id,
                        )
                        next_healing_id += 1
                    continue
                
                # Output already streamed, no need to print again
                
                curator_history.append({"role": "assistant", "content": curator_result['output']})
                
                # Check if Curator is asking for confirmation
                if curator_result.get("asking_confirmation"):
                    waiting_for_confirmation = True
                    # Try to extract refined query from Curator output
                    output = curator_result['output']
                    if "refined query ready:" in output.lower():
                        parts = output.split("refined query ready:", 1)
                        if len(parts) > 1:
                            refined_query = parts[1].split("\n")[0].strip().strip('"').strip("'")
                    if not refined_query:
                        refined_query = user_input  # Fallback to original
                    
                    print("\n" + "-"*60)
                    continue  # Wait for user's yes/no response
                else:
                    # Curator is still refining, continue conversation
                    # Clean return to prompt
                    continue

        except KeyboardInterrupt:
            print("\n\n\033[1;32mSession interrupted. Goodbye!\033[0m")
            break
        except Exception as e:
            print(f"\n\033[1;31mError: {e}\033[0m")
            healing_result = _handle_self_healing(
                error_capture,
                orchestrator,
                user_input,
                {"mode": "interactive"},
                str(e),
                exc=e,
            )
            if healing_result:
                _register_healing_record(
                    healing_result,
                    orchestrator,
                    healing_records,
                    next_healing_id,
                )
                next_healing_id += 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single-shot fallback
        ensure_model()
        prompt = " ".join(sys.argv[1:])
        result = run_council_sync(prompt)
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            error_capture = ErrorCapture(project_root=Path(__file__).resolve().parent)
            orchestrator = HealingOrchestrator(run_council_sync, project_root=Path(__file__).resolve().parent)
            healing_result = _handle_self_healing(
                error_capture,
                orchestrator,
                prompt,
                {"mode": "single_shot"},
                result["error"],
            )
            if healing_result:
                _register_healing_record(
                    healing_result,
                    orchestrator,
                    {},
                    1,
                )
            sys.exit(1)
        print("\n=== Council Results ===")
        print(f"Prompt: {result.get('prompt', prompt)}")
        for agent in result.get('agents', []):
            print(f"\n{agent['name']}:")
            print(agent['output'])
        print("\nFinal Answer:")
        print(result.get('final_answer', 'N/A'))
        print("\nReasoning Summary:")
        print(result.get('reasoning_summary', 'N/A'))
    else:
        interactive_mode()
