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

### 3. Pull the recommended model (in a new Terminal tab)

```bash
ollama pull phi3:mini
```

This downloads ~2.3 GB once. It's fast on CPU and perfect for your hardware.

**Alternative for more capability (slower)**: `ollama pull llama3:8b`

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

**Optional**: Open `.env` in a text editor and tweak (e.g., change model to `ollama/llama3:8b`, lower `LLM_MAX_TOKENS=300` for faster responses).

**That's it – setup complete!**

---

## Running the Council

### CLI Interface

```bash
python run_council.py "Test prompt: What is the capital of France?"
```

### API and Web UI

```bash
uvicorn src.api.main:app --reload
```

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
- **Timeouts**: Increase `LLM_MAX_TOKENS` in `.env` if responses are cut off.
- **RAM issues**: Close other apps; use smaller model (phi3:mini).
- **No external calls**: Project uses dummy/no keys; verify with network monitor.

