# Local Setup Guide for macOS (2018 MacBook Pro)

## Prerequisites

- **Homebrew**: Install via `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- **Python 3.10+**: `brew install python`
- Node.js not required (UI is static HTML/JS served by FastAPI).

## Step 1: Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Set Up Local LLM (Ollama)

Run the automation script:

```bash
chmod +x scripts/setup_local_llm.sh
./scripts/setup_local_llm.sh
```

This installs Ollama (if missing), pulls phi3:mini, and prints start instructions.

Manually start Ollama server:

```bash
ollama serve
```

(Keep this terminal open; it exposes http://localhost:11434.)

## Step 3: Configure .env

Copy `.env.example` to `.env` and adjust if needed (e.g., change model):

```bash
cp .env.example .env
```

## Step 4: Run the CLI

```bash
python run_council.py "Test prompt: What is the capital of France?"
```

## Step 5: Run the API and UI

```bash
uvicorn src.api.main:app --reload
```

- **API**: POST to http://localhost:8000/council
- **UI**: Open http://localhost:8000 in browser.

## Troubleshooting

- **If Ollama not responding**: Ensure `ollama serve` is running.
- **Timeouts**: Increase `LLM_MAX_TOKENS` if responses are cut off.
- **RAM issues**: Close other apps; use smaller model.
- **No external calls**: Project uses dummy/no keys; verify with network monitor.

