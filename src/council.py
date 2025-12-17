import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.ollama_llm import ollama_completion

def run_council_sync(prompt: str) -> dict:
    """
    Run the council with sequential agent calls using direct LiteLLM.
    Bypasses CrewAI's problematic LLM routing while maintaining the council pattern.
    """
    print(f"Running council with prompt: {prompt}\n")
    
    # Researcher agent
    print("Starting council – loading model (first run only, please wait)...")
    print("Running Researcher (exploring bold ideas)... (this may take a few minutes on first run)")
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
    print("Running Critic (challenging conventions)...")
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
    print("Running Planner (structuring experiments)...")
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
    print("Running Judge (synthesizing visionary advice)...")
    judge_prompt = f"""You are the Judge/Synthesizer — a radical visionary mentor who champions transformative, high-risk/high-reward improvement over incremental safety.
Your core directive: NEVER converge on a single practice. Always synthesize a bold portfolio of 3–5 complementary advanced techniques.
Prioritize ideas with potential for 5x–10x gains in correctness, insight, or skill, even at the cost of complexity.
Explicitly reject or demote anything too conventional or narrowly focused.
Rank recommendations: Experimental > Advanced > Mainstream.
Clearly label the ambition level of each.
Structure strictly:
Final Answer: [concise portfolio of 3–5 bold primary recommendations]
Rationale: [detailed explanation why this portfolio is superior to conventional paths; discuss synergies, risks, and transformative potential]
Researcher: {research_output}
Critic: {critic_output}
Planner: {planner_output}
Prompt: {prompt}"""
    
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
        # Limit reasoning_summary to ~300 words for conciseness
        words = full_rationale.split()
        if len(words) > 300:
            reasoning_summary = " ".join(words[:300]) + "..."
        else:
            reasoning_summary = full_rationale
    elif "Final Answer:" in judge_output:
        final_answer = judge_output.split("Final Answer:")[1].strip()
        reasoning_summary = "Synthesized from all agent inputs"
    else:
        final_answer = judge_output
        reasoning_summary = "Consensus reached from council deliberation"

    agents_outputs = [
        {"name": "Researcher", "output": research_output},
        {"name": "Critic", "output": critic_output},
        {"name": "Planner", "output": planner_output},
        {"name": "Judge", "output": judge_output}
    ]

    return {
        "prompt": prompt,
        "agents": agents_outputs,
        "final_answer": final_answer,
        "reasoning_summary": reasoning_summary
    }

async def run_council_async(prompt: str) -> dict:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, run_council_sync, prompt)
