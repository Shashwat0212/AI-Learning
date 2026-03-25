from __future__ import annotations

from typing import Iterable, Optional

from askmydocs.core.types import Chunk, DiffResult


class DeltaIndexer:
    """
    Applies incremental changes based on DiffResult.

    This is the execution layer of incremental ingestion.

    Current version (v1):
    - Simulates processing (counts only)
    - Designed to be extended with real embedding + indexing systems
    """

    def __init__(
        self,
        embedder: Optional[object] = None,
        vector_index: Optional[object] = None,
        docstore: Optional[object] = None,
    ) -> None:
        self.embedder = embedder
        self.vector_index = vector_index
        self.docstore = docstore

    # -----------------------------
    # Public API
    # -----------------------------

    def apply(self, diff: DiffResult) -> dict:
        """
        Apply changes from diff.

        Returns
        -------
        dict
            Summary of operations performed
        """

        added_count = self._handle_added(diff.added)
        removed_count = self._handle_removed(diff.removed)
        skipped_count = self._handle_unchanged(diff.unchanged)

        return {
            "added": added_count,
            "removed": removed_count,
            "skipped": skipped_count,
        }

    # -----------------------------
    # Internal Handlers
    # -----------------------------

    def _handle_added(self, chunks: Iterable[Chunk]) -> int:
        """
        Process newly added chunks.
        """
        count = 0

        for chunk in chunks:
            # TODO: Integrate embedding + indexing pipeline
            # embedding = self.embedder.embed(chunk.text)
            # self.vector_index.insert(embedding)
            # self.docstore.save(chunk)

            count += 1

        return count

    def _handle_removed(self, fingerprints: Iterable[str]) -> int:
        """
        Process removed chunks.
        """
        count = 0

        for fp in fingerprints:
            # TODO: Integrate deletion from vector index and docstore
            # self.vector_index.delete(fp)
            # self.docstore.delete(fp)

            count += 1

        return count

    def _handle_unchanged(self, chunks: Iterable[Chunk]) -> int:
        """
        Skip unchanged chunks.
        """
        count = 0

        for _ in chunks:
            count += 1

        return count

    def __repr__(self) -> str:
        return "DeltaIndexer(v1)"