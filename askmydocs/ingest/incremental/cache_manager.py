from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .chunk_cache import ChunkCache


class CacheManager:
    """
    Manages per-document chunk caches and a master index.

    Structure:

    base_dir/
      index.json
      doc_<doc_id>.json
    """

    def __init__(self, base_dir: str = ".cache") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.base_dir / "index.json"
        self._index: Dict[str, str] = {}

        self._load_index()

    # -----------------------------
    # Index Management
    # -----------------------------

    def _load_index(self) -> None:
        if not self.index_path.exists():
            self._index = {}
            return

        try:
            with self.index_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Invalid index format")

            self._index = {str(k): str(v) for k, v in data.items()}

        except Exception as e:
            raise RuntimeError(f"Failed to load cache index: {e}")

    def _save_index(self) -> None:
        try:
            with self.index_path.open("w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)

        except Exception as e:
            raise RuntimeError(f"Failed to save cache index: {e}")

    # -----------------------------
    # Path Resolution
    # -----------------------------

    def _get_doc_path(self, doc_id: str) -> Path:
        filename = f"doc_{doc_id}.json"
        return self.base_dir / filename

    # -----------------------------
    # Public API
    # -----------------------------

    def get_cache(self, doc_id: str) -> ChunkCache:
        """
        Load (or create) a cache for a specific document.
        """
        cache = ChunkCache()

        if doc_id in self._index:
            path = self.base_dir / self._index[doc_id]
            cache.load_from_file(path)
        else:
            # create mapping but don't save file yet
            path = self._get_doc_path(doc_id)
            self._index[doc_id] = path.name
            self._save_index()

        return cache

    def save_cache(self, doc_id: str, cache: ChunkCache) -> None:
        """
        Persist a document cache and update index.
        """
        if doc_id not in self._index:
            path = self._get_doc_path(doc_id)
            self._index[doc_id] = path.name
            self._save_index()

        path = self.base_dir / self._index[doc_id]
        cache.save_to_file(path)

    def delete_cache(self, doc_id: str) -> None:
        """
        Remove a document cache completely.
        """
        if doc_id not in self._index:
            return

        path = self.base_dir / self._index[doc_id]

        if path.exists():
            path.unlink()

        del self._index[doc_id]
        self._save_index()

    def list_documents(self) -> list[str]:
        """
        List all cached document IDs.
        """
        return list(self._index.keys())

    def __repr__(self) -> str:
        return f"CacheManager(docs={len(self._index)})"
