"""Retriever agent — searches vector memory for relevant historical context."""

from __future__ import annotations

from typing import Any

import structlog

from src.agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class RetrieverAgent(BaseAgent):
    """Retrieves relevant context from vector memory (ChromaDB)."""

    def __init__(self, memory: Any | None = None, top_k: int = 5) -> None:
        super().__init__("retriever")
        self._memory = memory
        self._top_k = top_k

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = input_data.get("query", "")
        results = await self.retrieve(query)
        return {"context": results}

    async def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """Search vector memory for top-k relevant documents."""
        k = top_k or self._top_k

        if self._memory is None:
            logger.warning("no_memory_backend_configured")
            return []

        try:
            results = self._memory.query(query_texts=[query], n_results=k)
            documents = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    documents.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0,
                    })
            logger.info("retrieval_complete", query_length=len(query), results=len(documents))
            return documents
        except Exception as exc:
            logger.error("retrieval_failed", error=str(exc))
            return []

    async def store(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        """Store a document in vector memory."""
        if self._memory is None:
            return
        self._memory.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {}],
        )
        logger.info("document_stored", doc_id=doc_id)
