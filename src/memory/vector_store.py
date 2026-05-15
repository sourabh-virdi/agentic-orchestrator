"""Persistent vector memory using ChromaDB for contextual retrieval."""

from __future__ import annotations

import uuid
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None  # type: ignore[assignment]
    ChromaSettings = None  # type: ignore[assignment,misc]


class VectorStore:
    """Wrapper around ChromaDB for persistent vector memory."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8100,
        collection_name: str = "campaign_memory",
    ) -> None:
        self._collection_name = collection_name
        self._client: Any = None
        self._collection: Any = None
        self._host = host
        self._port = port

    def connect(self) -> None:
        if chromadb is None:
            logger.warning("chromadb_not_installed_using_in_memory_fallback")
            return
        try:
            self._client = chromadb.HttpClient(host=self._host, port=self._port)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("vector_store_connected", collection=self._collection_name)
        except Exception as exc:
            logger.warning("vector_store_connection_failed_using_in_memory", error=str(exc))
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
            )

    def get_collection(self) -> Any:
        if self._collection is None:
            self.connect()
        return self._collection

    def add(self, ids: list[str], documents: list[str], metadatas: list[dict] | None = None) -> None:
        collection = self.get_collection()
        if collection is None:
            return
        collection.add(ids=ids, documents=documents, metadatas=metadatas or [{}] * len(ids))
        logger.info("vectors_added", count=len(ids))

    def query(self, query_texts: list[str], n_results: int = 5) -> dict:
        collection = self.get_collection()
        if collection is None:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        return collection.query(query_texts=query_texts, n_results=n_results)

    def count(self) -> int:
        collection = self.get_collection()
        if collection is None:
            return 0
        return collection.count()

    def delete(self, ids: list[str]) -> None:
        collection = self.get_collection()
        if collection is None:
            return
        collection.delete(ids=ids)
