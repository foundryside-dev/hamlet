import logging
from types import SimpleNamespace

import torch

from townlet.vfs.evaluator import VFSEvaluator


class DummyVar:
    def __init__(self, name: str, initial_value: float):
        self.name = name
        self.ast = None
        self.initial_value = initial_value


def test_vfs_debug_logging(caplog):
    evaluator = VFSEvaluator(debug_logging=True)
    profile = SimpleNamespace(variables=[DummyVar("foo", 1.0)], dependencies={})

    with caplog.at_level(logging.DEBUG):
        evaluator.evaluate_global_profile(profile, bars={}, vfs_state={}, marks={"foo"}, device=torch.device("cpu"))

    assert any("vfs_evaluation" in rec.message for rec in caplog.records)


def test_vfs_debug_disabled_by_default(caplog):
    evaluator = VFSEvaluator()
    profile = SimpleNamespace(variables=[DummyVar("foo", 1.0)], dependencies={})

    with caplog.at_level(logging.DEBUG):
        evaluator.evaluate_global_profile(profile, bars={}, vfs_state={}, marks={"foo"}, device=torch.device("cpu"))

    assert not any("vfs_evaluation" in rec.message for rec in caplog.records)


def test_vfs_debug_env_var_does_not_enable_logging(monkeypatch, caplog):
    monkeypatch.setenv("HAMLET_DEBUG_VFS", "true")
    evaluator = VFSEvaluator(debug_logging=False)
    profile = SimpleNamespace(variables=[DummyVar("foo", 1.0)], dependencies={})

    with caplog.at_level(logging.DEBUG):
        evaluator.evaluate_global_profile(profile, bars={}, vfs_state={}, marks=set(), device=torch.device("cpu"))

    assert not any("vfs_evaluation" in rec.message for rec in caplog.records)
