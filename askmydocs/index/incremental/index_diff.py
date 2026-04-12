

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set

from askmydocs.core.types import Chunk


@dataclass(frozen=True)
class IndexDiffResult:
    """
    Result of comparing currently indexed chunk ids with newly ingested chunks.

    Fields:
    - added: chunks that must be newly indexed
    - removed: chunk ids that must be deleted from index structures
    - unchanged: chunk ids that are already present and do not need re-indexing
    """

    added: List[Chunk]
    removed: List[str]
    unchanged: List[str]


class IndexDiff:
    """
    Compute incremental indexing diff using chunk fingerprints.

    Design rules:
    - fingerprint is the single source of truth for chunk identity
    - chunks with new fingerprints are treated as additions
    - indexed ids missing from the new chunk set are treated as removals

    TODO:
    - support richer diff metadata for observability
    - track updated counts / change ratios for reporting
    - validate behavior against large incremental test cases
    """

    def compute(self, indexed_ids: Iterable[str], new_chunks: Iterable[Chunk]) -> IndexDiffResult:
        """
        Compare existing indexed ids against newly ingested chunks.

        Args:
            indexed_ids: chunk ids already present in indexing layer
            new_chunks: newly ingested chunks (must contain fingerprints)

        Returns:
            IndexDiffResult with added chunks, removed ids, and unchanged ids.
        """
        indexed_set: Set[str] = set(indexed_ids)

        added: List[Chunk] = []
        unchanged: List[str] = []
        new_ids: Set[str] = set()

        for chunk in new_chunks:
            if chunk.fingerprint is None:
                raise ValueError("Chunk fingerprint cannot be None for incremental indexing")

            chunk_id = chunk.fingerprint
            new_ids.add(chunk_id)

            if chunk_id in indexed_set:
                unchanged.append(chunk_id)
            else:
                added.append(chunk)

        removed = sorted(indexed_set - new_ids)
        unchanged = sorted(set(unchanged))

        return IndexDiffResult(
            added=added,
            removed=removed,
            unchanged=unchanged,
        )