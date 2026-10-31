"""Every transition-rule example in the docs compiles in a real pack AND steps, doing what it says.

The examples are the fenced yaml blocks of ``docs/architecture/VFS.md`` and
``docs/config-schemas/transition_rules.md`` that are a ``transition_rules`` declaration (a
mapping with a top-level ``transition_rules`` key) or a list of rules (entries carrying
``writes``, wrapped into a declaration). Each is written into a scratch copy of
``configs/default_curriculum`` as its pack-scope ``transition_rules.yaml``, next to
declarations of the illustrative names the examples read, compiled through the universe
compiler, and stepped beside the same pack without the rules: every example's write must move
its target in at least one world.

Compiling against a hand-built target map, never stepping, is how four meter-targeting doc
examples shipped as crashes on the first step (re-review A1): the target map said a meter was
writable while the rule program had no commit path for one.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

REPO = Path(__file__).resolve().parents[4]
DOCS = (REPO / "docs" / "architecture" / "VFS.md", REPO / "docs" / "config-schemas" / "transition_rules.md")
PACK = REPO / "configs" / "default_curriculum"
LEVEL = "L1_full_observability"

#: World 0 starts every meter low and world 1 high, so a rule gated on a low meter
#: (`bar.satiation < 0.2`) fires in world 0 and one gated on a high meter
#: (`bar.health >= 0.7`) fires in world 1.
METER_START = (0.1, 0.9)


def _declaration(var_id: str, *, scope: str, type: str, initial_value: Any, writable_by: list[str]) -> dict[str, Any]:
    return {
        "id": var_id,
        "scope": scope,
        "type": type,
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": writable_by,
        "exposed_to": [],
        "initial_value": initial_value,
    }


#: The illustrative names the examples read, declared so their conditions hold: the agent was
#: observed, and the action it chose (`chosen_action`) matches every action-index constant.
ILLUSTRATIVE_DECLARATIONS = [
    _declaration("public_reputation", scope="agent", type="scalar", initial_value=0.5, writable_by=["engine"]),
    _declaration("was_observed", scope="agent", type="bool", initial_value=True, writable_by=["engine"]),
    _declaration("chosen_action", scope="agent", type="scalar", initial_value=1.0, writable_by=["engine"]),
    *(_declaration(name, scope="global", type="scalar", initial_value=1.0, writable_by=[]) for name in ("STEAL", "CALL_AMBULANCE", "HELP")),
]


def _doc_examples() -> list[tuple[str, dict[str, Any]]]:
    examples: list[tuple[str, dict[str, Any]]] = []
    for doc in DOCS:
        text = doc.read_text()
        for match in re.finditer(r"```yaml\n(.*?)```", text, flags=re.DOTALL):
            try:
                data = yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                continue
            line = text[: match.start()].count("\n") + 1
            label = f"{doc.name}:{line}"
            if isinstance(data, dict) and "transition_rules" in data:
                examples.append((label, data))
            elif isinstance(data, list) and data and all(isinstance(entry, dict) and "writes" in entry for entry in data):
                examples.append((label, {"version": "1.0", "transition_rules": data}))
    return examples


EXAMPLES = _doc_examples()


def test_the_docs_carry_the_transition_rule_examples() -> None:
    labels = [label for label, _ in EXAMPLES]
    assert len(EXAMPLES) >= 8, labels
    # The meter-targeting examples (§12.3, §14.3) are among them: they are the ones that crashed.
    targets = {write["variable_id"] for _, example in EXAMPLES for rule in example["transition_rules"] for write in rule["writes"]}
    assert {"bar.energy", "bar.mood", "public_reputation"} <= targets


def _pack(tmp_path: Path, rules: dict[str, Any] | None, name: str) -> Path:
    pack = tmp_path / name
    shutil.copytree(PACK, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables_path = pack / "variables.yaml"
    variables = yaml.safe_load(variables_path.read_text())
    variables["variables"]["declarations"] += ILLUSTRATIVE_DECLARATIONS
    variables_path.write_text(yaml.safe_dump(variables, sort_keys=False))
    if rules is not None:
        (pack / "transition_rules.yaml").write_text(yaml.safe_dump(rules, sort_keys=False))
    return pack


def _state_after_steps(pack: Path, targets: set[str], steps: int) -> dict[str, torch.Tensor]:
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    torch.manual_seed(0)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=len(METER_START), device="cpu")
    env.reset()
    for world, value in enumerate(METER_START):
        env.meters[world, :] = value
    wait = next(index for index, action in enumerate(env.action_space.actions) if action.name == "WAIT")
    for _ in range(steps):
        env.step(torch.full((env.num_agents,), wait, dtype=torch.long))
    state: dict[str, torch.Tensor] = {}
    for target in targets:
        if target.startswith("bar."):
            state[target] = env.meters[:, env.meter_name_to_index[target.removeprefix("bar.")]].clone()
        else:
            state[target] = env.vfs_registry.get(target, reader="engine").clone()
    return state


@pytest.mark.parametrize(("label", "example"), EXAMPLES, ids=[label for label, _ in EXAMPLES])
def test_a_doc_transition_rule_example_compiles_steps_and_writes_its_target(tmp_path: Path, label: str, example: dict[str, Any]) -> None:
    targets = {write["variable_id"] for rule in example["transition_rules"] for write in rule["writes"]}
    with_rules = _state_after_steps(_pack(tmp_path, example, "with_rules"), targets, steps=2)
    without = _state_after_steps(_pack(tmp_path, None, "without"), targets, steps=2)
    for target in targets:
        assert not torch.equal(with_rules[target], without[target]), f"{label}: the rule never moved {target}"


def test_doc_carries_no_old_family_examples() -> None:
    """A ``social_residue:`` document in the doc would be the deleted grammar."""
    for doc in DOCS:
        for block in re.findall(r"```yaml\n(.*?)```", doc.read_text(), flags=re.DOTALL):
            try:
                data = yaml.safe_load(block)
            except yaml.YAMLError:
                continue
            assert not (isinstance(data, dict) and "social_residue" in data), block
