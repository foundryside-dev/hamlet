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

    It is pinned BECAUSE it is vfs-VISIBLE: ``vfs_hash`` moves while observation_dim,
    action_count and observation_schema_hash do not (plan §3 H4). Do not harmonize it
    with task 4's vfs-INVISIBLE ``initial`` edit — they look like duplicates and are
    deliberate opposites.
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
    version: int = CHECKPOINT_FORMAT_VERSION,
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

    checkpoint: dict[str, Any] = {
        "version": version,
        "episode": episode,
        "timestamp": 1.0,
        "population_state": {"q_network": q_state},
    }
    assert server.compiled_universe is not None
    attach_universe_metadata(checkpoint, server.compiled_universe)

    path = checkpoint_dir / f"checkpoint_ep{episode:05d}.pt"
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
    """B3 — anti-simplification pin: across the B2 edit, observation_dim, action_count
    AND observation_schema_hash are identical while vfs_hash differs. A dimension check
    therefore cannot catch a universe swap; the identity guard is not replaceable by
    something cheaper."""
    base_pack = _copy_pack(tmp_path, "base")
    mutated_pack = _copy_pack(tmp_path, "mutated")
    _mutate_energy_passive(mutated_pack)

    base = UniverseCompiler().compile(base_pack, primary_level=LEVEL, use_cache=False)
    mutated = UniverseCompiler().compile(mutated_pack, primary_level=LEVEL, use_cache=False)

    assert base.metadata.observation_dim == mutated.metadata.observation_dim
    assert base.metadata.action_count == mutated.metadata.action_count
    # EXPECTED TO FLIP under WS-1(ii): when observation_schema_hash coverage widens this
    # equality breaks — that is hash coverage improving, not a regression. Re-point the
    # witness at whichever hash is still blind then; do not delete the test.
    assert base.observation_schema_hash == mutated.observation_schema_hash
    assert base.vfs_hash != mutated.vfs_hash


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
            config_dir=str(tmp_path),
            total_episodes=1,
            checkpoint_dir=str(tmp_path / "ckpts"),
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
