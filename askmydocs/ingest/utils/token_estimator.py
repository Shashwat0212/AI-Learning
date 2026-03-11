

from __future__ import annotations

import re

# Precompiled regex patterns for performance
_WORD_RE = re.compile(r"\w+")
_PUNCT_RE = re.compile(r"[^\w\s]")


def estimate_tokens(text: str) -> int:
    """
    Fast token estimation used during ingestion.

    This avoids calling a real tokenizer which is expensive and unnecessary
    during chunking. The heuristic approximates token count using:

    tokens ≈ words + punctuation + subword_estimate

    where subword_estimate approximates token fragments produced by
    subword tokenization used in modern LLMs.

    This method is ~100x faster than using a tokenizer and sufficiently
    accurate for chunk boundary estimation.
    """

    if not text:
        return 0

    char_count = len(text)

    # Word tokens
    word_count = len(_WORD_RE.findall(text))

    # Punctuation tokens
    punct_count = len(_PUNCT_RE.findall(text))

    # Approximate subword fragments
    subword_estimate = char_count // 10

    estimate = word_count + punct_count + subword_estimate

    return max(1, estimate)


def estimate_tokens_fast(text: str) -> int:
    """
    Ultra-fast fallback estimator.

    tokens ≈ characters / 4

    Useful for quick experimentation or very large corpora.
    """

    if not text:
        return 0

    return max(1, len(text) // 4)