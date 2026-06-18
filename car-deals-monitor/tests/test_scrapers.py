from bs4 import BeautifulSoup

from cardeals.config import AppConfig, SearchConfig
from cardeals.scrapers import SCRAPERS, get_scraper
from cardeals.scrapers.generic_html import _parse_card
from cardeals.scrapers.autoscout24 import _extract_next_data, _find_listings


def test_registry_has_core_portals():
    assert {"cochesnet", "autoscout24", "generic_html"} <= set(SCRAPERS)
    assert get_scraper("cochesnet").name == "cochesnet"


def test_generic_card_parsing():
    html = """
    <article class="card">
      <h2>Seat Ibiza 1.6 TDI</h2>
      <a href="/anuncio/123">ver</a>
      <span class="price">8.900 €</span>
      <span class="km">95.000 km</span>
    </article>
    """
    card = BeautifulSoup(html, "html.parser").select_one("article.card")
    fields = {
        "title": {"selector": "h2"},
        "url": {"selector": "a", "attr": "href"},
        "price": {"selector": ".price", "regex": r"[0-9.]+"},
        "km": {"selector": ".km", "regex": r"[0-9.]+"},
    }
    listing = _parse_card(card, fields, "flexicar", "https://www.flexicar.es")
    assert listing.title == "Seat Ibiza 1.6 TDI"
    assert listing.url == "https://www.flexicar.es/anuncio/123"
    assert listing.price == 8900
    assert listing.km == 95000
    assert listing.native_id  # derivado de la URL


def test_autoscout_next_data_extraction():
    html = (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"x":{"listings":[{"id":"a1","vehicle":{"make":"Audi","model":"A3"},'
        '"url":"/anuncio/a1","price":12000}]}}}'
        "</script></body></html>"
    )
    data = _extract_next_data(html)
    listings = _find_listings(data)
    assert len(listings) == 1
    assert listings[0]["id"] == "a1"


def test_appconfig_load(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "state_path: data/seen.json\n"
        "searches:\n"
        "  - name: Test\n"
        "    portal: cochesnet\n"
        "    params: {price_to: 10000}\n",
        encoding="utf-8",
    )
    app = AppConfig.load(cfg_file)
    assert len(app.searches) == 1
    assert app.searches[0].portal == "cochesnet"
    assert app.searches[0].params["price_to"] == 10000
