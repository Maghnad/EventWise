"""Unit tests for LLMClient and base agent infrastructure.

Mocks OpenAI client interactions to test retry logic, structured outputs,
and error handling without hitting real external endpoints.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import (
    APIConnectionError,
    OpenAIError,
    RateLimitError,
)
from pydantic import BaseModel

from app.ai.base_agent import AgentExecutionError, BaseAgent
from app.ai.llm_client import (
    LLMClient,
    LLMClientError,
    LLMConfigurationError,
    LLMRetryError,
    LLMStructuredOutputError,
)
from app.ai.tools import ToolRegistry, tool
from app.config import Settings

# ==============================================================================
# Test Schemas & Tools
# ==============================================================================


class EventPlan(BaseModel):
    title: str
    estimated_budget: float
    theme: str


class CalculationParams(BaseModel):
    x: int
    y: int


# ==============================================================================
# LLMClient Tests
# ==============================================================================


def test_client_initialization_with_key() -> None:
    """Verify LLMClient correctly stores explicit API key and model."""
    client = LLMClient(api_key="sk-test-key-123", model="gpt-4o-mini")
    assert client.model == "gpt-4o-mini"
    assert client.client is not None


def test_missing_api_key_raises_configuration_error() -> None:
    """Accessing .client with no key in settings or arguments raises LLMConfigurationError."""
    dummy_settings = Settings(openai_api_key="")
    client = LLMClient(api_key=None, settings=dummy_settings)
    with pytest.raises(LLMConfigurationError) as exc_info:
        _ = client.client
    assert "OpenAI API key is not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_text_success() -> None:
    """Verify generate_text calls chat.completions.create and returns content."""
    mock_choice = MagicMock()
    mock_choice.message.content = "  Welcome to the gala!  "
    mock_response = MagicMock(choices=[mock_choice])

    mock_openai = MagicMock()
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    client = LLMClient(client=mock_openai, model="gpt-4o")
    result = await client.generate_text(
        prompt="Write a welcome line",
        system_prompt="You are a helpful assistant",
        temperature=0.5,
    )

    assert result == "Welcome to the gala!"
    mock_openai.chat.completions.create.assert_awaited_once_with(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Write a welcome line"},
        ],
        temperature=0.5,
        max_tokens=None,
    )


@pytest.mark.asyncio
async def test_generate_structured_success() -> None:
    """Verify generate_structured calls beta.chat.completions.parse and returns Pydantic instance."""
    expected_plan = EventPlan(
        title="Gala 2026", estimated_budget=15000.0, theme="Starry Night"
    )
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = expected_plan
    mock_response = MagicMock(choices=[mock_choice])

    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

    client = LLMClient(client=mock_openai, model="gpt-4o")
    plan = await client.generate_structured(
        prompt="Generate a gala plan",
        response_model=EventPlan,
    )

    assert plan == expected_plan
    assert plan.title == "Gala 2026"
    assert plan.estimated_budget == 15000.0


@pytest.mark.asyncio
async def test_generate_structured_refusal_raises_error() -> None:
    """Model refusal in structured outputs raises LLMStructuredOutputError."""
    mock_choice = MagicMock()
    mock_choice.message.refusal = "Content policy violation"
    mock_choice.message.parsed = None
    mock_response = MagicMock(choices=[mock_choice])

    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

    client = LLMClient(client=mock_openai)
    with pytest.raises(LLMStructuredOutputError) as exc_info:
        await client.generate_structured(prompt="bad prompt", response_model=EventPlan)
    assert "refused generation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_structured_none_raises_error() -> None:
    """Parsed output being None raises LLMStructuredOutputError."""
    mock_choice = MagicMock()
    mock_choice.message.refusal = None
    mock_choice.message.parsed = None
    mock_response = MagicMock(choices=[mock_choice])

    mock_openai = MagicMock()
    mock_openai.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

    client = LLMClient(client=mock_openai)
    with pytest.raises(LLMStructuredOutputError) as exc_info:
        await client.generate_structured(prompt="parse test", response_model=EventPlan)
    assert "Failed to parse model output" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retry_logic_succeeds_after_transient_error() -> None:
    """Verify operation succeeds on retry if initial attempt raised RateLimitError."""
    mock_req = MagicMock()
    mock_rate_limit = RateLimitError(
        message="Rate limit exceeded", response=MagicMock(status_code=429), body=None
    )

    mock_choice = MagicMock()
    mock_choice.message.content = "Success after retry"
    mock_success = MagicMock(choices=[mock_choice])

    mock_openai = MagicMock()
    mock_openai.chat.completions.create = AsyncMock(
        side_effect=[mock_rate_limit, mock_success]
    )

    client = LLMClient(
        client=mock_openai,
        max_retries=2,
        initial_backoff_seconds=0.01,
        backoff_multiplier=1.0,
    )
    result = await client.generate_text(prompt="retry test")

    assert result == "Success after retry"
    assert mock_openai.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_retry_logic_exhaustion_raises_retry_error() -> None:
    """Persistent transient errors exceeding max_retries raise LLMRetryError."""
    mock_conn_error = APIConnectionError(request=MagicMock())

    mock_openai = MagicMock()
    mock_openai.chat.completions.create = AsyncMock(side_effect=mock_conn_error)

    client = LLMClient(
        client=mock_openai,
        max_retries=2,
        initial_backoff_seconds=0.01,
        backoff_multiplier=1.0,
    )
    with pytest.raises(LLMRetryError) as exc_info:
        await client.generate_text(prompt="fail test")

    assert "failed after 3 attempts" in str(exc_info.value)
    assert mock_openai.chat.completions.create.await_count == 3


@pytest.mark.asyncio
async def test_non_retryable_error_raises_client_error_immediately() -> None:
    """Non-transient OpenAIError raises LLMClientError without retries."""
    mock_openai = MagicMock()
    mock_openai.chat.completions.create = AsyncMock(
        side_effect=OpenAIError("Invalid authentication credentials")
    )

    client = LLMClient(client=mock_openai, max_retries=3)
    with pytest.raises(LLMClientError) as exc_info:
        await client.generate_text(prompt="auth fail")

    assert "generate_text failed" in str(exc_info.value)
    assert mock_openai.chat.completions.create.await_count == 1


# ==============================================================================
# BaseAgent & Tools Tests
# ==============================================================================


class SamplePlannerAgent(BaseAgent):
    """Test concrete implementation of BaseAgent."""

    async def run(self, input_text: str, context: dict[str, Any] | None = None) -> str:
        if "use_tool" in input_text:
            ans = await self.execute_tool("multiply", x=6, y=7)
            return f"Answer is {ans}"
        return await self.call_llm(input_text)


@pytest.mark.asyncio
async def test_agent_execution_and_tool_invocation() -> None:
    """Verify BaseAgent delegates to tools and LLM properly."""
    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Planned successfully"
    mock_openai.chat.completions.create = AsyncMock(
        return_value=MagicMock(choices=[mock_choice])
    )

    client = LLMClient(client=mock_openai)
    agent = SamplePlannerAgent(
        name="TestPlanner",
        description="Plans test events",
        system_prompt="System instructions",
        llm_client=client,
    )

    # Register tool using decorator
    @tool(
        name="multiply",
        description="Multiply two numbers",
        parameters_schema=CalculationParams,
    )
    def multiply_numbers(x: int, y: int) -> int:
        return x * y

    agent.register_tool(multiply_numbers)

    # Test tool invocation
    tool_result = await agent.run("use_tool")
    assert tool_result == "Answer is 42"

    # Test LLM invocation
    llm_result = await agent.run("Please plan an event")
    assert llm_result == "Planned successfully"


@pytest.mark.asyncio
async def test_agent_missing_tool_raises_agent_execution_error() -> None:
    """Executing an unregistered tool raises AgentExecutionError."""
    agent = SamplePlannerAgent(
        name="TestPlanner",
        description="Plans events",
        system_prompt="System",
    )
    with pytest.raises(AgentExecutionError) as exc_info:
        await agent.execute_tool("nonexistent_tool")
    assert "not available to agent" in str(exc_info.value)


def test_tool_registry_to_openai_tools() -> None:
    """Verify tool definitions convert to OpenAI function tool schemas."""
    registry = ToolRegistry()

    @tool(
        name="calculate_tax",
        description="Calculate tax amount",
        parameters_schema=CalculationParams,
    )
    def calc_tax(x: int, y: int) -> int:
        return x + y

    registry.register(calc_tax)
    schemas = registry.to_openai_tools()

    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "calculate_tax"
    assert schemas[0]["function"]["description"] == "Calculate tax amount"
    assert "properties" in schemas[0]["function"]["parameters"]
