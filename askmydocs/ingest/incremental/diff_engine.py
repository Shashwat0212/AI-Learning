from __future__ import annotations

from typing import Iterable, List, Set

from askmydocs.core.types import Chunk, DiffResult


class DiffEngine:
    """
    Compare current chunks against previously cached fingerprints to determine
    what changed for a specific document.

    This is the intelligence layer of incremental ingestion.
    """

    def compute_diff(
        self,
        old_fingerprints: Set[str],
        new_chunks: Iterable[Chunk],
    ) -> DiffResult:
        """
        Compute added, removed, and unchanged items.

        Parameters
        ----------
        old_fingerprints
            Fingerprints from the persisted cache for the document.

        new_chunks
            Newly generated chunks for the current document version.

        Returns
        -------
        DiffResult
            Structured diff output.
        """

        added: List[Chunk] = []
        unchanged: List[Chunk] = []
        new_fingerprints: Set[str] = set()

        for chunk in new_chunks:
            if not chunk.fingerprint:
                raise ValueError(
                    "DiffEngine requires chunks with fingerprints. "
                    "Run fingerprint generation before incremental diffing."
                )

            fingerprint = chunk.fingerprint
            new_fingerprints.add(fingerprint)

            if fingerprint in old_fingerprints:
                unchanged.append(chunk)
            else:
                added.append(chunk)

        removed = sorted(old_fingerprints - new_fingerprints)

        return DiffResult(
            added=added,
            removed=removed,
            unchanged=unchanged,
        )