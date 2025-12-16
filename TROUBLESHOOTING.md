# Troubleshooting Guide

## Issue: Script Hangs When Running

If `python run_council.py "your prompt"` hangs and doesn't respond:

### Quick Check
1. **Is Ollama running?** 
   ```bash
   curl http://localhost:11434/api/tags
   ```
   Should return a JSON list of models.

2. **Is the model available?**
   ```bash
   ollama list
   ```
   Should show `phi3:mini` (or your configured model).

### Common Causes

#### 1. LiteLLM Not Connecting to Ollama
The script patches LiteLLM in `run_council.py` to inject `api_base`, but if this fails:

**Solution:** Ensure environment variables are set:
```bash
export OLLAMA_API_BASE=http://localhost:11434
export OLLAMA_BASE_URL=http://localhost:11434
python run_council.py "your prompt"
```

#### 2. CrewAI/LiteLLM Version Issues
CrewAI 0.61.0 with certain LiteLLM versions may have connection issues.

**Solution:** Try downgrading LiteLLM:
```bash
source venv/bin/activate
pip install 'litellm==1.44.22'  # Version specified in requirements
```

#### 3. Model Name Format
The model must be in format `ollama/phi3:mini` (with `ollama/` prefix).

**Solution:** Check `.env` file:
```
LLM_MODEL=phi3:mini
```
(Not `ollama/phi3:mini` - the code adds the prefix automatically)

### Debug Mode

To see what's happening, you can add verbose logging:

```python
import litellm
litellm.set_verbose = True
```

Or set environment variable:
```bash
export LITELLM_LOG=DEBUG
python run_council.py "your prompt"
```

### Alternative: Direct LiteLLM Test

Test if LiteLLM can connect directly:

```python
import os
os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"
from litellm import completion

response = completion(
    model="ollama/phi3:mini",
    messages=[{"role": "user", "content": "test"}],
    api_base="http://localhost:11434"
)
print(response.choices[0].message.content)
```

If this works but CrewAI doesn't, the issue is in how CrewAI calls LiteLLM.

