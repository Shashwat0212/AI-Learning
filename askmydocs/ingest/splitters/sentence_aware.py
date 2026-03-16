from __future__ import annotations

import re
from typing import Iterator, List

from askmydocs.core.types import Document, Chunk
from askmydocs.ingest.splitters.base import BaseSplitter
from askmydocs.ingest.utils.chunk_builder import ChunkBuilder
from askmydocs.core.config import OverlapMode
from askmydocs.ingest.utils.token_estimator import estimate_tokens


# Fast sentence boundary regex
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class SentenceAwareSplitter(BaseSplitter):
    """
    Sentence-aware splitter that groups sentences until the target token
    threshold is reached while avoiding mid-sentence splits.

    Additional heuristics implemented:

    - minimum chunk size enforcement
    - never split inside a sentence
    - large sentence passthrough
    """

    def split(self, document: Document) -> Iterator[Chunk]:
        if not document.text:
            return

        builder = ChunkBuilder(document, overlap_mode=OverlapMode.SENTENCE)

        sentences = _SENTENCE_SPLIT_RE.split(document.text)

        current_group: List[str] = []
        current_tokens = 0

        min_chunk_tokens = int(self.target_tokens * 0.6)

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_tokens = estimate_tokens(sentence)

            # Handle extremely large single sentence
            if sentence_tokens >= self.target_tokens:
                if current_group:
                    group_text = " ".join(current_group) + " "
                    for chunk in builder.add_group(group_text):
                        yield chunk
                    current_group = []
                    current_tokens = 0

                # emit large sentence directly
                large_segment = sentence + " "
                for chunk in builder.add_group(large_segment):
                    yield chunk
                continue

            # Check if adding this sentence exceeds target
            if current_tokens + sentence_tokens > self.target_tokens:
                if current_tokens >= min_chunk_tokens:
                    group_text = " ".join(current_group) + " "
                    for chunk in builder.add_group(group_text):
                        yield chunk

                    current_group = [sentence]
                    current_tokens = sentence_tokens
                else:
                    # merge small chunk with next sentence
                    current_group.append(sentence)
                    current_tokens += sentence_tokens
            else:
                current_group.append(sentence)
                current_tokens += sentence_tokens

        # Flush remaining group
        if current_group:
            group_text = " ".join(current_group) + " "
            for chunk in builder.add_group(group_text):
                yield chunk

        # Emit any remaining buffered text
        for chunk in builder.flush():
            yield chunk
