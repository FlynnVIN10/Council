import argparse
import json
import os
import resource
import time
from pathlib import Path
from unittest import mock

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import council


RAM_LIMIT_BYTES = 12 * 1024 * 1024 * 1024


def _rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if rss < 100_000_000:
        return int(rss * 1024)
    return int(rss)


def _assert_ram_limit():
    rss_bytes = _rss_bytes()
    assert (
        rss_bytes < RAM_LIMIT_BYTES
    ), f"Process RSS too high: {rss_bytes} bytes"


def _patch_memory_calls():
    return mock.patch.multiple(
        council,
        get_recent_messages=mock.Mock(return_value=[]),
        get_latest_summary=mock.Mock(return_value=""),
        get_relevant_facts=mock.Mock(return_value=[]),
        get_all_preferences=mock.Mock(return_value={}),
        save_session=mock.Mock(return_value=1),
        add_message=mock.Mock(),
        save_summary=mock.Mock(),
        save_facts=mock.Mock(),
        build_session_summary=mock.Mock(return_value="summary"),
        generate_memory_snapshot=mock.Mock(return_value=("", [])),
    )


def _mock_success_completion():
    responses = [
        "Curator response (smoke).",
        "Curator response.",
        "Researcher response.",
        "Critic response.",
        "Planner response.",
        "Final Answer:\n1. One\n2. Two\n3. Three\n4. Four\nRationale: ok",
    ]
    counter = {"idx": 0}

    def _fake_completion(*args, **kwargs):
        response = responses[counter["idx"]]
        counter["idx"] += 1
        return response

    return _fake_completion


def _run_agent_smoke(use_ollama: bool) -> dict:
    timings = {}
    with _patch_memory_calls():
        if use_ollama:
            completion_patch = mock.patch.object(council, "ollama_completion", council.ollama_completion)
        else:
            completion_patch = mock.patch.object(council, "ollama_completion", _mock_success_completion())

        with completion_patch:
            start = time.perf_counter()
            curator_result = council.run_curator_only(
                "Please help me design a multi-agent test suite.",
                conversation_history=[{"role": "user", "content": "Earlier input"}],
                stream=False,
            )
            timings["curator_only_seconds"] = time.perf_counter() - start

            assert "output" in curator_result
            assert curator_result["output"]

            start = time.perf_counter()
            council_result = council.run_council_sync(
                "Provide a concise, 4-point plan for test infrastructure.",
                skip_curator=False,
                stream=False,
            )
            timings["full_council_seconds"] = time.perf_counter() - start

            agent_outputs = {agent["name"]: agent["output"] for agent in council_result["agents"]}
            for agent_name in ["Curator", "Researcher", "Critic", "Planner", "Judge"]:
                assert agent_name in agent_outputs
                assert agent_outputs[agent_name]

    return timings


def _run_ollama_failure_smoke():
    def _raise_error(*args, **kwargs):
        raise ConnectionError("Ollama is unreachable")

    with _patch_memory_calls(), mock.patch.object(council, "ollama_completion", _raise_error):
        curator_result = council.run_curator_only(
            "Please help me design a multi-agent test suite.",
            conversation_history=[{"role": "user", "content": "Earlier input"}],
            stream=False,
        )
        assert "error" in curator_result

        council_result = council.run_council_sync(
            "Provide a concise, 4-point plan for test infrastructure.",
            skip_curator=False,
            stream=False,
        )
        assert "error" in council_result


def main():
    parser = argparse.ArgumentParser(description="Council smoke tests")
    parser.add_argument("--use-ollama", action="store_true", help="Use live Ollama calls")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write latency baseline to data/smoke_latency.json",
    )
    args = parser.parse_args()

    timings = _run_agent_smoke(args.use_ollama)
    _run_ollama_failure_smoke()
    _assert_ram_limit()

    payload = {
        "timestamp": time.time(),
        "use_ollama": args.use_ollama,
        "latencies_seconds": timings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.write_baseline:
        baseline_path = os.path.join("data", "smoke_latency.json")
        with open(baseline_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
