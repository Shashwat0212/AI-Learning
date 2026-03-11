from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from askmydocs.core.types import Document, Chunk
from askmydocs.core.config import IngestConfig


class BaseSplitter(ABC):
    """
    Base interface for all document splitters.

    Splitters are responsible for deciding *where* to split a document.
    They should NOT construct Chunk objects directly. Instead they should
    pass text segments to ChunkBuilder, which handles:

    - span offsets
    - token estimation
    - overlap
    - chunk id generation

    All splitters must implement `split()`.
    """

    def __init__(
        self,
        target_tokens: int | None = None,
        overlap: float | None = None,
    ) -> None:
        """
        Initialize splitter configuration.

        Parameters
        ----------
        target_tokens
            Target chunk size in tokens.
        overlap
            Fractional overlap between chunks.
        """

        self.target_tokens = target_tokens or IngestConfig.TARGET_CHUNK_TOKENS
        self.overlap = overlap if overlap is not None else IngestConfig.CHUNK_OVERLAP

    @abstractmethod
    def split(self, document: Document) -> Iterator[Chunk]:
        """
        Split a document into chunks.

        Parameters
        ----------
        document
            The Document to split.

        Returns
        -------
        Iterator[Chunk]
            Stream of generated chunks.
        """
        raise NotImplementedError
