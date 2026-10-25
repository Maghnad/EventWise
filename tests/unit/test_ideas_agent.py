"""Unit tests for IdeasAgent (RAG) with mocked LLM and mocked/in-memory vector store.

Validates document embedding, indexing, semantic vector retrieval,
RAG prompt construction, and structured idea output.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.ideas_agent import (
    GeneratedIdea,
    IdeasAgent,
    InMemoryVectorStore,
    PersonalizedIdeasResponse,
    VectorDocument,
    compute_cosine_similarity,
)
from app.ai.llm_client import LLMClient

# ==============================================================================
# Fixtures
# ==============================================================================


def _mock_ideas_response() -> PersonalizedIdeasResponse:
    """Return a mock PersonalizedIdeasResponse."""
    return PersonalizedIdeasResponse(
        event_type="rustic wedding",
        category="Entertainment & Guest Experience",
        retrieved_context_count=2,
        ideas=[
            GeneratedIdea(
                title="Starlight Acoustic Courtyard Jam",
                description="Late evening acoustic duo playing guest requests around copper firepits with artisan s'mores.",
                category="Entertainment",
                tags=["live-music", "firepits", "interactive"],
                estimated_cost_tier="moderate",
                vendor_alignment="Leverages Local Acoustic Strings and Rustic Rentals LLC.",
            ),
            GeneratedIdea(
                title="Vintage Horse-Trailer Craft Cider Station",
                description="Restored 1970s trailer serving locally pressed spiced cider and seasonal craft cocktails.",
                category="Catering",
                tags=["cider", "vintage-bar", "craft-cocktails"],
                estimated_cost_tier="moderate",
                vendor_alignment="Directly integrates with Vintage Trailer Bars & Co.",
            ),
        ],
        summary="Rustic, interactive ideas leveraging local acoustic entertainment and mobile bar vendors.",
    )


# ==============================================================================
# Tests — Cosine Similarity
# ==============================================================================


def test_cosine_similarity_identical_vectors() -> None:
    """Identical vectors have cosine similarity of 1.0."""
    vec = [1.0, 2.0, 3.0]
    sim = compute_cosine_similarity(vec, vec)
    assert pytest.approx(sim, 0.001) == 1.0


def test_cosine_similarity_orthogonal_vectors() -> None:
    """Orthogonal vectors have cosine similarity of 0.0."""
    v1 = [1.0, 0.0]
    v2 = [0.0, 1.0]
    sim = compute_cosine_similarity(v1, v2)
    assert pytest.approx(sim, 0.001) == 0.0


def test_cosine_similarity_empty_or_zero_vectors() -> None:
    """Empty or all-zero vectors return 0.0 without division by zero error."""
    assert compute_cosine_similarity([], []) == 0.0
    assert compute_cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


# ==============================================================================
# Tests — In-Memory Vector Store
# ==============================================================================


@pytest.mark.asyncio
async def test_vector_store_add_and_search() -> None:
    """Vector store adds documents and returns top-k by cosine similarity."""
    store = InMemoryVectorStore()

    doc1 = VectorDocument(
        id="v1",
        content="Artisan sourdough bakery and dessert bar",
        metadata={"category": "Catering"},
        embedding=[1.0, 0.0, 0.0],
    )
    doc2 = VectorDocument(
        id="v2",
        content="Live bluegrass and folk acoustic trio",
        metadata={"category": "Music"},
        embedding=[0.0, 1.0, 0.0],
    )
    doc3 = VectorDocument(
        id="v3",
        content="French pastry catering and tiered cakes",
        metadata={"category": "Catering"},
        embedding=[0.9, 0.1, 0.0],
    )

    await store.add_document(doc1)
    await store.add_document(doc2)
    await store.add_document(doc3)

    # Search for catering query close to [1.0, 0.0, 0.0]
    results = await store.search(query_embedding=[1.0, 0.0, 0.0], top_k=2)

    assert len(results) == 2
    assert results[0][0].id == "v1"
    assert results[1][0].id == "v3"


# ==============================================================================
# Tests — IdeasAgent Execution with Mocked LLM & Vector Store
# ==============================================================================


@pytest.mark.asyncio
async def test_ideas_agent_embed_and_index_vendor() -> None:
    """IdeasAgent embeds vendor text and indexes it in the vector store."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.create_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])

    store = InMemoryVectorStore()
    agent = IdeasAgent(llm_client=mock_llm, vector_store=store)

    doc = await agent.embed_and_index_vendor(
        vendor_id="vend-123",
        name="Wildflower Florals",
        category="Florals",
        description="Organic sustainable meadow arrangements",
        pricing_tier="moderate",
    )

    assert doc.id == "vendor_vend-123"
    assert "Wildflower Florals" in doc.content
    assert doc.embedding == [0.1, 0.2, 0.3]
    mock_llm.create_embedding.assert_awaited_once()


@pytest.mark.asyncio
async def test_ideas_agent_rag_generates_personalized_ideas() -> None:
    """Agent retrieves vector context and produces structured PersonalizedIdeasResponse."""
    mock_response = _mock_ideas_response()

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.create_embedding = AsyncMock(return_value=[0.5, 0.5, 0.0])
    mock_llm.generate_structured = AsyncMock(return_value=mock_response)

    store = InMemoryVectorStore()
    await store.add_document(
        VectorDocument(
            id="v_test",
            content="Vintage Trailer Bars & Co.: Mobile craft beer and cider service",
            metadata={"category": "Catering"},
            embedding=[0.5, 0.5, 0.0],
        )
    )

    agent = IdeasAgent(llm_client=mock_llm, vector_store=store)

    result = await agent.run(
        input_text="Unique drink and dessert experiences",
        context={"event_type": "rustic wedding", "category": "Catering"},
    )

    assert isinstance(result, PersonalizedIdeasResponse)
    assert result.event_type == "rustic wedding"
    assert len(result.ideas) == 2
    assert result.ideas[0].title == "Starlight Acoustic Courtyard Jam"
    assert result.ideas[1].vendor_alignment
    mock_llm.generate_structured.assert_awaited_once()


@pytest.mark.asyncio
async def test_ideas_agent_build_prompt_includes_retrieved_context() -> None:
    """RAG prompt includes retrieved vendor documents in the prompt text."""
    mock_response = _mock_ideas_response()
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.create_embedding = AsyncMock(return_value=[0.1, 0.1, 0.1])
    mock_llm.generate_structured = AsyncMock(return_value=mock_response)

    mock_store = MagicMock(spec=InMemoryVectorStore)
    doc = VectorDocument(
        id="doc_1",
        content="Vendor: Neon Glow DJ | Electronic live violin and lights",
        metadata={"category": "Music"},
    )
    mock_store.search = AsyncMock(return_value=[(doc, 0.95)])

    agent = IdeasAgent(llm_client=mock_llm, vector_store=mock_store)
    await agent.run(
        input_text="High-energy dance music",
        context={"event_type": "birthday bash", "category": "Entertainment"},
    )

    call_kwargs = mock_llm.generate_structured.call_args.kwargs
    prompt = call_kwargs["prompt"]
    assert "Neon Glow DJ" in prompt
    assert "birthday bash" in prompt
