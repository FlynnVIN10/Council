#!/usr/bin/env python3
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None


QUERY = "Analyze the pros and cons of renewable energy adoption."
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama2:7b")
DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), "..", "BENCHMARKS.md")


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=1200) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ollama_rss_bytes() -> int:
    if psutil is None:
        return 0
    rss_total = 0
    for proc in psutil.process_iter(["name", "cmdline", "memory_info"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            if "ollama" in name or "ollama" in cmdline:
                rss_total += proc.info["memory_info"].rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rss_total


def _format_bytes(value: int) -> str:
    if value <= 0:
        return "n/a"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def _write_benchmarks(entry: dict) -> None:
    lines = []
    if not os.path.exists(BENCHMARKS_PATH):
        lines.append("# Benchmarks\n")
        lines.append("| Timestamp (UTC) | Model | Load Time (s) | Response Time (s) | Ollama RSS | Notes |\n")
        lines.append("| --- | --- | --- | --- | --- | --- |\n")

    lines.append(
        "| {timestamp} | {model} | {load_time:.2f} | {response_time:.2f} | {rss} | {notes} |\n".format(
            timestamp=entry["timestamp"],
            model=entry["model"],
            load_time=entry["load_time_seconds"],
            response_time=entry["response_time_seconds"],
            rss=entry["ollama_rss"],
            notes=entry["notes"],
        )
    )

    with open(BENCHMARKS_PATH, "a", encoding="utf-8") as handle:
        handle.writelines(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Ollama model performance")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Ollama host URL")
    args = parser.parse_args()

    model = args.model
    host = args.host.rstrip("/")
    generate_url = f"{host}/api/generate"

    print(f"Benchmarking model: {model}")
    print(f"Ollama host: {host}")

    load_payload = {
        "model": model,
        "prompt": "Say OK.",
        "stream": False,
        "options": {"num_predict": 1},
    }
    query_payload = {
        "model": model,
        "prompt": QUERY,
        "stream": False,
    }

    try:
        start = time.perf_counter()
        _post_json(generate_url, load_payload)
        load_time = time.perf_counter() - start

        start = time.perf_counter()
        response = _post_json(generate_url, query_payload)
        response_time = time.perf_counter() - start
    except urllib.error.URLError as exc:
        print("Error: Ollama is not running. Please start it with: ollama serve")
        print(f"Details: {exc}")
        return 1
    except urllib.error.HTTPError as exc:
        print(f"HTTP error from Ollama: {exc}")
        return 1

    rss_bytes = _ollama_rss_bytes()
    rss_formatted = _format_bytes(rss_bytes)
    response_text = response.get("response", "").strip()
    response_length = len(response_text)

    print(f"Model load time: {load_time:.2f}s")
    print(f"Response time: {response_time:.2f}s")
    print(f"Ollama RSS: {rss_formatted}")
    print(f"Response length: {response_length} chars")

    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "load_time_seconds": load_time,
        "response_time_seconds": response_time,
        "ollama_rss": rss_formatted,
        "notes": f"query_len={len(QUERY)} response_len={response_length}",
    }
    _write_benchmarks(entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
