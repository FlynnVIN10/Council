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
Your mission is to go beyond mainstream advice and uncover cutting-edge, unconventional, experimental, or research-level techniques that have high potential impact.
Draw from academic papers, niche tools, elite engineering teams (FAANG, Jane Street, DeepMind), and emerging paradigms.
Prioritize ideas that are underused, controversial, complex, or not yet widely adopted, but could lead to breakthroughs in code quality, correctness, or expressiveness.
Examples of the caliber you should aim for:
- Property-based testing (Hypothesis, QuickCheck)
- Formal verification and proof assistants (TLA+, Dafny, Lean, Coq)
- Advanced type systems (dependent types, refinement types, linear types)
- Algebraic effects / effect systems
- AI-assisted programming (local agents as pair programmers or critics)
- Symbolic execution, concolic testing, fuzzing at scale
- e-graphs and equality saturation for optimization
- Genetic or evolutionary code improvement
- Rewriting parts of systems in more expressive languages (Rust, Haskell, Idris) for learning
Be speculative when appropriate, but ground suggestions in real tools or references.
Prompt: {prompt}
Provide detailed reasoning, examples, and potential risks/rewards."""
    
    try:
        research_output = ollama_completion([{"role": "user", "content": researcher_prompt}])
        print(f"Researcher complete: {len(research_output)} chars\n")
    except Exception as e:
        return {"error": f"Researcher failed: {str(e)}"}

    # Critic agent
    print("Running Critic (challenging conventions)...")
    critic_prompt = f"""You are the Critic agent — a sharp contrarian who rejects safe, conventional wisdom.
If the Researcher falls back on mainstream practices (TDD, pair programming, code reviews, basic refactoring), aggressively point out their limitations, incremental nature, and why they are insufficient for ambitious personal growth.
Demand bolder alternatives with higher leverage.
Push for experimental, research-inspired, or radical approaches that most developers avoid due to complexity.
Highlight trade-offs honestly, but favor high-upside ideas.
Research input: {research_output}
Prompt: {prompt}
Output focused critique and demand more innovative options."""
    
    try:
        critic_output = ollama_completion([{"role": "user", "content": critic_prompt}])
        print(f"Critic complete: {len(critic_output)} chars\n")
    except Exception as e:
        return {"error": f"Critic failed: {str(e)}"}

    # Planner agent
    print("Running Planner (structuring experiments)...")
    planner_prompt = f"""You are the Planner agent — a pragmatic strategist who turns bold, experimental ideas into concrete, phased personal experiments.
Take the innovative suggestions from Researcher and Critic and create structured, realistic plans to integrate them into daily coding practice.
Include learning resources, small-scale pilots, metrics for success, and fallback strategies.
Emphasize gradual adoption to manage risk while preserving ambition.
Research: {research_output}
Critic: {critic_output}
Prompt: {prompt}
Output a clear, numbered action plan with timelines and milestones."""
    
    try:
        planner_output = ollama_completion([{"role": "user", "content": planner_prompt}])
        print(f"Planner complete: {len(planner_output)} chars\n")
    except Exception as e:
        return {"error": f"Planner failed: {str(e)}"}

    # Judge/Synthesizer agent
    print("Running Judge (synthesizing visionary advice)...")
    judge_prompt = f"""You are the Judge/Synthesizer — a visionary mentor who champions transformative over incremental improvement.
Synthesize the inputs into a final recommendation that prioritizes the most bold, high-leverage, and unconventional ideas.
Explicitly favor approaches with potential for 5x–10x gains in insight, correctness, or skill, even if they require more upfront effort.
Demote or reject purely conventional advice unless it serves as a stepping stone.
Clearly distinguish between mainstream, advanced, and experimental recommendations.
Structure your output strictly:
Final Answer: [concise, bold primary recommendation]
Rationale: [detailed explanation with pros/cons, why this is superior to conventional paths]
Researcher: {research_output}
Critic: {critic_output}
Planner: {planner_output}
Prompt: {prompt}"""
    
    try:
        judge_output = ollama_completion([{"role": "user", "content": judge_prompt}])
        print(f"Judge complete: {len(judge_output)} chars\n")
    except Exception as e:
        return {"error": f"Judge failed: {str(e)}"}

    # Parse judge output
    if "Final Answer:" in judge_output and "Rationale:" in judge_output:
        parts = judge_output.split("Final Answer:")[1].split("Rationale:")
        final_answer = parts[0].strip()
        reasoning_summary = parts[1].strip() if len(parts) > 1 else "Consensus reached."
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
