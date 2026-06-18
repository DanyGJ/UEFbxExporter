from cardeals.models import Listing
from cardeals.storage import SeenStore


def _listing(native_id, portal="coches.net"):
    return Listing(portal=portal, native_id=native_id, title="Coche", url="http://x")


def test_filter_new_marks_and_persists(tmp_path):
    path = tmp_path / "seen.json"
    store = SeenStore(path)

    batch = [_listing("1"), _listing("2"), _listing("2")]  # duplicado en el lote
    new = store.filter_new(batch)
    assert {l.native_id for l in new} == {"1", "2"}
    assert len(new) == 2  # el duplicado del lote se elimina

    store.mark_seen(new)
    store.save()

    # Una nueva instancia lee del disco y ya no los considera nuevos.
    store2 = SeenStore(path)
    assert store2.filter_new(batch) == []
    assert len(store2) == 2


def test_same_id_distinct_portals_are_different(tmp_path):
    store = SeenStore(tmp_path / "seen.json")
    new = store.filter_new([_listing("1", "coches.net"), _listing("1", "autoscout24")])
    assert len(new) == 2
