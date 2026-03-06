from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Iterator

from askmydocs.core.types import Document
from askmydocs.core.config import IngestConfig


SUPPORTED_EXTENSIONS = {".txt", ".md", ".jsonl"}


# -------------------------------------------------
# File Discovery
# -------------------------------------------------


def discover_files(path: str | Path) -> Iterator[Path]:
    """
    Discover supported files from a path.

    Supports:
    - single file
    - recursive directory traversal
    """

    p = Path(path)

    if p.is_file():
        if p.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield p
        return

    if p.is_dir():
        for root, _, files in os.walk(p):
            for f in files:
                fp = Path(root) / f
                if fp.suffix.lower() in SUPPORTED_EXTENSIONS:
                    yield fp


# -------------------------------------------------
# Encoding Detection
# -------------------------------------------------


def read_file_with_encoding_detection(path: Path) -> tuple[str, str]:
    """
    Attempts decoding with several encodings.

    Returns
    -------
    text : str
    encoding_used : str
    """

    raw = path.read_bytes()

    encodings = [
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "latin-1",
    ]

    for enc in encodings:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue

    # Fallback (should not happen because latin-1 always works)
    return raw.decode("latin-1", errors="replace"), "latin-1"


# -------------------------------------------------
# Text Normalization
# -------------------------------------------------


def normalize_text(text: str) -> str:
    """
    Normalize text to avoid downstream processing issues.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\x00", "")

    return text


# -------------------------------------------------
# Document ID Generation
# -------------------------------------------------


def generate_doc_id(tenant_id: str, source_uri: str, text: str) -> str:
    """
    Generates deterministic document IDs.

    Any content change results in a new doc_id.
    """

    h = hashlib.sha256()

    h.update(tenant_id.encode())
    h.update(source_uri.encode())
    h.update(text.encode())

    return h.hexdigest()


# -------------------------------------------------
# JSONL Loader
# -------------------------------------------------


def load_jsonl(path: Path, tenant_id: str) -> Iterator[Document]:
    """
    Each line in a JSONL file becomes a separate Document.
    """

    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()

            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = obj.get("text")

            if not text:
                continue

            text = normalize_text(text)

            doc_id = generate_doc_id(tenant_id, f"{path}:{i}", text)

            metadata = {
                "source_uri": str(path),
                "line_number": i,
                "extension": "jsonl",
            }

            yield Document(
                doc_id=doc_id,
                tenant_id=tenant_id,
                source_uri=str(path),
                text=text,
                metadata=metadata,
            )


# -------------------------------------------------
# Main Loader
# -------------------------------------------------


def load_documents(path: str | Path, tenant_id: str) -> Iterable[Document]:
    """
    Main ingestion entrypoint.

    Parameters
    ----------
    path : str | Path
        file or directory

    tenant_id : str
        multi-tenant isolation key
    """

    for file_path in discover_files(path):

        # JSONL handled separately
        if file_path.suffix.lower() == ".jsonl":
            yield from load_jsonl(file_path, tenant_id)
            continue

        text, encoding = read_file_with_encoding_detection(file_path)

        text = normalize_text(text)

        # Guardrails
        if len(text) > IngestConfig.MAX_DOCUMENT_CHARS:
            continue

        size_bytes = file_path.stat().st_size

        if size_bytes > IngestConfig.MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
            continue

        doc_id = generate_doc_id(tenant_id, str(file_path), text)

        metadata = {
            "source_uri": str(file_path),
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "encoding": encoding,
            "size_bytes": size_bytes,
        }

        yield Document(
            doc_id=doc_id,
            tenant_id=tenant_id,
            source_uri=str(file_path),
            text=text,
            metadata=metadata,
        )
