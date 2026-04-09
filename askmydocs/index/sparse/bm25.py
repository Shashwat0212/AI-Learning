

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import DefaultDict, Dict, List, Set, Tuple

from .base import SparseIndex


_TOKEN_PATTERN = re.compile(r"\w+")


def _tokenize(text: str) -> List[str]:
    """
    Simple tokenizer for sparse indexing.

    Lowercases text and extracts alphanumeric word tokens.

    TODO:
    - replace with more robust tokenization/stemming if needed
    - add stopword removal if retrieval quality requires it
    """
    return _TOKEN_PATTERN.findall(text.lower())


class BM25Index(SparseIndex):
    """
    Simple BM25-style sparse index.

    Characteristics:
    - stores document term frequencies in memory
    - maintains inverted index for candidate lookup
    - supports incremental add/remove operations

    TODO:
    - validate scoring quality on retrieval benchmarks
    - optimize memory usage for large corpora
    - persist sparse index to disk
    - add field-aware scoring if needed later
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

        # id -> token frequency map
        self._doc_term_freqs: Dict[str, Counter[str]] = {}

        # id -> document length (token count)
        self._doc_lengths: Dict[str, int] = {}

        # term -> ids containing term
        self._inverted_index: DefaultDict[str, Set[str]] = defaultdict(set)

        self._total_docs = 0
        self._total_length = 0

    def add(self, id: str, text: str) -> None:
        """
        Add or update a document in the sparse index.
        """
        # If document already exists, remove old version first
        if id in self._doc_term_freqs:
            self.remove(id)

        tokens = _tokenize(text)
        term_freqs = Counter(tokens)
        doc_length = len(tokens)

        self._doc_term_freqs[id] = term_freqs
        self._doc_lengths[id] = doc_length

        for term in term_freqs:
            self._inverted_index[term].add(id)

        self._total_docs += 1
        self._total_length += doc_length

    def remove(self, id: str) -> None:
        """
        Remove a document from the sparse index.
        """
        if id not in self._doc_term_freqs:
            return

        term_freqs = self._doc_term_freqs[id]
        doc_length = self._doc_lengths[id]

        for term in term_freqs:
            ids = self._inverted_index[term]
            ids.discard(id)
            if not ids:
                del self._inverted_index[term]

        del self._doc_term_freqs[id]
        del self._doc_lengths[id]

        self._total_docs -= 1
        self._total_length -= doc_length

    def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        """
        Search for top-k documents using BM25 scoring.
        """
        if self._total_docs == 0 or k <= 0:
            return []

        query_terms = _tokenize(query)
        if not query_terms:
            return []

        avg_doc_length = self._total_length / self._total_docs if self._total_docs > 0 else 0.0
        scores: Dict[str, float] = defaultdict(float)

        # Candidate generation through inverted index
        candidate_ids: Set[str] = set()
        for term in query_terms:
            candidate_ids.update(self._inverted_index.get(term, set()))

        for term in query_terms:
            docs_with_term = self._inverted_index.get(term, set())
            doc_freq = len(docs_with_term)
            if doc_freq == 0:
                continue

            # BM25 idf
            idf = math.log(1 + (self._total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

            for doc_id in candidate_ids:
                term_freqs = self._doc_term_freqs[doc_id]
                tf = term_freqs.get(term, 0)
                if tf == 0:
                    continue

                doc_length = self._doc_lengths[doc_id]
                norm = 1 - self.b + self.b * (doc_length / avg_doc_length) if avg_doc_length > 0 else 1.0
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * norm

                scores[doc_id] += idf * (numerator / denominator)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:k]

    def __len__(self) -> int:
        return self._total_docs