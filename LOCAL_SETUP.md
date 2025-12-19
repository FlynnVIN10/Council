# Local Setup Guide for macOS (2018 MacBook Pro)

## One-Time Setup (5–10 minutes)

Open Terminal and run these commands one by one:

### 1. Clone the repo

```bash
git clone https://github.com/FlynnVIN10/Council.git
cd Council
```

### 2. Install and start Ollama (if you don't have it already)

```bash
brew install ollama  # If Homebrew not installed, it will prompt you
ollama serve         # Run this in a separate Terminal tab/window – keep it open forever when using the council
```

**Important**: You must run `ollama serve` in a separate terminal before using the council. Keep it running while you use the project.

### 3. Pull the recommended model (in a new Terminal tab)

```bash
ollama pull phi3:mini
```

This downloads ~2.3 GB once. It's fast and capable on CPU – perfect for your hardware.

**Alternative for more capability (slower)**: `ollama pull llama3:8b`

**Note**: Uses direct LiteLLM calls to Ollama for reliable performance on CPU (bypasses CrewAI integration issues).

**The Curator Agent**: The council begins with the Curator — a fast assistant who greets, clarifies queries, and hands off to the full council for deep deliberation. This makes interactions feel more responsive and conversational.

## Performance Expectations on 2018 MacBook Pro (CPU-only)

- **First council run: 2–5 minutes**  
  This is normal — Ollama is loading the full model (~2.3 GB) into memory for the first time.

- **Subsequent runs: 15–60 seconds total**  
  The model remains loaded as long as `ollama serve` is running.

**Tip**: Keep the terminal running `ollama serve` open between sessions to avoid reloading.

### 4. Set up Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Copy config template

```bash
cp .env.example .env
```

**Recommended Settings**: Open `.env` in a text editor and configure:

```
LLM_TEMPERATURE=1.0
LLM_MAX_TOKENS=3700    # ~12 minute full council runs on CPU-only hardware
                       # Provides deep, untruncated outputs with acceptable wait time
```

This is the recommended configuration for daily use with complex or meta prompts.

**That's it – setup complete!**

---

## Running the Council

### CLI Interface

**Interactive Mode** (recommended):
```bash
python run_council.py
```

- Continuous chat with full history context
- Visual chain-of-thought: see all 4 agents deliberate
- Slick colored interface with clear sections
- Press Enter between responses for clean flow
- Type 'exit' to end session

**Single-shot Mode**:
```bash
python run_council.py "Test prompt: What is the capital of France?"
```

### API and Web UI

```bash
uvicorn src.api.main:app --reload
```

### One-Command Restart

For quick full restarts (kills old Ollama, starts fresh Ollama + API):

**Option 1: Use the helper script (Recommended)**

Simply run:
```bash
./council-restart.sh
```

**Option 2: Add as a shell alias**

Add this to your shell profile (`~/.zshrc` or `~/.bash_profile`):

```bash
alias council-restart='cd /Users/Flynn/Documents/GitHub/Council && ./council-restart.sh'
```

Then reload:
```bash
source ~/.zshrc   # or source ~/.bash_profile
```

Now you can run:
```bash
council-restart
```

This restarts everything and opens the web UI at http://localhost:8000.

- **API**: POST to http://localhost:8000/council
- **UI**: Open http://localhost:8000 in browser

---

## Alternative: Automated Setup Script

You can also use the provided automation script instead of steps 2-3:

```bash
chmod +x scripts/setup_local_llm.sh
./scripts/setup_local_llm.sh
```

Then manually start Ollama server:

```bash
ollama serve
```

(Keep this terminal open; it exposes http://localhost:11434.)

---

## Troubleshooting

- **If Ollama not responding**: Ensure `ollama serve` is running in a separate terminal.
- **Timeouts**: Ensure `LLM_MAX_TOKENS=3700` in `.env` for complete responses (recommended setting).
- **RAM issues**: Close other apps; use smaller model (phi3:mini).
- **No external calls**: Project uses dummy/no keys; verify with network monitor.

