from __future__ import annotations

import hashlib
from typing import Iterator, List

from askmydocs.core.types import Chunk, Document
from askmydocs.core.config import IngestConfig, OverlapMode
from askmydocs.ingest.utils.token_estimator import estimate_tokens


class ChunkBuilder:
    """
    Utility class used by splitters to safely construct Chunk objects.

    Responsibilities:
    - manage token-based buffering
    - track character span offsets
    - apply overlap between chunks
    - generate deterministic chunk IDs
    - enforce MAX_CHUNKS_PER_DOCUMENT guardrail
    """

    def __init__(self, document: Document, overlap_mode: OverlapMode = OverlapMode.TOKEN):
        self.document = document
        self.overlap_mode = overlap_mode

        self.buffer: List[str] = []
        self.buffer_tokens: int = 0

        self.span_start: int = 0
        self.current_offset: int = 0

        self.chunk_count: int = 0

        self.target_tokens = IngestConfig.TARGET_CHUNK_TOKENS
        self.overlap_tokens = int(self.target_tokens * IngestConfig.CHUNK_OVERLAP)

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def add_segment(self, text: str) -> Iterator[Chunk]:
        """
        Add text to the buffer and emit chunks when token limits are reached.
        """

        if not text:
            return

        token_count = estimate_tokens(text)

        self.buffer.append(text)
        self.buffer_tokens += token_count

        emitted: List[Chunk] = []

        if self.buffer_tokens >= self.target_tokens:
            emitted.append(self._emit_chunk())

        for chunk in emitted:
            yield chunk

        self.current_offset += len(text)

    def add_group(self, text: str) -> Iterator[Chunk]:
        """
        Add a pre-grouped semantic text block (already sentence-grouped by
        a splitter) and emit it as a chunk candidate.

        Unlike add_segment(), this bypasses incremental buffering because
        the splitter has already decided the semantic boundary.
        """

        if not text:
            return

        # Start this chunk exactly where the current offset is
        self.span_start = self.current_offset

        # Replace buffer with the grouped text
        self.buffer = [text]
        self.buffer_tokens = estimate_tokens(text)

        # Emit chunk directly
        chunk = self._emit_chunk()
        yield chunk

        # Advance offset after emitting
        self.current_offset += len(text)

    def flush(self) -> Iterator[Chunk]:
        """
        Emit remaining buffered text as the final chunk.
        """

        if self.buffer:
            yield self._emit_chunk(final=True)

    # -------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------

    def _emit_chunk(self, final: bool = False) -> Chunk:
        """
        Construct a Chunk object from the current buffer.
        """

        text = "".join(self.buffer)

        span_end = self.span_start + len(text)

        token_count = estimate_tokens(text)

        chunk_id = self._generate_chunk_id(text, span_end)

        chunk = Chunk(
            chunk_id=chunk_id,
            doc_id=self.document.doc_id,
            tenant_id=self.document.tenant_id,
            text=text,
            token_count=token_count,
            span=(self.span_start, span_end),
            metadata=self.document.metadata,
        )

        self.chunk_count += 1

        if self.chunk_count > IngestConfig.MAX_CHUNKS_PER_DOCUMENT:
            raise RuntimeError("Maximum chunks per document exceeded")

        # Prepare overlap buffer depending on configured mode
        if not final and self.overlap_mode == OverlapMode.TOKEN and self.overlap_tokens > 0:
            overlap_chars = self._apply_token_overlap(text)
            self.span_start = span_end - overlap_chars

        elif not final and self.overlap_mode == OverlapMode.SENTENCE:
            overlap_chars = self._apply_sentence_overlap(text)
            self.span_start = span_end - overlap_chars

        else:
            self.buffer = []
            self.buffer_tokens = 0
            self.span_start = span_end

        return chunk

    def _apply_token_overlap(self, text: str) -> int:
        """
        Retain overlap tokens from the end of the previous chunk.
        Returns the number of characters retained so span offsets can be fixed.
        """

        # approximate character overlap based on token overlap
        approx_chars_per_token = 4
        overlap_chars = min(len(text), self.overlap_tokens * approx_chars_per_token)

        overlap_text = text[-overlap_chars:]

        self.buffer = [overlap_text]
        self.buffer_tokens = estimate_tokens(overlap_text)

        return overlap_chars

    def _apply_sentence_overlap(self, text: str) -> int:
        """
        Retain the last sentence from the previous chunk for semantic overlap.
        Returns number of characters retained.
        """

        import re

        sentences = re.split(r"(?<=[.!?])\s+", text)

        if not sentences:
            return 0

        last_sentence = sentences[-1]

        overlap_chars = len(last_sentence)

        self.buffer = [last_sentence]
        self.buffer_tokens = estimate_tokens(last_sentence)

        return overlap_chars

    def _generate_chunk_id(self, text: str, span_end: int) -> str:
        """
        Generate deterministic chunk ID.
        """

        payload = f"{self.document.doc_id}:{span_end}:{text}".encode("utf-8")

        return hashlib.sha256(payload).hexdigest()