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
    print("Running Researcher... (this may take a few minutes on first run)")
    researcher_prompt = f"""You are the Researcher agent.
Your role: Gather information and explore options for the given prompt.
Your goal: Provide comprehensive insights and options.

Prompt: {prompt}

Respond thoroughly with insights and options:"""
    
    try:
        research_output = ollama_completion([{"role": "user", "content": researcher_prompt}])
        print(f"Researcher complete: {len(research_output)} chars\n")
    except Exception as e:
        return {"error": f"Researcher failed: {str(e)}"}

    # Critic agent
    print("Running Critic...")
    critic_prompt = f"""You are the Critic agent.
Your role: Evaluate and point out weaknesses in the researcher's proposal.
Your goal: Identify flaws, risks, and improvements in ideas.

Research findings: {research_output}
Original prompt: {prompt}

Point out weaknesses and improvements:"""
    
    try:
        critic_output = ollama_completion([{"role": "user", "content": critic_prompt}])
        print(f"Critic complete: {len(critic_output)} chars\n")
    except Exception as e:
        return {"error": f"Critic failed: {str(e)}"}

    # Planner agent
    print("Running Planner...")
    planner_prompt = f"""You are the Planner agent.
Your role: Turn ideas into structured steps or plans.
Your goal: Create clear, actionable steps from concepts.

Research: {research_output}
Critic feedback: {critic_output}
Original prompt: {prompt}

Create structured actionable steps:"""
    
    try:
        planner_output = ollama_completion([{"role": "user", "content": planner_prompt}])
        print(f"Planner complete: {len(planner_output)} chars\n")
    except Exception as e:
        return {"error": f"Planner failed: {str(e)}"}

    # Judge/Synthesizer agent
    print("Running Judge...")
    judge_prompt = f"""You are the Judge/Synthesizer agent.
Your role: Synthesize responses from other agents into a final answer with rationale.
Your goal: Combine inputs, resolve conflicts, and produce a coherent final output.

Researcher findings: {research_output}
Critic feedback: {critic_output}
Planner steps: {planner_output}
Original prompt: {prompt}

Synthesize into a final answer with brief rationale.
Format your response EXACTLY as:
Final Answer: [your final answer here]
Rationale: [brief summary of reasoning here]"""
    
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
