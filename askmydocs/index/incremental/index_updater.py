

from __future__ import annotations

from typing import Iterable

from askmydocs.core.types import Chunk
from askmydocs.index.dense.base import DenseIndex
from askmydocs.index.dense.embeddings import Embedder
from askmydocs.index.incremental.index_diff import IndexDiffResult
from askmydocs.index.sparse.base import SparseIndex
from askmydocs.index.store.doc_map import DocMap


class IndexUpdater:
    """
    Apply incremental indexing changes to all index structures.

    Responsibilities:
    - add newly changed chunks to dense index, sparse index, and doc_map
    - remove stale chunk ids from dense index, sparse index, and doc_map

    Design principles:
    - fingerprint is the primary key across all indexing components
    - added chunks must be embedded before insertion into dense index
    - removed chunk ids are deleted uniformly from every store

    TODO:
    - integrate tracing spans for add/remove/update stages
    - support batch embedding for added chunks
    - add counters / reporting for observability
    - handle partial failures with rollback strategy if needed
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

    def apply(self, diff: IndexDiffResult) -> None:
        """
        Apply incremental updates based on diff result.

        Behavior:
        - add all chunks in diff.added
        - remove all ids in diff.removed
        - do nothing for unchanged ids
        """

        # Remove stale ids first
        for chunk_id in diff.removed:
            self.dense_index.remove(chunk_id)
            self.sparse_index.remove(chunk_id)
            self.doc_map.delete(chunk_id)

        # Add new / changed chunks
        for chunk in diff.added:
            if chunk.fingerprint is None:
                raise ValueError("Chunk fingerprint cannot be None for incremental indexing")

            chunk_id = chunk.fingerprint
            vector = self.embedder.encode(chunk.text, chunk_id)

            self.dense_index.add(chunk_id, vector)
            self.sparse_index.add(chunk_id, chunk.text)
            self.doc_map.store(chunk_id, chunk)