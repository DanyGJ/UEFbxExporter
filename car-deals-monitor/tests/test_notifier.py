from cardeals.config import EmailConfig
from cardeals.models import Listing
from cardeals.notifier import EmailNotifier, build_html, build_text


def _grouped():
    return {
        "Búsqueda A": [
            Listing(portal="coches.net", native_id="1", title="BMW 320d",
                    url="http://x/1", price=11500, year=2016, km=120000, location="Madrid"),
        ]
    }


def test_build_html_contains_listing():
    html = build_html(_grouped())
    assert "BMW 320d" in html
    assert "http://x/1" in html
    assert "11.500" in html  # formato de precio español


def test_build_text_contains_listing():
    text = build_text(_grouped())
    assert "BMW 320d" in text
    assert "http://x/1" in text


def test_send_noop_without_novelties(monkeypatch):
    cfg = EmailConfig(user="a@b.com", password="x", recipients=["a@b.com"])
    sent = []
    monkeypatch.setattr("smtplib.SMTP", lambda *a, **k: sent.append(True))
    EmailNotifier(cfg).send({})  # sin novedades -> no abre SMTP
    assert sent == []


def test_send_requires_complete_config():
    notifier = EmailNotifier(EmailConfig())  # incompleta
    import pytest
    with pytest.raises(RuntimeError):
        notifier.send(_grouped())
