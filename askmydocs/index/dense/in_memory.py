from __future__ import annotations

from typing import Dict, List, Tuple

from .base import DenseIndex


# Local cosine similarity (kept here to avoid dependency issues if utils not implemented yet)
def _cosine_similarity(a: List[float], b: List[float]) -> float:
    # compute dot / (||a|| * ||b||)
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    # assume same length
    for i in range(len(a)):
        ai = a[i]
        bi = b[i]
        dot += ai * bi
        norm_a += ai * ai
        norm_b += bi * bi

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / ((norm_a ** 0.5) * (norm_b ** 0.5))


class InMemoryDenseIndex(DenseIndex):
    """
    Simple in-memory dense index using brute-force cosine similarity.

    Characteristics:
    - stores all vectors in memory
    - linear scan for search (O(N))
    - suitable for small to medium datasets (v1)

    TODO:
    - replace with optimized index (FAISS / HNSW)
    - add vector normalization for faster similarity computation
    - add batching support for search
    """

    def __init__(self):
        # id -> vector
        self._store: Dict[str, List[float]] = {}

    def add(self, id: str, vector: List[float]) -> None:
        """
        Add or update a vector in the index.
        """
        self._store[id] = vector

    def remove(self, id: str) -> None:
        """
        Remove a vector from the index.
        """
        if id in self._store:
            del self._store[id]

    def search(self, query_vector: List[float], k: int) -> List[Tuple[str, float]]:
        """
        Brute-force search over all vectors.
        """
        scores: List[Tuple[str, float]] = []

        for id, vector in self._store.items():
            score = _cosine_similarity(query_vector, vector)
            scores.append((id, score))

        # sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:k]

    def __len__(self) -> int:
        return len(self._store)