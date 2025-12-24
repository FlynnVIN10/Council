import os
import time

import pytest
import requests


DEFAULT_API_URL = "http://localhost:8000/api/council"
TEST_PROMPT = "Analyze the pros and cons of renewable energy adoption."


def _require_api_url() -> str:
    url = os.getenv("COUNCIL_API_URL", DEFAULT_API_URL).rstrip("/")
    try:
        requests.post(url, json={"prompt": "ping"}, timeout=2)
    except requests.RequestException:
        pytest.skip(f"Council API not reachable at {url}")
    return url


def _post_prompt(url: str, prompt: str, timeout: int = 1200):
    start = time.perf_counter()
    response = requests.post(url, json={"prompt": prompt}, timeout=timeout)
    elapsed = time.perf_counter() - start
    return response, elapsed


@pytest.mark.integration
def test_valid_query_returns_structure():
    url = _require_api_url()
    response, elapsed = _post_prompt(url, TEST_PROMPT)

    assert response.status_code == 200
    data = response.json()
    assert data.get("prompt")
    assert isinstance(data.get("agents"), list)
    assert data.get("final_answer")
    assert data.get("reasoning_summary") is not None
    assert elapsed >= 0


@pytest.mark.integration
def test_agent_contributions_included():
    url = _require_api_url()
    response, _elapsed = _post_prompt(url, TEST_PROMPT)

    assert response.status_code == 200
    data = response.json()
    agents = data.get("agents", [])
    names = {agent.get("name") for agent in agents}
    expected = {"Curator", "Researcher", "Critic", "Planner", "Judge"}
    assert expected.issubset(names)
    for agent in agents:
        assert agent.get("output")


@pytest.mark.integration
def test_synthesizer_output_present():
    url = _require_api_url()
    response, _elapsed = _post_prompt(url, TEST_PROMPT)

    assert response.status_code == 200
    data = response.json()
    assert data.get("final_answer")
    judge_outputs = [agent for agent in data.get("agents", []) if agent.get("name") == "Judge"]
    assert judge_outputs
    assert judge_outputs[0].get("output")


@pytest.mark.integration
def test_invalid_input_returns_error():
    url = _require_api_url()
    response = requests.post(url, json={}, timeout=10)
    assert response.status_code in {400, 422, 500}

    response = requests.post(url, json={"prompt": 123}, timeout=10)
    assert response.status_code in {400, 422, 500}


@pytest.mark.integration
def test_response_time_tracking():
    url = _require_api_url()
    response, elapsed = _post_prompt(url, TEST_PROMPT)

    assert response.status_code == 200
    assert elapsed >= 0
    assert response.elapsed.total_seconds() >= 0
