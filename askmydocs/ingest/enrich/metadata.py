

from __future__ import annotations

from typing import Iterator, Iterable, Dict, Any

from askmydocs.core.types import Chunk, Document


class MetadataEnricher:
    """
    Enriches chunks with additional metadata derived from the document and
    chunk-level information.

    This stage prepares chunks for better retrieval, filtering, and debugging.
    """

    def __init__(self) -> None:
        pass

    def enrich(
        self,
        chunks: Iterable[Chunk],
        document: Document
    ) -> Iterator[Chunk]:
        """
        Enrich each chunk with metadata.

        Parameters
        ----------
        chunks
            Iterable of Chunk objects from the splitter.

        document
            Source document from which chunks were generated.

        Returns
        -------
        Iterator[Chunk]
            Enriched Chunk objects.
        """

        # Convert to list once to compute total_chunks
        chunk_list = list(chunks)
        total_chunks = len(chunk_list)

        for idx, chunk in enumerate(chunk_list):
            enriched_metadata = self._build_metadata(
                chunk=chunk,
                document=document,
                chunk_index=idx,
                total_chunks=total_chunks
            )

            yield self._clone_chunk_with_metadata(chunk, enriched_metadata)

    def _build_metadata(
        self,
        chunk: Chunk,
        document: Document,
        chunk_index: int,
        total_chunks: int
    ) -> Dict[str, Any]:
        """
        Build enriched metadata dictionary.
        """

        metadata: Dict[str, Any] = {}

        # --- Base document metadata ---
        metadata.update(document.metadata or {})

        # --- Chunk positional metadata ---
        metadata["chunk_index"] = chunk_index
        metadata["total_chunks"] = total_chunks

        # --- Source tracking ---
        metadata["doc_id"] = document.doc_id
        metadata["source_uri"] = document.source_uri

        # --- Structural hints ---
        # If heading was injected in text (structure-aware splitter), try to extract
        heading = self._extract_heading(chunk.text)
        if heading:
            metadata["heading"] = heading

        # --- Length signals ---
        metadata["token_count"] = chunk.token_count
        metadata["char_count"] = len(chunk.text)

        return metadata

    def _extract_heading(self, text: str) -> str | None:
        """
        Heuristic: extract heading if present at the start of the chunk.

        Assumes structure-aware splitter prepends:
        Heading\n\ncontent...
        """

        if not text:
            return None

        parts = text.split("\n\n", 1)
        if len(parts) < 2:
            return None

        heading = parts[0].strip()

        # Avoid very long headings (likely not a real heading)
        if len(heading) > 200:
            return None

        return heading

    def _clone_chunk_with_metadata(
        self,
        chunk: Chunk,
        metadata: Dict[str, Any]
    ) -> Chunk:
        """
        Return a new Chunk with updated metadata (immutability).
        """

        return Chunk(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            tenant_id=chunk.tenant_id,
            text=chunk.text,
            token_count=chunk.token_count,
            span=chunk.span,
            metadata=metadata,
            fingerprint=chunk.fingerprint,
        )