"""Abstract base class for all EventWise AI agents.

Defines the core interface and shared execution harness for agents,
including prompt templating, LLM client delegation, and tool invocation.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.llm_client import LLMClient
from app.ai.tools import BaseTool, ToolNotFoundError, ToolRegistry

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ==============================================================================
# Exceptions
# ==============================================================================


class AgentError(Exception):
    """Base exception for all agent execution errors."""


class AgentConfigurationError(AgentError):
    """Raised when an agent is improperly configured."""


class AgentExecutionError(AgentError):
    """Raised when an agent encounters an unrecoverable failure during execution."""


# ==============================================================================
# Base Agent Abstract Class
# ==============================================================================


class BaseAgent(ABC):
    """Abstract base class providing common facilities for all AI agents.

    Subclasses must implement ``run()`` to define their domain-specific logic.
    """

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        llm_client: LLMClient | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            name: Identifier for the agent (e.g. "BudgetPlannerAgent").
            description: Concise summary of the agent's role and capabilities.
            system_prompt: Default system instructions steering the agent's behaviour.
            llm_client: Optional injected LLMClient instance. Defaults to a new instance.
            tools: Optional initial list of tools available to this agent.
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.llm_client = llm_client or LLMClient()
        self.tools = ToolRegistry()

        if tools:
            for t in tools:
                self.tools.register(t)

    def register_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent's registry.

        Args:
            tool: BaseTool instance to register.
        """
        self.tools.register(tool)

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool from the agent's registry by name.

        Args:
            tool_name: Registered name of the tool.
            **kwargs: Arguments to forward to the tool.

        Returns:
            The tool's execution result.

        Raises:
            AgentExecutionError: If tool is missing or fails.
        """
        try:
            return await self.tools.execute(tool_name, **kwargs)
        except ToolNotFoundError as exc:
            logger.error("Agent '%s' attempted to execute unregistered tool: %s", self.name, tool_name)
            raise AgentExecutionError(f"Tool '{tool_name}' not available to agent '{self.name}'.") from exc
        except Exception as exc:
            logger.exception("Agent '%s' failed executing tool '%s': %s", self.name, tool_name, exc)
            raise AgentExecutionError(f"Execution of tool '{tool_name}' failed: {exc}") from exc

    async def call_llm(
        self,
        prompt: str,
        system_override: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """Convenience method to request a text completion from the agent's LLM.

        Args:
            prompt: User prompt content.
            system_override: Optional system prompt to override the agent's default.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated response string.
        """
        sys_prompt = system_override if system_override is not None else self.system_prompt
        return await self.llm_client.generate_text(
            prompt=prompt,
            system_prompt=sys_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def call_llm_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_override: str | None = None,
        temperature: float = 0.2,
    ) -> T:
        """Convenience method to request structured output parsed into a Pydantic model.

        Args:
            prompt: User prompt content.
            response_model: Target Pydantic model schema.
            system_override: Optional system prompt override.
            temperature: Sampling temperature.

        Returns:
            An instance of ``response_model``.
        """
        sys_prompt = system_override if system_override is not None else self.system_prompt
        return await self.llm_client.generate_structured(
            prompt=prompt,
            response_model=response_model,
            system_prompt=sys_prompt,
            temperature=temperature,
        )

    @abstractmethod
    async def run(
        self,
        input_text: str,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute the agent's core workflow.

        Args:
            input_text: User request, instructions, or raw input query.
            context: Optional contextual data (e.g. event details, active budget).

        Returns:
            Domain-specific execution outcome (string, dict, or Pydantic model).
        """


__all__ = [
    "AgentConfigurationError",
    "AgentError",
    "AgentExecutionError",
    "BaseAgent",
]
