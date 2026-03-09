


from __future__ import annotations

from typing import Iterator, List

from askmydocs.core.types import Document
from askmydocs.core.config import IngestConfig


class DocumentBuilder:
    """
    Helper used by streaming loaders to incrementally construct Document objects
    without loading the entire file into memory.

    Responsibilities:
    - accumulate incoming text chunks
    - enforce MAX_DOCUMENT_CHARS
    - emit Document objects when limits are reached
    - reset internal buffer for next document part
    """

    def __init__(self, tenant_id: str, source_uri: str):
        self.tenant_id = tenant_id
        self.source_uri = source_uri

        self.buffer: List[str] = []
        self.char_count: int = 0
        self.part: int = 0

    def append(self, text: str) -> Iterator[str]:
        """
        Append incoming text and emit document text segments when the
        configured character limit is reached.
        """

        self.buffer.append(text)
        self.char_count += len(text)

        if self.char_count >= IngestConfig.MAX_DOCUMENT_CHARS:
            yield self._emit_text()

    def flush(self) -> Iterator[str]:
        """
        Emit remaining buffered text at end of stream.
        """

        if self.buffer:
            yield self._emit_text()

    def _emit_text(self) -> str:
        """
        Internal helper that joins the buffer and resets state.
        """

        text = "".join(self.buffer)

        self.buffer = []
        self.char_count = 0

        self.part += 1

        return text

    def build_documents(self, text_stream: Iterator[str], doc_id_fn) -> Iterator[Document]:
        """
        Convert a text stream into Document objects.

        Parameters
        ----------
        text_stream : Iterator[str]
            Stream of text chunks (lines or blocks)

        doc_id_fn : callable
            Function used to generate document IDs
        """

        for chunk in text_stream:
            for text in self.append(chunk):

                doc_id = doc_id_fn(self.tenant_id, f"{self.source_uri}#part{self.part}", text)

                metadata = {
                    "source_uri": self.source_uri,
                    "part": self.part,
                }

                yield Document(
                    doc_id=doc_id,
                    tenant_id=self.tenant_id,
                    source_uri=self.source_uri,
                    text=text,
                    metadata=metadata,
                )

        for text in self.flush():

            doc_id = doc_id_fn(self.tenant_id, f"{self.source_uri}#part{self.part}", text)

            metadata = {
                "source_uri": self.source_uri,
                "part": self.part,
            }

            yield Document(
                doc_id=doc_id,
                tenant_id=self.tenant_id,
                source_uri=self.source_uri,
                text=text,
                metadata=metadata,
            )