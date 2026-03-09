from __future__ import annotations

from pathlib import Path

from askmydocs.core.config import IngestConfig
from askmydocs.core.errors import DocumentTooLargeError
from askmydocs.ingest.safety.types import ScanFinding


# Allowed file extensions for ingestion
ALLOWED_EXTENSIONS = {".txt", ".md", ".jsonl"}


# Threshold for binary detection
# If too many non-printable characters are detected, the file is considered binary
MAX_BINARY_RATIO = 0.30



def validate_file(file_path: Path) -> list[ScanFinding]:
    """
    Validate a file before ingestion.

    This performs structural validation checks including:

    - extension allowlist
    - file size limit
    - binary content detection

    Returns
    -------
    list[ScanFinding]
        Findings detected during validation.
        An empty list means the file passed validation.
    """

    findings: list[ScanFinding] = []

    # ------------------------------
    # Extension allowlist
    # ------------------------------

    ext = file_path.suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        findings.append(
            ScanFinding(
                category="file_extension",
                severity="high",
                message=f"Unsupported file extension: {ext}",
                metadata={"extension": ext},
            )
        )

    # ------------------------------
    # File size check
    # ------------------------------

    size_bytes = file_path.stat().st_size

    max_bytes = IngestConfig.MAX_DOCUMENT_SIZE_MB * 1024 * 1024

    if size_bytes > max_bytes:
        raise DocumentTooLargeError(str(file_path), IngestConfig.MAX_DOCUMENT_SIZE_MB)

    # ------------------------------
    # Binary detection
    # ------------------------------

    # Read a small sample to estimate binary ratio
    sample_size = 4096

    try:
        with file_path.open("rb") as f:
            sample = f.read(sample_size)
    except Exception:
        findings.append(
            ScanFinding(
                category="file_read",
                severity="high",
                message="File could not be read during validation",
            )
        )
        return findings

    if sample:
        non_printable = sum(1 for b in sample if b < 9 or (13 < b < 32))
        binary_ratio = non_printable / len(sample)

        if binary_ratio > MAX_BINARY_RATIO:
            findings.append(
                ScanFinding(
                    category="binary_content",
                    severity="high",
                    message="File appears to contain binary content",
                    metadata={"binary_ratio": binary_ratio},
                )
            )

    return findings
