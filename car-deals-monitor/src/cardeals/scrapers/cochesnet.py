"""Scraper de Coches.net.

Coches.net sirve los resultados a través de una API JSON interna (la misma que
usa su web). Este scraper la consulta directamente, lo que es mucho más estable
que parsear HTML. El endpoint y el payload pueden cambiar con el tiempo: si deja
de funcionar, revisa en las DevTools del navegador (pestaña Network) la petición
que hace la web al buscar y actualiza ``API_URL`` / el payload.

Parámetros admitidos en ``params`` (todos opcionales):
    api_url      str   sobreescribe el endpoint por defecto
    api_payload  dict  payload JSON completo (control total; ignora los filtros)
    price_to     int   precio máximo en euros
    price_from   int
    year_from    int
    km_to        int
    make         str   marca (ej. "BMW")
    model        str   modelo
    text         str   texto libre de búsqueda
    order        str   por defecto "published_date" desc (novedades primero)
    page_size    int
"""
from __future__ import annotations

import logging
from typing import Any

from ..config import SearchConfig
from ..models import Listing
from .base import Scraper, register

log = logging.getLogger(__name__)

API_URL = "https://ms-mt--api-web.spain.advgo.net/search"
SITE = "https://www.coches.net"


@register("cochesnet")
class CochesNetScraper(Scraper):
    def _build_payload(self, search: SearchConfig) -> dict[str, Any]:
        p = search.params
        if "api_payload" in p:
            return dict(p["api_payload"])

        filters: dict[str, Any] = {
            "isFinanced": False,
            "offerTypeIds": [0, 2, 3, 4, 5],
        }
        if p.get("price_to") is not None or p.get("price_from") is not None:
            filters["price"] = {
                "from": p.get("price_from"),
                "to": p.get("price_to"),
            }
        if p.get("year_from") is not None:
            filters["year"] = {"from": p.get("year_from"), "to": None}
        if p.get("km_to") is not None:
            filters["km"] = {"from": None, "to": p.get("km_to")}
        if p.get("make"):
            filters["categories"] = {"makeIds": [], "modelIds": []}
            filters["text"] = p.get("make")
        if p.get("text"):
            filters["text"] = p["text"]

        return {
            "pagination": {"page": 1, "size": int(p.get("page_size", search.max_results))},
            "sort": {"order": p.get("order", "desc"), "term": "publishedDate"},
            "filters": filters,
        }

    def search(self, search: SearchConfig) -> list[Listing]:
        url = search.params.get("api_url", API_URL)
        payload = self._build_payload(search)
        headers = {
            "Content-Type": "application/json",
            "X-Adevinta-Channel": "web-desktop",
            "x-schibsted-tenant": "coches",
            "Origin": SITE,
            "Referer": f"{SITE}/",
        }
        try:
            resp = self._post(url, json=payload, headers=headers)
            data = resp.json()
        except Exception as exc:  # noqa: BLE001 - queremos degradar con elegancia
            log.warning("Coches.net: fallo al consultar la API (%s). Devuelvo 0 anuncios.", exc)
            return []

        items = _extract_items(data)
        listings: list[Listing] = []
        for item in items[: search.max_results]:
            listing = _parse_item(item)
            if listing:
                listings.append(listing)
        log.info("Coches.net [%s]: %d anuncios.", search.name, len(listings))
        return listings


def _extract_items(data: Any) -> list[dict]:
    """Localiza la lista de anuncios en la respuesta, tolerando cambios de esquema."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("items", "results", "ads", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _parse_item(item: dict) -> Listing | None:
    native_id = str(item.get("id") or item.get("adId") or "").strip()
    if not native_id:
        return None
    title = (
        item.get("title")
        or " ".join(str(x) for x in [item.get("make"), item.get("model")] if x)
        or "Anuncio sin título"
    )
    url = item.get("url") or item.get("detailUrl") or ""
    if url and url.startswith("/"):
        url = SITE + url

    price = _coerce_int(_nested(item, "price", "amount") or item.get("price"))
    year = _coerce_int(item.get("year"))
    km = _coerce_int(item.get("km") or item.get("kms"))
    image = None
    media = item.get("mainPhoto") or item.get("media") or item.get("photo")
    if isinstance(media, dict):
        image = media.get("url") or media.get("src")
    elif isinstance(media, str):
        image = media

    return Listing(
        portal="coches.net",
        native_id=native_id,
        title=str(title).strip(),
        url=url or SITE,
        price=price,
        year=year,
        km=km,
        fuel=item.get("fuelType") or item.get("fuel"),
        location=_nested(item, "location", "mainProvince") or item.get("province"),
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
    try:
        return int(float(str(value).replace(".", "").replace(",", ".").split()[0]))
    except (ValueError, IndexError):
        return None
