

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple


class SparseIndex(ABC):
    """
    Abstract interface for sparse (keyword/BM25-like) index.

    Responsibilities:
    - index text documents by terms
    - support keyword-based search
    - support incremental updates (add/remove)

    All implementations (simple inverted index, BM25, etc.) must follow this contract.
    """

    @abstractmethod
    def add(self, id: str, text: str) -> None:
        """
        Add a text document to the index.

        Args:
            id: unique identifier (fingerprint)
            text: raw text content of the chunk
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, id: str) -> None:
        """
        Remove a document from the index.

        Args:
            id: identifier of document to remove
        """
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        """
        Search for top-k documents using keyword-based scoring.

        Args:
            query: raw query text
            k: number of results

        Returns:
            List of (id, score) tuples sorted by relevance (descending)
        """
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        """
        Return number of indexed documents.
        """
        raise NotImplementedError