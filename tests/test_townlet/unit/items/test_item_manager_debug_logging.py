import logging
from types import SimpleNamespace

from townlet.items.manager import ItemManager


def test_item_manager_debug_logging(monkeypatch, caplog):
    monkeypatch.setenv("HAMLET_DEBUG_ITEMS", "1")
    catalog = SimpleNamespace(item_types=[])

    with caplog.at_level(logging.DEBUG):
        manager = ItemManager(catalog=catalog, max_items=1, device="cpu")
        manager._log_items("debug_spawn", instance_id=1)

    assert any("debug_spawn" in rec.message for rec in caplog.records)


def test_item_manager_debug_disabled_by_default(caplog):
    catalog = SimpleNamespace(item_types=[])

    with caplog.at_level(logging.DEBUG):
        manager = ItemManager(catalog=catalog, max_items=1, device="cpu")
        manager._log_items("should_not_log", instance_id=2)

    assert not any("should_not_log" in rec.message for rec in caplog.records)
