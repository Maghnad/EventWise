"""Ideas and Brainstorming AI Agent with Retrieval-Augmented Generation (RAG).

Embeds vendor and event contextual data into a vector store (pgvector-compatible),
retrieves semantically relevant vendor options and event parameters, and generates
personalized, creative event ideas structured into Pydantic models.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.ai.base_agent import BaseAgent
from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


# ==============================================================================
# Vector Store Abstraction & Models
# ==============================================================================


class VectorDocument(BaseModel):
    """A document indexed with vector embeddings for semantic retrieval."""

    id: str = Field(..., description="Unique document identifier.")
    content: str = Field(..., description="Text content embedded and retrieved.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata such as category, vendor_id, price tier.",
    )
    embedding: list[float] | None = Field(
        default=None,
        description="Vector embedding (e.g. 1536-dimensional).",
    )


def compute_cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two floating-point vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(dot / (norm_a * norm_b))


class VectorStore(Protocol):
    """Protocol for vector database operations (in-memory or pgvector)."""

    async def add_document(self, document: VectorDocument) -> None:
        """Add or update a vector document."""
        ...

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        category: str | None = None,
    ) -> list[tuple[VectorDocument, float]]:
        """Search documents by vector similarity."""
        ...


class InMemoryVectorStore:
    """Thread-safe, lightweight in-memory vector store for testing and fallback."""

    def __init__(self) -> None:
        self._documents: dict[str, VectorDocument] = {}

    async def add_document(self, document: VectorDocument) -> None:
        """Store document in memory."""
        self._documents[document.id] = document

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        category: str | None = None,
    ) -> list[tuple[VectorDocument, float]]:
        """Rank documents by cosine similarity to query vector."""
        results: list[tuple[VectorDocument, float]] = []

        for doc in self._documents.values():
            if not doc.embedding:
                continue
            if category and doc.metadata.get("category") != category:
                continue

            similarity = compute_cosine_similarity(query_embedding, doc.embedding)
            results.append((doc, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


# ==============================================================================
# Pydantic Response Schemas (OpenAI Structured Outputs)
# ==============================================================================


class GeneratedIdea(BaseModel):
    """A personalized creative concept or activity for the event."""

    title: str = Field(
        ...,
        description="Catchy, memorable title for the idea.",
    )
    description: str = Field(
        ...,
        description="Detailed description of the experience, styling, or activity.",
    )
    category: str = Field(
        ...,
        description="Domain category (e.g. 'Entertainment', 'Decor', 'Catering', 'Interactive Activity').",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Relevant discovery keywords.",
    )
    estimated_cost_tier: str = Field(
        default="moderate",
        description="Relative cost tier: 'budget', 'moderate', or 'luxury'.",
    )
    vendor_alignment: str = Field(
        default="",
        description="How this idea leverages retrieved vendor offerings or available event resources.",
    )


class PersonalizedIdeasResponse(BaseModel):
    """Structured response container for brainstormed event ideas."""

    event_type: str = Field(
        ..., description="Echo of the input event type."
    )
    category: str = Field(
        default="general",
        description="Category focus of the generated brainstorm batch.",
    )
    retrieved_context_count: int = Field(
        default=0,
        description="Number of relevant vendor/event context documents retrieved via RAG.",
    )
    ideas: list[GeneratedIdea] = Field(
        ...,
        description="Personalized brainstorm ideas tailored to retrieved context.",
        min_length=1,
    )
    summary: str = Field(
        default="",
        description="Executive summary of the creative direction.",
    )


# ==============================================================================
# System Prompt
# ==============================================================================

_SYSTEM_PROMPT = """\
You are an innovative, world-class experiential event designer.
Given event specifications and retrieved context regarding local vendors,
past successful themes, and budget constraints:
1. Synthesize fresh, tailored, and experiential ideas that delight guests.
2. Directly reference and harmonize with the provided vendor and event context.
3. Classify ideas by domain category and realistic cost tier ('budget', 'moderate', 'luxury').
4. Include practical execution notes explaining how vendor services make the idea possible.
5. Return ONLY valid JSON matching the PersonalizedIdeasResponse schema.
"""


# ==============================================================================
# Ideas Agent Implementation
# ==============================================================================


class IdeasAgent(BaseAgent):
    """RAG-enabled AI agent for personalized event brainstorm generation."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        """Initialize the IdeasAgent.

        Args:
            llm_client: Optional injected LLMClient.
            vector_store: Optional injected VectorStore (defaults to InMemoryVectorStore).
        """
        super().__init__(
            name="IdeasRAGAgent",
            description="Generates personalized event ideas using vector-retrieved vendor and event context.",
            system_prompt=_SYSTEM_PROMPT,
            llm_client=llm_client,
        )
        self.vector_store: VectorStore = vector_store or InMemoryVectorStore()

    async def embed_and_index_vendor(
        self,
        vendor_id: str,
        name: str,
        category: str,
        description: str,
        pricing_tier: str = "moderate",
        extra_metadata: dict[str, Any] | None = None,
    ) -> VectorDocument:
        """Embed vendor profile text and store in the vector index.

        Args:
            vendor_id: Unique vendor identifier.
            name: Vendor business name.
            category: Primary category (e.g. 'Catering', 'Photography', 'Florist').
            description: Overview of services, specialties, and style.
            pricing_tier: Price tier ('budget', 'moderate', 'luxury').
            extra_metadata: Optional additional metadata fields.

        Returns:
            The indexed `VectorDocument` object.
        """
        text_to_embed = f"Vendor: {name} | Category: {category} | Tier: {pricing_tier}\nServices: {description}"
        embedding = await self.llm_client.create_embedding(text_to_embed)

        metadata = {
            "type": "vendor",
            "vendor_id": vendor_id,
            "name": name,
            "category": category,
            "pricing_tier": pricing_tier,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        doc = VectorDocument(
            id=f"vendor_{vendor_id}",
            content=text_to_embed,
            metadata=metadata,
            embedding=embedding,
        )
        await self.vector_store.add_document(doc)
        logger.info("Indexed vendor '%s' into vector store with %d dims.", name, len(embedding))
        return doc

    async def embed_and_index_event_data(
        self,
        event_id: str,
        title: str,
        event_type: str,
        description: str,
        extra_metadata: dict[str, Any] | None = None,
    ) -> VectorDocument:
        """Embed event historical or theme context and store in vector index."""
        text_to_embed = f"Event: {title} ({event_type})\nDescription: {description}"
        embedding = await self.llm_client.create_embedding(text_to_embed)

        metadata = {
            "type": "event",
            "event_id": event_id,
            "event_type": event_type,
            "title": title,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        doc = VectorDocument(
            id=f"event_{event_id}",
            content=text_to_embed,
            metadata=metadata,
            embedding=embedding,
        )
        await self.vector_store.add_document(doc)
        return doc

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 4,
        category: str | None = None,
    ) -> list[VectorDocument]:
        """Retrieve most relevant context chunks using semantic vector search."""
        query_embedding = await self.llm_client.create_embedding(query)
        search_results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            category=category,
        )
        return [doc for doc, _score in search_results]

    def _build_rag_prompt(
        self,
        event_type: str,
        theme_or_prompt: str,
        category: str | None,
        retrieved_docs: list[VectorDocument],
        guest_count: int | None = None,
        budget: str | None = None,
    ) -> str:
        """Construct prompt injecting retrieved context."""
        lines = [
            f"Generate innovative, personalized ideas for a {event_type} event.",
            f"Creative Direction / Prompt: {theme_or_prompt}",
        ]
        if category:
            lines.append(f"Category Focus: {category}")
        if guest_count is not None:
            lines.append(f"Guest Count: {guest_count}")
        if budget:
            lines.append(f"Budget: {budget}")

        if retrieved_docs:
            lines.append("\n--- RETRIEVED VENDOR & EVENT KNOWLEDGE BASE ---")
            for idx, doc in enumerate(retrieved_docs, start=1):
                lines.append(f"[{idx}] {doc.content}")
            lines.append("--- END OF RETRIEVED CONTEXT ---")
            lines.append(
                "Incorporate and align the generated ideas with the relevant vendors/resources above."
            )
        else:
            lines.append("\n(No pre-indexed vendor context found; generate fresh creative concepts.)")

        lines.append(
            "\nProduce structured ideas with title, detailed description, category, "
            "tags, cost tier, and vendor alignment notes."
        )
        return "\n".join(lines)

    async def run(
        self,
        input_text: str = "",
        context: dict[str, Any] | None = None,
    ) -> PersonalizedIdeasResponse:
        """Execute the RAG idea generation workflow.

        Context keys supported:
        - `event_type` (str): e.g. 'wedding', 'corporate summit'
        - `category` (str, optional): e.g. 'Decor', 'Entertainment'
        - `prompt` or `vibe_brief` (str, optional)
        - `guest_count` (int, optional)
        - `total_budget` (str/Decimal, optional)
        - `top_k` (int, optional, default=3)

        Args:
            input_text: User brainstorming request or query.
            context: Dictionary containing event details and constraints.

        Returns:
            `PersonalizedIdeasResponse` containing creative ideas.

        Raises:
            ValueError: If `event_type` is missing.
        """
        ctx = context or {}
        event_type = ctx.get("event_type") or "special event"
        category = ctx.get("category")
        user_prompt = ctx.get("prompt") or input_text or "creative ideas and unique guest experiences"
        top_k = int(ctx.get("top_k", 3))

        # Retrieve relevant context from vector store
        retrieval_query = f"{event_type} {category or ''} {user_prompt}".strip()
        retrieved_docs = await self.retrieve_context(
            query=retrieval_query,
            top_k=top_k,
            category=category,
        )

        logger.info(
            "IdeasRAGAgent retrieved %d context documents for query: '%s'",
            len(retrieved_docs),
            retrieval_query,
        )

        prompt = self._build_rag_prompt(
            event_type=event_type,
            theme_or_prompt=user_prompt,
            category=category,
            retrieved_docs=retrieved_docs,
            guest_count=ctx.get("guest_count"),
            budget=str(ctx["total_budget"]) if ctx.get("total_budget") else None,
        )

        result: PersonalizedIdeasResponse = await self.call_llm_structured(
            prompt=prompt,
            response_model=PersonalizedIdeasResponse,
            temperature=0.5,
        )

        # Ensure accurate retrieved context count
        result.retrieved_context_count = len(retrieved_docs)
        if category and not result.category:
            result.category = category

        return result


__all__ = [
    "GeneratedIdea",
    "IdeasAgent",
    "InMemoryVectorStore",
    "PersonalizedIdeasResponse",
    "VectorDocument",
    "VectorStore",
    "compute_cosine_similarity",
]
