"""Real declaration compilation through CLI, server metadata and runner admission."""

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
LEVEL = "L1_full_observability"
TRANSPORTS = ("conventional", "renamed_training", "renamed_experiment", "multidocument")
SOURCES = (
    ROOT / "scripts/run_demo.py",
    ROOT / "src/townlet/demo/runner.py",
    ROOT / "src/townlet/config/resolved_launch.py",
    ROOT / "src/townlet/demo/unified_server.py",
    Path(__file__).resolve(),
)


def _resolve(entry, level):
    from townlet.config.resolved_launch import resolve_launch

    return resolve_launch(entry, level_name=level)


def _pack(directory, transport):
    source, target = ROOT / "configs/default_curriculum", directory / "pack"
    for file in source.rglob("*"):
        if file.is_file() and file.suffix in {".yaml", ".yml"} and not any(part.startswith(".") for part in file.relative_to(source).parts):
            copied = target / file.relative_to(source)
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, copied)  # Native authored YAML DATA only.
    baseline = _resolve(target, LEVEL)
    training = target / "levels" / LEVEL / "training.yaml"
    if transport == "renamed_training":
        moved = training.parent / "nested/hyperparameters.yml"
        moved.parent.mkdir()
        training.replace(moved)
    elif transport == "renamed_experiment":
        moved = target / "nested/identity.yml"
        moved.parent.mkdir()
        (target / "experiment.yaml").replace(moved)
    elif transport == "multidocument":
        curriculum = training.parent / "curriculum.yaml"
        training.write_text(training.read_text() + "\n---\n" + curriculum.read_text())
        curriculum.unlink()
    else:
        assert transport == "conventional"
    resolved = _resolve(target, LEVEL)
    assert resolved.root == target.resolve() and resolved.level_name == LEVEL
    assert resolved.effective.training.training_loop.max_episodes == 100000
    assert resolved.compiled.get_level(LEVEL).training.training_loop.max_episodes == 100000
    assert resolved.effective.execution_hash == baseline.effective.execution_hash
    return target, resolved


CLI_CHILD = """
import hashlib, json, logging, runpy, sys
from pathlib import Path
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
request = json.loads(sys.argv[1])
expected = request['sources']
def identity():
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in expected.items())
identity()
from townlet.demo.unified_server import UnifiedServer
import townlet.demo.unified_server as server_module
import townlet.demo.runner as runner_module
import townlet.config.resolved_launch as launch_module
for module in (server_module, runner_module, launch_module):
    assert str(Path(module.__file__).resolve()) in expected
assert torch.get_num_threads() == torch.get_num_interop_threads() == 1
def bounded_start(self):
    training = self._load_training_config()
    run_directory = self._determine_run_directory('T06-fixed-boundary')
    assert self.training_thread is None and self.inference_thread is None
    checkpoint = None
    if self.checkpoint_dir is not None:
        checkpoint = str(self.checkpoint_dir.resolve())
    record = {'root': str(self.config_dir.resolve()), 'level': self.level_name, 'episodes': self.total_episodes,
        'checkpoint': checkpoint, 'port': self.inference_port, 'force': self.force_new_vfs,
        'training_path': str(self.training_config_path.resolve()),
        'authored_episodes': training.training_loop.max_episodes,
        'output_subdir': training.run_metadata.output_subdir, 'run_directory': str(run_directory),
        'logging_level': logging.getLogger().getEffectiveLevel()}
    print('T06_RESULT=' + json.dumps(record), flush=True)
    self.stop()
UnifiedServer.start = bounded_start
sys.argv = [request['script'], *request['argv']]
try:
    runpy.run_path(request['script'], run_name='__main__')
finally:
    identity()
    assert torch.get_num_threads() == torch.get_num_interop_threads() == 1
"""


def _arguments(entry, episodes, checkpoint):
    arguments = [
        "--config",
        str(entry),
        "--level",
        LEVEL,
        "--inference-port",
        "8897",
        "--checkpoint-dir",
        str(checkpoint),
        "--force-new-vfs",
        "--debug",
    ]
    if episodes is not None:
        arguments.extend(("--episodes", str(episodes)))
    return arguments


def _cli(arguments, directory):
    expected = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in SOURCES}
    environment = dict(os.environ)
    environment.update(
        PYTHONPATH=str(ROOT / "src"),
        PYTHONDONTWRITEBYTECODE="1",
        CUDA_VISIBLE_DEVICES="",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
    )
    request = {"script": str(SOURCES[0]), "argv": arguments, "sources": expected}
    result = subprocess.run(
        [sys.executable, "-c", CLI_CHILD, json.dumps(request)],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in SOURCES} == expected
    return result


def _training_path(resolved):
    locator = resolved.declaration_origins[f"levels/{LEVEL}/training"]
    file, line = locator.rsplit(":", 1)
    assert line.isdecimal() and int(line) > 0 and Path(file).is_absolute() and Path(file).is_file()
    return Path(file)


def _runner(entry, directory, episodes):
    from townlet.demo.runner import DemoRunner

    handlers = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
    try:
        with DemoRunner(
            config_dir=entry,
            db_path=directory / "metrics.db",
            checkpoint_dir=directory / "checkpoints",
            max_episodes=episodes,
            level_name=LEVEL,
            force_new_vfs=True,
            max_environment_steps=7,
        ) as runner:
            result = {
                "root": runner.config_dir.resolve(),
                "level": runner.level_name,
                "episodes": runner.max_episodes,
                "force": runner.force_new_vfs,
                "budget": runner.max_environment_steps,
                "training_path": runner.training_config_path,
                "training": runner.training_config.model_dump(),
            }
    finally:
        for number, handler in handlers.items():
            signal.signal(number, handler)
    return result


def _server(entry, directory, episodes):
    from townlet.demo.unified_server import UnifiedServer

    server = UnifiedServer(str(entry), episodes, str(directory / "checkpoints"), 8897, LEVEL, True)
    try:
        training = server._load_training_config()
        result = {
            "root": server.config_dir.resolve(),
            "level": server.level_name,
            "episodes": server.total_episodes,
            "force": server.force_new_vfs,
            "training_path": server.training_config_path,
            "training": training.model_dump(),
            "run_directory": server._determine_run_directory("T06-fixed-boundary"),
        }
        assert server.training_thread is None and server.inference_thread is None
    finally:
        server.stop()
    return result


def _assert_consumer(consumer, entry, resolved, directory, episodes):
    requested = 100000
    if episodes is not None:
        requested = episodes
    if consumer == "cli":
        checkpoint = directory / "checkpoint receipts"
        result = _cli(_arguments(entry, episodes, checkpoint), directory)
        assert result.returncode == 0, f"A compiled valid transport failed actual CLI/server dispatch:\n{result.stdout}\n{result.stderr}"
        records = [line.removeprefix("T06_RESULT=") for line in result.stdout.splitlines() if line.startswith("T06_RESULT=")]
        assert len(records) == 1
        observed = json.loads(records[0])
        assert observed["checkpoint"] == str(checkpoint.resolve()) and observed["port"] == 8897 and observed["force"] is True
        assert observed["authored_episodes"] == 100000 and observed["output_subdir"] == LEVEL and observed["logging_level"] == 10
        assert observed["run_directory"] == f"runs/{LEVEL}/T06-fixed-boundary"
        assert observed["root"] == str(resolved.root) and observed["training_path"] == str(_training_path(resolved))
    else:
        if consumer == "runner":
            observed = _runner(entry, directory, episodes)
            assert observed["budget"] == 7
        else:
            assert consumer == "server"
            observed = _server(entry, directory, requested)
            assert observed["run_directory"] == Path("runs") / LEVEL / "T06-fixed-boundary"
        assert observed["root"] == resolved.root and observed["training_path"] == _training_path(resolved)
        assert observed["training"] == resolved.compiled.get_level(LEVEL).training.model_dump() and observed["force"] is True
    assert observed["episodes"] == requested and observed["level"] == LEVEL
    assert resolved.effective.training.training_loop.max_episodes == 100000


@pytest.mark.parametrize("transport", TRANSPORTS)
@pytest.mark.parametrize("episodes", (3, None))
@pytest.mark.parametrize("consumer", ("cli", "runner", "server"))
def test_real_cli_and_runner_accept_transport_changes(tmp_path, transport, episodes, consumer):
    root, resolved = _pack(tmp_path, transport)
    _assert_consumer(consumer, root, resolved, tmp_path, episodes)


@pytest.mark.parametrize("consumer", ("cli", "runner", "server"))
@pytest.mark.parametrize("transport", ("conventional", "renamed_experiment"))
def test_direct_level_transport_preserves_explicit_selection(tmp_path, consumer, transport):
    root, resolved = _pack(tmp_path, transport)
    entry = root / "levels" / LEVEL
    assert _resolve(entry, LEVEL).root == resolved.root
    _assert_consumer(consumer, entry, resolved, tmp_path, 3)


@pytest.mark.parametrize("missing", ("--config", "--level", "--inference-port"))
def test_cli_required_parser_flags_remain_required(tmp_path, missing):
    root, _ = _pack(tmp_path, "conventional")
    arguments = _arguments(root, 3, tmp_path / "checkpoints")
    offset = arguments.index(missing)
    del arguments[offset : offset + 2]
    result = _cli(arguments, tmp_path)
    assert result.returncode == 2 and missing in result.stderr and "required" in result.stderr
    assert "T06_RESULT=" not in result.stdout


@pytest.mark.parametrize("consumer", ("cli", "runner", "server"))
@pytest.mark.parametrize("invalid", ("missing_training", "conflicting_level"))
def test_invalid_launch_retains_located_compiler_diagnostics(tmp_path, consumer, invalid):
    from townlet.universe.errors import CompilationError

    root, resolved = _pack(tmp_path, "renamed_training")
    entry, level = root, LEVEL
    if invalid == "missing_training":
        _training_path(resolved).unlink()
    else:
        entry, level = root / "levels" / LEVEL, "L3_temporal_mechanics"
    with pytest.raises(CompilationError) as expected:
        _resolve(entry, level)
    if consumer == "cli":
        arguments = _arguments(entry, 3, tmp_path / "checkpoints")
        arguments[arguments.index("--level") + 1] = level
        result = _cli(arguments, tmp_path)
        assert result.returncode == 1 and str(expected.value) in result.stderr
    elif invalid == "missing_training":
        with pytest.raises(CompilationError) as actual:
            if consumer == "runner":
                _runner(entry, tmp_path, 3)
            else:
                _server(entry, tmp_path, 3)
        assert str(actual.value) == str(expected.value)
    else:
        # The existing helpers use LEVEL, so exercise explicit conflicting public selection directly.
        from townlet.demo.runner import DemoRunner
        from townlet.demo.unified_server import UnifiedServer

        handlers = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
        try:
            with pytest.raises(CompilationError):
                if consumer == "runner":
                    with DemoRunner(entry, tmp_path / "metrics.db", tmp_path / "checkpoints", 3, level_name=level):
                        pass
                else:
                    server = UnifiedServer(str(entry), 3, str(tmp_path / "checkpoints"), 8897, level, False)
                    server.stop()
        finally:
            for number, handler in handlers.items():
                signal.signal(number, handler)


@pytest.mark.parametrize("episodes", (3, None))
def test_runner_records_explicit_override_without_mutating_authored_config(tmp_path, episodes):
    from townlet.demo.runner import DemoRunner

    root, resolved = _pack(tmp_path, "conventional")
    handlers = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
    try:
        with DemoRunner(root, tmp_path / "metrics.db", tmp_path / "checkpoints", episodes, level_name=LEVEL) as runner:
            overrides = getattr(runner, "launch_overrides", None)
            assert overrides is not None, "T06 requires an immutable receipt for explicit runner episode overrides"
            expected = {}
            if episodes is not None:
                expected = {"max_episodes": 3}
            assert dict(overrides) == expected
            with pytest.raises(TypeError):
                overrides["max_episodes"] = 9
            assert runner.training_config.training_loop.max_episodes == resolved.effective.training.training_loop.max_episodes == 100000
    finally:
        for number, handler in handlers.items():
            signal.signal(number, handler)


STANDALONE_TRAINING = """run_metadata:
  output_subdir: 'Phase 1: Demo'
recording:
  enabled: false
training:
  version: "1.0"
  seed: 42
  population:
    size: 1
  enabled_affordances: []
  randomize_affordances: false
  enabled_actions: null
  q_learning:
    use_double_dqn: true
    gamma: 0.9
    learning_rate: 0.001
    target_update_frequency: 1
  replay_buffer:
    capacity: 10
    batch_size: 1
    min_size: 1
  exploration:
    epsilon_start: 1.0
    epsilon_end: 0.1
    epsilon_decay: 0.9
  intrinsic:
    rnd:
      feature_dim: 1
      learning_rate: 0.001
    annealing:
      threshold: 1.0
      decay_rate: 0.5
      min_weight: 0.0
    initial_weight: 0.1
    min_survival_fraction: 0.1
    survival_window: 1
  training_loop:
    max_episodes: 1
    max_steps_per_episode: 1
    train_frequency: 1
    sequence_length: 1
    max_grad_norm: 1.0
    checkpointing:
      interval: 1
  curriculum:
    strategy: static
"""


def _standalone_training(directory):
    root = directory / "standalone"
    training = root / "levels" / LEVEL / "training.yaml"
    training.parent.mkdir(parents=True)
    training.write_text(STANDALONE_TRAINING)
    return root, training


def _assert_no_server_resources(server, checkpoint, handlers):
    import logging

    assert not checkpoint.exists()
    assert not (checkpoint.parent / "config_snapshot").exists()
    assert not (checkpoint.parent / "training.log").exists()
    assert server.training_thread is None and server.inference_thread is None
    assert not getattr(server, "_file_handler", None)
    assert tuple(logging.getLogger().handlers) == handlers


def _forbid_server_resources(server, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Incomplete launch reached a server resource side effect")

    for name in ("_determine_run_directory", "_persist_config_snapshot", "_setup_file_logging"):
        monkeypatch.setattr(server, name, forbidden)


@pytest.mark.parametrize("direct_level", (False, True))
def test_server_standalone_training_preserves_prestart_metadata(tmp_path, direct_level):
    from townlet.config.training_v2_config import load_training_v2_config
    from townlet.demo.unified_server import UnifiedServer

    root, training_path = _standalone_training(tmp_path)
    expected = load_training_v2_config(training_path.parent)
    assert expected.run_metadata.output_subdir == "Phase 1: Demo"
    assert expected.training_loop.max_episodes == 1
    entry = training_path.parent if direct_level else root
    server = UnifiedServer(str(entry), 10, str(tmp_path / "checkpoints"), 8897, LEVEL, True)
    try:
        assert server._training_config is None, "Conventional construction must preserve lazy training validation"
        assert server.resolved_launch is None
        assert server.training_config_origin is None
        assert server.config_dir == root.resolve() and server.level_name == LEVEL
        assert server.training_config_path == training_path.resolve()
        training = server._load_training_config()
        assert training.model_dump() == expected.model_dump()
        assert server._load_training_config() is training
        assert server._determine_run_directory("T06-standalone") == Path("runs/Phase_1_Demo/T06-standalone")
        assert server.resolved_launch is None and server.training_config_origin is None
        assert server.total_episodes == 10 and server.force_new_vfs is True and server.inference_port == 8897
        assert dict(server.launch_request) == {"total_episodes": 10}
        with pytest.raises(TypeError):
            server.launch_request["total_episodes"] = 20
        assert server.training_thread is None and server.inference_thread is None
    finally:
        server.stop()


@pytest.mark.parametrize("explicit_checkpoint", (False, True))
def test_server_cached_standalone_training_cannot_admit_start(tmp_path, monkeypatch, explicit_checkpoint):
    import logging

    from townlet.demo.unified_server import UnifiedServer
    from townlet.universe.error_codes import ErrorCode
    from townlet.universe.errors import CompilationError

    root, _ = _standalone_training(tmp_path)
    checkpoint = tmp_path / "uncreated" / "checkpoints"
    server = UnifiedServer(str(root), 10, str(checkpoint) if explicit_checkpoint else None)
    try:
        training = server._load_training_config()
        assert training.run_metadata.output_subdir == "Phase 1: Demo"
        assert server.resolved_launch is None
        with pytest.raises(CompilationError) as expected:
            _resolve(root, LEVEL)
        assert expected.value.issues and all(issue.code == ErrorCode.DECLARATION_MISSING for issue in expected.value.issues)
        handlers = tuple(logging.getLogger().handlers)
        _forbid_server_resources(server, monkeypatch)
        with pytest.raises(CompilationError) as actual:
            server.start()
        assert actual.value.issues == expected.value.issues
        assert server._load_training_config() is training and server.resolved_launch is None
        if not explicit_checkpoint:
            assert server.checkpoint_dir is None
        _assert_no_server_resources(server, checkpoint, handlers)
    finally:
        server.stop()


@pytest.mark.parametrize("invalid", ("duplicate", "yaml_syntax", "scope", "training_recording", "top_level_recording"))
def test_server_standalone_helper_refuses_nonmissing_diagnostics(tmp_path, monkeypatch, invalid):
    import logging

    from townlet.config.training_v2_config import load_training_v2_config
    from townlet.demo.unified_server import UnifiedServer
    from townlet.universe.error_codes import ErrorCode
    from townlet.universe.errors import CompilationError

    root, training = _standalone_training(tmp_path)
    # A real valid standalone DTO and missing-only discovery qualify the input before corruption.
    assert load_training_v2_config(training.parent).run_metadata.output_subdir == "Phase 1: Demo"
    with pytest.raises(CompilationError) as missing:
        _resolve(root, LEVEL)
    assert missing.value.issues and all(issue.code == ErrorCode.DECLARATION_MISSING for issue in missing.value.issues)
    if invalid == "duplicate":
        shutil.copyfile(training, training.parent / "duplicate-training.yaml")
    elif invalid == "yaml_syntax":
        (training.parent / "broken-sidecar.yaml").write_text("{invalid")
    elif invalid == "scope":
        shutil.copyfile(training, root / "misplaced-training.yaml")
    elif invalid == "training_recording":
        training.write_text(STANDALONE_TRAINING.replace('  version: "1.0"', '  version: "1.0"\n  recording:\n    enabled: not-a-boolean'))
    else:
        assert invalid == "top_level_recording"
        training.write_text(STANDALONE_TRAINING.replace("recording:\n  enabled: false", "recording:\n  enabled: not-a-boolean"))
    with pytest.raises(CompilationError) as expected:
        _resolve(root, LEVEL)
    assert any(issue.code != ErrorCode.DECLARATION_MISSING for issue in expected.value.issues)
    if invalid in {"training_recording", "top_level_recording"}:
        assert any(issue.code == ErrorCode.LEVEL_LOAD_ERROR for issue in expected.value.issues)
    checkpoint = tmp_path / "uncreated" / "checkpoints"
    server = UnifiedServer(str(root), 10, str(checkpoint))
    try:
        handlers = tuple(logging.getLogger().handlers)
        _forbid_server_resources(server, monkeypatch)
        with pytest.raises(CompilationError) as actual:
            server._load_training_config()
        assert actual.value.issues == expected.value.issues
        assert server._training_config is None and server.resolved_launch is None
        with pytest.raises(CompilationError) as actual_start:
            server.start()
        assert actual_start.value.issues == expected.value.issues
        _assert_no_server_resources(server, checkpoint, handlers)
    finally:
        server.stop()


def test_server_standalone_direct_level_conflict_is_located(tmp_path):
    from townlet.demo.unified_server import UnifiedServer
    from townlet.universe.error_codes import ErrorCode
    from townlet.universe.errors import CompilationError

    _, training = _standalone_training(tmp_path)
    with pytest.raises(CompilationError) as actual:
        UnifiedServer(str(training.parent), 10, level_name="L3_temporal_mechanics")
    assert any(issue.code == ErrorCode.DECLARATION_SCOPE and issue.location == f"{training.parent}:1" for issue in actual.value.issues)
    assert not (tmp_path / "checkpoints").exists()


def test_server_standalone_training_validation_remains_lazy(tmp_path):
    from townlet.config.training_v2_config import load_training_v2_config
    from townlet.demo.unified_server import UnifiedServer

    root, training = _standalone_training(tmp_path)
    training.write_text("training: {}\n")
    with pytest.raises(ValueError) as expected:
        load_training_v2_config(training.parent)
    server = UnifiedServer(str(root), 10)
    try:
        assert server._training_config is None
        with pytest.raises(type(expected.value)) as actual:
            server._load_training_config()
        assert str(actual.value) == str(expected.value)
        assert server.resolved_launch is None
    finally:
        server.stop()


def test_server_runtime_admission_replaces_standalone_cache(tmp_path, monkeypatch):
    from townlet.demo.unified_server import UnifiedServer

    root, _ = _standalone_training(tmp_path)
    server = UnifiedServer(str(root), 10)
    try:
        standalone = server._load_training_config()
        assert standalone.run_metadata.output_subdir == "Phase 1: Demo"
        complete, _ = _pack(tmp_path / "complete", "conventional")
        for source in complete.rglob("*"):
            if source.is_file() and source.suffix in {".yaml", ".yml"}:
                target = root / source.relative_to(complete)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)

        class AdmissionBoundaryError(RuntimeError):
            pass

        def admitted_before_resources(timestamp):
            resolved = server.resolved_launch
            assert resolved is not None and resolved.root == root.resolve() and resolved.level_name == LEVEL
            selected = resolved.compiled.get_level(LEVEL).training
            assert server._load_training_config() is selected and selected is not standalone
            assert selected.training_loop.max_episodes == 100000 and selected.run_metadata.output_subdir == LEVEL
            assert server.training_config_origin == resolved.declaration_origins[f"levels/{LEVEL}/training"]
            assert server.training_config_path == _training_path(resolved)
            assert dict(server.launch_request) == {"total_episodes": 10}
            assert server.training_thread is None and server.inference_thread is None and server.checkpoint_dir is None
            raise AdmissionBoundaryError("Complete admission verified before checkpoint naming")

        monkeypatch.setattr(server, "_determine_run_directory", admitted_before_resources)
        with pytest.raises(AdmissionBoundaryError):
            server.start()
        assert server.checkpoint_dir is None and not (root / "config_snapshot").exists()
    finally:
        server.stop()
