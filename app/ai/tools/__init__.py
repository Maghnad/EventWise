"""Tools and tool registry framework for AI agents.

Provides:
- ``BaseTool``: Abstract base class for all agent tools
- ``FunctionTool``: Wrapper to create tools from standard async functions
- ``ToolRegistry``: Central registry for discovering, inspecting, and executing tools
- ``tool`` decorator: Decorator for turning Python functions into registered tools
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


# ==============================================================================
# Exceptions
# ==============================================================================


class ToolError(Exception):
    """Base exception for all tool execution errors."""


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found in the registry."""


class ToolExecutionError(ToolError):
    """Raised when tool execution fails with an internal error."""


# ==============================================================================
# Base Tool
# ==============================================================================


class BaseTool(ABC):
    """Abstract base class for all tools available to AI agents."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: type[BaseModel] | None = None,
    ) -> None:
        """Initialize tool definition.

        Args:
            name: Unique identifier for the tool (e.g. "calculate_budget").
            description: Concise explanation of what the tool does and when to use it.
            parameters_schema: Optional Pydantic model defining argument validation schema.
        """
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool logic with validated arguments.

        Args:
            **kwargs: Arguments matching ``parameters_schema``.

        Returns:
            The tool execution result (serializable dictionary, string, or primitive).
        """

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert the tool definition to the OpenAI Function Tool schema format."""
        schema: dict[str, Any] = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            },
        }
        if self.parameters_schema:
            schema["function"]["parameters"] = (
                self.parameters_schema.model_json_schema()
            )
        else:
            schema["function"]["parameters"] = {
                "type": "object",
                "properties": {},
            }
        return schema


# ==============================================================================
# Function Tool Wrapper
# ==============================================================================


class FunctionTool(BaseTool):
    """Tool implementation wrapping an async or sync callable function."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any | Awaitable[Any]],
        parameters_schema: type[BaseModel] | None = None,
    ) -> None:
        super().__init__(
            name=name, description=description, parameters_schema=parameters_schema
        )
        self._func = func

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the wrapped function, converting sync to async if needed."""
        try:
            if self.parameters_schema:
                validated = self.parameters_schema(**kwargs)
                call_args = validated.model_dump()
            else:
                call_args = kwargs

            if inspect.iscoroutinefunction(self._func):
                return await self._func(**call_args)
            return self._func(**call_args)
        except Exception as exc:
            raise ToolExecutionError(
                f"Error executing tool '{self.name}': {exc}"
            ) from exc


# ==============================================================================
# Tool Registry
# ==============================================================================


class ToolRegistry:
    """Registry maintaining a collection of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> BaseTool:
        """Register a tool instance.

        Args:
            tool: BaseTool instance to register.

        Returns:
            The registered tool instance.
        """
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> BaseTool | None:
        """Retrieve a tool by name, returning None if not found."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered by name."""
        return name in self._tools

    def __contains__(self, name: str) -> bool:
        """Support 'name in registry' syntax."""
        return name in self._tools

    def list_tools(self) -> list[BaseTool]:
        """Return a list of all registered tools."""
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Return all registered tools formatted for OpenAI function calling."""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs: Any) -> Any:
        """Look up and execute a tool by name.

        Args:
            name: The tool name.
            **kwargs: Arguments to pass to the tool.

        Returns:
            Execution result.

        Raises:
            ToolNotFoundError: If no tool is registered with ``name``.
            ToolExecutionError: If execution fails.
        """
        tool = self.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' is not registered.")
        return await tool.execute(**kwargs)


# Global default registry
default_registry = ToolRegistry()


def tool(
    name: str | None = None,
    description: str | None = None,
    parameters_schema: type[BaseModel] | None = None,
    registry: ToolRegistry | None = None,
) -> Callable[[Callable[..., Any]], FunctionTool]:
    """Decorator to convert an async or sync function into a registered BaseTool.

    Args:
        name: Tool name. Defaults to the decorated function's name.
        description: Description of the tool. Defaults to function's docstring.
        parameters_schema: Optional Pydantic schema for parameters.
        registry: Target registry to add to. Defaults to ``default_registry``.
    """

    def decorator(fn: Callable[..., Any]) -> FunctionTool:
        tool_name = name or fn.__name__
        tool_desc = description or fn.__doc__ or f"Execute {tool_name}"
        t = FunctionTool(
            name=tool_name,
            description=tool_desc.strip(),
            func=fn,
            parameters_schema=parameters_schema,
        )
        target_registry = registry or default_registry
        target_registry.register(t)
        return t

    return decorator


__all__ = [
    "BaseTool",
    "FunctionTool",
    "ToolError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolRegistry",
    "default_registry",
    "tool",
]
