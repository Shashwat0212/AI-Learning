

from __future__ import annotations

from typing import Iterable, List

from askmydocs.core.types import Chunk

from .dense.base import DenseIndex
from .dense.embeddings import Embedder
from .sparse.base import SparseIndex
from .store.doc_map import DocMap


class IndexingPipeline:
    """
    Orchestrates the full indexing flow.

    Responsibilities:
    - embed chunks
    - update dense index
    - update sparse index
    - store chunks in doc_map

    Supports both baseline and incremental modes (incremental logic to be added later).

    TODO:
    - integrate tracing spans (embedding, dense, sparse, storage)
    - support incremental indexing mode using diff engine
    - batch embedding for performance
    - add error handling and retries
    """

    def __init__(
        self,
        embedder: Embedder,
        dense_index: DenseIndex,
        sparse_index: SparseIndex,
        doc_map: DocMap,
    ) -> None:
        self.embedder = embedder
        self.dense_index = dense_index
        self.sparse_index = sparse_index
        self.doc_map = doc_map

    def run(self, chunks: Iterable[Chunk]) -> None:
        """
        Run indexing pipeline on given chunks.

        Baseline mode:
        - processes all chunks
        - embeds and indexes each chunk
        """

        for chunk in chunks:
            if chunk.fingerprint is None:
                raise ValueError("Chunk fingerprint cannot be None")
            
            chunk_id = chunk.fingerprint

            # Step 1: embedding (with cache)
            vector = self.embedder.encode(chunk.text, chunk_id)

            # Step 2: update dense index
            self.dense_index.add(chunk_id, vector)

            # Step 3: update sparse index
            self.sparse_index.add(chunk_id, chunk.text)

            # Step 4: store full chunk
            self.doc_map.store(chunk_id, chunk)

    def remove(self, chunk_ids: List[str]) -> None:
        """
        Remove chunks from all indexing structures.

        Used for incremental updates.
        """

        for chunk_id in chunk_ids:
            self.dense_index.remove(chunk_id)
            self.sparse_index.remove(chunk_id)
            self.doc_map.delete(chunk_id)

    def __len__(self) -> int:
        """
        Return number of indexed chunks.
        """
        return len(self.doc_map)