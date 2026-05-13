"""Base agent interface following LangChain-style patterns."""

from __future__ import annotations

import abc
from typing import Any

import structlog


class BaseAgent(abc.ABC):
    """Abstract base class for all subagents."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = structlog.get_logger(agent=name)

    @abc.abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's primary action."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
