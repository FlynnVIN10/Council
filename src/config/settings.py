import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama

load_dotenv()

# CrewAI 0.30.11 accepts LangChain LLM objects directly
# Add timeout and request_timeout to prevent hangs
llm = ChatOllama(
    model="phi3:mini",
    base_url="http://localhost:11434",
    temperature=float(os.getenv("LLM_TEMPERATURE", 0.7)),
    timeout=600,  # 10 minutes for model loading and generation
    request_timeout=600,  # 10 minutes per request
)
