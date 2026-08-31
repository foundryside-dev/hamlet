"""WS-1 task 5 (hamlet-1029f99f4b): the serving path runs the shared identity guard.

Before this task, ``LiveInferenceServer._check_and_load_checkpoint`` verified the file
digest (INTEGRITY: the file is not corrupted) and ran ZERO identity guards (the
checkpoint matches this universe). Measured A/B, 2026-08-11: DemoRunner RAISED on a
vfs-visible mutation while the serving path returned True with no exception — and this
is the tech-demo path, so the wrong-universe agent would have rendered completely
normally.

These tests drive the server headless (``_initialize_components`` +
``_check_and_load_checkpoint``); no uvicorn is started. Every test chdirs into
``tmp_path`` FIRST because the server opens a q-value log in CWD.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.demo.live_inference import LiveInferenceServer
from townlet.training.checkpoint_utils import (
    CHECKPOINT_FORMAT_VERSION,
    attach_universe_metadata,
    persist_checkpoint_digest,
)
from townlet.universe.compiler import UniverseCompiler

# Resolved to an absolute path BEFORE any monkeypatch.chdir moves CWD.
SOURCE_PACK = Path(__file__).resolve().parents[3] / "configs" / "test" / "model_config"
LEVEL = "L0_test"


def _copy_pack(tmp_path: Path, name: str) -> Path:
    """Copy the test pack, stripping every compiled artifact (stale-cache hazard)."""
    dest = tmp_path / name
    shutil.copytree(SOURCE_PACK, dest)
    for compiled_dir in dest.rglob(".compiled"):
        shutil.rmtree(compiled_dir, ignore_errors=True)
    for artifact in dest.rglob("*.msgpack"):
        artifact.unlink()
    return dest


def _mutate_energy_passive(pack: Path) -> None:
    """``bars.yaml`` energy ``depletion.passive`` 0.01 → 0.03 — keep this edit exactly.

    It is pinned because the compiled meter signature is network-visible: observation
    identity and ``vfs_hash`` move while dimensions, the transfer schema and positional
    layout remain unchanged.
    """
    bars_path = pack / "levels" / LEVEL / "bars.yaml"
    data = yaml.safe_load(bars_path.read_text())
    meter = next(m for m in data["bars"]["meters"] if m["name"] == "energy")
    assert meter["depletion"]["passive"] == 0.01, "test pack changed under this pin — re-derive the edit"
    meter["depletion"]["passive"] = 0.03
    bars_path.write_text(yaml.safe_dump(data, sort_keys=False))


def _make_server(pack: Path, checkpoint_dir: Path) -> LiveInferenceServer:
    server = LiveInferenceServer(
        checkpoint_dir=checkpoint_dir,
        level_name=LEVEL,
        port=8799,
        step_delay=0.0,
        total_episodes=10,
        config_dir=pack,
    )
    server._initialize_components()
    return server


def _write_checkpoint(
    checkpoint_dir: Path,
    server: LiveInferenceServer,
    *,
    episode: int = 7,
    filename_episode: int | None = None,
    version: int = CHECKPOINT_FORMAT_VERSION,
    epsilon: float = 0.37,
) -> Path:
    """A checkpoint stamped exactly as DemoRunner stamps one, from the server's universe.

    One weight tensor is deliberately perturbed so a successful load provably CHANGES
    the serving network — otherwise "weights applied" and "weights untouched" are
    indistinguishable when saving from the same network that later loads.
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    assert server.population is not None
    q_state = {k: v.clone() for k, v in server.population.q_network.state_dict().items()}
    first_key = next(iter(q_state))
    q_state[first_key] = q_state[first_key] + 1.0

    assert server.env is not None
    assert server.curriculum is not None
    population_state = server.population.get_checkpoint_state()
    population_state["q_network"] = q_state
    level = server.compiled_universe.get_level(server.compiled_universe.metadata.primary_level)
    checkpoint: dict[str, Any] = {
        "version": version,
        "episode": episode,
        "timestamp": 1.0,
        "substrate_metadata": {
            "position_dim": server.env.substrate.position_dim,
            "substrate_type": type(server.env.substrate).__name__,
        },
        "population_state": population_state,
        "curriculum_state": server.curriculum.checkpoint_state(),
        "affordance_layout": server.env.get_affordance_positions(),
        "agent_ids": server.population.agent_ids,
        "epsilon": epsilon,
        "training_config": level.training.model_dump(),
        "config_dir": str(server.config_dir),
    }
    attach_universe_metadata(checkpoint, server.compiled_universe)

    path = checkpoint_dir / f"checkpoint_ep{filename_episode if filename_episode is not None else episode:05d}.pt"
    torch.save(checkpoint, path)
    persist_checkpoint_digest(path)
    return path


def _q_state_snapshot(server: LiveInferenceServer) -> dict[str, torch.Tensor]:
    assert server.population is not None
    return {k: v.clone() for k, v in server.population.q_network.state_dict().items()}


@pytest.mark.asyncio
async def test_serving_path_accepts_matching_checkpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """B1 — the honest A/A case. Guards must not be over-tight: a checkpoint built via
    ``attach_universe_metadata`` from the same universe loads, weights and all."""
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"

    server = _make_server(pack, checkpoint_dir)
    checkpoint_path = _write_checkpoint(checkpoint_dir, server)

    before = _q_state_snapshot(server)
    loaded = await server._check_and_load_checkpoint()

    assert loaded is True
    assert server.current_checkpoint_path == checkpoint_path
    assert server.current_checkpoint_episode == 7
    # The perturbed weights were actually applied.
    after = _q_state_snapshot(server)
    assert any(not torch.equal(before[k], after[k]) for k in before), "load reported success but no weight changed"


@pytest.mark.asyncio
async def test_serving_path_uses_canonical_top_level_epsilon(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"
    server = _make_server(pack, checkpoint_dir)
    _write_checkpoint(checkpoint_dir, server, epsilon=0.73)

    assert await server._check_and_load_checkpoint() is True
    assert server.current_epsilon == 0.73


@pytest.mark.asyncio
async def test_serving_path_refuses_filename_payload_episode_mismatch_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"
    server = _make_server(pack, checkpoint_dir)
    _write_checkpoint(checkpoint_dir, server, episode=7, filename_episode=8)
    before = _q_state_snapshot(server)

    with pytest.raises(ValueError, match="filename episode mismatch"):
        await server._check_and_load_checkpoint()

    after = _q_state_snapshot(server)
    assert all(torch.equal(before[key], after[key]) for key in before)


@pytest.mark.asyncio
@pytest.mark.parametrize("schema_change", ("missing", "unknown"))
async def test_serving_path_refuses_outer_schema_change_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, schema_change: str
) -> None:
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"
    server = _make_server(pack, checkpoint_dir)
    path = _write_checkpoint(checkpoint_dir, server)
    checkpoint = torch.load(path, weights_only=False)
    if schema_change == "missing":
        checkpoint.pop("epsilon")
    else:
        checkpoint["removed_epsilon"] = 0.5
    torch.save(checkpoint, path)
    persist_checkpoint_digest(path)
    before = _q_state_snapshot(server)

    with pytest.raises(ValueError, match="Demo checkpoint key set mismatch"):
        await server._check_and_load_checkpoint()

    after = _q_state_snapshot(server)
    assert all(torch.equal(before[key], after[key]) for key in before)


@pytest.mark.asyncio
async def test_serving_path_refuses_incomplete_population_payload_before_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"
    server = _make_server(pack, checkpoint_dir)
    path = _write_checkpoint(checkpoint_dir, server)
    checkpoint = torch.load(path, weights_only=False)
    checkpoint["population_state"].pop("target_network")
    torch.save(checkpoint, path)
    persist_checkpoint_digest(path)
    before = _q_state_snapshot(server)

    with pytest.raises(ValueError, match="Population checkpoint key set mismatch"):
        await server._check_and_load_checkpoint()

    after = _q_state_snapshot(server)
    assert all(torch.equal(before[key], after[key]) for key in before)


@pytest.mark.asyncio
async def test_serving_path_refuses_malformed_curriculum_before_network_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"
    server = _make_server(pack, checkpoint_dir)
    path = _write_checkpoint(checkpoint_dir, server)
    checkpoint = torch.load(path, weights_only=False)
    checkpoint["curriculum_state"].pop(next(iter(checkpoint["curriculum_state"])))
    torch.save(checkpoint, path)
    persist_checkpoint_digest(path)
    before = _q_state_snapshot(server)

    with pytest.raises(ValueError, match="curriculum checkpoint key set mismatch"):
        await server._check_and_load_checkpoint()

    after = _q_state_snapshot(server)
    assert all(torch.equal(before[key], after[key]) for key in before)


@pytest.mark.asyncio
async def test_serving_path_refuses_network_action_shape_mismatch_before_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"
    server = _make_server(pack, checkpoint_dir)
    path = _write_checkpoint(checkpoint_dir, server)
    checkpoint = torch.load(path, weights_only=False)
    assert server.env is not None
    action_parameters = [
        key
        for key, tensor in checkpoint["population_state"]["q_network"].items()
        if tensor.ndim > 0 and tensor.shape[0] == server.env.action_dim
    ]
    assert action_parameters, "test network has no action-sized output parameter"
    action_parameter = action_parameters[-1]
    checkpoint["population_state"]["q_network"][action_parameter] = checkpoint["population_state"]["q_network"][action_parameter][:-1]
    torch.save(checkpoint, path)
    persist_checkpoint_digest(path)
    before = _q_state_snapshot(server)

    with pytest.raises(ValueError, match="q_network.*shape mismatch"):
        await server._check_and_load_checkpoint()

    after = _q_state_snapshot(server)
    assert all(torch.equal(before[key], after[key]) for key in before)


@pytest.mark.asyncio
async def test_serving_path_rejects_checkpoint_from_mutated_universe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """B2 — THE pinning test. One vfs-visible YAML value separates the universes; the
    serving path must fail loudly and apply nothing. Before task 5 this returned True
    with no exception (measured, tracker A/B)."""
    monkeypatch.chdir(tmp_path)
    base_pack = _copy_pack(tmp_path, "base")
    mutated_pack = _copy_pack(tmp_path, "mutated")
    _mutate_energy_passive(mutated_pack)

    checkpoint_dir = tmp_path / "ckpts"
    base_server = _make_server(base_pack, checkpoint_dir)
    _write_checkpoint(checkpoint_dir, base_server)

    serving = _make_server(mutated_pack, checkpoint_dir)
    before = _q_state_snapshot(serving)

    with pytest.raises(ValueError, match="vfs_hash mismatch"):
        await serving._check_and_load_checkpoint()

    # No weights applied; the server keeps serving its previous (here: initial) state.
    assert serving.current_checkpoint_path is None
    assert serving.current_checkpoint_episode == 0
    after = _q_state_snapshot(serving)
    assert all(torch.equal(before[k], after[k]) for k in before), "guard raised but weights were still applied"


def test_dimension_checks_provably_cannot_catch_a_universe_swap(tmp_path: Path) -> None:
    """B3 — dimensions and layout stay blind while compiled content identity moves."""
    base_pack = _copy_pack(tmp_path, "base")
    mutated_pack = _copy_pack(tmp_path, "mutated")
    _mutate_energy_passive(mutated_pack)

    base = UniverseCompiler().compile(base_pack, primary_level=LEVEL, use_cache=False)
    mutated = UniverseCompiler().compile(mutated_pack, primary_level=LEVEL, use_cache=False)
    base_level = base.get_level(base.metadata.primary_level)
    mutated_level = mutated.get_level(mutated.metadata.primary_level)

    assert base.metadata.observation_dim == mutated.metadata.observation_dim
    assert base.metadata.action_count == mutated.metadata.action_count
    assert base_level.token_type_schema_hash == mutated_level.token_type_schema_hash
    assert base_level.layout_hash == mutated_level.layout_hash
    assert base_level.observation_schema_hash != mutated_level.observation_schema_hash
    assert base_level.vfs_hash != mutated_level.vfs_hash


def test_unified_server_raises_when_inference_server_never_starts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """B4 — startup propagation. uvicorn (pinned 0.46.0, verified) returns NORMALLY from
    ``serve()`` when lifespan startup fails — which is exactly what happens when the
    identity guard rejects the initial checkpoint inside ``startup()``. Without the
    ``server.started`` check, training runs for hours beside a dead inference server."""
    import uvicorn

    from townlet.demo import live_inference
    from townlet.demo.unified_server import UnifiedServer

    monkeypatch.chdir(tmp_path)

    class _StubInferenceServer:
        def __init__(self, **kwargs: Any) -> None:
            async def _noop_app(scope: Any, receive: Any, send: Any) -> None:  # pragma: no cover - never invoked
                return None

            self.app = _noop_app

    monkeypatch.setattr(live_inference, "LiveInferenceServer", _StubInferenceServer)

    def _make_unified() -> UnifiedServer:
        return UnifiedServer(
            config_dir=str(SOURCE_PACK),
            total_episodes=1,
            checkpoint_dir=str(tmp_path / "ckpts"),
            level_name=LEVEL,
        )

    # Control leg: serve() completes normally WITH a successful startup — no shutdown.
    async def _serve_started(self: uvicorn.Server) -> None:
        self.started = True

    monkeypatch.setattr(uvicorn.Server, "serve", _serve_started)
    healthy = _make_unified()
    healthy._run_inference()
    assert healthy.shutdown_requested is False

    # Failure leg: serve() returns normally but startup never happened — the check must
    # raise, and _run_inference's error handler must request shutdown.
    async def _serve_never_started(self: uvicorn.Server) -> None:
        return None

    monkeypatch.setattr(uvicorn.Server, "serve", _serve_never_started)
    dead = _make_unified()
    dead._run_inference()
    assert dead.shutdown_requested is True


@pytest.mark.asyncio
async def test_serving_path_rejects_wrong_format_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """B5 — a wrong-format checkpoint is refused by name, before anything else is
    trusted to even be present."""
    monkeypatch.chdir(tmp_path)
    pack = _copy_pack(tmp_path, "base")
    checkpoint_dir = tmp_path / "ckpts"

    server = _make_server(pack, checkpoint_dir)
    _write_checkpoint(checkpoint_dir, server, version=2)

    with pytest.raises(ValueError, match="Unsupported checkpoint version"):
        await server._check_and_load_checkpoint()

    assert server.current_checkpoint_path is None
    assert server.current_checkpoint_episode == 0
