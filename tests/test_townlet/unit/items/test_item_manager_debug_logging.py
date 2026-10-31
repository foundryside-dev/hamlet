import logging
from types import SimpleNamespace

from tests.test_townlet.utils.builders import make_grid2d_substrate
from townlet.items.manager import ItemManager


def test_item_manager_debug_logging(monkeypatch, caplog):
    monkeypatch.setenv("HAMLET_DEBUG_ITEMS", "1")
    catalog = SimpleNamespace(item_types=[], max_items_per_agent=1)

    with caplog.at_level(logging.DEBUG):
        manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=1, device="cpu")
        manager._log_items("debug_spawn", instance_id=1)

    assert any("debug_spawn" in rec.message for rec in caplog.records)


def test_item_manager_debug_disabled_by_default(caplog):
    catalog = SimpleNamespace(item_types=[], max_items_per_agent=1)

    with caplog.at_level(logging.DEBUG):
        manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=1, device="cpu")
        manager._log_items("should_not_log", instance_id=2)

    assert not any("should_not_log" in rec.message for rec in caplog.records)
