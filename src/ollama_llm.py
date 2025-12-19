import os
import litellm
from dotenv import load_dotenv

load_dotenv()

# Configure LiteLLM for longer timeouts on CPU first loads
litellm.success_callback = []  # Optional: suppress logs if needed
litellm.failure_callback = []

def ollama_completion(messages: list, **kwargs):
    """
    Direct LiteLLM completion call to Ollama – bypasses CrewAI routing issues
    """
    # Allow max_tokens to be overridden via kwargs, otherwise use env variable
    max_tokens = kwargs.pop("max_tokens", int(os.getenv("LLM_MAX_TOKENS", 500)))
    
    response = litellm.completion(
        model="ollama/phi3:mini",
        messages=messages,
        api_base="http://localhost:11434",
        temperature=kwargs.pop("temperature", float(os.getenv("LLM_TEMPERATURE", 0.7))),
        max_tokens=max_tokens,
        timeout=kwargs.pop("timeout", 1800),  # 30 minutes for slow CPU first load
        **kwargs
    )
    return response.choices[0].message.content

# For compatibility if needed elsewhere
class OllamaLLM:
    def __call__(self, messages: list):
        return ollama_completion(messages)

