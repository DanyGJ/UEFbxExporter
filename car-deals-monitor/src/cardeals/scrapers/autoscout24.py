"""Scraper de AutoScout24.

La web de AutoScout24 está hecha con Next.js e incrusta todos los datos de la
búsqueda en un bloque JSON ``<script id="__NEXT_DATA__">`` dentro del HTML. Este
scraper descarga la página de resultados y extrae ese JSON, lo que evita depender
de selectores CSS frágiles.

La forma más sencilla de usarlo es construir la búsqueda en la web
(https://www.autoscout24.es) aplicando tus filtros y pegar la URL resultante en
``params.url``. Por defecto se ordena por "novedades" si añades ``&sort=age``.

Parámetros admitidos en ``params``:
    url   str   URL completa de la búsqueda de AutoScout24 (recomendado)
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..config import SearchConfig
from ..models import Listing
from .base import Scraper, register

log = logging.getLogger(__name__)

SITE = "https://www.autoscout24.es"
_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


@register("autoscout24")
class AutoScout24Scraper(Scraper):
    def search(self, search: SearchConfig) -> list[Listing]:
        url = search.params.get("url")
        if not url:
            raise ValueError(
                f"La búsqueda '{search.name}' (autoscout24) necesita params.url "
                "con la URL de búsqueda de AutoScout24."
            )
        try:
            resp = self._get(url)
            data = _extract_next_data(resp.text)
        except Exception as exc:  # noqa: BLE001
            log.warning("AutoScout24: fallo al obtener resultados (%s). Devuelvo 0.", exc)
            return []

        if data is None:
            log.warning("AutoScout24 [%s]: no se encontró __NEXT_DATA__.", search.name)
            return []

        raw_listings = _find_listings(data)
        listings: list[Listing] = []
        seen: set[str] = set()
        for item in raw_listings:
            listing = _parse_item(item)
            if listing and listing.native_id not in seen:
                listings.append(listing)
                seen.add(listing.native_id)
            if len(listings) >= search.max_results:
                break
        log.info("AutoScout24 [%s]: %d anuncios.", search.name, len(listings))
        return listings


def _extract_next_data(html_text: str) -> Any | None:
    match = _NEXT_DATA_RE.search(html_text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _find_listings(data: Any) -> list[dict]:
    """Busca recursivamente la lista de anuncios dentro del JSON de Next.js."""
    best: list[dict] = []

    def looks_like_listing(d: dict) -> bool:
        return "id" in d and ("vehicle" in d or "make" in d or "vehicleDetails" in d)

    def walk(node: Any) -> None:
        nonlocal best
        if isinstance(node, list):
            candidates = [x for x in node if isinstance(x, dict) and looks_like_listing(x)]
            if len(candidates) > len(best):
                best = candidates
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)

    walk(data)
    return best


def _parse_item(item: dict) -> Listing | None:
    native_id = str(item.get("id") or item.get("guid") or "").strip()
    if not native_id:
        return None

    vehicle = item.get("vehicle") or item.get("vehicleDetails") or {}
    make = vehicle.get("make") or item.get("make")
    model = vehicle.get("model") or item.get("model")
    title = item.get("title") or " ".join(str(x) for x in [make, model] if x) or "Anuncio"

    url = item.get("url") or item.get("urlPath") or ""
    if url and url.startswith("/"):
        url = SITE + url
    if not url:
        url = f"{SITE}/anuncios/{native_id}"

    price = _coerce_int(
        _nested(item, "tracking", "price")
        or _nested(item, "price", "priceFormatted")
        or item.get("price")
    )
    year = _coerce_int(vehicle.get("firstRegistrationDate") or item.get("year"))
    km = _coerce_int(vehicle.get("mileage") or item.get("mileage"))

    images = item.get("images") or item.get("photos") or []
    image = None
    if isinstance(images, list) and images:
        first = images[0]
        image = first.get("uri") if isinstance(first, dict) else first

    return Listing(
        portal="autoscout24",
        native_id=native_id,
        title=str(title).strip(),
        url=url,
        price=price,
        year=year,
        km=km,
        fuel=vehicle.get("fuelCategory") or vehicle.get("fuelType"),
        gearbox=vehicle.get("transmissionType"),
        location=_nested(item, "location", "city") or item.get("zip"),
        image=image,
    )


def _nested(d: dict, *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    digits = re.sub(r"[^\d]", "", str(value).split(",")[0])
    return int(digits) if digits else None
