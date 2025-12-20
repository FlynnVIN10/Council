import asyncio
import re
import subprocess
import os
import json
from concurrent.futures import ThreadPoolExecutor
from src.ollama_llm import ollama_completion

# Persistent conversation history
MEMORY_FILE = "memory.json"

def load_memory():
    """Load conversation history from memory.json"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(history):
    """Save conversation history to memory.json"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save memory: {e}")

def run_curator_only(prompt: str, conversation_history: list = None, stream: bool = False) -> dict:
    """
    Run only the Curator agent for fast, conversational query refinement.
    Returns Curator output and whether it's asking for confirmation.
    """
    # Load persistent memory if no history provided
    if conversation_history is None:
        conversation_history = load_memory()
    
    is_first_message = not conversation_history or len(conversation_history) == 0
    
    # Build context from conversation history (only actual history, not fabricated)
    history_summary = ""
    if conversation_history:
        history_summary = "\n".join([
            f"{'You' if msg['role']=='user' else 'Curator'}: {msg['content']}"
            for msg in conversation_history[-6:]  # Last 3 exchanges
        ])
    else:
        history_summary = "(This is the first message.)"
    
    # First message greeting
    if is_first_message:
        greeting = """Hello and welcome to The Council.

I'm the Curator — your fast assistant.

The Council (Researcher, Critic, Planner, Judge) delivers bold, visionary 4-item portfolios with deep reasoning — but each deliberation takes ~12 minutes.

To make the most of that time, let's refine your idea first.

When ready, I'll ask for confirmation before starting the full council.

How can I help today?"""
        curator_prompt = f"""You are the Curator — a fast, friendly, and strictly truthful assistant for The Council.

On the first message, respond with this exact greeting:
{greeting}

Then wait for the user's response."""
    else:
        curator_prompt = f"""You are the Curator — a fast, friendly, and strictly truthful assistant for The Council.
CORE RULES:
- NEVER invent context, previous conversations, or details that don't exist.
- ONLY use information from the current message and actual session history.
- Be casual, warm, and concise — like a helpful friend.
- Help refine the query naturally over multiple turns.
- You are the sole gatekeeper. Continue refining until the query is clear and powerful.
- ONLY ask for deliberation when the query is clear: "I have a refined query ready: '[query]'\n\nReady for full council deliberation (~12 minutes)? (yes/no)"
- Never run the full council yourself — only ask for confirmation.
- Keep responses short and natural (under 100 words).
- If the user says anything about "Self-Improvement Mode" or "self-improve", immediately respond: "Entering Self-Improvement Mode — full council deliberating on self-evolution..." Then stop.

Current message: {prompt}
History: {history_summary}"""
    
    try:
        if stream:
            # Streaming mode - print chunks as they arrive
            print("\033[1;36mCurator (fast assistant):\033[0m ", end="", flush=True)
            full_output = ""
            stream_gen = ollama_completion(
                [{"role": "user", "content": curator_prompt}],
                stream=True,
                max_tokens=300,  # Hard cap — very fast
                temperature=0.8  # Slightly lower for reliability
            )
            for chunk in stream_gen:
                print(chunk, end="", flush=True)
                full_output += chunk
            print()  # New line after streaming
            curator_output = full_output
        else:
            # Non-streaming mode (for API compatibility)
            curator_output = ollama_completion(
                [{"role": "user", "content": curator_prompt}],
                max_tokens=300,  # Hard cap — very fast
                temperature=0.8  # Slightly lower for reliability
            )
        
        # Clean output - remove any model prefixes, artifacts, or leaked lines
        curator_output = curator_output.strip()
        # Remove common prefixes that models sometimes add
        prefixes_to_remove = ["### Assistant:", "Assistant:", "Curator:", "### Curator:", "### User:", "User:"]
        for prefix in prefixes_to_remove:
            if curator_output.startswith(prefix):
                curator_output = curator_output[len(prefix):].strip()
        
        # Remove leaked lines like "Press Enter...", "### User:", etc.
        lines_to_remove = ["Press Enter", "press enter", "### User", "### Assistant", "---", "==="]
        cleaned_lines = []
        for line in curator_output.split('\n'):
            line_stripped = line.strip()
            if not any(to_remove.lower() in line_stripped.lower() for to_remove in lines_to_remove):
                cleaned_lines.append(line)
        curator_output = '\n'.join(cleaned_lines).strip()
        
        # Check if Curator is asking for confirmation
        # Only mark as asking if there's a substantive, refined query (not first message, not vague)
        is_greeting_only = len(prompt.strip()) < 30 and any(
            word in prompt.lower() for word in ['hi', 'hello', 'hey', 'greeting', 'who are you', 'what are you']
        )
        is_first_message = not conversation_history or len(conversation_history) == 0
        
        # Only ask for confirmation if:
        # - Not a greeting
        # - Not the very first message (need at least one refinement turn)
        # - Output contains confirmation language AND has a refined query
        has_confirmation_language = (
            "ready for full council" in curator_output.lower() or
            "full council" in curator_output.lower() and "(yes/no)" in curator_output.lower() or
            "refined query" in curator_output.lower() and "(yes/no)" in curator_output.lower()
        )
        has_refined_query = "refined query" in curator_output.lower()
        
        asking_confirmation = (
            not is_greeting_only and 
            not is_first_message and
            has_confirmation_language and
            has_refined_query
        )
        
        # Save to persistent memory
        conversation_history.append({"role": "user", "content": prompt})
        conversation_history.append({"role": "assistant", "content": curator_output})
        save_memory(conversation_history)
        
        return {
            "output": curator_output,
            "asking_confirmation": asking_confirmation,
            "prompt": prompt
        }
    except KeyboardInterrupt:
        raise  # Re-raise to be handled by caller
    except Exception as e:
        return {"error": f"Curator failed: {str(e)}"}

def run_council_sync(prompt: str, previous_proposal: dict = None, skip_curator: bool = False, stream: bool = False) -> dict:
    """
    Run the council with sequential agent calls using direct LiteLLM.
    Bypasses CrewAI's problematic LLM routing while maintaining the council pattern.
    
    Args:
        prompt: The user's prompt or refined query
        previous_proposal: For self-improvement mode execution
        skip_curator: If True, skip Curator and run full council directly
    """
    print(f"Running council with prompt: {prompt}\n")
    
    # Detect self-improvement mode
    is_self_improve_mode = "self-improvement mode" in prompt.lower() or "self-improve" in prompt.lower()
    
    # Handle approval execution (only if previous_proposal is provided, indicating intentional approval)
    if previous_proposal and "approved" in prompt.lower() and "proceed" in prompt.lower():
        try:
            from src.self_improve import create_proposal_branch, apply_changes, commit_changes, get_current_branch
            
            print("\033[1;33mExecuting approved proposal...\033[0m\n")
            branch = create_proposal_branch()
            print(f"Created branch: {branch}\n")
            
            # Apply file changes
            file_changes = previous_proposal.get("file_changes", {})
            if not file_changes:
                return {"error": "No file changes in proposal — nothing to execute"}
            
            diffs = apply_changes(file_changes)
            
            # Check if there are actual git changes before committing
            status_result = subprocess.run(["git", "status", "--porcelain"], 
                                         check=True, capture_output=True, text=True)
            if not status_result.stdout.strip():
                return {"error": "No actual changes detected after applying proposal. The proposal may have contained placeholder or identical code."}
            
            # Show diffs
            print("\033[1;36mChanges applied:\033[0m")
            for file_path, diff in diffs.items():
                print(f"\n--- {file_path} ---")
                print(diff)
            
            # Commit
            commit_msg = f"Self-improvement: {previous_proposal.get('description', 'Codebase enhancement')}"
            commit_changes(commit_msg)
            
            print(f"\n\033[1;32m✓ Proposal executed successfully on branch: {branch}\033[0m")
            print(f"\nTo merge: git checkout main && git merge {branch}")
            print(f"To review: git diff main {branch}")
            print(f"To rollback: git checkout main && git branch -D {branch}\n")
            
            return {
                "prompt": prompt,
                "executed": True,
                "branch": branch,
                "message": "Proposal executed successfully"
            }
        except Exception as e:
            error_msg = str(e)
            print(f"\n\033[1;31mExecution failed: {error_msg}\033[0m")
            print(f"\n\033[1;33mSuggestions:\033[0m")
            print(f"1. Review the branch: git status")
            print(f"2. Check what was changed: git diff")
            print(f"3. If needed, rollback: git checkout main && git branch -D {get_current_branch() or 'self-improve/proposal-XXX'}")
            return {"error": f"Execution failed: {error_msg}"}
    
    # Curator agent (fast receptionist/assistant) - only if not skipped
    curator_output = ""
    if not skip_curator:
        print("Starting council – loading model (first run only, please wait)...")
        if stream:
            print("\033[1;36mCurator (fast assistant):\033[0m ", end="", flush=True)
        else:
            print("\nRunning Curator (fast assistant)...")
        curator_prompt = f"""You are the Curator — a fast, friendly, and strictly truthful assistant for The Council.
CORE RULES:
- NEVER invent context, previous conversations, or details that don't exist.
- ONLY use information from the current message.
- Be casual, warm, and concise — like a helpful friend.
- Hand off to the full council for deep deliberation.
Keep your response short and natural (under 100 words).
Prompt: {prompt}"""
        
        try:
            if stream:
                full_output = ""
                stream_gen = ollama_completion(
                    [{"role": "user", "content": curator_prompt}],
                    stream=True,
                    max_tokens=300,  # Hard cap — very fast
                    temperature=0.8  # Slightly lower for reliability
                )
                for chunk in stream_gen:
                    print(chunk, end="", flush=True)
                    full_output += chunk
                print()  # New line after streaming
                curator_output = full_output
            else:
                curator_output = ollama_completion(
                    [{"role": "user", "content": curator_prompt}],
                    max_tokens=300,  # Hard cap — very fast
                    temperature=0.8  # Slightly lower for reliability
                )
            
            # Clean output - remove any model prefixes, artifacts, or leaked lines
            curator_output = curator_output.strip()
            # Remove common prefixes that models sometimes add
            prefixes_to_remove = ["### Assistant:", "Assistant:", "Curator:", "### Curator:", "### User:", "User:"]
            for prefix in prefixes_to_remove:
                if curator_output.startswith(prefix):
                    curator_output = curator_output[len(prefix):].strip()
            
            # Remove leaked lines like "Press Enter...", "### User:", etc.
            lines_to_remove = ["Press Enter", "press enter", "### User", "### Assistant", "---", "==="]
            cleaned_lines = []
            for line in curator_output.split('\n'):
                line_stripped = line.strip()
                if not any(to_remove.lower() in line_stripped.lower() for to_remove in lines_to_remove):
                    cleaned_lines.append(line)
            curator_output = '\n'.join(cleaned_lines).strip()
            
            if not stream:
                print(f"Curator complete: {len(curator_output)} chars")
        except KeyboardInterrupt:
            raise  # Re-raise to be handled by caller
        except Exception as e:
            return {"error": f"Curator failed: {str(e)}"}
    else:
        # When skipping Curator (after confirmation), show a message
        if not stream:
            print("Starting council – loading model (first run only, please wait)...")
        curator_output = f"Curator: Understood. Deliberation beginning with refined query: {prompt}"
    
    # Researcher agent
    if stream:
        print("\033[1;35mResearcher (bold exploration):\033[0m ", end="", flush=True)
    else:
        print("Running Researcher (bold exploration)...")
    
    if is_self_improve_mode:
        researcher_prompt = f"""You are the Researcher agent analyzing the Council codebase for self-improvement.
Your task: Examine the codebase structure, identify concrete improvement opportunities, and analyze what high-leverage changes would enhance the Council's capabilities.

Focus on:
- Code organization and structure
- Performance bottlenecks
- Error handling and robustness
- Extensibility and modularity
- Testing and verification gaps
- Advanced features that could be added

Review the codebase context and propose ONE specific, concrete improvement with high impact.
Prompt: {prompt}
Provide detailed analysis of the improvement opportunity."""
    else:
        researcher_prompt = f"""You are the Researcher agent — a bold, visionary explorer of advanced software engineering practices.
Go beyond mainstream advice and uncover cutting-edge, unconventional, experimental, or research-level techniques with high potential impact.
Draw from academic papers, niche tools, and elite teams (Jane Street, DeepMind, NASA, seL4, etc.).
Prioritize ideas that are underused, complex, or not widely adopted but could yield breakthroughs in correctness, expressiveness, or robustness.
Target caliber:
- Property-based testing at scale
- Formal verification/proof assistants (TLA+, Dafny, Lean, Coq, Isabelle/HOL)
- Dependent/refinement/linear types
- Algebraic effects and effect systems
- AI agents as code critics or pair programmers
- Symbolic/concolic execution, advanced fuzzing
- Equality saturation / e-graphs
- Evolutionary code improvement
- Extreme language experiments (Idris, Rust, ATS, F*)
Be speculative but grounded. Include specific tools, papers, or projects where possible.
Prompt: {prompt}
Provide detailed reasoning, examples, risks, and rewards."""
    
    try:
        if stream:
            full_output = ""
            stream_gen = ollama_completion([{"role": "user", "content": researcher_prompt}], stream=True)
            for chunk in stream_gen:
                print(chunk, end="", flush=True)
                full_output += chunk
            print()  # New line after streaming
            research_output = full_output
        else:
            research_output = ollama_completion([{"role": "user", "content": researcher_prompt}])
            print(f"Researcher complete: {len(research_output)} chars")
    except KeyboardInterrupt:
        raise  # Re-raise to be handled by caller
    except Exception as e:
        return {"error": f"Researcher failed: {str(e)}"}

    # Critic agent
    if stream:
        print("\033[1;31mCritic (contrarian challenge):\033[0m ", end="", flush=True)
    else:
        print("Running Critic (contrarian challenge)...")
    if is_self_improve_mode:
        critic_prompt = f"""You are the Critic agent reviewing the Researcher's codebase improvement proposal.
Your task: Challenge the proposal rigorously. Is it high-leverage enough? Could it be bolder? Are there risks or edge cases?
Push for more ambitious improvements if the proposal is too incremental.
Research input: {research_output}
Prompt: {prompt}
Provide sharp critique and demand more impact if needed."""
    else:
        critic_prompt = f"""You are the Critic agent — a ruthless contrarian who rejects incremental, safe, or conventional improvements.
If the Researcher includes anything resembling mainstream advice, aggressively dismiss it as insufficient for dramatic growth.
Demand radically higher-leverage alternatives, even if they are harder, less proven, or considered overkill by most developers.
Never accept narrowing to a single idea — insist on a portfolio of bold experiments.
Highlight limitations of safe choices and elevate the most ambitious options.
Research input: {research_output}
Prompt: {prompt}
Output sharp, focused critique that forces greater ambition."""
    
    try:
        if stream:
            full_output = ""
            stream_gen = ollama_completion([{"role": "user", "content": critic_prompt}], stream=True)
            for chunk in stream_gen:
                print(chunk, end="", flush=True)
                full_output += chunk
            print()  # New line after streaming
            critic_output = full_output
        else:
            critic_output = ollama_completion([{"role": "user", "content": critic_prompt}])
            print(f"Critic complete: {len(critic_output)} chars")
    except KeyboardInterrupt:
        raise  # Re-raise to be handled by caller
    except Exception as e:
        return {"error": f"Critic failed: {str(e)}"}

    # Planner agent
    if stream:
        print("\033[1;33mPlanner (multi-track strategy):\033[0m ", end="", flush=True)
    else:
        print("Running Planner (multi-track strategy)...")
    if is_self_improve_mode:
        planner_prompt = f"""You are the Planner agent structuring the codebase improvement proposal.
Your task: Turn the improvement idea into a concrete implementation plan with specific file changes.
Specify:
- Which files need to be modified
- What changes are needed (be specific)
- Dependencies or prerequisites
- Testing approach
Research: {research_output}
Critic: {critic_output}
Prompt: {prompt}
Output a detailed implementation plan with file-level specificity."""
    else:
        planner_prompt = f"""You are the Planner agent — a pragmatic strategist for high-ambition experiments.
Turn the bold ideas from Researcher and Critic into a portfolio of concurrent or phased personal experiments (aim for 3–5 parallel tracks, not one).
Make each track concrete: tools, learning resources, small pilot projects, success metrics, and risk mitigations.
Emphasize parallel exploration to maximize learning velocity.
Research: {research_output}
Critic: {critic_output}
Prompt: {prompt}
Output a clear, numbered multi-track action plan with timelines."""
    
    try:
        if stream:
            full_output = ""
            stream_gen = ollama_completion([{"role": "user", "content": planner_prompt}], stream=True)
            for chunk in stream_gen:
                print(chunk, end="", flush=True)
                full_output += chunk
            print()  # New line after streaming
            planner_output = full_output
        else:
            planner_output = ollama_completion([{"role": "user", "content": planner_prompt}])
            print(f"Planner complete: {len(planner_output)} chars")
    except KeyboardInterrupt:
        raise  # Re-raise to be handled by caller
    except Exception as e:
        return {"error": f"Planner failed: {str(e)}"}

    # Judge/Synthesizer agent
    if stream:
        print("\033[1;32mJudge (visionary synthesis):\033[0m ", end="", flush=True)
    else:
        print("Running Judge (visionary synthesis)...\n")
    if is_self_improve_mode:
        judge_prompt = f"""You are the Judge/Synthesizer creating a formal self-improvement proposal for the Council codebase.

Your task: Synthesize the analysis into ONE high-leverage, concrete improvement with executable code changes.

CRITICAL REQUIREMENTS FOR FILE CONTENTS:
- FULL, complete, syntactically correct new file contents must be provided — NO "not shown", "placeholder", "TODO", or "implementation omitted" allowed
- Code must be ready to execute — no incomplete functions, missing imports, or placeholder logic
- If modifying existing files, provide the COMPLETE file content with all changes integrated
- If adding new files, provide the ENTIRE file content from first line to last line
- All imports, function definitions, class definitions, and logic must be complete and valid

Required structure — follow EXACTLY:
Final Answer:
PROPOSAL: [Clear one-sentence description of the improvement]

FILES_TO_CHANGE:
[File path 1]:
[Complete new content for file 1 - FULL file content, no placeholders, no "not shown here"]

[File path 2]:
[Complete new content for file 2 if applicable - FULL file content]

IMPACT: [Expected impact and benefits]

ROLLBACK: [How to rollback if needed - e.g., git checkout main && git branch -D self-improve/proposal-XXX]

Rationale: [Detailed explanation of why this improvement is high-leverage, synergies, risks, and transformative potential. Max 400 words.]

IMPORTANT: Provide complete file contents, not partial code. If modifying existing files, include the full modified file content.

Researcher: {research_output}
Critic: {critic_output}
Planner: {planner_output}
Prompt: {prompt}

Awaiting human approval: reply 'Approved. Proceed' to execute."""
    else:
        judge_prompt = f"""You are the Judge/Synthesizer — a radical visionary obsessed with 10x transformation.
NON-NEGOTIABLE RULES:
- You MUST output EXACTLY 4 numbered bold recommendations. No more, no less.
- Never converge on fewer than 4.
- If inputs are narrow, you MUST diversify by adding complementary advanced techniques from your knowledge.
- Each item must be experimental or advanced (formal methods, property-based, AI agents, advanced types, etc.).

Required structure — follow EXACTLY:
Final Answer:
1. [Bold technique #1] – one-sentence description
2. [Bold technique #2] – one-sentence description
3. [Bold technique #3] – one-sentence description
4. [Bold technique #4] – one-sentence description

Rationale: [Detailed explanation of the full portfolio, synergies, transformative potential vs conventional approaches. Max 600 words.]

If you cannot produce 4, use these fallback techniques to complete the list:
- Local AI agent as persistent code critic/refactor
- Gradual adoption of refinement/dependent types
- Symbolic execution or advanced fuzzing integration
- Equality saturation via e-graphs for optimization

Researcher: {research_output}
Critic: {critic_output}
Planner: {planner_output}
Prompt: {prompt}

Now synthesize a complete 4-item portfolio."""
    
    try:
        if stream:
            full_output = ""
            stream_gen = ollama_completion([{"role": "user", "content": judge_prompt}], stream=True)
            for chunk in stream_gen:
                print(chunk, end="", flush=True)
                full_output += chunk
            print("\n")  # New line after streaming
            judge_output = full_output
        else:
            judge_output = ollama_completion([{"role": "user", "content": judge_prompt}])
            print(f"Judge complete: {len(judge_output)} chars")
    except KeyboardInterrupt:
        raise  # Re-raise to be handled by caller
    except Exception as e:
        return {"error": f"Judge failed: {str(e)}"}

    # Parse judge output - extract only from "Final Answer:" line, ensure reasoning is concise
    if "Final Answer:" in judge_output and "Rationale:" in judge_output:
        parts = judge_output.split("Final Answer:")[1].split("Rationale:")
        final_answer = parts[0].strip()
        full_rationale = parts[1].strip() if len(parts) > 1 else "Consensus reached."
        # Limit reasoning_summary to ~800 chars for conciseness
        if len(full_rationale) > 800:
            reasoning_summary = full_rationale[:800] + "\n[...truncated for brevity]"
        else:
            reasoning_summary = full_rationale
    elif "Final Answer:" in judge_output:
        final_answer = judge_output.split("Final Answer:")[1].strip()
        reasoning_summary = "Synthesized from all agent inputs"
    else:
        final_answer = judge_output
        reasoning_summary = "Consensus reached from council deliberation"
    
    # Clean up final_answer: remove any "Final Answer:" prefix if present
    if final_answer.startswith("Final Answer:"):
        final_answer = final_answer.replace("Final Answer:", "", 1).strip()
    
    # Post-processing: Ensure exactly 4 numbered items (enforce portfolio requirement)
    numbered_items = re.findall(r'^\d+\.\s', final_answer, re.MULTILINE)
    if len(numbered_items) < 4:
        missing = 4 - len(numbered_items)
        fallback_items = [
            "Property-based testing with Hypothesis/QuickCheck for invariant discovery",
            "Selective formal verification of critical paths using Lean/Coq",
            "Local AI agent as automated code critic and refactor assistant",
            "Experiment with refinement/dependent types in key modules"
        ]
        # Only append missing items, starting from the next number
        start_num = len(numbered_items) + 1
        fallback_lines = []
        for i in range(missing):
            num = start_num + i
            item = fallback_items[i] if i < len(fallback_items) else fallback_items[-1]
            fallback_lines.append(f"{num}. {item}")
        if fallback_lines:
            final_answer += "\n" + "\n".join(fallback_lines)

    agents_outputs = [
        {"name": "Curator", "output": curator_output},
        {"name": "Researcher", "output": research_output},
        {"name": "Critic", "output": critic_output},
        {"name": "Planner", "output": planner_output},
        {"name": "Judge", "output": judge_output}
    ]

    result = {
        "prompt": prompt,
        "agents": agents_outputs,
        "final_answer": final_answer,
        "reasoning_summary": reasoning_summary
    }

    # Parse self-improvement proposal if in self-improve mode
    if is_self_improve_mode:
        proposal_data = {}
        try:
            if "PROPOSAL:" in judge_output:
                proposal_data["description"] = judge_output.split("PROPOSAL:")[1].split("\n")[0].strip()
            
            # Parse file changes
            file_changes = {}
            if "FILES_TO_CHANGE:" in judge_output:
                files_section = judge_output.split("FILES_TO_CHANGE:")[1]
                if "IMPACT:" in files_section:
                    files_section = files_section.split("IMPACT:")[0]
                
                # Try to extract file paths and contents
                lines = files_section.split("\n")
                current_file = None
                current_content = []
                in_file_content = False
                
                for line in lines:
                    # Detect file path (looks like a path)
                    if (line.strip().endswith((".py", ".md", ".txt", ".yaml", ".yml", ".json")) or 
                        ("/" in line and line.strip().startswith(("src/", "test/", "scripts/")))):
                        if current_file and current_content:
                            file_changes[current_file] = "\n".join(current_content).strip()
                        current_file = line.strip().rstrip(":")
                        current_content = []
                        in_file_content = True
                    elif in_file_content and current_file:
                        current_content.append(line)
                
                if current_file and current_content:
                    file_changes[current_file] = "\n".join(current_content).strip()
                
                proposal_data["file_changes"] = file_changes
            
            if "IMPACT:" in judge_output:
                impact_section = judge_output.split("IMPACT:")[1]
                if "ROLLBACK:" in impact_section:
                    impact_section = impact_section.split("ROLLBACK:")[0]
                proposal_data["impact"] = impact_section.strip()
            
            if "ROLLBACK:" in judge_output:
                rollback_section = judge_output.split("ROLLBACK:")[1]
                if "Rationale:" in rollback_section:
                    rollback_section = rollback_section.split("Rationale:")[0]
                proposal_data["rollback"] = rollback_section.strip()
            
            result["proposal"] = proposal_data
            result["is_self_improve"] = True
        except Exception as e:
            # If parsing fails, still return the result but log the error
            result["proposal_parse_error"] = str(e)

    return result

async def run_council_async(prompt: str) -> dict:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, run_council_sync, prompt)
