from crewai import Agent
from src.config.settings import llm

researcher = Agent(
    role="Researcher",
    goal="Gather information and explore options for the given prompt",
    backstory="You are a thorough researcher who gathers facts, explores ideas, and provides comprehensive insights.",
    verbose=True,
    llm=llm,
    allow_delegation=False
)

analyst = Agent(
    role="Analyst",
    goal="Analyze data and generate insights from information provided",
    backstory="You are a skilled analyst who examines information deeply, identifies patterns, and produces data-driven insights.",
    verbose=True,
    llm=llm,
    allow_delegation=False
)

critic = Agent(
    role="Critic",
    goal="Evaluate and point out weaknesses in the researcher's proposal",
    backstory="You are a sharp critic who identifies flaws, risks, and improvements in ideas.",
    verbose=True,
    llm=llm,
    allow_delegation=False
)

planner = Agent(
    role="Planner",
    goal="Turn ideas into structured steps or plans",
    backstory="You are an organized planner who creates clear, actionable steps from concepts.",
    verbose=True,
    llm=llm,
    allow_delegation=False
)

judge = Agent(
    role="Synthesizer/Judge",
    goal="Synthesize responses from other agents into a final answer with rationale",
    backstory="You are a wise judge who combines inputs, resolves conflicts, and produces a coherent final output.",
    verbose=True,
    llm=llm,
    allow_delegation=False
)
