from __future__ import annotations

from typing import Dict

# Assuming Chunk type exists in core.types
from askmydocs.core.types import Chunk


class DocMap:
    """
    In-memory mapping from chunk_id (fingerprint) to full Chunk object.

    Responsibilities:
    - store chunk objects
    - retrieve chunks by id
    - support deletion (for incremental updates)

    This acts as the source of truth for reconstructing content after retrieval.

    TODO:
    - persist doc_map to disk or database
    - add serialization/deserialization support
    - add metadata filtering support if needed
    """

    def __init__(self) -> None:
        # id (fingerprint) -> Chunk
        self._store: Dict[str, Chunk] = {}

    def store(self, id: str, chunk: Chunk) -> None:
        """
        Store or update a chunk.
        """
        self._store[id] = chunk

    def get(self, id: str) -> Chunk:
        """
        Retrieve a chunk by id.

        Raises:
            KeyError if id not found
        """
        return self._store[id]

    def delete(self, id: str) -> None:
        """
        Remove a chunk from the map.
        """
        if id in self._store:
            del self._store[id]

    def exists(self, id: str) -> bool:
        """
        Check if a chunk exists in the map.
        """
        return id in self._store

    def __len__(self) -> int:
        """
        Return number of stored chunks.
        """
        return len(self._store)