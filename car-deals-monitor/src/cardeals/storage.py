"""Persistencia de anuncios ya vistos para deduplicar entre ejecuciones.

Se usa un simple fichero JSON: ``uid -> ISO timestamp`` de la primera vez que se
vio el anuncio. Es suficiente para uso personal y se puede *commitear* de vuelta
al repo desde GitHub Actions para mantener estado entre ejecuciones programadas.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import Listing


class SeenStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._seen: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._seen = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._seen = {}
        else:
            self._seen = {}

    def is_new(self, listing: Listing) -> bool:
        return listing.uid not in self._seen

    def filter_new(self, listings: Iterable[Listing]) -> list[Listing]:
        """Devuelve solo los anuncios no vistos, deduplicando dentro del lote."""
        out: list[Listing] = []
        batch_uids: set[str] = set()
        for listing in listings:
            if listing.uid in batch_uids:
                continue
            if self.is_new(listing):
                out.append(listing)
                batch_uids.add(listing.uid)
        return out

    def mark_seen(self, listings: Iterable[Listing]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for listing in listings:
            self._seen.setdefault(listing.uid, now)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._seen, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )

    def __len__(self) -> int:
        return len(self._seen)
