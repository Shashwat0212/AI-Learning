from __future__ import annotations

from typing import List


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns a value in range [-1, 1].

    Assumes both vectors are of same length.

    TODO:
    - optimize using numpy for large-scale usage
    - validate behavior for edge cases
    """
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for i in range(len(a)):
        ai = a[i]
        bi = b[i]
        dot += ai * bi
        norm_a += ai * ai
        norm_b += bi * bi

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / ((norm_a ** 0.5) * (norm_b ** 0.5))


def l2_normalize(vec: List[float]) -> List[float]:
    """
    Normalize a vector using L2 norm.

    Returns a new normalized vector.

    TODO:
    - consider in-place normalization for performance
    """
    norm = 0.0
    for v in vec:
        norm += v * v

    if norm == 0.0:
        return vec

    norm = norm ** 0.5

    return [v / norm for v in vec]