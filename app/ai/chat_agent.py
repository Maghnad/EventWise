"""Conversational Event Planning AI Agent.

Maintains conversation history and can invoke specialized domain tools
(BudgetPlanner, TimelinePlanner, VendorChecklist) to refine and generate
event planning deliverables directly through dialogue.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.ai.base_agent import BaseAgent
from app.ai.budget_agent import BudgetAgent
from app.ai.llm_client import LLMClient
from app.ai.timeline_agent import TimelineAgent
from app.ai.tools import BaseTool, FunctionTool
from app.ai.vendor_agent import VendorAgent

logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic Schemas
# ==============================================================================


class ChatMessage(BaseModel):
    """A turn in the conversation history."""

    role: str = Field(
        ..., description="Role of the speaker: 'user', 'assistant', or 'system'."
    )
    content: str = Field(..., description="Text content of the message.")


class ToolExecutionRecord(BaseModel):
    """Audit record of a tool invoked during the chat interaction."""

    tool_name: str = Field(..., description="Name of the invoked tool.")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments provided to the tool."
    )
    result_summary: str = Field(
        ..., description="High-level summary of the tool outcome."
    )
    status: str = Field(default="success", description="Status: 'success' or 'error'.")


class ChatTurnResponse(BaseModel):
    """Structured response for a conversational turn."""

    reply: str = Field(
        ...,
        description="Conversational response addressed to the user.",
    )
    tool_calls_executed: list[ToolExecutionRecord] = Field(
        default_factory=list,
        description="List of tools invoked to fulfill the user's request.",
    )
    suggested_actions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up queries or next steps for the user.",
    )
    plan_data: dict[str, Any] | None = Field(
        default=None,
        description="Structured deliverable (budget, timeline, vendor checklist) if produced.",
    )


# ==============================================================================
# Tool Schemas for OpenAI Function Calling
# ==============================================================================


class BudgetToolInput(BaseModel):
    """Inputs for generating an event budget allocation."""

    event_type: str = Field(..., description="Event type (e.g. 'wedding', 'birthday').")
    guest_count: int = Field(..., description="Total anticipated guest count.")
    total_budget: float = Field(..., description="Total budget in dollars.")
    location: str = Field(..., description="City or venue location.")


class TimelineToolInput(BaseModel):
    """Inputs for reverse-engineering an event countdown timeline."""

    event_type: str = Field(
        ..., description="Event type (e.g. 'conference', 'wedding')."
    )
    event_date: str = Field(..., description="Target event date (YYYY-MM-DD).")
    guest_count: int | None = Field(default=None, description="Optional guest count.")


class VendorToolInput(BaseModel):
    """Inputs for creating a categorized vendor checklist."""

    event_type: str = Field(
        ..., description="Event type (e.g. 'corporate dinner', 'wedding')."
    )
    total_budget: float = Field(..., description="Total budget in dollars.")
    guest_count: int | None = Field(default=None, description="Optional guest count.")


# ==============================================================================
# System Prompt
# ==============================================================================

_SYSTEM_PROMPT = """\
You are EventWise, an expert AI event planning concierge.
You guide planners through every step of event creation with enthusiasm,
clarity, and practical advice.

Capabilities:
1. Converse naturally while maintaining full conversation context.
2. When the user requests a budget, timeline, or vendor plan (or asks to adjust one),
   you can invoke the corresponding planning tools:
   - budget_planner: Generates itemized budget breakdowns.
   - timeline_planner: Reverse-engineers milestones counting backward from the event date.
   - vendor_checklist: Produces categorized vendor tasks with questions and booking lead times.
3. Suggest 2-3 logical follow-up actions to keep the planning process moving forward.
4. Return ONLY valid JSON conforming to the ChatTurnResponse schema.
"""


# ==============================================================================
# Chat Agent Implementation
# ==============================================================================


class ChatAgent(BaseAgent):
    """Conversational AI agent capable of invoking planning tools and tracking history."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        budget_agent: BudgetAgent | None = None,
        timeline_agent: TimelineAgent | None = None,
        vendor_agent: VendorAgent | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        """Initialize the ChatAgent and register default planning tools."""
        super().__init__(
            name="ChatConciergeAgent",
            description="Conversational event planning assistant with multi-turn history and tool execution.",
            system_prompt=_SYSTEM_PROMPT,
            llm_client=llm_client,
            tools=tools,
        )

        self.budget_agent = budget_agent or BudgetAgent(llm_client=self.llm_client)
        self.timeline_agent = timeline_agent or TimelineAgent(
            llm_client=self.llm_client
        )
        self.vendor_agent = vendor_agent or VendorAgent(llm_client=self.llm_client)

        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register domain planning tools into the agent's tool registry."""

        async def _run_budget(
            event_type: str,
            guest_count: int,
            total_budget: float,
            location: str,
        ) -> dict[str, Any]:
            res = await self.budget_agent.run(
                context={
                    "event_type": event_type,
                    "guest_count": guest_count,
                    "total_budget": total_budget,
                    "location": location,
                }
            )
            return res.model_dump()

        async def _run_timeline(
            event_type: str,
            event_date: str,
            guest_count: int | None = None,
        ) -> dict[str, Any]:
            res = await self.timeline_agent.run(
                context={
                    "event_type": event_type,
                    "event_date": event_date,
                    "guest_count": guest_count,
                }
            )
            return res.model_dump()

        async def _run_vendor(
            event_type: str,
            total_budget: float,
            guest_count: int | None = None,
        ) -> dict[str, Any]:
            res = await self.vendor_agent.run(
                context={
                    "event_type": event_type,
                    "total_budget": total_budget,
                    "guest_count": guest_count,
                }
            )
            return res.model_dump()

        self.register_tool(
            FunctionTool(
                name="budget_planner",
                description="Generates an itemized event budget allocation breakdown.",
                func=_run_budget,
                parameters_schema=BudgetToolInput,
            )
        )
        self.register_tool(
            FunctionTool(
                name="timeline_planner",
                description="Creates a reverse-engineered countdown timeline of planning tasks.",
                func=_run_timeline,
                parameters_schema=TimelineToolInput,
            )
        )
        self.register_tool(
            FunctionTool(
                name="vendor_checklist",
                description="Builds a categorized vendor checklist with booking lead times.",
                func=_run_vendor,
                parameters_schema=VendorToolInput,
            )
        )

    def _format_conversation_history(
        self,
        history: list[ChatMessage | dict[str, Any]],
        current_message: str,
    ) -> str:
        """Build conversation transcript for the prompt."""
        transcript_lines: list[str] = []

        for msg in history:
            if isinstance(msg, ChatMessage):
                role = msg.role.capitalize()
                content = msg.content
            elif isinstance(msg, dict):
                role = str(msg.get("role", "User")).capitalize()
                content = str(msg.get("content", ""))
            else:
                continue

            transcript_lines.append(f"{role}: {content}")

        transcript_lines.append(f"User: {current_message}")
        return "\n".join(transcript_lines)

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> ChatTurnResponse:
        """Execute conversational turn.

        Context keys supported:
        - `history` (list[ChatMessage | dict]): Previous conversation turns.
        - `tool_call` (dict, optional): Direct instruction to execute a tool, e.g.:
            `{"tool": "budget_planner", "arguments": {...}}`
        - `event_context` (dict, optional): Current event parameters (e.g. type, budget).

        Args:
            input_text: The user's latest incoming message.
            context: Optional dictionary containing chat history and event context.

        Returns:
            `ChatTurnResponse` containing reply, tool records, and suggestions.
        """
        from app.shared.sanitizer import sanitize_text

        ctx = context or {}
        raw_history = ctx.get("history", [])
        current_message = sanitize_text(input_text or ctx.get("message", "")) or ""

        tool_records: list[ToolExecutionRecord] = []
        plan_data: dict[str, Any] | None = None

        # Check for explicit or detected tool call request in context
        requested_tool = ctx.get("tool_call")
        if requested_tool and isinstance(requested_tool, dict):
            tool_name = requested_tool.get("tool") or requested_tool.get("name")
            tool_args = requested_tool.get("arguments", {})
            if tool_name and self.tools.has(tool_name):
                try:
                    logger.info("ChatConciergeAgent executing tool: %s", tool_name)
                    tool_result = await self.execute_tool(tool_name, **tool_args)
                    plan_data = (
                        tool_result
                        if isinstance(tool_result, dict)
                        else {"result": tool_result}
                    )
                    tool_records.append(
                        ToolExecutionRecord(
                            tool_name=tool_name,
                            arguments=tool_args,
                            result_summary=f"Successfully generated {tool_name} deliverable.",
                            status="success",
                        )
                    )
                except Exception as exc:
                    logger.exception("Error executing tool %s: %s", tool_name, exc)
                    tool_records.append(
                        ToolExecutionRecord(
                            tool_name=tool_name,
                            arguments=tool_args,
                            result_summary=f"Tool failed: {exc}",
                            status="error",
                        )
                    )

        # Formulate prompt including conversation history and tool outputs
        transcript = self._format_conversation_history(raw_history, current_message)
        prompt_lines = [
            "You are responding in an ongoing conversation with an event planner.",
            "\n--- CONVERSATION HISTORY ---",
            transcript,
            "--- END CONVERSATION HISTORY ---",
        ]

        if tool_records:
            prompt_lines.append("\n--- TOOLS EXECUTED IN THIS TURN ---")
            for rec in tool_records:
                prompt_lines.append(f"Tool '{rec.tool_name}': {rec.result_summary}")
            prompt_lines.append(
                "Reference the results of these tool executions naturally in your conversational reply."
            )

        prompt_lines.append(
            "\nGenerate a warm, helpful response answering the user, summarize any deliverables, "
            "and suggest 2-3 logical follow-up actions."
        )

        final_prompt = "\n".join(prompt_lines)

        result: ChatTurnResponse = await self.call_llm_structured(
            prompt=final_prompt,
            response_model=ChatTurnResponse,
            temperature=0.4,
        )

        # Merge tool records and plan data into final response
        if tool_records:
            result.tool_calls_executed = tool_records
        if plan_data:
            result.plan_data = plan_data

        return result


__all__ = [
    "ChatAgent",
    "ChatMessage",
    "ChatTurnResponse",
    "ToolExecutionRecord",
]
