import asyncio
from concurrent.futures import ThreadPoolExecutor
from crewai import Task, Crew, Process
from src.agents import researcher, critic, planner, judge

def run_council_sync(prompt: str) -> dict:
    # Define tasks (all on same prompt, but role-specific)
    research_task = Task(
        description=f"Research and explore: {prompt}",
        expected_output="Comprehensive insights and options",
        agent=researcher
    )

    critic_task = Task(
        description=f"Critique the research on: {prompt}",
        expected_output="Weaknesses and improvements",
        agent=critic,
        context=[research_task]  # Depends on research
    )

    plan_task = Task(
        description=f"Plan structured steps for: {prompt}",
        expected_output="Actionable plan",
        agent=planner,
        context=[research_task, critic_task]  # Builds on prior
    )

    judge_task = Task(
        description=f"Synthesize all responses for: {prompt}",
        expected_output="Final answer and brief rationale",
        agent=judge,
        context=[research_task, critic_task, plan_task]  # Combines all
    )

    # Create crew
    crew = Crew(
        agents=[researcher, critic, planner, judge],
        tasks=[research_task, critic_task, plan_task, judge_task],
        process=Process.sequential,
        verbose=2
    )

    # Run with timeout handling
    try:
        result = crew.kickoff()
    except Exception as e:
        return {"error": str(e)}

    # Parse outputs - CrewAI output can be string or object with .raw_output
    def get_output(task):
        if hasattr(task.output, 'raw_output'):
            return task.output.raw_output
        elif hasattr(task.output, 'content'):
            return task.output.content
        else:
            return str(task.output) if task.output else "No output"
    
    agents_outputs = [
        {"name": "Researcher", "output": get_output(research_task)},
        {"name": "Critic", "output": get_output(critic_task)},
        {"name": "Planner", "output": get_output(plan_task)},
        {"name": "Judge", "output": get_output(judge_task)}
    ]

    # Extract final from judge (assume judge outputs "Final Answer: ...\nRationale: ...")
    judge_output = get_output(judge_task)
    if "Rationale:" in judge_output:
        parts = judge_output.split("Rationale:")
        final_answer = parts[0].replace("Final Answer:", "").strip()
        reasoning_summary = parts[1].strip() if len(parts) > 1 else "N/A"
    else:
        final_answer = judge_output
        reasoning_summary = "Synthesized from all agent inputs"

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

