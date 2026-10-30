"""VFS WP10 (round-2 F5): every semantic edit to the `variables` declaration moves a compared hash.

This is `review-2026-10-24/vfs_round2/r8_hash_coverage.py` as a test. Before WP10 the first
two lines of r8 moved NOTHING a checkpoint compares — a hidden expression could go from
``x * 1`` to ``x * 3`` and a resume accepted the checkpoint while the reward tripled — because
expression text and ``semantic_type`` lived only on the compiled profiles, which no hash read,
and the pack-scope ``variables`` declaration had no pack hash at all.

Two things now carry that identity, and this file pins both plus what "canonical" means:

- ``vfs_hash`` gains a fifth term over the compiled global/agent expression programs
  (``compute_expression_schema_hash``: canonical AST, result type, lifetime, semantic_type,
  dependency set) and ``variable_schema_hash`` binds ``semantic_type``, ``exposed_to`` and the
  complete normalization.
- ``variables_hash`` is the sixth pack hash: the canonical CONTENT of the discovered
  declaration — declarations sorted by identity, role lists sorted — so where the author put
  a declaration, and in what order, is transport. Declaration order IS semantic for a flat
  reader's slot layout, and ``layout_hash`` is where that lives.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    PACK_HASH_KEYS,
    assert_checkpoint_identity,
    attach_universe_metadata,
)
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.schema_hashes import canonical_expression_ast, compute_variables_hash
from townlet.world.expression import ExpressionParser

REPO = Path(__file__).resolve().parents[4]
WITNESS = REPO / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"

# Every field `assert_checkpoint_identity` hard-compares (mirrors the pack-hash guard test).
COMPARED = frozenset(
    {
        "vfs_hash",
        "action_dim",
        "layout_hash",
        "token_type_schema_hash",
        "drive_hash",
        "brain_hash",
        "curriculum_hash",
        "bars_hash",
        "affordances_hash",
        "training_hash",
        "primary_level",
        *PACK_HASH_KEYS,
    }
)

MINMAX = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}


def _pack(tmp_path: Path, name: str) -> Path:
    dest = tmp_path / name
    shutil.copytree(WITNESS, dest, ignore=shutil.ignore_patterns(".compiled", "*.msgpack"))
    return dest


def _edit_yaml(path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    payload = yaml.safe_load(path.read_text())
    mutate(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _edit_variables(pack: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    _edit_yaml(pack / "variables.yaml", lambda payload: mutate(payload["variables"]))


def _set_field(var_id: str, **fields: Any) -> Callable[[dict[str, Any]], None]:
    def mutate(variables: dict[str, Any]) -> None:
        for declaration in variables["declarations"]:
            if declaration["id"] == var_id:
                declaration.update(fields)
                return
        raise AssertionError(f"witness lost declaration {var_id!r}; re-derive this test")

    return mutate


def _declaration(var_id: str, **extra: Any) -> dict[str, Any]:
    declaration: dict[str, Any] = {
        "id": var_id,
        "scope": "agent",
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": 0.0,
    }
    declaration.update(extra)
    return declaration


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _stamped(universe: CompiledUniverse) -> dict[str, object]:
    checkpoint: dict[str, object] = {"version": CHECKPOINT_FORMAT_VERSION}
    attach_universe_metadata(checkpoint, universe)
    return checkpoint


def _moved(base: CompiledUniverse, other: CompiledUniverse) -> set[str]:
    base_checkpoint, other_checkpoint = _stamped(base), _stamped(other)
    return {key for key in COMPARED if base_checkpoint[key] != other_checkpoint[key]}


# --- r8: every line moves at least one compared hash --------------------------------------

R8_LINES = {
    # scaled_public is a HIDDEN agent expression: public_state * immutable_scale
    "hidden_expression_text": _set_field("scaled_public", expression="public_state * 10.0"),
    "hidden_semantic_type": _set_field("hidden_score", semantic_type="temporal"),
    "hidden_initial_value": _set_field("hidden_score", initial_value=3.0),
    "exposed_norm_kind_minmax_to_log": _set_field(
        "public_state", normalization={"kind": "log_scaled", "min": 0.0, "max": 4.0, "clip": True}
    ),
}


@pytest.mark.parametrize("line", sorted(R8_LINES), ids=sorted(R8_LINES))
def test_r8_every_semantic_edit_moves_vfs_hash_and_variables_hash_and_refuses_resume(tmp_path: Path, line: str) -> None:
    base_pack = _pack(tmp_path, "base")
    mutated_pack = _pack(tmp_path, "mutated")
    _edit_variables(mutated_pack, R8_LINES[line])

    base, mutated = _compile(base_pack), _compile(mutated_pack)
    moved = _moved(base, mutated)

    # Both carriers move: the VFS identity (with its --force-new-vfs fork escape) and the
    # pack-scope declaration content (a hard refusal, like every other pack hash).
    assert {"vfs_hash", "variables_hash"} <= moved, f"{line}: moved={sorted(moved)}"

    # The unedited pack resumes; the edited universe is refused through the composed gate.
    assert assert_checkpoint_identity(_stamped(base), base, force_new_vfs=False) is True
    with pytest.raises(ValueError, match="mismatch"):
        assert_checkpoint_identity(_stamped(base), mutated, force_new_vfs=False)


def _step(env: VectorizedHamletEnv, action_name: str) -> torch.Tensor:
    index = next(i for i, action in enumerate(env.action_space.actions) if action.name == action_name)
    _, reward, _, _ = env.step(torch.full((env.num_agents,), index, dtype=torch.long))
    return reward


def test_r8_exposed_rewarded_expression_x1_to_x3_moves_hashes_and_changes_reward(tmp_path: Path) -> None:
    """The behavioural half of F5: the same checkpoint, a tripled reward, and (now) a refusal."""
    outcomes: dict[str, tuple[CompiledUniverse, list[float]]] = {}
    for label, expression in (("x1", "public_state * 1.0"), ("x3", "public_state * 3.0")):
        pack = _pack(tmp_path, label)
        _edit_variables(
            pack,
            lambda variables, expression=expression: variables["declarations"].append(
                _declaration("bonus", exposed_to=["agent"], normalization=MINMAX, expression=expression)
            ),
        )
        _edit_yaml(
            pack / "levels" / LEVEL / "drive.yaml",
            lambda payload: payload["drive"]["extrinsic"]["variable_bonuses"].append({"variable": "bonus", "weight": 1.0}),
        )
        universe = _compile(pack)
        env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=1, device="cpu")
        env.reset()
        _step(env, "ADVANCE")
        reward = _step(env, "ADVANCE")
        outcomes[label] = (universe, reward.tolist())

    (x1, reward_x1), (x3, reward_x3) = outcomes["x1"], outcomes["x3"]
    assert reward_x1 != reward_x3, "the expression edit no longer changes the reward; re-derive this test"
    moved = _moved(x1, x3)
    assert {"vfs_hash", "variables_hash"} <= moved, f"moved={sorted(moved)}"
    with pytest.raises(ValueError, match="mismatch"):
        assert_checkpoint_identity(_stamped(x1), x3, force_new_vfs=False)


def test_removing_an_expression_moves_vfs_hash(tmp_path: Path) -> None:
    """An expression vanishing is a move the registry entry alone cannot see: the literal stays."""
    base_pack = _pack(tmp_path, "base")
    literal_pack = _pack(tmp_path, "literal")

    def drop_expression(variables: dict[str, Any]) -> None:
        for declaration in variables["declarations"]:
            if declaration["id"] == "scaled_public":
                del declaration["expression"]

    _edit_variables(literal_pack, drop_expression)
    moved = _moved(_compile(base_pack), _compile(literal_pack))
    assert {"vfs_hash", "variables_hash"} <= moved, f"moved={sorted(moved)}"


# --- canonical: transport and spelling are not identity -------------------------------------


def test_moving_the_declaration_to_another_file_moves_nothing(tmp_path: Path) -> None:
    """`variables_hash` hashes the DISCOVERED declaration, never `variables.yaml` by name."""
    base_pack = _pack(tmp_path, "base")
    moved_pack = _pack(tmp_path, "moved")
    source = moved_pack / "variables.yaml"
    target = moved_pack / "state" / "roster.yml"
    target.parent.mkdir()
    target.write_text(source.read_text())
    source.unlink()

    assert _moved(_compile(base_pack), _compile(moved_pack)) == set()


def test_hidden_declaration_moved_into_an_earlier_fragment_moves_nothing(tmp_path: Path) -> None:
    """Collection fragments merge in sorted-path order, so this reorders `declarations`.

    No fact about any variable changed, so nothing the gate compares may move — not
    `variables_hash` (sorted by identity), not `vfs_hash` (its variable and expression terms
    sort too; a hidden variable binds no token slot).
    """
    base_pack = _pack(tmp_path, "base")
    split_pack = _pack(tmp_path, "split")
    payload = yaml.safe_load((split_pack / "variables.yaml").read_text())
    declarations = payload["variables"]["declarations"]
    (hidden,) = [declaration for declaration in declarations if declaration["id"] == "hidden_score"]
    declarations.remove(hidden)
    (split_pack / "variables.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))
    # "aaa_" sorts before "variables.yaml", so the moved declaration now leads the merged roster.
    fragment = {"variables": {"version": "1.0", "declarations": [hidden]}}
    (split_pack / "aaa_more_state.yaml").write_text(yaml.safe_dump(fragment, sort_keys=False))

    assert _moved(_compile(base_pack), _compile(split_pack)) == set()


def test_exposed_declaration_reorder_is_layout_not_variables_identity(tmp_path: Path) -> None:
    """Order IS semantic for a flat reader — a variable-element slot is bound in declaration order
    — and `layout_hash` is the contract that carries it. `variables_hash` does not duplicate it.
    A token-set brain does not compare `layout_hash`, and correctly resumes across a pure
    reorder: slot permutation is entity variation a token net absorbs by design."""
    base_pack = _pack(tmp_path, "base")
    reordered_pack = _pack(tmp_path, "reordered")
    # The witness exposes one variable; a permutation needs two. `bonus` binds a second
    # variable-element slot after `public_state` in the base pack.
    second_exposed = _declaration("bonus", exposed_to=["agent"], normalization=MINMAX)
    _edit_variables(base_pack, lambda variables: variables["declarations"].append(second_exposed))

    def second_exposed_first(variables: dict[str, Any]) -> None:
        variables["declarations"].insert(0, second_exposed)

    _edit_variables(reordered_pack, second_exposed_first)
    base, reordered = _compile(base_pack), _compile(reordered_pack)
    moved = _moved(base, reordered)
    assert "layout_hash" in moved, f"the exposed permutation no longer moves the flat layout; moved={sorted(moved)}"
    assert "variables_hash" not in moved
    assert moved <= {"layout_hash", "vfs_hash"}, f"moved={sorted(moved)}"


def test_role_order_and_expression_whitespace_are_spelling(tmp_path: Path) -> None:
    base_pack = _pack(tmp_path, "base")
    respelled_pack = _pack(tmp_path, "respelled")

    def respell(variables: dict[str, Any]) -> None:
        for declaration in variables["declarations"]:
            declaration["readable_by"] = list(reversed(declaration["readable_by"]))
            if declaration["id"] == "scaled_public":
                declaration["expression"] = "(public_state)*immutable_scale"

    _edit_variables(respelled_pack, respell)
    assert _moved(_compile(base_pack), _compile(respelled_pack)) == set()


def _respell_advance_write(expression: str) -> Callable[[dict[str, Any]], None]:
    def mutate(payload: dict[str, Any]) -> None:
        (advance,) = [action for action in payload["actions"]["custom_actions"] if action["name"] == "ADVANCE"]
        (write,) = [write for write in advance["writes"] if write["variable_id"] == "public_state"]
        assert write["expression"] == "1.0", "witness ADVANCE write changed; re-derive this test"
        write["expression"] = expression

    return mutate


def test_action_write_expression_respelling_moves_nothing(tmp_path: Path) -> None:
    """Action-write text reaches two hashes — `actions_hash` (the declaration) and `vfs_hash`
    (slot 4, the compiled transition rules). Both hash the canonical AST, so `'1.0'` and
    `'( 1.0 )'` are one write; `'2.0'` is another and moves both."""
    base_pack = _pack(tmp_path, "base")
    respelled_pack = _pack(tmp_path, "respelled")
    changed_pack = _pack(tmp_path, "changed")
    _edit_yaml(respelled_pack / "actions.yaml", _respell_advance_write("( 1.0 )"))
    _edit_yaml(changed_pack / "actions.yaml", _respell_advance_write("2.0"))

    base = _compile(base_pack)
    assert _moved(base, _compile(respelled_pack)) == set()
    assert {"actions_hash", "vfs_hash"} <= _moved(base, _compile(changed_pack))


def test_yaml_comment_is_not_content(tmp_path: Path) -> None:
    base_pack = _pack(tmp_path, "base")
    commented_pack = _pack(tmp_path, "commented")
    path = commented_pack / "variables.yaml"
    path.write_text("# an author's note\n" + path.read_text())
    assert _moved(_compile(base_pack), _compile(commented_pack)) == set()


def test_variables_hash_is_canonical_content_of_the_parsed_declaration(tmp_path: Path) -> None:
    universe = _compile(_pack(tmp_path, "base"))
    from townlet.universe.raw_configs_v21 import RawConfigsV21

    raw = RawConfigsV21.from_experiment_dir(universe.experiment_dir)
    assert universe.variables_hash == compute_variables_hash(raw.variables)
    assert len(universe.variables_hash) == 64


def test_canonical_expression_ast_strips_positions_and_keeps_constant_types() -> None:
    parser = ExpressionParser()
    assert canonical_expression_ast(parser.parse("x*1")) == canonical_expression_ast(parser.parse("( x ) * 1"))
    assert canonical_expression_ast(parser.parse("x * 1")) != canonical_expression_ast(parser.parse("x * 3"))
    assert canonical_expression_ast(parser.parse("1")) != canonical_expression_ast(parser.parse("1.0"))
    payload = canonical_expression_ast(parser.parse("if a > b then max(a, 2) else -b"))
    assert "line" not in str(payload) and "column" not in str(payload)
    assert payload["node"] == "if" and payload["then"]["node"] == "call" and payload["else"]["node"] == "unary"
