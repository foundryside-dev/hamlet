"""PRD-0002 criterion 5: every pinned-family code has a real located refusal."""

from __future__ import annotations

import inspect
import re
import shutil
from pathlib import Path

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError
from townlet.universe.validation import limits


def registered_families() -> dict[str, set[ErrorCode]]:
    """Walk the registry's declared groups, rather than counting passing examples."""
    families: dict[str, set[ErrorCode]] = {"preflight": set(), "load-error": set(), "limits": set(), "vocabulary-lockstep": set()}
    stage = None
    for line in inspect.getsource(ErrorCode).splitlines():
        heading = re.search(r"# --- Stage (\d+):", line)
        if heading:
            stage = int(heading[1])
        member = re.match(r"\s+([A-Z][A-Z_]+) =", line)
        if member is None:
            continue
        code = ErrorCode[member[1]]
        family = {0: "preflight", 1: "load-error", 2: "limits"}.get(stage)
        if family is not None:
            families[family].add(code)
        elif "VOCAB_MISMATCH" in code.name or re.fullmatch(r"(?:CASCADE|MODULATION)_(?:MISSING|EXTRA)", code.name):
            families["vocabulary-lockstep"].add(code)
    return families


# These cases run the public compiler against altered authored input. They do not
# manufacture CompilationMessage objects or substitute validators with test doubles.
WITNESSES = {
    ErrorCode.CONFIG_PATH_INVALID: "absent_pack",
    ErrorCode.SCOPING_LEVEL_DIRECTORY: "direct_level",
    ErrorCode.YAML_SYNTAX_ERROR: "malformed_yaml",
    ErrorCode.DECLARATION_UNKNOWN: "unknown_document",
    ErrorCode.DECLARATION_SCOPE: "misplaced_bars",
    ErrorCode.DECLARATION_COLLISION: "duplicate_drive",
    ErrorCode.DECLARATION_MISSING: "missing_brain",
    ErrorCode.CLOCK_REFERENCE: "unknown_clock",
    ErrorCode.LOAD_ERROR: "invalid_experiment",
    ErrorCode.LEVEL_LOAD_ERROR: "invalid_curriculum",
    ErrorCode.NO_CURRICULUM_LEVELS: "absent_levels",
    ErrorCode.CONFIG_LIMIT_EXCEEDED: "meter_budget",
    ErrorCode.ITEM_TYPES_LIMIT_EXCEEDED: "item_budget",
    ErrorCode.GRID_SIZE_LIMIT_EXCEEDED: "grid_budget",
    ErrorCode.SPAWN_RULE_LIMIT_EXCEEDED: "spawn_budget",
    ErrorCode.METER_VOCAB_MISMATCH: "meter_vocabulary",
    ErrorCode.AFFORDANCE_VOCAB_MISMATCH: "affordance_vocabulary",
    ErrorCode.CASCADE_MISSING: "missing_cascade",
    ErrorCode.CASCADE_EXTRA: "extra_cascade",
    ErrorCode.MODULATION_MISSING: "missing_modulation",
    ErrorCode.MODULATION_EXTRA: "extra_modulation",
}


def test_pinned_families_have_a_witness_for_every_registered_code() -> None:
    registered = set().union(*registered_families().values())
    assert set(WITNESSES) == registered, (
        f"Unexercised registered codes: {sorted(registered - WITNESSES.keys())}; "
        f"witnesses outside the pinned families: {sorted(WITNESSES.keys() - registered)}"
    )


def change_document(path: Path, mutation) -> None:
    document = yaml.safe_load(path.read_text())
    mutation(document)
    path.write_text(yaml.safe_dump(document, sort_keys=False))


@pytest.mark.parametrize(
    ("family", "code"),
    [(family, code) for family, codes in registered_families().items() for code in sorted(codes)],
)
def test_every_pinned_refusal_has_an_actual_source_and_line(tmp_path: Path, monkeypatch, family: str, code: ErrorCode) -> None:
    case = WITNESSES[code]
    item_case = case in {"item_budget", "spawn_budget"}
    source = Path("configs/test/items_smoke" if item_case else "configs/test/model_config")
    root = tmp_path / "pack"
    shutil.copytree(source, root, ignore=shutil.ignore_patterns(".compiled"))
    primary = "L0_smoke" if item_case else "L0_test"
    level = root / "levels" / primary
    target = root

    if case == "absent_pack":
        target = tmp_path / "absent"
    elif case == "direct_level":
        target = level
    elif case == "malformed_yaml":
        (root / "mistake.yml").write_text("broken: [yaml: syntax")
    elif case == "unknown_document":
        (root / "mistake.yml").write_text("unrecognised_mechanic: true\n")
    elif case == "misplaced_bars":
        shutil.copyfile(level / "bars.yaml", root / "misplaced.yml")
    elif case == "duplicate_drive":
        shutil.copyfile(level / "drive.yaml", level / "duplicate.yml")
    elif case == "missing_brain":
        (root / "brain.yaml").unlink()
    elif case == "unknown_clock":
        change_document(level / "curriculum.yaml", lambda doc: doc["curriculum"].update(day_length={"period_of": "missing_clock"}))
    elif case == "invalid_experiment":
        change_document(root / "experiment.yaml", lambda doc: doc["experiment"].pop("experiment_name"))
    elif case == "invalid_curriculum":
        change_document(level / "curriculum.yaml", lambda doc: doc["curriculum"].update(active_vision="unknown_mode"))
    elif case == "absent_levels":
        shutil.rmtree(root / "levels")
    elif case == "meter_budget":
        monkeypatch.setattr(limits, "MAX_METERS", 0)
    elif case == "item_budget":
        monkeypatch.setattr(limits, "MAX_ITEM_TYPES", 0)
    elif case == "grid_budget":
        monkeypatch.setattr(limits, "MAX_GRID_CELLS", 0)
    elif case == "spawn_budget":
        monkeypatch.setattr(limits, "MAX_SPAWN_RULES_PER_ITEM", 0)
    elif case == "meter_vocabulary":
        change_document(level / "bars.yaml", lambda doc: doc["bars"]["meters"].pop())
    elif case == "affordance_vocabulary":
        change_document(level / "affordances.yaml", lambda doc: doc["affordances"]["affordances"].pop())
    elif case == "missing_cascade":
        change_document(level / "bars.yaml", lambda doc: doc["bars"]["cascades"].pop())
    elif case == "extra_cascade":
        change_document(
            level / "bars.yaml",
            lambda doc: doc["bars"]["cascades"].append({**doc["bars"]["cascades"][0], "source": "energy", "target": "health"}),
        )
    elif case == "missing_modulation":
        change_document(level / "affordances.yaml", lambda doc: doc["affordances"]["modulations"].pop())
    elif case == "extra_modulation":
        change_document(
            level / "affordances.yaml",
            lambda doc: doc["affordances"]["modulations"].append({**doc["affordances"]["modulations"][0], "bar": "health"}),
        )
    else:
        pytest.fail(f"No actual negative input for {family}:{code}")

    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(target, primary_level=primary, use_cache=False)

    assert code in {issue.code for issue in caught.value.issues}, str(caught.value)
    for issue in caught.value.issues:
        assert issue.code in ErrorCode, f"Unregistered code: {issue.code}"
        assert issue.location is not None, str(caught.value)
        path, separator, line = issue.location.rpartition(":")
        assert separator and line.isdigit() and int(line) > 0, str(caught.value)
        origin = Path(path)
        assert origin.is_absolute(), str(caught.value)
        if code == ErrorCode.CONFIG_PATH_INVALID:
            assert origin == target
        else:
            assert origin.exists() and origin.is_relative_to(root), str(caught.value)
            if origin.is_file():
                assert int(line) <= max(1, len(origin.read_text().splitlines())), str(caught.value)
