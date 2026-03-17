

from __future__ import annotations

import hashlib
from typing import Iterable, Iterator

from askmydocs.core.types import Chunk


class FingerprintGenerator:
    """
    Generates deterministic fingerprints for chunks.

    Used for:
    - deduplication
    - embedding cache keys
    - incremental ingestion (change detection)
    """

    def __init__(self) -> None:
        pass

    def generate(self, chunks: Iterable[Chunk]) -> Iterator[Chunk]:
        """
        Attach fingerprint to each chunk.

        Parameters
        ----------
        chunks : Iterable[Chunk]

        Returns
        -------
        Iterator[Chunk]
            New Chunk objects with fingerprint populated
        """

        for chunk in chunks:
            fingerprint = self._compute_fingerprint(chunk)
            yield self._clone_with_fingerprint(chunk, fingerprint)

    def _compute_fingerprint(self, chunk: Chunk) -> str:
        """
        Compute SHA256 hash of normalized chunk text.

        Normalization ensures stability across small formatting changes.
        """

        normalized_text = self._normalize_text(chunk.text)

        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text before hashing.

        This reduces unnecessary fingerprint changes.
        """

        if not text:
            return ""

        # Lowercase (optional but useful for dedupe stability)
        text = text.lower()

        # Normalize whitespace
        text = " ".join(text.split())

        return text

    def _clone_with_fingerprint(self, chunk: Chunk, fingerprint: str) -> Chunk:
        """
        Return new Chunk with fingerprint set (immutability).
        """

        return Chunk(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            tenant_id=chunk.tenant_id,
            text=chunk.text,
            token_count=chunk.token_count,
            span=chunk.span,
            metadata=chunk.metadata,
            fingerprint=fingerprint,
        )