"""Registro de scrapers. Importar este paquete registra todos los portales."""
from .base import SCRAPERS, Scraper, get_scraper, register  # noqa: F401

# Importar los módulos concretos provoca el auto-registro vía @register.
from . import cochesnet  # noqa: F401,E402
from . import autoscout24  # noqa: F401,E402
from . import generic_html  # noqa: F401,E402

__all__ = ["SCRAPERS", "Scraper", "get_scraper", "register"]
