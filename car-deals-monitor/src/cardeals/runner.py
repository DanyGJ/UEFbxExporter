"""Orquestación: ejecuta todas las búsquedas, deduplica y notifica."""
from __future__ import annotations

import logging

from .config import AppConfig
from .models import Listing
from .notifier import EmailNotifier
from .scrapers import get_scraper
from .storage import SeenStore

log = logging.getLogger(__name__)


def run(config: AppConfig, *, dry_run: bool = False) -> dict[str, list[Listing]]:
    """Ejecuta todas las búsquedas habilitadas y notifica las novedades.

    Devuelve el diccionario de novedades agrupadas por nombre de búsqueda.
    Con ``dry_run=True`` no envía email ni persiste el estado (útil para probar).
    """
    store = SeenStore(config.state_path)
    new_by_search: dict[str, list[Listing]] = {}
    all_new: list[Listing] = []

    for search in config.searches:
        if not search.enabled:
            log.info("Búsqueda '%s' deshabilitada; se omite.", search.name)
            continue
        try:
            scraper = get_scraper(search.portal)
            results = scraper.search(search)
        except Exception as exc:  # noqa: BLE001 - un portal que falla no debe tumbar el resto
            log.error("Error en la búsqueda '%s' (%s): %s", search.name, search.portal, exc)
            continue

        new = store.filter_new(results)
        if new:
            new_by_search[search.name] = new
            all_new.extend(new)
            log.info("Búsqueda '%s': %d novedades de %d resultados.",
                     search.name, len(new), len(results))
        else:
            log.info("Búsqueda '%s': sin novedades (%d resultados).",
                     search.name, len(results))

    if all_new:
        if dry_run:
            log.info("[dry-run] %d novedades; no se envía email ni se guarda estado.",
                     len(all_new))
        else:
            EmailNotifier(config.email).send(new_by_search)
            store.mark_seen(all_new)
            store.save()
            log.info("Estado actualizado: %d anuncios conocidos en total.", len(store))
    else:
        log.info("No hay novedades en ninguna búsqueda.")

    return new_by_search
