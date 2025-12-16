import os
os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"
from litellm import completion
response = completion(
    model="ollama/phi3:mini",
    messages=[{"role": "user", "content": "What is 2+2? Answer in one word."}],
    api_base="http://localhost:11434"
)
print("Response:", response.choices[0].message.content)
