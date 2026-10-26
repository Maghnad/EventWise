"""OpenAI LLM Client wrapper for EventWise.

Provides a robust, typed async interface to OpenAI (GPT-4o) with:
- Environment-based configuration (via ``app.config.get_settings``)
- Configurable exponential backoff retry logic for transient API/network errors
- Native structured output parsing into Pydantic models
- Rich exception hierarchy and logging
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from openai import (
    APIConnectionError,
    AsyncOpenAI,
    InternalServerError,
    OpenAIError,
    RateLimitError,
)
from pydantic import BaseModel

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ==============================================================================
# Exceptions
# ==============================================================================


class LLMClientError(Exception):
    """Base exception for all LLM client errors."""


class LLMConfigurationError(LLMClientError):
    """Raised when required configuration (e.g. API key) is missing."""


class LLMRetryError(LLMClientError):
    """Raised when maximum retry attempts have been exhausted."""


class LLMStructuredOutputError(LLMClientError):
    """Raised when model output fails to parse into the requested schema."""


# ==============================================================================
# LLM Client
# ==============================================================================


class LLMClient:
    """Async wrapper around OpenAI GPT-4o with retries and structured output."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        initial_backoff_seconds: float = 0.5,
        backoff_multiplier: float = 2.0,
        settings: Settings | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        """Initialize the LLM client.

        Args:
            api_key: Optional explicit API key. Defaults to settings.openai_api_key.
            model: Optional model name. Defaults to settings.openai_model ("gpt-4o").
            max_retries: Max retry attempts for transient errors.
            initial_backoff_seconds: Initial delay in seconds before first retry.
            backoff_multiplier: Multiplier for exponential backoff delay.
            settings: Optional custom Settings instance.
            client: Optional injected AsyncOpenAI instance (useful for testing/mocking).
        """
        app_settings = settings or get_settings()
        self._api_key = api_key or app_settings.openai_api_key
        self.model = model or app_settings.openai_model or "gpt-4o"
        self.max_retries = max(0, max_retries)
        self.initial_backoff = initial_backoff_seconds
        self.backoff_multiplier = backoff_multiplier

        self._client: AsyncOpenAI | None = None
        if client is not None:
            self._client = client
        elif self._api_key:
            self._client = AsyncOpenAI(api_key=self._api_key)

    @property
    def client(self) -> AsyncOpenAI:
        """Return the underlying AsyncOpenAI client, validating presence of API key."""
        if self._client is None:
            raise LLMConfigurationError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY in .env."
            )
        return self._client

    async def _execute_with_retry(
        self,
        operation: Callable[[], Awaitable[Any]],
        operation_name: str = "OpenAI API call",
    ) -> Any:
        """Execute an async operation with exponential backoff on transient errors."""
        last_exception: Exception | None = None
        delay = self.initial_backoff

        for attempt in range(1, self.max_retries + 2):
            try:
                return await operation()
            except (RateLimitError, APIConnectionError, InternalServerError) as exc:
                last_exception = exc
                if attempt > self.max_retries:
                    break
                logger.warning(
                    "%s encountered %s on attempt %d/%d. Retrying in %.2fs...",
                    operation_name,
                    type(exc).__name__,
                    attempt,
                    self.max_retries + 1,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= self.backoff_multiplier
            except OpenAIError as exc:
                # Non-retryable OpenAI errors (e.g. AuthenticationError, BadRequestError)
                raise LLMClientError(f"{operation_name} failed: {exc}") from exc
            except LLMClientError:
                # Let our own error hierarchy (e.g. LLMStructuredOutputError) propagate
                raise
            except Exception as exc:
                raise LLMClientError(
                    f"Unexpected error in {operation_name}: {exc}"
                ) from exc

        raise LLMRetryError(
            f"{operation_name} failed after {self.max_retries + 1} attempts. Last error: {last_exception}"
        ) from last_exception

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        model_override: str | None = None,
    ) -> str:
        """Generate a raw text completion.

        Args:
            prompt: User prompt text.
            system_prompt: Optional system instructions.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Optional token generation limit.
            model_override: Optional model name to override default.

        Returns:
            The completion response string.
        """
        client = self.client
        model = model_override or self.model

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async def _call() -> str:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""

        return str(
            await self._execute_with_retry(_call, operation_name="generate_text")
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.2,
        model_override: str | None = None,
    ) -> T:
        """Generate structured output parsed directly into a Pydantic schema.

        Uses OpenAI Structured Outputs (beta.chat.completions.parse).

        Args:
            prompt: User prompt text.
            response_model: Pydantic model class defining desired schema.
            system_prompt: Optional system instructions.
            temperature: Sampling temperature.
            model_override: Optional model override.

        Returns:
            An instance of ``response_model`` populated with structured response.

        Raises:
            LLMStructuredOutputError: If model refused or failed parsing into schema.
            LLMRetryError: If transient errors persisted past max_retries.
            LLMClientError: On other API errors.
        """
        client = self.client
        model = model_override or self.model

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async def _call() -> T:
            completion = await client.beta.chat.completions.parse(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                response_format=response_model,
                temperature=temperature,
            )
            message = completion.choices[0].message
            if getattr(message, "refusal", None):
                raise LLMStructuredOutputError(
                    f"Model refused generation: {message.refusal}"
                )

            parsed = getattr(message, "parsed", None)
            if parsed is None:
                raise LLMStructuredOutputError(
                    f"Failed to parse model output into {response_model.__name__}."
                )
            return parsed

        result = await self._execute_with_retry(
            _call, operation_name=f"generate_structured[{response_model.__name__}]"
        )
        return result  # type: ignore[no-any-return]

    async def create_embedding(
        self,
        text: str,
        model_override: str | None = None,
    ) -> list[float]:
        """Generate text embedding vector using OpenAI embeddings API.

        Args:
            text: Input text string to embed.
            model_override: Optional embedding model name (defaults to 'text-embedding-3-small').

        Returns:
            List of floats representing the embedding vector.
        """
        client = self.client
        model = model_override or "text-embedding-3-small"

        async def _call() -> list[float]:
            response = await client.embeddings.create(
                input=text,
                model=model,
            )
            return response.data[0].embedding

        result = await self._execute_with_retry(
            _call, operation_name=f"create_embedding[{model}]"
        )
        return result  # type: ignore[no-any-return]
