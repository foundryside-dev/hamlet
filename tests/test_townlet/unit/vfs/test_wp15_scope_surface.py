"""The VFS scope surface is the scopes something can use (VFS WP15: S2, S6, S7, F8, F14).

Converted from review-2026-10-24/vfs_round2 r5_message_scope.py, r7_agent_private.py and
r16_L5_inert.py. Under the owner's S1 ruling the env batch is N independent
single-agent worlds, so:

- ``pair`` and ``message`` are deleted: a pair has no partner and a message no
  addressee in a one-agent world, and ``append_event`` wrote the sender's own row
  where nothing could read it (r5).
- ``agent_private`` is deleted: ``agent`` with ``readable_by: [engine]`` and
  ``exposed_to: []`` is the same privacy and keeps every consumer, and the old scope
  silently overrode a declared ``readable_by: [engine, agent]`` (r7).
- L5 exposes no constant token: ``deficit_energy`` is an expression of energy, and the
  never-written ``trust``/``occupied_by``/``time_since_last_sleep`` are gone (r16).

Each deleted name fails at parse with the author's ``file:line`` and the surviving
vocabulary, never with a migration path.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, get_args

import pytest
import torch
import yaml
from pydantic import ValidationError

from townlet.config.transition_rules_config import TransitionRuleWriteConfig
from townlet.config.variables_config import VariableDeclaration
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs import compile_vtc_transition_rules
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope, WriteSpec
from townlet.vfs.vtc import RULE_WRITE_COMPOSITIONS, VTCWriteTarget

REPO = Path(__file__).resolve().parents[4]
L5 = REPO / "configs" / "L5_multi_agent"
L5_LEVEL = "L5_multi_agent"
DELETED_SCOPES = ("pair", "message", "agent_private")
SURVIVING_SCOPES = "'global', 'agent', 'item' or 'affordance'"


def _declaration(variable_id: str, scope: str, **extra: Any) -> dict[str, Any]:
    declaration: dict[str, Any] = {
        "id": variable_id,
        "scope": scope,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": 0.0,
    }
    declaration.update(extra)
    return declaration


def _l5_copy(tmp_path: Path) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(L5, pack, ignore=shutil.ignore_patterns(".compiled"))
    return pack


# --- the deleted scopes refuse at parse ----------------------------------------------


def test_scope_vocabulary_is_the_four_usable_scopes() -> None:
    assert [scope.value for scope in VariableScope] == ["global", "agent", "item", "affordance"]


@pytest.mark.parametrize("scope", DELETED_SCOPES)
def test_deleted_scope_refuses_in_the_variables_declaration(scope: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        VariableDeclaration(**_declaration("old_state", scope))
    assert SURVIVING_SCOPES in str(excinfo.value)


@pytest.mark.parametrize("scope", DELETED_SCOPES)
def test_deleted_scope_refuses_in_the_runtime_definition(scope: str) -> None:
    with pytest.raises(ValidationError, match="scope"):
        VariableDef(
            id="old_state",
            scope=scope,  # type: ignore[arg-type]
            type="scalar",
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
            default=0.0,
        )


@pytest.mark.parametrize("scope", DELETED_SCOPES)
def test_pack_declaring_a_deleted_scope_fails_at_parse_with_its_location(tmp_path: Path, scope: str) -> None:
    pack = _l5_copy(tmp_path)
    variables_path = pack / "variables.yaml"
    payload = yaml.safe_load(variables_path.read_text())
    payload["variables"]["declarations"].append(_declaration("old_state", scope))
    variables_path.write_text(yaml.safe_dump(payload, sort_keys=False))

    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(pack, primary_level=L5_LEVEL, use_cache=False)

    message = str(excinfo.value)
    assert "Stage 1" in message
    assert f"{variables_path}:" in message
    assert "scope" in message and SURVIVING_SCOPES in message


def test_append_event_composition_refuses_at_parse() -> None:
    """r5: append_event wrote the sender's own message row; with no message scope it has no target."""
    with pytest.raises(ValidationError, match="composition"):
        WriteSpec(
            variable_id="state",
            expression="1.0",
            condition=None,
            composition="append_event",  # type: ignore[arg-type]
            phase="apply_action_writes",
            priority=0,
            clamp=None,
            telemetry_label="append",
        )
    with pytest.raises(ValidationError, match="composition"):
        TransitionRuleWriteConfig(
            variable_id="state",
            expression="1.0",
            composition="append_event",  # type: ignore[arg-type]
            condition=None,
            clamp=None,
            effect=None,
        )


@pytest.mark.parametrize("composition", ["claim_if_free", "capacity_claim"])
def test_occupancy_claim_compositions_are_action_write_only(composition: str) -> None:
    """A rule write with a claim composition parsed and then raised NotImplementedError at step.

    A rule has no claimant and no source affordance, so the claims leave the rule vocabulary:
    the DTO refuses them at parse and the compiler's raw path refuses them too.
    """
    with pytest.raises(ValidationError, match="composition"):
        TransitionRuleWriteConfig(
            variable_id="state", expression="1.0", composition=composition, condition=None, clamp=None, effect=None  # type: ignore[arg-type]
        )
    rule = {
        "id": "claim",
        "phase": "apply_social_residue_effects",
        "condition": None,
        "writes": [{"variable_id": "state", "expression": "1.0", "composition": composition}],
    }
    with pytest.raises(ValueError, match=f"composition '{composition}' is not one of"):
        compile_vtc_transition_rules([rule], {"state": VTCWriteTarget(VariableScope.AGENT, "scalar", meter=False, expression=None)})


def test_rule_composition_vocabulary_has_one_definition() -> None:
    literal = get_args(TransitionRuleWriteConfig.model_fields["composition"].annotation)
    assert literal == RULE_WRITE_COMPOSITIONS


# --- agent + readable_by is the privacy agent_private offered, with no override --------


def _registry(readable_by: list[str], exposed_to: list[str]) -> VariableRegistry:
    variable = VariableDef(
        id="hidden_reward",
        scope=VariableScope.AGENT,
        type="scalar",
        lifetime="episode",
        readable_by=readable_by,  # type: ignore[arg-type]
        writable_by=["engine"],
        exposed_to=exposed_to,
        default=0.0,
    )
    return VariableRegistry(variables=[variable], num_agents=2, device=torch.device("cpu"))


def test_engine_only_agent_variable_is_private() -> None:
    registry = _registry(["engine"], [])
    assert registry.get("hidden_reward", reader="engine").shape == (2,)
    with pytest.raises(PermissionError):
        registry.get("hidden_reward", reader="agent")


def test_declared_agent_readers_are_never_silently_overridden() -> None:
    """r7: agent_private refused agent reads its own readable_by granted. The declaration is the authority now."""
    registry = _registry(["engine", "agent"], [])
    assert registry.get("hidden_reward", reader="agent").shape == (2,)


# --- L5 is honest ---------------------------------------------------------------------


def test_l5_declares_no_deleted_or_unwritten_relational_state() -> None:
    universe = UniverseCompiler().compile(L5, primary_level=L5_LEVEL, use_cache=False)
    variables = {variable.id: variable for variable in universe.get_level(L5_LEVEL).vfs_variables}
    assert "trust" not in variables
    assert "occupied_by" not in variables
    # The unwired literal is gone; WP14 re-added it as a live expression (test_wp14_history.py).
    agent_expressions = {variable.name: variable.expression for variable in universe.compiled_vfs_profiles.agent_profile.variables}
    assert agent_expressions["time_since_last_sleep"] is not None
    assert {VariableScope(variable.scope) for variable in variables.values()} <= {VariableScope.GLOBAL, VariableScope.AGENT}


def test_l5_compiles_with_no_constant_exposed_variable() -> None:
    """r16: two exposed tick-lifetime variables were written by nothing, so their tokens were
    constant zero. Every exposed variable now tracks state: deficit_energy rises as energy
    drains below its 0.5 target, and is observed with full-range normalization;
    time_since_last_sleep (WP14) counts the ticks since energy last rose."""
    universe = UniverseCompiler().compile(L5, primary_level=L5_LEVEL, use_cache=False)
    level = universe.get_level(L5_LEVEL)
    exposed = [variable for variable in level.vfs_variables if "agent" in variable.exposed_to]
    assert [variable.id for variable in exposed] == ["deficit_energy", "time_since_last_sleep"]
    assert level.token_spec.census["variable_element"] == len(exposed)

    env = universe.create_environment(num_agents=2, level_name=L5_LEVEL, device="cpu")
    env.reset()
    energy_index = env.meter_name_to_index["energy"]
    seen: dict[str, set[float]] = {variable.id: set() for variable in exposed}
    wait = torch.full((2,), env.action_dim - 1, dtype=torch.long)
    for _ in range(80):
        _, _, dones, _ = env.step(wait)
        energy = env.meters[:, energy_index]
        deficit = env.vfs_registry.get("deficit_energy", reader="engine")
        live = ~dones
        assert torch.allclose(deficit[live], torch.clamp(0.5 - energy[live], min=0.0), atol=1e-6)
        for variable in exposed:
            seen[variable.id].update(env.vfs_registry.get(variable.id, reader="engine").tolist())
        if bool(dones.all()):
            break
    for variable_id, values in seen.items():
        assert len(values) > 1, f"exposed variable {variable_id!r} never changed: {sorted(values)}"
