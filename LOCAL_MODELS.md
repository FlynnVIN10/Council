# Recommended Local Models

All models run CPU-only on your Mac via Ollama. Choose small, quantized ones for speed.

## Primary Recommendation

**Phi-3** (3.8B parameters): Fast, capable for reasoning/planning. Good for 16GB RAM.

```bash
ollama pull phi3
```

The Council automatically uses `phi3` as the default model. Configure in `.env` if needed: `LLM_MODEL=ollama/phi3`

Expected size: ~2.3 GB download.
Expected speed: 20-40 tokens/sec on your hardware.

If you want a smaller tag (when available):

```bash
ollama pull phi3:mini
```

In `.env`: `LLM_MODEL=ollama/phi3:mini`

## Alternative

**Llama 3** (8B parameters): More capable but slower (10-20 tokens/sec).

```bash
ollama pull llama3:8b
```

In `.env`: `LLM_MODEL=ollama/llama3:8b`

## Start Server

Always run `ollama serve` before using the project. No OpenAI-compatible endpoint tweaks needed—CrewAI handles it.
