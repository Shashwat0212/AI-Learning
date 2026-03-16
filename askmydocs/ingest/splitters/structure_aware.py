

from __future__ import annotations

import re
from typing import Iterator, List, Tuple

from askmydocs.core.types import Chunk, Document
from askmydocs.ingest.splitters.base import BaseSplitter
from askmydocs.ingest.utils.chunk_builder import ChunkBuilder
from askmydocs.core.config import OverlapMode
from askmydocs.ingest.utils.token_estimator import estimate_tokens


# Matches Markdown-style headings such as:
# # Title
# ## Section
# ### Subsection
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$", re.MULTILINE)

# Fast sentence boundary regex used for fallback grouping inside sections
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class StructureAwareSplitter(BaseSplitter):
    """
    Splitter that prefers document structure (Markdown headings/sections)
    and falls back to sentence-aware grouping within each section.

    Strategy
    --------
    1. Detect Markdown headings and split the document into sections.
    2. For each section, preserve the heading as an anchor by prepending it
       to grouped text emitted from that section.
    3. Within a section, group sentences until the target token threshold is
       reached while avoiding mid-sentence splits.
    4. Emit semantic groups through ChunkBuilder.add_group().

    This is the most retrieval-friendly splitter for technical documents,
    markdown notes, wikis, and structured long-form text.
    """

    def split(self, document: Document) -> Iterator[Chunk]:
        if not document.text:
            return

        builder = ChunkBuilder(document, overlap_mode=OverlapMode.NONE)
        sections = self._split_sections(document.text)

        for heading, body in sections:
            heading_prefix = f"{heading}\n\n" if heading else ""
            sentences = self._split_sentences(body)

            if not sentences:
                # Section has no sentence boundaries but still contains text.
                raw_text = body.strip()
                if raw_text:
                    group_text = heading_prefix + raw_text
                    for chunk in builder.add_group(group_text):
                        yield chunk
                continue

            current_group: List[str] = []
            current_tokens = estimate_tokens(heading_prefix) if heading_prefix else 0
            min_chunk_tokens = int(self.target_tokens * 0.6)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                sentence_tokens = estimate_tokens(sentence)

                # Extremely large single sentence: emit directly as its own group.
                if sentence_tokens >= self.target_tokens:
                    if current_group:
                        group_text = self._build_group_text(heading_prefix, current_group)
                        for chunk in builder.add_group(group_text):
                            yield chunk
                        current_group = []
                        current_tokens = estimate_tokens(heading_prefix) if heading_prefix else 0

                    large_group = heading_prefix + sentence
                    for chunk in builder.add_group(large_group):
                        yield chunk
                    continue

                projected_tokens = current_tokens + sentence_tokens

                if projected_tokens > self.target_tokens:
                    # If the current group is already reasonably sized, emit it.
                    if current_group and current_tokens >= min_chunk_tokens:
                        group_text = self._build_group_text(heading_prefix, current_group)
                        for chunk in builder.add_group(group_text):
                            yield chunk

                        current_group = [sentence]
                        current_tokens = (
                            (estimate_tokens(heading_prefix) if heading_prefix else 0)
                            + sentence_tokens
                        )
                    else:
                        # Merge a small trailing group with the next sentence rather than
                        # creating a tiny chunk. This may slightly exceed target size.
                        current_group.append(sentence)
                        current_tokens = projected_tokens
                else:
                    current_group.append(sentence)
                    current_tokens = projected_tokens

            if current_group:
                group_text = self._build_group_text(heading_prefix, current_group)
                for chunk in builder.add_group(group_text):
                    yield chunk

        for chunk in builder.flush():
            yield chunk

    def _split_sections(self, text: str) -> List[Tuple[str | None, str]]:
        """
        Split a document into (heading, body) sections.

        If no headings are present, the entire document is returned as a
        single section with heading=None.
        """

        matches = list(_HEADING_RE.finditer(text))

        if not matches:
            return [(None, text)]

        sections: List[Tuple[str | None, str]] = []

        # Preamble before the first heading
        first_match = matches[0]
        if first_match.start() > 0:
            preamble = text[: first_match.start()].strip()
            if preamble:
                sections.append((None, preamble))

        for idx, match in enumerate(matches):
            heading_text = match.group(2).strip()
            body_start = match.end()
            body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[body_start:body_end].strip()
            sections.append((heading_text, body))

        return sections

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split section text into sentences using a fast regex heuristic.
        """

        if not text.strip():
            return []

        return [s for s in _SENTENCE_SPLIT_RE.split(text) if s and s.strip()]

    def _build_group_text(self, heading_prefix: str, sentences: List[str]) -> str:
        """
        Build one semantic group from a section heading and grouped sentences.
        """

        body = " ".join(s.strip() for s in sentences if s and s.strip())
        return heading_prefix + body