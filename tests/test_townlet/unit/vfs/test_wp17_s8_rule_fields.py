"""WP17 S8: transition-rule fields are derived or deleted (findings_vfs_round2 S8, r6).

`r6_rules_pair_global.py` showed that a rule compiled and ran with `reads: [no_such_variable]`
while its expression read something else, and that `kind` changed only a telemetry prefix.
Now a rule's reads are derived from its expression and condition ASTs, a rule has no kind,
telemetry names the rule by its id, and the family is `transition_rules`. The old spellings
(`reads`, `kind`, a `social_residue:` document) fail at parse with the author's `file:line`.
"""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.action_metadata import RuntimeAction
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.vfs import compile_vtc_transition_rules
from townlet.vfs.schema import VariableScope
from townlet.vfs.schema_hashes import canonical_transition_graph_schema, compute_transition_graph_hash
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.vfs.vtc import VTCWriteRefusalError, VTCWriteTarget, compile_vtc_action_writes_with_phase_graph

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
PHASE = "apply_social_residue_effects"


def _target(scope: VariableScope, var_type: str = "scalar", *, meter: bool = False) -> VTCWriteTarget:
    return VTCWriteTarget(scope, var_type, meter=meter, expression=None)


TARGETS = {
    "gsum": _target(VariableScope.GLOBAL),
    "energy": _target(VariableScope.AGENT, meter=True),
    "state": _target(VariableScope.AGENT),
    "flag": _target(VariableScope.AGENT, "bool"),
}


def _rule(expression: str, *, condition: str | None = None, effect: str | None = None, rule_id: str = "r", target: str = "state") -> dict:
    write: dict = {"variable_id": target, "expression": expression, "composition": "additive_delta"}
    if effect is not None:
        write["effect"] = effect
    return {"id": rule_id, "phase": PHASE, "condition": condition, "writes": [write]}


# --- derived reads ------------------------------------------------------------------------


def test_derived_reads_are_the_variables_the_asts_read_across_every_spelling() -> None:
    """Expression and condition reads, through `x`, `vfs.x`, `self.vfs.x` and `bar.x`, resolve to variable ids, sorted."""
    program = compile_vtc_transition_rules([_rule("vfs.state + vfs.gsum", condition="self.vfs.flag and bar.energy > 0.5")], TARGETS)
    (rule,) = program.rules
    assert rule.reads == ("energy", "flag", "gsum", "state")


def test_a_literal_rule_reads_nothing() -> None:
    (rule,) = compile_vtc_transition_rules([_rule("1.0", target="gsum")], TARGETS).rules
    assert rule.reads == ()


def test_an_expression_naming_nothing_declared_refuses_at_compile() -> None:
    """r6 `reads_lies` inverted: the only way to claim a read is to read, and an unknown name refuses."""
    with pytest.raises(VTCWriteRefusalError, match="no_such_variable"):
        compile_vtc_transition_rules([_rule("no_such_variable")], TARGETS)


@pytest.mark.parametrize("field,value", [("reads", ["gsum"]), ("kind", "social_residue")])
def test_a_mapping_source_carrying_a_deleted_field_is_refused(field: str, value: object) -> None:
    """The compiler's raw-mapping path (serialized sources, tests) refuses the deleted fields too."""
    with pytest.raises(ValueError, match=f"declares '{field}'"):
        compile_vtc_transition_rules([{**_rule("1.0"), field: value}], TARGETS)


# --- telemetry -----------------------------------------------------------------------------


def test_telemetry_label_is_rule_id_and_effect_or_variable() -> None:
    program = compile_vtc_transition_rules(
        [_rule("1.0", effect="pressure_delta", rule_id="labelled"), _rule("1.0", rule_id="bare")],
        TARGETS,
    )
    assert sorted(rule.telemetry_label for rule in program.rules) == ["bare:state", "labelled:pressure_delta"]
    assert not any(hasattr(rule, "kind") for rule in program.rules)


# --- hashing --------------------------------------------------------------------------------


def _program(expression: str):
    return compile_vtc_transition_rules([_rule(expression, condition="bar.energy > 0.5")], TARGETS)


def test_hash_is_stable_under_whitespace_and_moves_with_the_expression() -> None:
    phase_graph = TransitionPhaseGraph.default()
    actions = compile_vtc_action_writes_with_phase_graph([], {}, phase_graph)

    def digest(expression: str) -> str:
        return compute_transition_graph_hash(phase_graph, actions, transition_rule_program=_program(expression))

    assert digest("state + 1.0") == digest("state   +   1.0") == digest("(state + 1.0)")
    assert digest("state + 1.0") != digest("state + 2.0")
    assert digest("state + 1.0") != digest("energy + 1.0")


def test_hash_payload_carries_no_authored_reads_or_kind() -> None:
    """Derived reads are not identity (the ASTs are); kind no longer exists."""
    phase_graph = TransitionPhaseGraph.default()
    actions = compile_vtc_action_writes_with_phase_graph([], {}, phase_graph)
    (payload,) = canonical_transition_graph_schema(phase_graph, actions, transition_rule_program=_program("state + 1.0"))["rules"]
    assert "reads" not in payload and "kind" not in payload
    assert payload["rule_id"] == "r" and payload["telemetry_label"] == "r:state"


# --- parse refusals with file:line ----------------------------------------------------------


def _pack(tmp_path: Path, name: str, document: str) -> Path:
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    (pack / "transition_rules.yaml").write_text(document)
    return pack


WRITE = """      - variable_id: public_state
        expression: "1.0"
        composition: additive_delta
        condition: null
        clamp: null
        effect: null
"""


def _issues(pack: Path) -> list:
    with pytest.raises(CompilationError) as refusal:
        RawConfigsV21.from_experiment_dir(pack)
    return refusal.value.issues


def test_authored_reads_fails_at_parse_with_location(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        "reads",
        'version: "1.0"\ntransition_rules:\n  - id: inc\n    phase: '
        + PHASE
        + "\n    reads: [no_such_variable]\n    condition: null\n    writes:\n"
        + WRITE,
    )
    (issue,) = _issues(pack)
    assert issue.code == ErrorCode.LOAD_ERROR
    assert "reads" in issue.message and "Extra inputs are not permitted" in issue.message
    assert issue.location is not None and issue.location.startswith(f"{pack / 'transition_rules.yaml'}:")


def test_authored_kind_fails_at_parse_with_location(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        "kind",
        'version: "1.0"\ntransition_rules:\n  - id: inc\n    kind: institutional_rule\n    phase: '
        + PHASE
        + "\n    condition: null\n    writes:\n"
        + WRITE,
    )
    (issue,) = _issues(pack)
    assert issue.code == ErrorCode.LOAD_ERROR
    assert "kind" in issue.message and "Extra inputs are not permitted" in issue.message
    assert issue.location is not None and issue.location.startswith(f"{pack / 'transition_rules.yaml'}:")


def test_old_family_name_fails_at_parse_with_location(tmp_path: Path) -> None:
    """A `social_residue:` document matches no family: unknown declaration, not an alias."""
    pack = _pack(
        tmp_path,
        "old_family",
        'version: "1.0"\nsocial_residue:\n  - id: inc\n    phase: ' + PHASE + "\n    condition: null\n    writes:\n" + WRITE,
    )
    (issue,) = _issues(pack)
    assert issue.code == ErrorCode.DECLARATION_UNKNOWN
    assert "social_residue" in issue.message
    assert issue.location == f"{pack / 'transition_rules.yaml'}:1"


def test_new_family_compiles_and_runs_with_derived_reads(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        "new_family",
        'version: "1.0"\ntransition_rules:\n  - id: inc\n    phase: '
        + PHASE
        + '\n    condition: "immutable_scale > 0.0"\n    writes:\n'
        + WRITE,
    )
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    (rule,) = universe.get_level(LEVEL).transition_schedule.transition_rule_program.rules
    assert rule.rule_id == "inc" and rule.reads == ("immutable_scale",) and rule.telemetry_label == "inc:public_state"
    serialized = universe.to_dict()["all_levels"][LEVEL]["transition_schedule"]
    (source,) = serialized["transition_rules"]
    assert "reads" not in source and "kind" not in source
    assert "social_residue_rules" not in serialized


# --- ActionConfig.reads -------------------------------------------------------------------


def test_runtime_action_has_no_reads_field() -> None:
    """`ActionConfig.reads` and its `RuntimeAction` mirror are deleted: nothing consumed them."""
    assert "reads" not in {field.name for field in dataclasses.fields(RuntimeAction)}
