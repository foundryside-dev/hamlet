"""The effects `reduce` command is deleted (phase B3d).

It could never compile from a pack: it required a collection typed `list` or `tensor`, and
no declared path has either type. A pipeline that still authors `reduce:` is refused at
parse, at the command's own `effects.yaml:<line>`, as an extra field of the command node.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from townlet.config.effects_config import CommandConfig
from townlet.effects.schema import CommandNode, CommandType
from townlet.universe.compiled import _serialize_command_node
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

REPO = Path(__file__).resolve().parents[4]
WITNESS = REPO / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"

REDUCE = {"reduce": "bar.col", "reduce_as": "x", "reduce_init": "0", "reduce_body": "acc + x", "reduce_into": "vfs.mood"}


def test_the_command_vocabulary_has_no_reduce() -> None:
    assert "reduce" not in {member.value for member in CommandType}
    assert not any(name.startswith("reduce") for name in CommandNode.__dataclass_fields__)
    assert not any(name.startswith("reduce") for name in CommandConfig.model_fields)


def test_reduce_fields_are_refused_as_extra_at_the_command_node() -> None:
    with pytest.raises(ValidationError, match="reduce"):
        CommandConfig.model_validate(REDUCE)


def test_an_authored_reduce_is_refused_at_parse_at_its_line(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    effect = {
        "id": "buzz",
        "scope": "agent",
        "duration": 3,
        "reapply_policy": "renew",
        "observable": True,
        "on_spawn": [REDUCE],
        "on_tick": [],
        "on_despawn": [],
        "on_interrupt": [],
    }
    budget = {"global": 0, "agent": 2, "item": 0, "affordance": 0}
    (pack / "effects.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "max_active_effects": budget, "effect_definitions": [effect]}, sort_keys=False)
    )

    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    message = str(refusal.value)
    assert "Stage 1: Parse" in message
    assert "on_spawn.reduce" in message
    assert re.search(r"effects\.yaml:\d+", message), message


def test_serialized_command_nodes_carry_no_reduce_keys() -> None:
    payload = _serialize_command_node(CommandNode(type=CommandType.MODIFY, path="target.bar.energy", value_expr="0.5"))
    assert not any(key.startswith("reduce") for key in payload)
