import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

llm = LLM(
    model=os.getenv("LLM_MODEL", "ollama/phi3:mini"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434"),
    temperature=float(os.getenv("LLM_TEMPERATURE", 0.7)),
    max_tokens=int(os.getenv("LLM_MAX_TOKENS", 500)),
    # Note: Context length is model-dependent; not directly settable here but can influence prompts
)

