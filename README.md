# Local 4-Agent AI Council

This project implements a fully local, offline "AI council" with 4 agents running on small, quantized models via Ollama. No cloud APIs or external keys are required. It's optimized for a 2018 MacBook Pro (6-core i7, 16GB RAM, CPU-only).

## Features

- **Agents**: Researcher (gathers info/explores), Critic (points out weaknesses), Planner (structures steps), Synthesizer/Judge (combines into final answer).
- **Orchestration**: CrewAI for sequential task execution.
- **API**: FastAPI for HTTP access.
- **CLI**: Simple terminal interface.
- **UI**: Minimal web UI served by the API (plain HTML/JS).
- **Config**: Editable via .env for model, temperature, etc.
- **Offline**: Runs entirely locally after model download.

See `LOCAL_SETUP.md` for macOS installation steps.
See `LOCAL_MODELS.md` for model recommendations.
See `EXAMPLES.md` for sample prompts and outputs.

## Quick Start

1. Follow `LOCAL_SETUP.md` to set up Ollama and models.
2. Copy `.env.example` to `.env` and adjust if needed.
3. Activate venv: `source venv/bin/activate`
4. Run CLI: `python run_council.py "Your prompt here"`
5. Run API/UI: `uvicorn src.api.main:app --reload`
6. Open http://localhost:8000 in your browser for the UI.
7. Or POST to http://localhost:8000/council with JSON `{"prompt": "Your prompt"}`.

## Performance Notes

- On your 2018 Mac, expect 10-30 seconds per agent response (depending on prompt length and model).
- Tweak `.env`: Lower `LLM_MAX_TOKENS` or `LLM_TEMPERATURE` for faster responses.
- If sluggish, switch to a smaller model in `LOCAL_MODELS.md`.
- Monitor RAM: Keep under 12GB usage to avoid swapping.

