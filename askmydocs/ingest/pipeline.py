

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

# Incremental ingestion
from askmydocs.ingest.incremental.cache_manager import CacheManager
from askmydocs.ingest.incremental.diff_engine import DiffEngine
from askmydocs.ingest.incremental.delta_indexer import DeltaIndexer


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
        mode: str = "baseline",
    ) -> None:
        self.loader = loader
        self.splitter = splitter
        self.validator = validator
        self.scanner = scanner

        self.metadata_enricher = MetadataEnricher()
        self.fingerprint_generator = FingerprintGenerator()

        # Incremental components
        self.mode = mode
        self.cache_manager = CacheManager()
        self.diff_engine = DiffEngine()
        self.delta_indexer = DeltaIndexer()

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
                # TODO: log rejected documents for observability
                continue

            # --- Step 2: Split ---
            chunks = self.splitter.split(document)

            # --- Step 3: Metadata Enrichment ---
            enriched_chunks = self.metadata_enricher.enrich(chunks, document)

            # --- Step 4: Fingerprinting ---
            fingerprinted_chunks = self.fingerprint_generator.generate(enriched_chunks)

            # Convert to list (needed for diffing)
            fingerprinted_chunks = list(fingerprinted_chunks)
            # TODO: support streaming diff to avoid full materialization

            if self.mode == "incremental":

                # TODO: use stable doc_id (e.g., file path or file hash)
                doc_id = (document.metadata or {}).get("source") or str(hash(document.text))

                # Load existing cache
                cache = self.cache_manager.get_cache(doc_id)
                old_fingerprints = cache.get_all_fingerprints()

                # Compute diff
                diff = self.diff_engine.compute_diff(old_fingerprints, fingerprinted_chunks)

                # Apply changes
                result = self.delta_indexer.apply(diff)
                # TODO: use result for logging / tracing

                # Update cache
                # Ensure fingerprints are valid (non-None)
                new_mapping = {
                    c.fingerprint: c.fingerprint
                    for c in diff.added
                    if c.fingerprint is not None
                }
                # TODO: enforce fingerprint presence earlier in pipeline (strong validation)
                cache.bulk_add(new_mapping)
                cache.bulk_remove(diff.removed)
                self.cache_manager.save_cache(doc_id, cache)

                # Yield only added chunks
                for chunk in diff.added:
                    yield chunk

            else:
                # Baseline mode → yield all chunks
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