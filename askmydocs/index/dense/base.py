

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple


class DenseIndex(ABC):
    """
    Abstract interface for dense (vector) index.

    Responsibilities:
    - store vector embeddings
    - support similarity search
    - support incremental updates (add/remove)

    All implementations (in-memory, FAISS, etc.) must follow this contract.
    """

    @abstractmethod
    def add(self, id: str, vector: List[float]) -> None:
        """
        Add a vector to the index.

        Args:
            id: unique identifier (fingerprint)
            vector: embedding vector
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, id: str) -> None:
        """
        Remove a vector from the index.

        Args:
            id: identifier of vector to remove
        """
        raise NotImplementedError

    @abstractmethod
    def search(self, query_vector: List[float], k: int) -> List[Tuple[str, float]]:
        """
        Search for top-k nearest vectors.

        Args:
            query_vector: embedding of query
            k: number of results

        Returns:
            List of (id, score) tuples sorted by similarity (descending)
        """
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        """
        Return number of indexed vectors.
        """
        raise NotImplementedError