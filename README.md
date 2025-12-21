# The Council (5-Agent System)

This project implements a fully local, offline "AI council" with 5 agents running on small, quantized models via Ollama. No cloud APIs or external keys are required. It's optimized for a 2018 MacBook Pro (6-core i7, 16GB RAM, CPU-only).

## Features

- **Agents**: Curator (fast assistant/receptionist), Researcher (gathers info/explores), Critic (points out weaknesses), Planner (structures steps), Synthesizer/Judge (combines into final answer).
- **Orchestration**: CrewAI for sequential task execution.
- **CLI**: Interactive terminal interface with natural conversation flow.
- **Config**: Editable via .env for model, temperature, etc.
- **Offline**: Runs entirely locally after model download.

See `LOCAL_SETUP.md` for macOS installation steps.
See `LOCAL_MODELS.md` for model recommendations.
See `EXAMPLES.md` for sample prompts and outputs.

## Quick Start (Local CLI - Recommended)

The Council runs locally by default for simplicity, stability, and direct control. This is the recommended approach.

1. Follow `LOCAL_SETUP.md` to set up Ollama and models.
2. Copy `.env.example` to `.env` and adjust if needed.
3. Run: `./council-restart.sh`
4. The script starts Ollama locally and drops you directly into the interactive CLI prompt ("You:").
5. Conversation flows naturally with the Curator and full council deliberation on demand.

**Alternative**: Run manually:
```bash
source venv/bin/activate
python run_council.py  # Interactive mode
# or
python run_council.py "Your prompt here"  # Single-shot
```

**Note**: First run will automatically pull the phi3 model via `ollama pull phi3` (~2.3GB), which takes a few minutes.

### Docker Deployment (Advanced/Optional)

Docker is available for portability or containerized environments, but it's **optional and advanced**. The local CLI is simpler, more stable, and recommended for most users.

If you need Docker:

```bash
docker-compose up --build
```

- Starts Ollama and The Council CLI in containers
- Drops directly into interactive "You:" prompt
- All memory and data persisted in volumes
- Web UI available at http://localhost:8000 if desired

To restart cleanly:
```bash
docker-compose down && docker-compose up --build
```

**Important**: Local CLI is the default and recommended approach. Docker is for advanced use cases and may require additional configuration.

## Performance Notes

- **Note**: Uses direct LiteLLM calls to Ollama for reliable performance on CPU (bypasses CrewAI integration issues).
- **Important**: Always run `ollama serve` in a separate terminal before starting the council.
- On your 2018 Mac with recommended settings (LLM_MAX_TOKENS=3700), expect ~12 minutes for a full council run.
- Monitor RAM: Keep under 12GB usage to avoid swapping.
- **Recommended model**: phi3 (capable on CPU).

## Performance Expectations on 2018 MacBook Pro (CPU-only)

- **First council run: 2–5 minutes**  
  This is normal — Ollama is loading the full model (~2.3 GB) into memory for the first time.

- **Subsequent runs with recommended settings: ~12 minutes total**  
  With `LLM_MAX_TOKENS=3700`, full council runs take approximately 12 minutes. The model remains loaded as long as `ollama serve` is running.

**Tip**: Keep the terminal running `ollama serve` open between sessions to avoid reloading.

## Running The Council

**Start (Local CLI - recommended):**
```bash
./council-restart.sh
```
The script starts Ollama locally and drops you directly into the interactive CLI prompt ("You:").

Conversation flows naturally with the Curator and full council deliberation on demand.

**Stop:**
Press `Ctrl+C` to exit the CLI, then:
```bash
pkill -f "ollama serve"
```
This stops the local Ollama server.

**Docker (advanced/optional):**
If using Docker, use `docker-compose down` to stop containers. Note: Local CLI is recommended for stability and simplicity.

## CLI Experience (LLM-Style Conversation)

Run: `python run_council.py`

- **Continuous chat** with full history context across multiple turns
- **Visual chain-of-thought**: see all 5 agents deliberate (Curator → Researcher → Critic → Planner → Judge)
- **Slick colored interface** with clear sections highlighting each agent's contribution
- **Press Enter** between responses for clean flow
- **Type 'exit'** to end session

The interactive mode provides a conversational experience where you can build on previous responses. Single-shot mode is still available by passing a prompt as an argument.

## Council Mode: Bold & Experimental

The council is intentionally tuned for radical, high-leverage software engineering growth.
It prioritizes frontier practices (formal methods, advanced types, property-based testing, AI agents, etc.) and produces portfolios of ambitious experiments rather than single safe recommendations.

## The Curator Agent

The council begins with the Curator — a fast, engaging assistant who:
- Greets and clarifies your query through quick conversation
- Refines your query to ensure clarity and power
- Asks for confirmation before starting the full ~12-minute council deliberation
- Provides quick initial feedback while keeping the experience responsive

**Interaction Flow**:
1. You ask a question or make a request
2. Curator responds quickly, refining and clarifying as needed
3. When the query is ready, Curator asks: "Are you ready for the full council deliberation? (yes/no)"
4. Reply "yes" to proceed with full deliberation, or "no" to continue refining with Curator

This gives you full control and prevents unwanted long runs. The Curator uses a lower token limit (400 tokens) for quick responses, while the full council (Researcher → Critic → Planner → Judge) uses the full token allocation for deep, bold deliberation.

### Recommended Settings (Bold & Deep Mode)

For the optimal balance of rich, complete 4-item portfolios and reasonable runtime:

```
LLM_TEMPERATURE=1.0
LLM_MAX_TOKENS=3700    # ~12 minute full council runs on CPU-only hardware
                       # Provides deep, untruncated outputs with acceptable wait time
```

**Note**: This is the recommended configuration for daily use with complex or meta prompts.

## Self-Improvement Mode (Proposal Only)

Simply include `"self-improvement mode"` or `"self-improve"` in your message to trigger. Single-line input, natural conversation flow.

**Example**: `"Council, enter self-improvement mode and analyze how to improve error handling"`

The Council will:
- **Curator responds**: "Entering Self-Improvement Mode — the full council will now deliberate on a self-evolution proposal (~12 minutes)."
- **Full council deliberates**: Analyzes its own codebase, examines structure, identifies improvement opportunities
- **Proposes one high-leverage improvement** with concrete, complete code changes
- **Presents proposal**: Shows file changes, impact, and rollback instructions for human review

**Important**: Self-Improvement Mode is **proposal-only**. Execution is disabled for safety. The Council generates proposals for human review — you must manually apply code changes if desired.

**Example flow**:
1. Type: `"Council, enter self-improvement mode and analyze how to improve error handling"`
2. Curator acknowledges, full council deliberates (~12 minutes)
3. Review the proposal (files to change, impact, rollback plan)
4. If approved, manually apply the changes using git or your preferred method
5. The proposal contains complete file contents ready for application

This enables safe self-evolution under human oversight without risk of automatic execution.

### Success Example: Meta-Cognitive Self-Improvement

The council demonstrated true meta-cognition by analyzing and proposing radical improvements to its own codebase. When asked to self-improve, it produced a diverse 4-item portfolio of bold recommendations:

**Prompt**: "Ask yourself how you can and would like to dramatically improve the correctness and quality of your personal code? Look at your code and the entire codebase for the 'Council' platform in which you exist. How can the Council self-improve its own Council codebase/platform?"

**Final Answer** (4-item portfolio):
1. **Advanced Symbolic Execution with custom generators** – Apply symbolic execution with custom generators to verify complex agent interaction patterns and detect edge cases in the sequential deliberation workflow.
2. **AI-Enhanced Property Testing (with local AI agents)** – Integrate local AI agents to generate and refine property-based tests, ensuring invariants across all 4 agent outputs and detecting regressions automatically.
3. **Formal Model Checking + Interactive Theorem Proving (TLA+ / Isabelle/HOL)** – Model the council's agent orchestration logic formally to prove correctness properties about deliberation order, data flow, and error handling.
4. **Dependent Types & Linear Logic Integration (Idris/Agda)** – Gradually migrate critical paths to languages with dependent types to encode and enforce domain-specific constraints at compile-time, preventing entire classes of runtime errors.

This output showcases the council's ability to think recursively, applying advanced software engineering techniques to improve itself—a rare capability for a fully private, CPU-only system running a small model.

