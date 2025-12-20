import os
import litellm
from dotenv import load_dotenv

load_dotenv()

# Configure LiteLLM for longer timeouts on CPU first loads
litellm.success_callback = []  # Optional: suppress logs if needed
litellm.failure_callback = []

def ollama_completion(messages: list, stream: bool = False, **kwargs):
    """
    Direct LiteLLM completion call to Ollama – bypasses CrewAI routing issues
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        stream: If True, returns a generator that yields content chunks
        **kwargs: Additional arguments passed to litellm.completion
    """
    # Allow max_tokens to be overridden via kwargs, otherwise use env variable
    max_tokens = kwargs.pop("max_tokens", int(os.getenv("LLM_MAX_TOKENS", 500)))
    
    # Support OLLAMA_HOST environment variable for Docker (defaults to localhost)
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    response = litellm.completion(
        model="ollama/phi3:mini",
        messages=messages,
        api_base=ollama_host,
        temperature=kwargs.pop("temperature", float(os.getenv("LLM_TEMPERATURE", 0.7))),
        max_tokens=max_tokens,
        timeout=kwargs.pop("timeout", 1800),  # 30 minutes for slow CPU first load
        stream=stream,
        **kwargs
    )
    
    if stream:
        # Return generator that yields content chunks
        def stream_generator():
            full_content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content
            # Store full content in a closure for later access (optional)
            stream_generator.full_content = full_content
        return stream_generator()
    else:
        return response.choices[0].message.content

# For compatibility if needed elsewhere
class OllamaLLM:
    def __call__(self, messages: list):
        return ollama_completion(messages)

