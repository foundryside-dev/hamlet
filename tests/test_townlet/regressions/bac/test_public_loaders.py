"""Standalone public DTO loading through canonical declaration transport."""

import shutil
from pathlib import Path

import pytest
import yaml

from townlet.config.curriculum import CurriculumConfig, load_curriculum_config
from townlet.config.exploration import ExplorationConfig, load_exploration_config
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError

ROOT = Path(__file__).resolve().parents[4]
LEVEL = "L3_temporal_mechanics"
TRANSPORTS = ("conventional", "renamed", "multidocument")
TRAINING = """training:
  exploration:
    epsilon_start: 0.8
    epsilon_end: 0.1
    epsilon_decay: 0.9
"""
CURRICULUM = """curriculum:
  version: "1.0"
  active_vision: global
  vision_range: 0.5
  active_temporal: true
  day_length: 24
"""


def _sections(directory):
    directory.mkdir(parents=True)
    (directory / "training.yaml").write_text(TRAINING)
    (directory / "curriculum.yaml").write_text(CURRICULUM)
    return directory


def _relocate(directory, transport):
    training = directory / "training.yaml"
    curriculum = directory / "curriculum.yaml"
    if transport == "renamed":
        nested = directory / "nested" / "authored"
        nested.mkdir(parents=True)
        training.replace(nested / "learner.yml")
        curriculum.replace(nested / "schedule.yml")
    elif transport == "multidocument":
        bundled = directory / "nested" / "sections.yml"
        bundled.parent.mkdir()
        bundled.write_text("# Combined T07 declarations\n\n" + training.read_text() + "\n---\n\n" + curriculum.read_text())
        training.unlink()
        curriculum.unlink()
    else:
        assert transport == "conventional"


def _assert_sections(directory, epsilon, day_length):
    exploration = load_exploration_config(directory)
    curriculum = load_curriculum_config(directory)
    assert isinstance(exploration, ExplorationConfig) and isinstance(curriculum, CurriculumConfig)
    assert exploration.epsilon_start == epsilon
    assert exploration.epsilon_end == 0.1 and exploration.epsilon_decay == 0.9
    assert curriculum.curriculum.active_temporal is True and curriculum.curriculum.day_length == day_length
    return exploration, curriculum


def _native_pack(directory):
    target = directory / "pack"
    source = ROOT / "configs" / "default_curriculum"
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if path.is_file() and path.suffix in {".yaml", ".yml"} and not any(part.startswith(".") for part in relative.parts):
            copied = target / relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, copied)  # Authored YAML data, never a source checkout.
    return target


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_public_loaders_accept_relocation_and_period_of(tmp_path, transport):
    root = _native_pack(tmp_path)
    level = root / "levels" / LEVEL
    # The existing exploration DTO route validates this real shipped input first.
    original = load_exploration_config(level)
    assert isinstance(original, ExplorationConfig)
    assert original.epsilon_start == 1.0 and original.epsilon_end == 0.01 and original.epsilon_decay == 0.995
    _relocate(level, transport)
    exploration = load_exploration_config(level)
    curriculum = load_curriculum_config(level)
    assert isinstance(exploration, ExplorationConfig) and isinstance(curriculum, CurriculumConfig)
    assert exploration.model_dump() == original.model_dump()
    assert curriculum.curriculum.active_temporal is True
    assert curriculum.curriculum.day_length == 24, "The shipped day_phase period must lower before the original DTO is constructed"


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_public_loaders_preserve_minimal_standalone_sections(tmp_path, transport):
    root = _sections(tmp_path / "standalone")
    original = _assert_sections(root, 0.8, 24)
    # No experiment/brain/actions/variables/training-loop declarations exist.
    assert not (root / "variables.yaml").exists()
    _relocate(root, transport)
    actual = _assert_sections(root, 0.8, 24)
    assert tuple(item.model_dump() for item in actual) == tuple(item.model_dump() for item in original)


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_public_loaders_root_local_target_wins(tmp_path, transport):
    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    for name in ("A", "B"):
        child = _sections(root / "levels" / name)
        (child / "training.yaml").write_text(TRAINING.replace("epsilon_start: 0.8", "epsilon_start: 0.2"))
        (child / "curriculum.yaml").write_text(CURRICULUM.replace("day_length: 24", "day_length: 12"))
        _assert_sections(child, 0.2, 12)
    _relocate(root, transport)
    _assert_sections(root, 0.8, 24)


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_public_loaders_direct_level_and_sole_pack_selection(tmp_path, transport):
    root = tmp_path / "pack"
    level = _sections(root / "levels" / "selected")
    _assert_sections(level, 0.8, 24)
    _relocate(level, transport)
    direct = _assert_sections(level, 0.8, 24)
    inferred = _assert_sections(root, 0.8, 24)
    assert tuple(item.model_dump() for item in inferred) == tuple(item.model_dump() for item in direct)


@pytest.mark.parametrize("loader", (load_exploration_config, load_curriculum_config))
def test_public_loaders_ambiguous_pack_is_located(tmp_path, loader):
    root = tmp_path / "pack"
    for name in ("A", "B"):
        _assert_sections(_sections(root / "levels" / name), 0.8, 24)
    with pytest.raises(CompilationError) as actual:
        loader(root)
    assert any(issue.code == ErrorCode.DECLARATION_SCOPE and issue.location == f"{root / 'levels'}:1" for issue in actual.value.issues)
    assert "A" in str(actual.value) and "B" in str(actual.value)


@pytest.mark.parametrize(
    "invalid", ("missing", "wrong_id", "wrong_expression", "bool_period", "fractional_period", "extra_reference_key", "duplicated_numeric")
)
def test_public_loader_clock_validation_is_located(tmp_path, invalid):
    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)  # Numeric standalone curriculum needs no variables.
    variables = yaml.safe_load((ROOT / "configs/default_curriculum/variables.yaml").read_text())
    clock = variables["variables"]["declarations"][0]
    assert clock["id"] == "day_phase" and clock["normalization"]["period"] == 24
    reference = {"period_of": "day_phase"}
    if invalid == "wrong_id":
        reference["period_of"] = "unknown_clock"
    elif invalid == "wrong_expression":
        clock["expression"] = "tick + 1"
    elif invalid == "bool_period":
        clock["normalization"]["period"] = True
    elif invalid == "fractional_period":
        clock["normalization"]["period"] = 23.5
    elif invalid == "extra_reference_key":
        reference["offset"] = 0
    curriculum = yaml.safe_load(CURRICULUM)
    if invalid != "duplicated_numeric":
        curriculum["curriculum"]["day_length"] = reference
    curriculum_path = root / "curriculum.yaml"
    curriculum_path.write_text(yaml.safe_dump(curriculum, sort_keys=False))
    if invalid != "missing":
        (root / "ambient-clock.yml").write_text(yaml.safe_dump(variables, sort_keys=False))
    with pytest.raises(CompilationError) as actual:
        load_curriculum_config(root)
    assert any(issue.code == ErrorCode.CLOCK_REFERENCE for issue in actual.value.issues)
    assert any(issue.location and issue.location.startswith(f"{curriculum_path}:") for issue in actual.value.issues)


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_public_loaders_reject_bare_training_wrapper(tmp_path, transport):
    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    (root / "training.yaml").write_text("exploration:\n  epsilon_start: 0.8\n  epsilon_end: 0.1\n  epsilon_decay: 0.9\n")
    _relocate(root, transport)
    with pytest.raises((ValueError, CompilationError)) as actual:
        load_exploration_config(root)
    assert "training" in str(actual.value) or "exploration" in str(actual.value)


@pytest.mark.parametrize("transport", TRANSPORTS)
@pytest.mark.parametrize("family", ("exploration", "curriculum"))
def test_public_loaders_preserve_original_dto_validation(tmp_path, transport, family):
    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    if family == "exploration":
        (root / "training.yaml").write_text(TRAINING.replace("epsilon_start: 0.8", "epsilon_start: not-a-number"))
        loader, field = load_exploration_config, "epsilon_start"
    else:
        (root / "curriculum.yaml").write_text(CURRICULUM.replace("active_temporal: true", "active_temporal: not-a-boolean"))
        loader, field = load_curriculum_config, "active_temporal"
    _relocate(root, transport)
    with pytest.raises((ValueError, CompilationError)) as actual:
        loader(root)
    assert field in str(actual.value)


def test_public_loader_missing_exploration_does_not_invent_a_section(tmp_path):
    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    (root / "training.yaml").write_text("training: {}\n")
    with pytest.raises(ValueError, match="exploration"):
        load_exploration_config(root)


@pytest.mark.parametrize("family", ("training", "curriculum"))
def test_public_loader_missing_target_is_located(tmp_path, family):
    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    (root / f"{family}.yaml").unlink()
    loader = load_exploration_config if family == "training" else load_curriculum_config
    with pytest.raises(CompilationError) as actual:
        loader(root)
    assert any(issue.code == ErrorCode.DECLARATION_MISSING and issue.location == f"{root}:1" for issue in actual.value.issues)


@pytest.mark.parametrize("invalid", ("duplicate_declaration", "duplicate_key", "yaml_syntax"))
def test_section_inventory_preserves_duplicate_and_syntax_diagnostics(tmp_path, invalid):
    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    incoming = root / "zz-incoming.yml"
    if invalid == "duplicate_declaration":
        incoming.write_text("# Incoming declaration\n\n" + TRAINING)
        expected_code = ErrorCode.DECLARATION_COLLISION
    elif invalid == "duplicate_key":
        incoming.write_text("training:\n  exploration:\n    epsilon_start: 0.8\n    epsilon_start: 0.9\n")
        expected_code = ErrorCode.YAML_SYNTAX_ERROR
    else:
        incoming.write_text("{invalid")
        expected_code = ErrorCode.YAML_SYNTAX_ERROR
    with pytest.raises(CompilationError) as actual:
        load_exploration_config(root)
    assert any(issue.code == expected_code and issue.location.startswith(f"{incoming}:") for issue in actual.value.issues)
    if invalid == "duplicate_declaration":
        assert any(issue.location == f"{incoming}:3" for issue in actual.value.issues)
        assert f"{root / 'training.yaml'}:1" in str(actual.value)


@pytest.mark.parametrize("invalid", ("top_level", "nested", "conflict"))
def test_section_inventory_preserves_training_sidecar_validation(tmp_path, invalid):
    root = _sections(tmp_path / "standalone")
    training = root / "training.yaml"
    valid = "recording:\n  enabled: false\n" + TRAINING.replace("training:\n", "training:\n  recording:\n    enabled: false\n")
    training.write_text(valid)
    _assert_sections(root, 0.8, 24)
    if invalid == "top_level":
        training.write_text(valid.replace("recording:\n  enabled: false", "recording:\n  enabled: not-a-boolean"))
    elif invalid == "nested":
        training.write_text(valid.replace("  recording:\n    enabled: false", "  recording:\n    enabled: not-a-boolean"))
    else:
        training.write_text(valid.replace("  recording:\n    enabled: false", "  recording:\n    enabled: true"))
    with pytest.raises(CompilationError) as actual:
        load_exploration_config(root)
    expected_code = ErrorCode.DECLARATION_COLLISION if invalid == "conflict" else ErrorCode.LOAD_ERROR
    assert any(issue.code == expected_code and issue.location.startswith(f"{training}:") for issue in actual.value.issues)
    assert "recording" in str(actual.value)


def test_section_inventory_retains_multidocument_source_origin(tmp_path):
    from townlet.config import resolved_launch

    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    _relocate(root, "multidocument")
    resolver = getattr(resolved_launch, "resolve_config_section", None)
    assert callable(resolver), "T07 needs an explicit standalone declaration-section producer, not full-compile fallback"
    training = resolver(root, family="training")
    curriculum = resolver(root, family="curriculum")
    authored = root / "nested" / "sections.yml"
    assert training.origin == f"{authored}:3" and curriculum.origin == f"{authored}:11"
    assert training.payload["exploration"]["epsilon_start"] == 0.8
    assert curriculum.payload["day_length"] == 24


def test_section_resolution_matches_selected_compiled_dtos(tmp_path):
    from townlet.config.resolved_launch import resolve_launch

    root = _native_pack(tmp_path)
    baseline = resolve_launch(root, level_name=LEVEL)
    assert baseline.compiled.get_level(LEVEL).curriculum.curriculum.day_length == 24
    level = root / "levels" / LEVEL
    _relocate(level, "multidocument")
    resolved = resolve_launch(root, level_name=LEVEL)
    assert resolved.effective.execution_hash == baseline.effective.execution_hash
    selected = resolved.compiled.get_level(LEVEL)
    exploration = load_exploration_config(level)
    curriculum = load_curriculum_config(level)
    assert isinstance(exploration, ExplorationConfig) and isinstance(curriculum, CurriculumConfig)
    assert exploration.model_dump() == selected.training.model_dump()["exploration"]
    assert curriculum.model_dump() == selected.curriculum.model_dump()
    assert curriculum.curriculum.day_length == 24


@pytest.mark.parametrize("direct_level", (False, True))
def test_full_declaration_discovery_keeps_strict_scope_and_required_families(tmp_path, direct_level):
    from townlet.universe.declarations import DeclarationStore

    root = tmp_path / "pack"
    entry = _sections(root / "levels" / "selected") if direct_level else _sections(root)
    _assert_sections(entry, 0.8, 24)
    with pytest.raises(CompilationError) as actual:
        DeclarationStore.discover(root)
    codes = {issue.code for issue in actual.value.issues}
    assert ErrorCode.DECLARATION_MISSING in codes
    if not direct_level:
        assert ErrorCode.DECLARATION_SCOPE in codes
    else:
        with pytest.raises(CompilationError) as direct:
            DeclarationStore.discover(entry)
        assert any(issue.code == ErrorCode.SCOPING_LEVEL_DIRECTORY for issue in direct.value.issues)


def _corrupt_section_scope(directory, invalid, transport):
    if invalid == "duplicate":
        incoming = directory / "zz-duplicate.yml"
        incoming.write_text(TRAINING + "\n---\n" + CURRICULUM)
        return incoming, ErrorCode.DECLARATION_COLLISION
    if invalid == "yaml_syntax":
        incoming = directory / "zz-broken-sidecar.yml"
        incoming.write_text("{invalid")
        return incoming, ErrorCode.YAML_SYNTAX_ERROR
    assert invalid == "sidecar"
    paths = {
        "conventional": directory / "training.yaml",
        "renamed": directory / "nested" / "authored" / "learner.yml",
        "multidocument": directory / "nested" / "sections.yml",
    }
    training = paths[transport]
    training.write_text("recording:\n  enabled: not-a-boolean\n" + training.read_text())
    code = ErrorCode.LEVEL_LOAD_ERROR if directory.parent.name == "levels" else ErrorCode.LOAD_ERROR
    return training, code


@pytest.mark.parametrize("family", ("exploration", "curriculum"))
@pytest.mark.parametrize("direct_level", (False, True))
@pytest.mark.parametrize("transport", TRANSPORTS)
@pytest.mark.parametrize("invalid", ("duplicate", "yaml_syntax", "sidecar"))
def test_public_loaders_ignore_unselected_level_corruption(tmp_path, family, direct_level, transport, invalid):
    from townlet.universe.declarations import DeclarationStore

    root = tmp_path / "pack"
    entry = _sections(root / "levels" / "A") if direct_level else _sections(root)
    unrelated = _sections(root / "levels" / "B")
    _assert_sections(entry, 0.8, 24)
    _assert_sections(unrelated, 0.8, 24)
    _relocate(entry, transport)
    # Both target DTOs remain genuinely valid after the same transport transformation.
    _assert_sections(entry, 0.8, 24)
    unrelated_path, unrelated_code = _corrupt_section_scope(unrelated, invalid, "conventional")
    loader = load_exploration_config if family == "exploration" else load_curriculum_config
    actual = loader(entry)
    if family == "exploration":
        assert isinstance(actual, ExplorationConfig)
        assert actual.epsilon_start == 0.8 and actual.epsilon_end == 0.1 and actual.epsilon_decay == 0.9
    else:
        assert isinstance(actual, CurriculumConfig)
        assert actual.curriculum.active_temporal is True and actual.curriculum.day_length == 24

    # Excluding the sibling from this narrow loader never admits the invalid whole pack.
    with pytest.raises(CompilationError) as whole_pack:
        DeclarationStore.discover(root)
    assert any(
        issue.code == unrelated_code and issue.location and issue.location.startswith(f"{unrelated_path}:")
        for issue in whole_pack.value.issues
    )

    # Selected requested-family corruption still refuses; curriculum does not need training sidecars.
    selected_path, selected_code = _corrupt_section_scope(entry, invalid, transport)
    if family == "curriculum" and invalid == "sidecar":
        assert loader(entry).curriculum.day_length == 24
        loader = load_exploration_config
    with pytest.raises(CompilationError) as selected:
        loader(entry)
    assert any(
        issue.code == selected_code and issue.location and issue.location.startswith(f"{selected_path}:") for issue in selected.value.issues
    )


@pytest.mark.parametrize("transport", TRANSPORTS)
@pytest.mark.parametrize("placement", ("top_level", "nested"))
def test_public_curriculum_ignores_identifiable_training_sidecar_error(tmp_path, transport, placement):
    from townlet.universe.declarations import DeclarationStore

    root = _sections(tmp_path / "standalone")
    _assert_sections(root, 0.8, 24)
    _relocate(root, transport)
    _assert_sections(root, 0.8, 24)
    paths = {
        "conventional": root / "training.yaml",
        "renamed": root / "nested" / "authored" / "learner.yml",
        "multidocument": root / "nested" / "sections.yml",
    }
    training = paths[transport]
    if placement == "top_level":
        training.write_text("recording:\n  enabled: not-a-boolean\n" + training.read_text())
    else:
        training.write_text(training.read_text().replace("training:\n", "training:\n  recording:\n    enabled: not-a-boolean\n"))
    curriculum = load_curriculum_config(root)
    assert isinstance(curriculum, CurriculumConfig)
    assert curriculum.curriculum.active_temporal is True and curriculum.curriculum.day_length == 24
    with pytest.raises(CompilationError) as requested_training:
        load_exploration_config(root)
    assert any(
        issue.code == ErrorCode.LOAD_ERROR and issue.location and issue.location.startswith(f"{training}:")
        for issue in requested_training.value.issues
    )
    with pytest.raises(CompilationError) as whole_pack:
        DeclarationStore.discover(root)
    assert any(issue.code == ErrorCode.LOAD_ERROR for issue in whole_pack.value.issues)

    # Once its YAML cannot be safely classified, the selected-scope document must still refuse.
    training.write_text("{invalid")
    with pytest.raises(CompilationError) as syntax:
        load_curriculum_config(root)
    assert any(issue.code == ErrorCode.YAML_SYNTAX_ERROR for issue in syntax.value.issues)


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_direct_numeric_curriculum_ignores_unclassifiable_ancestor_yaml(tmp_path, transport):
    from townlet.universe.declarations import DeclarationStore

    root = tmp_path / "pack"
    level = _sections(root / "levels" / "A")
    _assert_sections(level, 0.8, 24)
    _relocate(level, transport)
    assert load_curriculum_config(level).curriculum.day_length == 24
    ancestor = root / "unrelated-broken.yml"
    ancestor.write_text("{invalid")
    curriculum = load_curriculum_config(level)
    assert isinstance(curriculum, CurriculumConfig)
    assert curriculum.curriculum.active_temporal is True and curriculum.curriculum.day_length == 24
    with pytest.raises(CompilationError) as whole_pack:
        DeclarationStore.discover(root)
    assert any(
        issue.code == ErrorCode.YAML_SYNTAX_ERROR and issue.location and issue.location.startswith(f"{ancestor}:")
        for issue in whole_pack.value.issues
    )
    selected = level / "selected-broken.yml"
    selected.write_text("{invalid")
    with pytest.raises(CompilationError) as selected_error:
        load_curriculum_config(level)
    assert any(
        issue.code == ErrorCode.YAML_SYNTAX_ERROR and issue.location and issue.location.startswith(f"{selected}:")
        for issue in selected_error.value.issues
    )


@pytest.mark.parametrize("transport", TRANSPORTS)
@pytest.mark.parametrize("dependency", ("missing", "malformed", "valid"))
def test_direct_period_of_keeps_strict_ancestor_dependency(tmp_path, transport, dependency):
    root = tmp_path / "pack"
    level = _sections(root / "levels" / "A")
    _assert_sections(level, 0.8, 24)
    curriculum = CURRICULUM.replace("day_length: 24", "day_length:\n    period_of: day_phase")
    (level / "curriculum.yaml").write_text(curriculum)
    _relocate(level, transport)
    clock = root / "ambient-clock.yml"
    if dependency == "valid":
        clock.write_text((ROOT / "configs/default_curriculum/variables.yaml").read_text())
        actual = load_curriculum_config(level)
        assert isinstance(actual, CurriculumConfig) and actual.curriculum.day_length == 24
    else:
        expected_code = ErrorCode.CLOCK_REFERENCE
        if dependency == "malformed":
            clock.write_text("{invalid")
            expected_code = ErrorCode.YAML_SYNTAX_ERROR
        with pytest.raises(CompilationError) as actual:
            load_curriculum_config(level)
        assert any(issue.code == expected_code and issue.location for issue in actual.value.issues)


@pytest.mark.parametrize("transport", TRANSPORTS)
@pytest.mark.parametrize("ancestor_layout", ("valid_only", "malformed_before", "malformed_after", "valid_before_malformed_document"))
def test_direct_numeric_curriculum_retains_recognized_ambient_clock_authority(tmp_path, transport, ancestor_layout):
    root = tmp_path / "pack"
    level = _sections(root / "levels" / "A")
    _assert_sections(level, 0.8, 24)
    _relocate(level, transport)
    assert load_curriculum_config(level).curriculum.day_length == 24
    authored = (ROOT / "configs/default_curriculum/variables.yaml").read_text()
    clock = root / "ambient-clock.yml"
    clock.write_text(authored)
    if ancestor_layout == "malformed_before":
        (root / "00-unrelated-broken.yml").write_text("{invalid")
    elif ancestor_layout == "malformed_after":
        (root / "zz-unrelated-broken.yml").write_text("{invalid")
    elif ancestor_layout == "valid_before_malformed_document":
        clock.write_text(authored + "\n---\n{invalid")
    else:
        assert ancestor_layout == "valid_only"
    with pytest.raises(CompilationError) as actual:
        load_curriculum_config(level)
    assert any(issue.code == ErrorCode.CLOCK_REFERENCE for issue in actual.value.issues)
    assert "Duplicated clock period" in str(actual.value)


@pytest.mark.parametrize("transport", TRANSPORTS)
def test_direct_numeric_curriculum_refuses_identifiable_invalid_clock_authority(tmp_path, transport):
    root = tmp_path / "pack"
    level = _sections(root / "levels" / "A")
    _assert_sections(level, 0.8, 24)
    _relocate(level, transport)
    assert load_curriculum_config(level).curriculum.day_length == 24
    variables = yaml.safe_load((ROOT / "configs/default_curriculum/variables.yaml").read_text())
    clock_variable = variables["variables"]["declarations"][0]
    assert clock_variable["id"] == "day_phase" and clock_variable["normalization"]["period"] == 24
    clock_variable["normalization"]["period"] = "not-a-period"
    clock = root / "ambient-clock.yml"
    clock.write_text(yaml.safe_dump(variables, sort_keys=False))
    with pytest.raises(CompilationError) as actual:
        load_curriculum_config(level)
    assert any(
        issue.code == ErrorCode.LOAD_ERROR and issue.location and issue.location.startswith(f"{clock}:") for issue in actual.value.issues
    )
