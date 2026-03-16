

from __future__ import annotations

from typing import Iterator

from askmydocs.core.types import Document, Chunk
from askmydocs.ingest.splitters.base import BaseSplitter
from askmydocs.ingest.utils.chunk_builder import ChunkBuilder
from askmydocs.core.config import OverlapMode


class FixedTokenSplitter(BaseSplitter):
    """
    Baseline splitter that segments text using simple paragraph boundaries
    and relies on ChunkBuilder to enforce token limits.

    Strategy
    --------
    1. Split document text into coarse segments (paragraphs).
    2. Feed segments into ChunkBuilder.
    3. ChunkBuilder emits chunks when token limits are reached.

    This splitter prioritizes simplicity and predictable chunk sizes.
    """

    def split(self, document: Document) -> Iterator[Chunk]:
        """
        Split a document into token-bounded chunks.

        Parameters
        ----------
        document
            The Document object to split.

        Returns
        -------
        Iterator[Chunk]
            Stream of chunks generated from the document.
        """

        if not document.text:
            return

        builder = ChunkBuilder(document, overlap_mode=OverlapMode.TOKEN)

        # Basic segmentation: paragraphs separated by blank lines
        segments = document.text.split("\n\n")

        for segment in segments:
            segment = segment.strip()

            # Skip empty segments
            if not segment:
                continue

            # Reattach newline separation so paragraphs don't merge
            segment = segment + "\n\n"

            for chunk in builder.add_segment(segment):
                yield chunk

        # Emit any remaining buffered text
        for chunk in builder.flush():
            yield chunk