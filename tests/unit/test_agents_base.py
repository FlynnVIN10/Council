import logging

import pytest

from src.agents import Agent


class TestAgent(Agent):
    @property
    def agent_name(self) -> str:
        return "TestAgent"

    @property
    def agent_role(self) -> str:
        return "Tester"

    def __init__(self):
        super().__init__()
        self.calls = []

    def process(self, value):
        self.calls.append(("process", value))
        return f"processed-{value}"

    def on_start(self) -> None:
        self.calls.append(("on_start", None))
        super().on_start()

    def on_finish(self, result) -> None:
        self.calls.append(("on_finish", result))
        super().on_finish(result)

    def on_error(self, error: Exception) -> None:
        self.calls.append(("on_error", str(error)))
        super().on_error(error)


class FailingAgent(TestAgent):
    def process(self, value):
        raise RuntimeError(f"boom-{value}")


def test_abstract_agent_requires_implementation():
    class IncompleteAgent(Agent):
        pass

    with pytest.raises(TypeError):
        IncompleteAgent()


def test_generate_response_calls_process_and_hooks(caplog):
    agent = TestAgent()
    with caplog.at_level(logging.INFO):
        result = agent.generate_response("ping")

    assert result == "processed-ping"
    assert agent.calls == [
        ("on_start", None),
        ("process", "ping"),
        ("on_finish", "processed-ping"),
    ]
    messages = [record.getMessage() for record in caplog.records]
    assert any("Agent start: TestAgent" in msg for msg in messages)
    assert any("Agent finished: TestAgent" in msg for msg in messages)


def test_generate_response_error_calls_on_error(caplog):
    agent = FailingAgent()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="boom-crash"):
            agent.generate_response("crash")

    assert ("on_error", "boom-crash") in agent.calls
    messages = [record.getMessage() for record in caplog.records]
    assert any("Agent error: TestAgent" in msg for msg in messages)


def test_logging_integration_default_logger_name():
    agent = TestAgent()
    assert agent.logger.name.endswith("TestAgent")
