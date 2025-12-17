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

- **Note**: Uses direct LiteLLM calls to Ollama for reliable performance on CPU (bypasses CrewAI integration issues).
- **Important**: Always run `ollama serve` in a separate terminal before starting the council.
- On your 2018 Mac with recommended settings (LLM_MAX_TOKENS=3700), expect ~12 minutes for a full council run.
- Monitor RAM: Keep under 12GB usage to avoid swapping.
- **Recommended model**: phi3:mini (capable on CPU).

## Performance Expectations on 2018 MacBook Pro (CPU-only)

- **First council run: 2–5 minutes**  
  This is normal — Ollama is loading the full model (~2.3 GB) into memory for the first time.

- **Subsequent runs with recommended settings: ~12 minutes total**  
  With `LLM_MAX_TOKENS=3700`, full council runs take approximately 12 minutes. The model remains loaded as long as `ollama serve` is running.

**Tip**: Keep the terminal running `ollama serve` open between sessions to avoid reloading.

## Council Mode: Bold & Experimental

The council is intentionally tuned for radical, high-leverage software engineering growth.
It prioritizes frontier practices (formal methods, advanced types, property-based testing, AI agents, etc.) and produces portfolios of ambitious experiments rather than single safe recommendations.

### Recommended Settings (Bold & Deep Mode)

For optimal rich, untruncated 4-item portfolios with detailed rationales and plans:

```
LLM_TEMPERATURE=1.0
LLM_MAX_TOKENS=3700    # ~12 minute full council runs on CPU-only hardware
                       # Provides maximum depth and completeness without cutoff
```

**Note**: This setting delivers the full visionary power of the bold/experimental council.

### Success Example: Meta-Cognitive Self-Improvement

The council demonstrated true meta-cognition by analyzing and proposing radical improvements to its own codebase. When asked to self-improve, it produced a diverse 4-item portfolio of bold recommendations:

**Prompt**: "Ask yourself how you can and would like to dramatically improve the correctness and quality of your personal code? Look at your code and the entire codebase for the 'Council' platform in which you exist. How can the Council self-improve its own Council codebase/platform?"

**Final Answer** (4-item portfolio):
1. **Advanced Symbolic Execution with custom generators** – Apply symbolic execution with custom generators to verify complex agent interaction patterns and detect edge cases in the sequential deliberation workflow.
2. **AI-Enhanced Property Testing (with local AI agents)** – Integrate local AI agents to generate and refine property-based tests, ensuring invariants across all 4 agent outputs and detecting regressions automatically.
3. **Formal Model Checking + Interactive Theorem Proving (TLA+ / Isabelle/HOL)** – Model the council's agent orchestration logic formally to prove correctness properties about deliberation order, data flow, and error handling.
4. **Dependent Types & Linear Logic Integration (Idris/Agda)** – Gradually migrate critical paths to languages with dependent types to encode and enforce domain-specific constraints at compile-time, preventing entire classes of runtime errors.

This output showcases the council's ability to think recursively, applying advanced software engineering techniques to improve itself—a rare capability for a fully private, CPU-only system running a small model.

