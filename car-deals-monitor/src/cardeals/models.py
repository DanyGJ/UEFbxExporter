"""Modelos de datos del dominio."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass(frozen=True)
class Listing:
    """Un anuncio de coche normalizado, independiente del portal de origen.

    El identificador único global es ``uid`` (``portal:native_id``), que es lo
    que se usa para deduplicar entre ejecuciones.
    """

    portal: str
    native_id: str
    title: str
    url: str
    price: Optional[int] = None          # euros
    year: Optional[int] = None
    km: Optional[int] = None             # kilómetros
    fuel: Optional[str] = None
    gearbox: Optional[str] = None
    location: Optional[str] = None
    image: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return f"{self.portal}:{self.native_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def price_str(self) -> str:
        if self.price is None:
            return "Precio no indicado"
        return f"{self.price:,.0f} €".replace(",", ".")
