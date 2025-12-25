import logging
from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def agent_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def agent_role(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def generate_response(self, *args: Any, **kwargs: Any) -> Any:
        self.on_start()
        try:
            result = self.process(*args, **kwargs)
            self.on_finish(result)
            return result
        except Exception as exc:
            self.on_error(exc)
            raise

    def on_start(self) -> None:
        self.logger.info("Agent start: %s (%s)", self.agent_name, self.agent_role)

    def on_finish(self, result: Any) -> None:
        self.logger.info("Agent finished: %s", self.agent_name)

    def on_error(self, error: Exception) -> None:
        self.logger.exception("Agent error: %s", self.agent_name, exc_info=error)
