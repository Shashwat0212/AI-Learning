from __future__ import annotations
import json
import os

from typing import List, Dict, Optional

# NOTE: sentence-transformers is required
from sentence_transformers import SentenceTransformer


class Embedder:
    """
    Semantic embedder using sentence-transformers.

    Responsibilities:
    - text -> vector embedding
    - in-memory embedding cache
    - deterministic outputs

    TODO:
    - optimize encode_batch using true batch inference
    - persist embedding cache to disk
    - add LRU eviction for cache
    - support external embedding providers (OpenAI, etc.)
    - add embedding latency tracking for SLA validation
    - experiment with L2 normalization strategies
    - make model singleton across processes if needed
    - implement true batch processing using model.encode(list)
    - replace JSON cache with disk-backed key-value store (sqlite/lmdb)
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = int(self.model.get_sentence_embedding_dimension() or 0)

        # in-memory cache: fingerprint -> vector
        self._cache: Dict[str, List[float]] = {}

        self.cache_path = os.path.join(os.path.dirname(__file__), "..", ".cache", "embeddings.json")
        self.cache_path = os.path.abspath(self.cache_path)

        # ensure directory exists
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        # load cache if exists
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def encode(self, text: str, fingerprint: Optional[str] = None) -> List[float]:
        """
        Encode a single text into embedding vector.

        If fingerprint is provided, use it for caching.
        """

        if not text:
            return [0.0] * self.embedding_dim

        # cache lookup
        if fingerprint and fingerprint in self._cache:
            return self._cache[fingerprint]

        # model encoding
        vector = self.model.encode(text)

        # convert to list for consistency
        vector_list = vector.tolist()

        # cache store
        if fingerprint:
            self._cache[fingerprint] = vector_list

            # persist to disk
            try:
                with open(self.cache_path, "w") as f:
                    json.dump(self._cache, f)
            except Exception:
                pass

        return vector_list

    def encode_batch(self, texts: List[str], fingerprints: Optional[List[str]] = None) -> List[List[float]]:
        """
        Encode multiple texts.

        NOTE: v1 implementation loops over encode.
        TODO: implement true batch processing using model.encode(list_of_texts)
        """

        results: List[List[float]] = []

        if fingerprints and len(fingerprints) != len(texts):
            raise ValueError("fingerprints length must match texts length")

        for i, text in enumerate(texts):
            fp = fingerprints[i] if fingerprints else None
            results.append(self.encode(text, fp))

        return results

    def get_embedding_dim(self) -> int:
        return self.embedding_dim

    def clear_cache(self) -> None:
        """
        Clear in-memory embedding cache.
        """
        self._cache.clear()
