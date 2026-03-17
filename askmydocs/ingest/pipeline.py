

from __future__ import annotations

from typing import Iterable, Iterator, List

from askmydocs.core.types import Document, Chunk

# Loader
from askmydocs.ingest.loaders.text_loader import TextLoader

# Safety
from askmydocs.ingest.safety.validator import SafetyValidator
from askmydocs.ingest.safety.scanners import SafetyScanner

# Splitters
from askmydocs.ingest.splitters.base import BaseSplitter

# Enrichment
from askmydocs.ingest.enrich.metadata import MetadataEnricher
from askmydocs.ingest.enrich.hash_fingerprint import FingerprintGenerator


class IngestionPipeline:
    """
    Orchestrates the full ingestion flow.

    Flow:
        files
         ↓
        loader
         ↓
        document
         ↓
        safety
         ↓
        splitter
         ↓
        chunks
         ↓
        metadata enrichment
         ↓
        fingerprinting
         ↓
        final chunks
    """

    def __init__(
        self,
        loader: TextLoader,
        splitter: BaseSplitter,
        validator: SafetyValidator,
        scanner: SafetyScanner,
    ) -> None:
        self.loader = loader
        self.splitter = splitter
        self.validator = validator
        self.scanner = scanner

        self.metadata_enricher = MetadataEnricher()
        self.fingerprint_generator = FingerprintGenerator()

    def run(self, paths: Iterable[str]) -> Iterator[Chunk]:
        """
        Execute ingestion pipeline.

        Parameters
        ----------
        paths : Iterable[str]
            File or directory paths

        Returns
        -------
        Iterator[Chunk]
            Fully processed chunks
        """

        for document in self.loader.load(paths):

            # --- Step 1: Safety Scan ---
            scan_result = self.scanner.scan(document.text)

            decision = self.validator.validate(scan_result)

            if not decision.allowed:
                # Skip unsafe documents
                continue

            # --- Step 2: Split ---
            chunks = self.splitter.split(document)

            # --- Step 3: Metadata Enrichment ---
            enriched_chunks = self.metadata_enricher.enrich(chunks, document)

            # --- Step 4: Fingerprinting ---
            fingerprinted_chunks = self.fingerprint_generator.generate(enriched_chunks)

            # --- Yield final chunks ---
            for chunk in fingerprinted_chunks:
                yield chunk


# --- Helper factory (optional) ---

def build_default_pipeline(
    loader: TextLoader,
    splitter: BaseSplitter,
) -> IngestionPipeline:
    """
    Convenience builder for default pipeline.
    """

    scanner = SafetyScanner()
    validator = SafetyValidator()

    return IngestionPipeline(
        loader=loader,
        splitter=splitter,
        validator=validator,
        scanner=scanner,
    )