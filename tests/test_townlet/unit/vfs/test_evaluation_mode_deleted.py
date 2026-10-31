"""V3 (review-2026-10-24 F3, probe2 F): `evaluation_mode` and `eager` are deleted.

The eager evaluator rebuilt expression context from each static's declared literal, so an
expression over an engine-written global static was permanently stale. Mark-and-sweep is
the only evaluator; a pack that still declares the setting fails at parse as an extra field.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import copy_config_pack
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

PACK = Path("configs/static_epistemic_access")
LEVEL = "L0_simple"

_INCREMENT_GCOUNT = {
    "version": "1.0",
    "transition_rules": [
        {
            "id": "inc",
            "phase": "apply_transition_rules",
            "condition": None,
            "writes": [
                {
                    "variable_id": "gcount",
                    "expression": "gcount + 1.0",
                    "composition": "overwrite",
                    "condition": None,
                    "clamp": None,
                    "effect": None,
                }
            ],
        }
    ],
}


def _declaration(identifier: str, *, scope: str, expression: str | None = None) -> dict:
    payload = {
        "id": identifier,
        "scope": scope,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": 0.0,
    }
    if expression is not None:
        payload["expression"] = expression
    return payload


def _pack(tmp_path: Path, declarations: list[dict], headers: dict, *, rules: dict | None = None) -> Path:
    pack = copy_config_pack(PACK, tmp_path)
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"].update(headers)
    payload["variables"]["declarations"].extend(declarations)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    if rules is not None:
        (pack / "transition_rules.yaml").write_text(yaml.safe_dump(rules, sort_keys=False))
    return pack


_GLOBAL_COUNTER = [_declaration("gcount", scope="global"), _declaration("gtwice", scope="global", expression="gcount * 2.0")]


@pytest.mark.parametrize(
    "case,declarations,rules",
    [
        ("eager_stale", _GLOBAL_COUNTER, _INCREMENT_GCOUNT),
        ("eager_agent_static", [_declaration("derived", scope="agent", expression="public_state * 2.0")], None),
    ],
)
@pytest.mark.parametrize("headers", [{"evaluation_mode": "eager"}, {"evaluation_mode": "mark_and_sweep"}, {"debug_logging": False}])
def test_deleted_evaluation_settings_refuse_at_parse(tmp_path: Path, case: str, declarations, rules, headers: dict):
    """probe2 F `eager_stale` / `eager_agent_static`: the key itself is unknown vocabulary."""
    (key,) = headers
    pack = _pack(tmp_path, declarations, headers, rules=rules)
    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert re.search(rf"variables\.yaml:\d+ - Invalid variables declaration \({key}\): Extra inputs are not permitted", str(refusal.value))


def test_expression_over_a_rule_written_global_static_tracks_it(tmp_path: Path):
    """probe2 F `mas_control`: the single remaining path reads the static's runtime value."""
    pack = _pack(tmp_path, _GLOBAL_COUNTER, {}, rules=_INCREMENT_GCOUNT)
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    wait = universe.get_level(LEVEL).runtime_action_space.action_ids["WAIT"]
    for tick in range(1, 4):
        env.step(torch.full((env.num_agents,), wait, dtype=torch.long))
        gcount = env.vfs_registry.get("gcount", reader="engine")
        assert gcount.tolist() == [float(tick)] * env.num_agents  # every world's rule advanced
        assert torch.equal(env.vfs_registry.get("gtwice", reader="engine"), gcount * 2.0)
