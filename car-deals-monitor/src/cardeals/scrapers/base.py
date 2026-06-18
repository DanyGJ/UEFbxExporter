"""Base de scrapers y registro de portales.

Para añadir un portal nuevo basta con crear una clase que herede de ``Scraper`` y
decorarla con ``@register("nombre")``. El runner la encontrará automáticamente.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Callable, Type

import requests

from ..config import SearchConfig
from ..models import Listing

log = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

# Registro global: nombre de portal -> clase de scraper.
SCRAPERS: dict[str, Type["Scraper"]] = {}


def register(name: str) -> Callable[[Type["Scraper"]], Type["Scraper"]]:
    def deco(cls: Type["Scraper"]) -> Type["Scraper"]:
        SCRAPERS[name] = cls
        cls.name = name
        return cls
    return deco


def get_scraper(name: str) -> "Scraper":
    if name not in SCRAPERS:
        raise KeyError(
            f"Portal desconocido: '{name}'. Disponibles: {sorted(SCRAPERS)}"
        )
    return SCRAPERS[name]()


class Scraper(ABC):
    """Interfaz común a todos los portales."""

    name: str = "base"
    request_delay: float = 1.0  # segundos de cortesía entre peticiones

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _get(self, url: str, **kwargs) -> requests.Response:
        time.sleep(self.request_delay)
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp

    def _post(self, url: str, **kwargs) -> requests.Response:
        time.sleep(self.request_delay)
        resp = self.session.post(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp

    @abstractmethod
    def search(self, search: SearchConfig) -> list[Listing]:
        """Ejecuta la búsqueda y devuelve la lista de anuncios encontrados."""
        raise NotImplementedError
