"""
backend/rag/rag_engine.py
==========================
RAG Engine — works fully in-memory, no database setup required.

HOW IT WORKS:
    1. At startup, all knowledge documents are embedded with all-MiniLM-L6-v2
       and stored in memory as a list of (embedding, document) pairs.
    2. When a query arrives, it is embedded and cosine similarity is computed
       against all stored embeddings — O(n) where n = number of documents.
    3. Top-k most similar documents are passed to Groq LLM as context.
    4. Groq generates an answer grounded strictly in the retrieved content.

WHY IN-MEMORY (not vector DB)?
    For 20-50 documents, in-memory cosine similarity is instant (<5ms).
    No database setup required — works on first run.
    For 10,000+ documents, use pgvector or Pinecone instead.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from ml.embeddings import embeddings_service
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    category: str
    source: str
    content: str
    tags: list
    similarity: float


@dataclass
class RAGResponse:
    answer: str
    sources: list
    query: str
    retrieval_count: int


class RAGEngine:
    """
    In-memory RAG engine. Embeddings computed at first query, cached in memory.
    No database required.
    """

    def __init__(self):
        # List of dicts: {"embedding": [...], "doc": {...}}
        self._index: list[dict] = []
        self._built = False

    def _build_index(self) -> None:
        """
        Embed all knowledge documents and store in memory.
        Called once on first query. Takes ~5-15 seconds depending on number of docs.
        """
        if self._built:
            return

        from rag.knowledge_base import KNOWLEDGE_DOCUMENTS

        logger.info(f"Building RAG index for {len(KNOWLEDGE_DOCUMENTS)} documents...")

        for doc in KNOWLEDGE_DOCUMENTS:
            try:
                # Embed the document content — this is what gets compared against queries
                embedding = embeddings_service.get_embedding(doc["content"])
                self._index.append({
                    "embedding": embedding,
                    "doc": doc,
                })
            except Exception as e:
                logger.warning(f"Failed to embed doc {doc['id']}: {e}")

        self._built = True
        logger.info(f"✅ RAG index built: {len(self._index)} documents indexed")

    def retrieve(self, query: str, top_k: int = 4, category_filter: Optional[str] = None) -> list[RetrievedChunk]:
        """
        Find the most semantically similar knowledge chunks.
        """
        # Build index on first call
        self._build_index()

        if not self._index:
            logger.warning("RAG index is empty")
            return []

        # Embed the user query
        query_embedding = embeddings_service.get_embedding(query)

        scored = []
        for item in self._index:
            doc = item["doc"]

            # Skip if category filter doesn't match
            if category_filter and doc.get("category") != category_filter:
                continue

            # Cosine similarity
            similarity = embeddings_service.cosine_similarity(query_embedding, item["embedding"])
            scored.append((similarity, doc))

        # Sort by similarity, highest first
        scored.sort(key=lambda x: x[0], reverse=True)

        # Take top_k with minimum similarity threshold of 0.15
        # Lower threshold = more results but potentially less relevant
        results = []
        for sim, doc in scored[:top_k]:
            if sim >= 0.15:
                results.append(RetrievedChunk(
                    doc_id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    category=doc.get("category", ""),
                    source=doc.get("source", ""),
                    content=doc.get("content", ""),
                    tags=doc.get("tags") or [],
                    similarity=round(float(sim), 4),
                ))

        logger.info(f"RAG retrieved {len(results)} chunks for query: '{query[:50]}...' (top similarity: {scored[0][0]:.3f} if scored else 0)")
        return results

    async def generate(self, query: str, retrieved_chunks: list[RetrievedChunk]) -> str:
        """
        Generate an answer grounded in the retrieved knowledge base chunks.
        Uses Groq LLM with the retrieved content injected as context.
        """
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage

        if not retrieved_chunks:
            # Fallback: search all docs and return most relevant content directly
            self._build_index()
            query_emb = embeddings_service.get_embedding(query)
            best = max(self._index, key=lambda x: embeddings_service.cosine_similarity(query_emb, x["embedding"]), default=None)
            if best:
                doc = best["doc"]
                return f"**{doc['title']}** (Source: {doc['source']})\n\n{doc['content'][:800]}\n\n---\n*For personalized advice, please consult a licensed mental health professional.*"
            return "I couldn't find relevant information for that query. Please try rephrasing or consult a mental health professional."

        # Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks):
            context_parts.append(f"[{i+1}] {chunk.title} (Source: {chunk.source})\n{chunk.content}")

        context = "\n\n---\n\n".join(context_parts)

        SYSTEM = f"""You are MINDWATCH Knowledge Assistant — an evidence-based mental health information specialist.

Answer the user's question using the knowledge base context provided below.
Be specific, practical, and compassionate. Always mention which source the information comes from.
If the person seems to be in crisis, always include crisis resources (988 or Crisis Text Line).

KNOWLEDGE BASE CONTEXT:
{context}

INSTRUCTIONS:
- Answer directly and helpfully using the above context
- Cite specific techniques or frameworks mentioned in the sources
- Keep your answer focused and practical (not too long)
- End with a brief note recommending professional help for clinical decisions
- If crisis indicators are present in the question, prioritize safety resources"""

        try:
            llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name="llama-3.1-8b-instant",
                temperature=0.4,
                max_tokens=800,
            )
            response = llm.invoke([
                SystemMessage(content=SYSTEM),
                HumanMessage(content=query),
            ])
            return response.content
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            # Direct fallback — return the retrieved content
            return f"**{retrieved_chunks[0].title}**\n\n{retrieved_chunks[0].content[:600]}\n\n*Source: {retrieved_chunks[0].source}*"

    async def query(self, user_query: str, top_k: int = 4, category_filter: Optional[str] = None) -> RAGResponse:
        """Full RAG pipeline: retrieve + generate."""
        chunks = self.retrieve(user_query, top_k=top_k, category_filter=category_filter)
        answer = await self.generate(user_query, chunks)
        return RAGResponse(
            answer=answer,
            sources=chunks,
            query=user_query,
            retrieval_count=len(chunks),
        )


# Module-level singleton — shared across all requests
rag_engine = RAGEngine()


async def ingest_knowledge_base() -> dict:
    """
    (Re)build the in-memory RAG index.
    Also optionally persists to Supabase if rag_documents table exists.
    """
    # Force rebuild
    rag_engine._index = []
    rag_engine._built = False
    rag_engine._build_index()

    # Try to persist to Supabase (optional — fails gracefully if table doesn't exist)
    persisted = 0
    try:
        from database import supabase_client
        from rag.knowledge_base import KNOWLEDGE_DOCUMENTS

        for doc, item in zip(KNOWLEDGE_DOCUMENTS, rag_engine._index):
            supabase_client.table("rag_documents").upsert({
                "doc_id":    doc["id"],
                "title":     doc["title"],
                "category":  doc["category"],
                "source":    doc["source"],
                "content":   doc["content"],
                "tags":      doc["tags"],
                "embedding": item["embedding"],
            }, on_conflict="doc_id").execute()
            persisted += 1
    except Exception as e:
        logger.info(f"Supabase persistence skipped (optional): {e}")

    from rag.knowledge_base import KNOWLEDGE_DOCUMENTS
    return {
        "total_documents": len(KNOWLEDGE_DOCUMENTS),
        "indexed_in_memory": len(rag_engine._index),
        "persisted_to_db": persisted,
        "status": "complete",
    }
