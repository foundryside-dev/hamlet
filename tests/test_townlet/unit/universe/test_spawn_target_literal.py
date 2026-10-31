"""A constant spawn_effect target is refused at compile, at its own file:line (owner ruling S1).

An integer-literal target (`target: 3`) names one batch row: an agent row is its world, an
item row belongs to one world. In every other world it is another world's entity, and it
was refused only at runtime (when the spawning world was not that row's). Now every
authored pipeline (affordance interactions, item hooks, effect lifecycles) refuses a target
that reads no state, as `[EFFECT-SPAWN-TARGET]` at the command's declaration.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

REPO = Path(__file__).resolve().parents[4]
WITNESS = REPO / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"

EFFECT = {
    "id": "buzz",
    "scope": "agent",
    "duration": 3,
    "reapply_policy": "renew",
    "observable": True,
    "on_spawn": [],
    "on_tick": [],
    "on_despawn": [],
    "on_interrupt": [],
}


def _edit(path: Path, edit: Any) -> None:
    payload = yaml.safe_load(path.read_text())
    edit(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _pack(tmp_path: Path, *, sleep_target: str | None = None, effect_target: str | None = None) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    effects = [dict(EFFECT)]
    if effect_target is not None:
        effects.append({**EFFECT, "id": "cascade", "on_spawn": [{"spawn_effect": "buzz", "target": effect_target, "intensity": 1.0}]})
    budget = {"global": 0, "agent": 2, "item": 0, "affordance": 0}
    (pack / "effects.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "max_active_effects": budget, "effect_definitions": effects}, sort_keys=False)
    )
    if sleep_target is not None:

        def add_spawn(payload: dict) -> None:
            sleep = next(a for a in payload["affordances"]["affordances"] if a["name"] == "SLEEP")
            sleep["interactions"]["on_start"].append({"spawn_effect": "buzz", "target": sleep_target, "intensity": 1.0})

        _edit(pack / "levels" / LEVEL / "affordances.yaml", add_spawn)
    return pack


def _refusal(pack: Path) -> str:
    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    return str(refusal.value)


@pytest.mark.parametrize("target", ["0", "3", "-1", "1 + 1"])
def test_a_constant_affordance_spawn_target_is_refused_at_its_line(tmp_path: Path, target: str) -> None:
    message = _refusal(_pack(tmp_path, sleep_target=target))
    assert "[EFFECT-SPAWN-TARGET]" in message
    assert f"spawn_effect target '{target}' is a constant row index" in message
    assert re.search(r"affordances\.yaml:\d+", message), message


def test_a_constant_effect_cascade_target_is_refused_at_its_line(tmp_path: Path) -> None:
    message = _refusal(_pack(tmp_path, effect_target="2"))
    assert "[EFFECT-SPAWN-TARGET]" in message
    assert re.search(r"effects\.yaml:\d+", message), message


def test_a_constant_item_hook_spawn_target_is_refused_at_its_line(tmp_path: Path) -> None:
    pack = tmp_path / "items"
    shutil.copytree(REPO / "configs" / "reference" / "model_pack", pack, ignore=shutil.ignore_patterns(".compiled"))
    text = (pack / "items.yaml").read_text()
    assert "target: target" in text
    (pack / "items.yaml").write_text(text.replace("target: target", "target: '1'", 1))
    levels = sorted(p.name for p in (pack / "levels").iterdir())
    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=levels[0], use_cache=False)
    message = str(refusal.value)
    assert "[EFFECT-SPAWN-TARGET]" in message
    assert re.search(r"items\.yaml:\d+", message), message


def test_an_unparseable_spawn_target_is_refused_at_its_line(tmp_path: Path) -> None:
    message = _refusal(_pack(tmp_path, sleep_target="1 +"))
    assert "[EFFECT-SPAWN-TARGET]" in message and "does not parse" in message
    assert re.search(r"affordances\.yaml:\d+", message), message


def test_self_and_target_still_compile(tmp_path: Path) -> None:
    UniverseCompiler().compile(_pack(tmp_path, sleep_target="target", effect_target="target"), primary_level=LEVEL, use_cache=False)
