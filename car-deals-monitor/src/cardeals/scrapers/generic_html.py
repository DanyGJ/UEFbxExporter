"""Scraper genérico configurable por selectores CSS.

Permite añadir CUALQUIER portal (Flexicar, Milanuncios, concesionarios, etc.)
sin escribir código: solo describes en el YAML qué CSS apunta a cada dato.

Ejemplo de ``params``::

    url: "https://www.flexicar.es/coches-segunda-mano/?precio_hasta=10000"
    portal: "flexicar"
    base_url: "https://www.flexicar.es"
    item_selector: "div.card-vehicle"
    fields:
      title:   {selector: "h3.card-title"}
      url:     {selector: "a.card-link", attr: "href"}
      price:   {selector: "span.price", regex: "\\d+"}
      year:    {selector: "li.year"}
      km:      {selector: "li.km", regex: "\\d+"}
      image:   {selector: "img", attr: "src"}

``native_id`` se deriva de la URL del anuncio si no se especifica.
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..config import SearchConfig
from ..models import Listing
from .base import Scraper, register

log = logging.getLogger(__name__)


@register("generic_html")
class GenericHtmlScraper(Scraper):
    def search(self, search: SearchConfig) -> list[Listing]:
        p = search.params
        url = p.get("url")
        item_selector = p.get("item_selector")
        fields = p.get("fields") or {}
        if not url or not item_selector:
            raise ValueError(
                f"La búsqueda '{search.name}' (generic_html) necesita params.url e "
                "params.item_selector."
            )
        portal = p.get("portal", "generic")
        base_url = p.get("base_url") or url

        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as exc:  # noqa: BLE001
            log.warning("%s: fallo al obtener la página (%s). Devuelvo 0.", portal, exc)
            return []

        cards = soup.select(item_selector)
        listings: list[Listing] = []
        for card in cards[: search.max_results]:
            listing = _parse_card(card, fields, portal, base_url)
            if listing:
                listings.append(listing)
        log.info("%s [%s]: %d anuncios.", portal, search.name, len(listings))
        return listings


def _extract(card, spec: dict[str, Any], base_url: str) -> Optional[str]:
    selector = spec.get("selector")
    el = card.select_one(selector) if selector else card
    if el is None:
        return None
    attr = spec.get("attr")
    value = el.get(attr) if attr else el.get_text(" ", strip=True)
    if value is None:
        return None
    value = str(value).strip()
    if attr in ("href", "src") and value:
        value = urljoin(base_url, value)
    regex = spec.get("regex")
    if regex:
        match = re.search(regex, value)
        value = match.group(0) if match else None
    return value


def _to_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


def _parse_card(card, fields: dict, portal: str, base_url: str) -> Optional[Listing]:
    def field(name: str) -> Optional[str]:
        spec = fields.get(name)
        return _extract(card, spec, base_url) if isinstance(spec, dict) else None

    url = field("url")
    title = field("title")
    if not url and not title:
        return None
    url = url or base_url

    native_id = field("native_id")
    if not native_id:
        native_id = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]

    return Listing(
        portal=portal,
        native_id=native_id,
        title=title or "Anuncio",
        url=url,
        price=_to_int(field("price")),
        year=_to_int(field("year")),
        km=_to_int(field("km")),
        fuel=field("fuel"),
        location=field("location"),
        image=field("image"),
    )
