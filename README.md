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

## Quick Start

### Docker Deployment (Recommended for Portability)

The easiest way to run The Council consistently on any machine:

```bash
docker-compose up --build
```

- Starts Ollama and The Council CLI
- Drops directly into interactive "You:" prompt
- All memory and data persisted in volumes
- Web UI still available at http://localhost:8000 if desired

To restart cleanly:
```bash
docker-compose down && docker-compose up --build
```

**Note**: First run will download the phi3:mini model (~2.3GB), which takes a few minutes.

### Local Development

1. Follow `LOCAL_SETUP.md` to set up Ollama and models.
2. Copy `.env.example` to `.env` and adjust if needed.
3. Run: `./council-restart.sh`
4. The script starts Ollama and drops you directly into the interactive CLI prompt ("You:").
5. Conversation flows naturally with the Curator and full council deliberation on demand.

**Alternative**: Run manually:
```bash
source venv/bin/activate
python run_council.py  # Interactive mode
# or
python run_council.py "Your prompt here"  # Single-shot
```

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

## Full Platform Control

**Start:**
```bash
./council-restart.sh
```
The script starts Ollama and drops you directly into the interactive CLI prompt ("You:").

Conversation flows naturally with the Curator and full council deliberation on demand.

**Stop:**
```bash
./council-down.sh
```
Cleanly shuts down all containers and processes.

**Global aliases** (add to `~/.zshrc` for access from anywhere):
```bash
alias council-restart='/Users/Flynn/Documents/GitHub/Council/council-restart.sh'
alias council-down='/Users/Flynn/Documents/GitHub/Council/council-down.sh'
```

Then `source ~/.zshrc` and you can run `council-restart` or `council-down` from any directory.

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

## Self-Improvement Mode

Simply include `"self-improvement mode"` or `"self-improve"` in your message to trigger. Single-line input, natural conversation flow.

**Example**: `"Council, enter self-improvement mode and analyze how to improve error handling"`

The Council will:
- **Curator responds**: "Entering Self-Improvement Mode — the full council will now deliberate on a self-evolution proposal (~12 minutes)."
- **Full council deliberates**: Analyzes its own codebase, examines structure, identifies improvement opportunities
- **Proposes one high-leverage improvement** with concrete, complete code changes
- **Waits for approval**: Presents the proposal with file changes, impact, and rollback instructions

**To approve and execute**: Type `"Approved. Proceed"` after reviewing the proposal.

**Safety features**:
- All changes are made on a safe branch: `self-improve/proposal-<timestamp>`
- No destructive actions (no file deletion, no main branch changes)
- Complete rollback instructions included
- Full diffs shown before and after execution
- Validation ensures complete, executable code (no placeholders)

**Example flow**:
1. Type: `"Council, enter self-improvement mode and analyze how to improve error handling"`
2. Curator acknowledges, full council deliberates (~12 minutes)
3. Review the proposal (files to change, impact, rollback plan)
4. Approve: `"Approved. Proceed"`
5. Changes are applied and committed to the proposal branch
6. Review with `git diff main self-improve/proposal-XXX`
7. Merge when satisfied or rollback with `git checkout main && git branch -D self-improve/proposal-XXX`

This turns the Council into a true self-evolving system under human oversight.

### Success Example: Meta-Cognitive Self-Improvement

The council demonstrated true meta-cognition by analyzing and proposing radical improvements to its own codebase. When asked to self-improve, it produced a diverse 4-item portfolio of bold recommendations:

**Prompt**: "Ask yourself how you can and would like to dramatically improve the correctness and quality of your personal code? Look at your code and the entire codebase for the 'Council' platform in which you exist. How can the Council self-improve its own Council codebase/platform?"

**Final Answer** (4-item portfolio):
1. **Advanced Symbolic Execution with custom generators** – Apply symbolic execution with custom generators to verify complex agent interaction patterns and detect edge cases in the sequential deliberation workflow.
2. **AI-Enhanced Property Testing (with local AI agents)** – Integrate local AI agents to generate and refine property-based tests, ensuring invariants across all 4 agent outputs and detecting regressions automatically.
3. **Formal Model Checking + Interactive Theorem Proving (TLA+ / Isabelle/HOL)** – Model the council's agent orchestration logic formally to prove correctness properties about deliberation order, data flow, and error handling.
4. **Dependent Types & Linear Logic Integration (Idris/Agda)** – Gradually migrate critical paths to languages with dependent types to encode and enforce domain-specific constraints at compile-time, preventing entire classes of runtime errors.

This output showcases the council's ability to think recursively, applying advanced software engineering techniques to improve itself—a rare capability for a fully private, CPU-only system running a small model.

