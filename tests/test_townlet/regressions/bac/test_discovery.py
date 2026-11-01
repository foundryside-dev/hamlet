"""Canonical launch discovery preserves compiler selection, identity and provenance."""

from __future__ import annotations

import importlib
import importlib.util
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.declarations import DeclarationStore
from townlet.universe.errors import CompilationError

DATA = Path(__file__).resolve().parents[4] / "configs/test/bac_remediation"
SELECTED = "L0_0_minimal"
OTHER = "L0_5_dual_resource"


def _dump(path: Path, documents: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump_all(documents, sort_keys=False), encoding="utf-8")


def _make_pack(root: Path, *, second_level: bool) -> Path:
    """Copy authored YAML DATA only; every generated runtime artifact stays in tmp_path."""
    source = DATA / "feedforward"
    levels = {SELECTED, OTHER} if second_level else {SELECTED}
    for path in sorted(source.rglob("*.yaml")):
        relative = path.relative_to(source)
        if relative.parts[0] == "levels" and relative.parts[1] not in levels:
            continue
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())

    pack_brain = yaml.safe_load((root / "brain.yaml").read_text(encoding="utf-8"))
    token_brain = yaml.safe_load((DATA / "token_set/brain.yaml").read_text(encoding="utf-8"))
    pack_brain["architecture"]["token_set"] = token_brain["architecture"]["token_set"]
    _dump(root / "brain.yaml", [pack_brain])

    # A complete recurrent replacement intentionally omits the pack's token_set preset.
    brain = yaml.safe_load((DATA / "recurrent/brain.yaml").read_text(encoding="utf-8"))
    brain["architecture"]["feedforward"] = {
        "hidden_layers": [17, 0],
        "activation": "tanh",
        "dropout": 0.2,
        "layer_norm": False,
    }
    brain["q_learning"].update(gamma=0.41, target_update_frequency=211, use_double_dqn=False)
    brain["optimizer"]["learning_rate"] = 0.0019
    brain["replay"]["capacity"] = 7001
    _dump(root / "levels" / SELECTED / "brain.yaml", [brain])

    training_path = root / "levels" / SELECTED / "training.yaml"
    training = yaml.safe_load(training_path.read_text(encoding="utf-8"))
    training["training"]["q_learning"].update(gamma=0.73, learning_rate=0.0007, target_update_frequency=13, use_double_dqn=True)
    training["training"]["replay_buffer"]["capacity"] = 4321
    _dump(training_path, [training])
    return root


def _transport(root: Path, mode: str) -> dict[str, Path]:
    locations = {
        "experiment": root / "experiment.yaml",
        "brain": root / "brain.yaml",
        f"levels/{SELECTED}/brain": root / "levels" / SELECTED / "brain.yaml",
        f"levels/{SELECTED}/training": root / "levels" / SELECTED / "training.yaml",
    }
    paths = sorted(root.rglob("*.yaml"))
    if mode == "renamed":
        for index, path in enumerate(paths):
            relative = path.relative_to(root)
            scope = root / "levels" / relative.parts[1] if relative.parts[0] == "levels" else root
            target = scope / "nested" / f"content-{index}.yaml"
            target.parent.mkdir(parents=True, exist_ok=True)
            path.rename(target)
            locations = {key: target if value == path else value for key, value in locations.items()}
    elif mode == "multidoc":
        scopes = [root, *(root / "levels" / name for name in (SELECTED, OTHER) if (root / "levels" / name).is_dir())]
        for scope in scopes:
            members = [path for path in paths if path.parent == scope]
            documents = [document for path in members for document in yaml.safe_load_all(path.read_text(encoding="utf-8"))]
            target = scope / "nested" / "combined.yaml"
            _dump(target, documents)
            for path in members:
                path.unlink()
            locations = {key: target if value in members else value for key, value in locations.items()}
    else:
        assert mode == "original"
    return locations


def _resolver() -> Any:
    # Keep collection/import/fixture failures distinct from the missing T05 feature.
    name = "townlet.config.resolved_launch"
    assert importlib.util.find_spec(name) is not None, "T05 canonical launch resolver is absent"
    module = importlib.import_module(name)
    assert callable(getattr(module, "resolve_launch", None)), "T05 resolve_launch public API is absent"
    return module.resolve_launch


def _assert_launch(launch: Any, root: Path, reference: Any, locations: dict[str, Path]) -> None:
    assert launch.root == root.resolve()
    assert launch.level_name == SELECTED
    assert launch.compiled.metadata.primary_level == SELECTED
    assert launch.effective is launch.compiled.effective_run
    assert launch.effective.primary_level == SELECTED
    assert launch.effective.execution_hash == reference.execution_hash
    assert launch.effective.authored_identity == reference.authored_identity
    assert launch.effective.authored_identity != launch.effective.execution_hash
    assert launch.compiled.brain_hash == reference.brain_hash
    assert launch.compiled.pack_brain_hash == reference.pack_brain_hash
    assert launch.compiled.brain_hash != launch.compiled.pack_brain_hash
    assert launch.compiled.brain.model_dump() == reference.brain.model_dump()
    assert launch.effective.base_brain.model_dump() == reference.brain.model_dump()
    assert launch.compiled.brain.architecture.type == "recurrent"
    assert launch.compiled.brain.architecture.token_set is None
    assert list(launch.compiled.brain.architecture.feedforward.hidden_layers) == [17, 0]
    assert launch.compiled.brain.q_learning.gamma == 0.41
    assert launch.compiled.brain.q_learning.target_update_frequency == 211
    assert launch.compiled.brain.q_learning.use_double_dqn is False
    assert launch.compiled.brain.optimizer.learning_rate == 0.0019
    assert launch.compiled.brain.replay.capacity == 7001

    effective_brain = launch.effective.effective_brain
    assert effective_brain.q_learning.gamma == 0.73
    assert effective_brain.q_learning.target_update_frequency == 13
    assert effective_brain.q_learning.use_double_dqn is True
    assert effective_brain.optimizer.learning_rate == 0.0007
    assert effective_brain.replay.capacity == 4321
    assert list(effective_brain.architecture.feedforward.hidden_layers) == [17, 0]
    assert launch.effective.options == reference.effective_run.options
    assert launch.effective.authored_options == reference.effective_run.authored_options
    assert launch.effective.exploration == reference.effective_run.exploration
    assert launch.effective.training.model_dump() == reference.get_level(SELECTED).training.model_dump()

    declarations = DeclarationStore.discover(root)
    assert dict(launch.declaration_origins) == {declaration.key: declaration.origin for declaration in declarations.declarations.values()}
    for key, path in locations.items():
        family = key.rsplit("/", 1)[-1]
        scope = SELECTED if key.startswith("levels/") else None
        declaration = declarations.get(family, scope)
        assert declaration is not None
        assert declaration.path == path.resolve()
        assert declaration.line > 0
        assert launch.declaration_origins[key] == f"{path.resolve()}:{declaration.line}"


def test_pack_level_and_multidoc_resolution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catch filename heuristics, wrong level/cache projections and repeated or partial option resolution."""
    root = _make_pack(tmp_path / "original", second_level=True)
    locations = _transport(root, "original")
    reference = UniverseCompiler().compile(root, primary_level=SELECTED, use_cache=False)
    assert not (root / ".compiled").exists()
    resolve_launch = _resolver()
    launch = resolve_launch(root, level_name=SELECTED)
    _assert_launch(launch, root, reference, locations)
    assert (root / ".compiled" / f"universe-{SELECTED}.msgpack").is_file()

    cache_reads: list[str] = []
    read_cache = UniverseCompiler._read_cache_artifact

    def observe_cache(compiler: UniverseCompiler, path: Path) -> Any:
        cached = read_cache(compiler, path)
        if cached is not None:
            cache_reads.append(cached.execution_hash)
        return cached

    monkeypatch.setattr(UniverseCompiler, "_read_cache_artifact", observe_cache)
    direct = resolve_launch(root / "levels" / SELECTED, level_name=None)
    _assert_launch(direct, root, reference, locations)
    assert cache_reads == [reference.execution_hash]
    explicit_direct = resolve_launch(root / "levels" / SELECTED, level_name=SELECTED)
    _assert_launch(explicit_direct, root, reference, locations)

    fingerprints = {launch.compiled.metadata.config_hash}
    for mode in ("renamed", "multidoc"):
        transported_root = _make_pack(tmp_path / mode, second_level=True)
        transported_locations = _transport(transported_root, mode)
        uncached = UniverseCompiler().compile(transported_root, primary_level=SELECTED, use_cache=False)
        assert uncached.execution_hash == reference.execution_hash
        resolved = resolve_launch(transported_root, level_name=SELECTED)
        _assert_launch(resolved, transported_root, uncached, transported_locations)
        _assert_launch(
            resolve_launch(transported_root / "levels" / SELECTED, level_name=None), transported_root, uncached, transported_locations
        )
        fingerprints.add(resolved.compiled.metadata.config_hash)
    assert len(fingerprints) > 1


def test_single_level_pack_needs_no_implicit_primary_fallback(tmp_path: Path) -> None:
    root = _make_pack(tmp_path / "single", second_level=False)
    locations = _transport(root, "multidoc")
    reference = UniverseCompiler().compile(root, primary_level=SELECTED, use_cache=False)
    _assert_launch(_resolver()(root, level_name=None), root, reference, locations)


@pytest.mark.parametrize("level_name", [None, "not_a_declared_level"])
def test_ambiguous_or_unknown_level_is_located(tmp_path: Path, level_name: str | None) -> None:
    root = _make_pack(tmp_path / "ambiguous", second_level=True)
    _transport(root, "renamed")
    UniverseCompiler().compile(root, primary_level=SELECTED, use_cache=False)
    resolve_launch = _resolver()
    with pytest.raises(CompilationError) as error:
        resolve_launch(root, level_name=level_name)
    assert str(root.resolve()) in str(error.value)
    assert re.search(r":\d+\b", str(error.value))


@pytest.mark.parametrize("defect", ["missing_experiment", "missing_training", "duplicate_brain", "conflicting_training"])
def test_invalid_declarations_refuse_with_source_location(tmp_path: Path, defect: str) -> None:
    root = _make_pack(tmp_path / defect, second_level=True)
    _transport(root, "renamed")
    UniverseCompiler().compile(root, primary_level=SELECTED, use_cache=False)
    resolve_launch = _resolver()
    declarations = DeclarationStore.discover(root)
    family = "experiment" if defect == "missing_experiment" else "brain" if defect == "duplicate_brain" else "training"
    scope = None if family in {"experiment", "brain"} else SELECTED
    declaration = declarations.get(family, scope)
    assert declaration is not None
    duplicate: Path | None = None
    if defect.startswith("missing_"):
        declaration.path.unlink()
    else:
        duplicate = declaration.path.parent / "collision.yaml"
        document = yaml.safe_load(declaration.path.read_text(encoding="utf-8"))
        if defect == "conflicting_training":
            document["training"]["seed"] = 43
        _dump(duplicate, [document])

    with pytest.raises(CompilationError) as error:
        resolve_launch(root, level_name=SELECTED)
    assert family in str(error.value).lower()
    assert str(root.resolve()) in str(error.value)
    assert re.search(r":\d+\b", str(error.value))
    if duplicate is not None:
        assert str(duplicate.resolve()) in str(error.value)
