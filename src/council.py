import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from src.ollama_llm import ollama_completion

def run_curator_only(prompt: str, conversation_history: list = None) -> dict:
    """
    Run only the Curator agent for fast, conversational query refinement.
    Returns Curator output and whether it's asking for confirmation.
    """
    if conversation_history is None:
        conversation_history = []
    
    # Build context from conversation history (only actual history, not fabricated)
    history_summary = ""
    if conversation_history:
        history_summary = "\n".join([
            f"{'You' if msg['role']=='user' else 'Curator'}: {msg['content']}"
            for msg in conversation_history[-6:]  # Last 3 exchanges
        ])
    else:
        history_summary = "(This is the first message in this session.)"
    
    curator_prompt = f"""You are the Curator — a fast, helpful, and strictly factual assistant for The Council.
CORE RULES:
- NEVER invent names, titles, or details. Use only the user's provided name (e.g., if they say "I'm Flynn", call them Flynn). If no name, use "you".
- NEVER reference non-existent conversations, members, or history.
- ONLY respond based on the current message and actual session history.
- Be warm, casual, and engaging — like a friendly assistant.
- Help refine the query naturally over turns.
- ONLY ask for deliberation when the query is clear/refined: "I have a refined query ready: '[query]' \nReady for the full council deliberation? (yes/no)"
- Keep responses short, direct, and engaging (under 150 words).

Prompt: {prompt}
Session history (if any): {history_summary}"""
    
    try:
        curator_output = ollama_completion(
            [{"role": "user", "content": curator_prompt}],
            max_tokens=300,  # Hard cap — very fast
            temperature=0.8  # Slightly lower for reliability
        )
        
        # Check if Curator is asking for confirmation
        # Only mark as asking if there's a substantive query (not just greetings)
        is_greeting_only = len(prompt.strip()) < 30 and any(
            word in prompt.lower() for word in ['hi', 'hello', 'hey', 'greeting', 'who are you', 'what are you']
        )
        asking_confirmation = (
            not is_greeting_only and (
                "ready for the full council" in curator_output.lower() or
                "full council deliberation" in curator_output.lower() or
                "(yes/no)" in curator_output.lower() or
                "refined query ready" in curator_output.lower()
            )
        )
        
        return {
            "output": curator_output,
            "asking_confirmation": asking_confirmation,
            "prompt": prompt
        }
    except Exception as e:
        return {"error": f"Curator failed: {str(e)}"}

def run_council_sync(prompt: str, previous_proposal: dict = None, skip_curator: bool = False) -> dict:
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
            diffs = apply_changes(file_changes)
            
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
            return {"error": f"Execution failed: {str(e)}"}
    
    # Curator agent (fast receptionist/assistant) - only if not skipped
    curator_output = ""
    if not skip_curator:
        print("Starting council – loading model (first run only, please wait)...")
        print("\nRunning Curator (fast assistant)...")
        curator_prompt = f"""You are the Curator — a fast, witty, knowledgeable assistant (inspired by the Curator from Ready Player One).
Your role:
- Greet the user warmly  
- Quickly understand and clarify/refine the query if ambiguous
- Summarize the intent concisely
- Hand off to the full council for deep, bold deliberation
Keep your response short and engaging (target ~150-300 tokens max).
Never give the final answer yourself — always pass to the council.
Prompt: {prompt}"""
        
        try:
            curator_output = ollama_completion(
                [{"role": "user", "content": curator_prompt}],
                max_tokens=300,  # Hard cap — very fast
                temperature=0.8  # Slightly lower for reliability
            )
            print(f"Curator complete: {len(curator_output)} chars\n")
        except Exception as e:
            return {"error": f"Curator failed: {str(e)}"}
    else:
        # When skipping Curator (after confirmation), show a message
        curator_output = f"Curator: Understood. Deliberation beginning with refined query: {prompt}"
        print("Starting full council deliberation...\n")
    
    # Researcher agent
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
        research_output = ollama_completion([{"role": "user", "content": researcher_prompt}])
        print(f"Researcher complete: {len(research_output)} chars\n")
    except Exception as e:
        return {"error": f"Researcher failed: {str(e)}"}

    # Critic agent
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
        critic_output = ollama_completion([{"role": "user", "content": critic_prompt}])
        print(f"Critic complete: {len(critic_output)} chars\n")
    except Exception as e:
        return {"error": f"Critic failed: {str(e)}"}

    # Planner agent
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
        planner_output = ollama_completion([{"role": "user", "content": planner_prompt}])
        print(f"Planner complete: {len(planner_output)} chars\n")
    except Exception as e:
        return {"error": f"Planner failed: {str(e)}"}

    # Judge/Synthesizer agent
    print("Running Judge (visionary synthesis)...\n")
    if is_self_improve_mode:
        judge_prompt = f"""You are the Judge/Synthesizer creating a formal self-improvement proposal for the Council codebase.

Your task: Synthesize the analysis into ONE high-leverage, concrete improvement with executable code changes.

Required structure — follow EXACTLY:
Final Answer:
PROPOSAL: [Clear one-sentence description of the improvement]

FILES_TO_CHANGE:
[File path 1]:
[Complete new content for file 1 - include full file content, not just diffs]

[File path 2]:
[Complete new content for file 2 if applicable]

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
        judge_output = ollama_completion([{"role": "user", "content": judge_prompt}])
        print(f"Judge complete: {len(judge_output)} chars\n")
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
