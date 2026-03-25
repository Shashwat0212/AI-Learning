from __future__ import annotations

from typing import Dict, Set, Iterable

import json
from pathlib import Path
import tempfile
import os


class ChunkCache:
    """
    In-memory cache mapping fingerprint → chunk_id.

    This acts as the state store for incremental ingestion.

    Responsibilities:
    - Track previously seen chunk fingerprints
    - Allow fast lookup for existence checks
    - Support bulk updates after ingestion runs
    """

    def __init__(self) -> None:
        # fingerprint -> chunk_id
        self._store: Dict[str, str] = {}

    # -----------------------------
    # Core Read Operations
    # -----------------------------

    def get_all_fingerprints(self) -> Set[str]:
        """
        Return all stored fingerprints.
        """
        return set(self._store.keys())

    def exists(self, fingerprint: str) -> bool:
        """
        Check if fingerprint already exists in cache.
        """
        return fingerprint in self._store

    def get_chunk_id(self, fingerprint: str) -> str | None:
        """
        Get chunk_id for a given fingerprint.
        """
        return self._store.get(fingerprint)

    # -----------------------------
    # Core Write Operations
    # -----------------------------

    def add(self, fingerprint: str, chunk_id: str) -> None:
        """
        Add a fingerprint → chunk_id mapping.
        """
        self._store[fingerprint] = chunk_id

    def remove(self, fingerprint: str) -> None:
        """
        Remove a fingerprint from cache.
        """
        self._store.pop(fingerprint, None)

    def bulk_add(self, items: Dict[str, str]) -> None:
        """
        Add multiple fingerprint mappings at once.

        Parameters
        ----------
        items : Dict[fingerprint, chunk_id]
        """
        self._store.update(items)

    def bulk_remove(self, fingerprints: Iterable[str]) -> None:
        """
        Remove multiple fingerprints from cache.
        """
        for fp in fingerprints:
            self._store.pop(fp, None)

    def clear(self) -> None:
        """
        Clear entire cache.
        """
        self._store.clear()

    # -----------------------------
    # Debug / Introspection
    # -----------------------------

    def size(self) -> int:
        """
        Return number of cached entries.
        """
        return len(self._store)


    # -----------------------------
    # Persistence
    # -----------------------------

    def load_from_file(self, path: str | Path) -> None:
        """
        Load cache state from a JSON file.

        If the file does not exist, this is a no-op.
        """
        p = Path(path)
        if not p.exists():
            return

        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Invalid cache file format: expected dict")

            # Ensure keys/values are strings
            self._store = {str(k): str(v) for k, v in data.items()}

        except Exception as e:
            raise RuntimeError(f"Failed to load chunk cache from {p}: {e}")

    def save_to_file(self, path: str | Path) -> None:
        """
        Persist cache state to a JSON file using an atomic write.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = None  # ensure defined for cleanup

        # Write to a temp file first, then atomically replace
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, dir=str(p.parent), encoding="utf-8") as tmp:
                json.dump(self._store, tmp, ensure_ascii=False, indent=2)
                tmp_path = Path(tmp.name)

            os.replace(tmp_path, p)

        except Exception as e:
            # Best-effort cleanup if temp file exists
            try:
                if tmp_path and tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise RuntimeError(f"Failed to save chunk cache to {p}: {e}")

    def __repr__(self) -> str:
        return f"ChunkCache(size={len(self._store)})"