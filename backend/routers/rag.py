"""
backend/routers/rag.py
=======================
PURPOSE:
    REST API endpoints for the MINDWATCH RAG system.

    POST /rag/ingest  — Embed all knowledge documents and store in Supabase (run once)
    POST /rag/query   — Query the knowledge base with a mental health question
    GET  /rag/docs    — List all available knowledge documents
"""

import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from models.schemas import APIEnvelope

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request/Response schemas ──────────────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    """User's question to the knowledge base."""
    query: str = Field(..., min_length=5, description="Mental health question or topic")
    top_k: int = Field(default=3, ge=1, le=5, description="Number of knowledge chunks to retrieve")
    category_filter: Optional[str] = Field(
        default=None,
        description="Filter by category: depression | anxiety | crisis | coping | therapy | self-care"
    )


class SourceDocument(BaseModel):
    """A retrieved source document shown to the user."""
    title: str
    category: str
    source: str
    tags: list[str]
    similarity: float
    excerpt: str  # first 200 chars of content for preview


class RAGQueryResponse(BaseModel):
    """Complete RAG response with answer and cited sources."""
    answer: str
    sources: list[SourceDocument]
    query: str
    retrieval_count: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=APIEnvelope[dict])
async def ingest_documents():
    """
    Embed all knowledge base documents and store them in Supabase.

    Run this once after initial setup (or whenever knowledge_base.py is updated).
    Creates or updates the rag_documents table with embeddings.

    This is equivalent to "building the index" in a traditional search system.
    """
    try:
        from rag.rag_engine import ingest_knowledge_base
        result = await ingest_knowledge_base()
        return APIEnvelope.success(result)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return APIEnvelope.failure("INGEST_ERROR", str(e))


@router.post("/query", response_model=APIEnvelope[RAGQueryResponse])
async def query_knowledge_base(body: RAGQueryRequest):
    """
    Query the mental health knowledge base using RAG.

    Pipeline:
        1. Embed the user's query with all-MiniLM-L6-v2
        2. Retrieve the top-k most semantically similar knowledge chunks from Supabase
        3. Pass retrieved chunks to Groq LLM as context
        4. Return LLM answer grounded in the knowledge base + cited sources

    Example queries:
        - "What are CBT techniques for depression?"
        - "How do I help someone who is suicidal?"
        - "What is behavioral activation?"
        - "How does exercise help with anxiety?"
    """
    try:
        from rag.rag_engine import rag_engine
        response = await rag_engine.query(
            user_query=body.query,
            top_k=body.top_k,
            category_filter=body.category_filter,
        )

        # Convert internal RetrievedChunk to API response format
        sources = [
            SourceDocument(
                title=chunk.title,
                category=chunk.category,
                source=chunk.source,
                tags=chunk.tags,
                similarity=chunk.similarity,
                excerpt=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            )
            for chunk in response.sources
        ]

        return APIEnvelope.success(RAGQueryResponse(
            answer=response.answer,
            sources=sources,
            query=response.query,
            retrieval_count=response.retrieval_count,
        ))

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return APIEnvelope.failure("RAG_ERROR", str(e))


@router.get("/docs", response_model=APIEnvelope[dict])
async def list_documents(category: Optional[str] = None):
    """
    List all available knowledge base documents.
    Useful for the frontend to show what topics are available.
    """
    try:
        from rag.knowledge_base import KNOWLEDGE_DOCUMENTS

        docs = KNOWLEDGE_DOCUMENTS
        if category:
            docs = [d for d in docs if d["category"] == category]

        # Get unique categories
        categories = list(set(d["category"] for d in KNOWLEDGE_DOCUMENTS))

        return APIEnvelope.success({
            "total": len(docs),
            "categories": sorted(categories),
            "documents": [
                {
                    "id": d["id"],
                    "title": d["title"],
                    "category": d["category"],
                    "source": d["source"],
                    "tags": d["tags"],
                }
                for d in docs
            ],
        })
    except Exception as e:
        return APIEnvelope.failure("LIST_ERROR", str(e))


@router.get("/categories", response_model=APIEnvelope[list])
async def list_categories():
    """List all knowledge base categories with document counts."""
    try:
        from rag.knowledge_base import KNOWLEDGE_DOCUMENTS
        from collections import Counter

        counts = Counter(d["category"] for d in KNOWLEDGE_DOCUMENTS)
        categories = [{"category": k, "count": v} for k, v in sorted(counts.items())]
        return APIEnvelope.success(categories)
    except Exception as e:
        return APIEnvelope.failure("ERROR", str(e))
