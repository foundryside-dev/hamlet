"""Helpers for checkpoint metadata and secure loading."""

from __future__ import annotations

import hashlib
import logging
import pickle
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import torch

from townlet.universe.compiled import CompiledUniverse

_DIGEST_SUFFIX = ".sha256"
_DIGEST_BUFFER_SIZE = 1024 * 1024  # 1 MiB chunks keep memory bounded

# WS-1 task 5: the single source of truth for the checkpoint payload format.
# Previously hardcoded as a magic `3` at two sites in demo/runner.py.
CHECKPOINT_FORMAT_VERSION = 3

logger = logging.getLogger(__name__)


def attach_universe_metadata(checkpoint: dict[str, Any], universe: CompiledUniverse) -> None:
    """Add config hash and dimension metadata to a checkpoint payload.

    HIGH-05: Now includes brain_hash for network architecture validation.

    Raises:
        ValueError: If universe is None
    """
    # LOW-05: Explicit None check for universe parameter
    if universe is None:
        raise ValueError("universe parameter cannot be None - compiled universe required for metadata attachment")

    checkpoint["config_hash"] = universe.metadata.config_hash
    # D5. The only field separating two levels that collide on every content hash.
    # Stamped here; compared on resume by assert_checkpoint_identity (task 5).
    checkpoint["primary_level"] = universe.metadata.primary_level
    checkpoint["observation_dim"] = universe.metadata.observation_dim
    checkpoint["action_dim"] = universe.metadata.action_count
    checkpoint["meter_count"] = universe.metadata.meter_count
    checkpoint["observation_field_uuids"] = [field.uuid for field in universe.observation_spec.fields]
    checkpoint["observation_schema_hash"] = universe.observation_schema_hash
    checkpoint["drive_hash"] = universe.drive_hash
    checkpoint["curriculum_hash"] = universe.curriculum_hash
    checkpoint["bars_hash"] = universe.bars_hash
    checkpoint["affordances_hash"] = universe.affordances_hash
    checkpoint["training_hash"] = universe.training_hash
    checkpoint["brain_hash"] = universe.brain_hash
    checkpoint["vfs_hash"] = universe.vfs_hash


def assert_checkpoint_dimensions(checkpoint: Mapping[str, Any], universe: CompiledUniverse) -> None:
    """Raise ValueError when checkpoint observation/action dims mismatch universe.

    Raises:
        ValueError: If universe is None or dimensions mismatch
    """
    # LOW-05: Explicit None check for universe parameter
    if universe is None:
        raise ValueError("universe parameter cannot be None - compiled universe required for dimension validation")

    obs_dim = checkpoint.get("observation_dim")
    if obs_dim is not None and obs_dim != universe.metadata.observation_dim:
        raise ValueError(f"Checkpoint observation_dim mismatch: checkpoint={obs_dim}, current={universe.metadata.observation_dim}")

    action_dim = checkpoint.get("action_dim")
    if action_dim is not None and action_dim != universe.metadata.action_count:
        raise ValueError(f"Checkpoint action_dim mismatch: checkpoint={action_dim}, current={universe.metadata.action_count}")

    expected_uuids = [field.uuid for field in universe.observation_spec.fields]
    checkpoint_uuids = checkpoint.get("observation_field_uuids")
    if checkpoint_uuids is None:
        raise ValueError("Checkpoint missing observation_field_uuids; regenerate the checkpoint with the latest compiler.")
    # MED-18: UUID comparison is order-sensitive by design - field order matters for observation encoding
    # If UUIDs match but order differs, the checkpoint is incompatible (dimension mapping would be wrong)
    if list(checkpoint_uuids) != expected_uuids:
        raise ValueError(
            "Checkpoint observation field UUIDs mismatch current universe specification. "
            "This comparison is order-sensitive - field ordering must match exactly."
        )

    # CRIT-06: Validate drive_hash to ensure reward function consistency
    checkpoint_drive_hash = checkpoint.get("drive_hash")
    if checkpoint_drive_hash is None:
        raise ValueError("Checkpoint missing drive_hash; regenerate the checkpoint with the latest compiler.")
    if universe.drive_hash is None:
        raise ValueError("Universe missing drive_hash; ensure DAC config is compiled.")
    if checkpoint_drive_hash != universe.drive_hash:
        raise ValueError(
            f"Checkpoint drive_hash mismatch: checkpoint={checkpoint_drive_hash[:16]}..., "
            f"current={universe.drive_hash[:16]}... "
            "The reward function configuration has changed since the checkpoint was created."
        )

    # HIGH-05: Validate brain_hash to ensure network architecture consistency
    checkpoint_brain_hash = checkpoint.get("brain_hash")
    if checkpoint_brain_hash is None:
        raise ValueError("Checkpoint missing brain_hash; regenerate the checkpoint with the latest compiler.")
    if universe.brain_hash is None:
        raise ValueError("Universe missing brain_hash; ensure the brain config is compiled.")
    if checkpoint_brain_hash != universe.brain_hash:
        raise ValueError(
            f"Checkpoint brain_hash mismatch: checkpoint={checkpoint_brain_hash[:16]}..., "
            f"current={universe.brain_hash[:16]}... "
            "The network architecture configuration has changed since the checkpoint was created."
        )

    # WS-1 task 4: the four per-level content hashes. Computed and serialized since the
    # compiler was written, compared by nobody until now — a level's bars/affordances/
    # curriculum/training could change under a checkpoint with no signal at all.
    # These copy the drive_hash pattern deliberately: missing on either side RAISES.
    # Do not reintroduce an `if universe.<x> is not None` escape; that is what made the
    # brain_hash guard above vacuous on one side.
    checkpoint_curriculum_hash = checkpoint.get("curriculum_hash")
    if checkpoint_curriculum_hash is None:
        raise ValueError("Checkpoint missing curriculum_hash; regenerate the checkpoint with the latest compiler.")
    if universe.curriculum_hash is None:
        raise ValueError("Universe missing curriculum_hash; recompile the config pack.")
    if checkpoint_curriculum_hash != universe.curriculum_hash:
        raise ValueError(
            f"Checkpoint curriculum_hash mismatch: checkpoint={checkpoint_curriculum_hash[:16]}..., "
            f"current={universe.curriculum_hash[:16]}... "
            "The curriculum configuration has changed since the checkpoint was created."
        )

    checkpoint_bars_hash = checkpoint.get("bars_hash")
    if checkpoint_bars_hash is None:
        raise ValueError("Checkpoint missing bars_hash; regenerate the checkpoint with the latest compiler.")
    if universe.bars_hash is None:
        raise ValueError("Universe missing bars_hash; recompile the config pack.")
    if checkpoint_bars_hash != universe.bars_hash:
        raise ValueError(
            f"Checkpoint bars_hash mismatch: checkpoint={checkpoint_bars_hash[:16]}..., "
            f"current={universe.bars_hash[:16]}... "
            "The bars configuration has changed since the checkpoint was created."
        )

    checkpoint_affordances_hash = checkpoint.get("affordances_hash")
    if checkpoint_affordances_hash is None:
        raise ValueError("Checkpoint missing affordances_hash; regenerate the checkpoint with the latest compiler.")
    if universe.affordances_hash is None:
        raise ValueError("Universe missing affordances_hash; recompile the config pack.")
    if checkpoint_affordances_hash != universe.affordances_hash:
        raise ValueError(
            f"Checkpoint affordances_hash mismatch: checkpoint={checkpoint_affordances_hash[:16]}..., "
            f"current={universe.affordances_hash[:16]}... "
            "The affordances configuration has changed since the checkpoint was created."
        )

    checkpoint_training_hash = checkpoint.get("training_hash")
    if checkpoint_training_hash is None:
        raise ValueError("Checkpoint missing training_hash; regenerate the checkpoint with the latest compiler.")
    if universe.training_hash is None:
        raise ValueError("Universe missing training_hash; recompile the config pack.")
    if checkpoint_training_hash != universe.training_hash:
        raise ValueError(
            f"Checkpoint training_hash mismatch: checkpoint={checkpoint_training_hash[:16]}..., "
            f"current={universe.training_hash[:16]}... "
            "The training configuration has changed since the checkpoint was created."
        )


def assert_checkpoint_vfs_hash(checkpoint: Mapping[str, Any], universe: CompiledUniverse, *, force_new_vfs: bool) -> bool:
    """Validate checkpoint VFS identity before resume.

    Returns True when the checkpoint may be resumed. Returns False only for an explicit
    force-new-VFS branch request, meaning callers must start fresh and skip state load.
    """
    if universe is None:
        raise ValueError("universe parameter cannot be None - compiled universe required for VFS hash validation")

    checkpoint_vfs_hash = checkpoint.get("vfs_hash")
    if checkpoint_vfs_hash is None:
        raise ValueError("Checkpoint missing vfs_hash; regenerate the checkpoint with the latest compiler.")

    if checkpoint_vfs_hash == universe.vfs_hash:
        return True

    message = (
        f"Checkpoint vfs_hash mismatch: checkpoint={str(checkpoint_vfs_hash)[:16]}..., "
        f"current={universe.vfs_hash[:16]}... "
        "Resume against a different VFS schema is a fork, not a continuation."
    )
    if force_new_vfs:
        logger.warning("%s Starting a new VFS branch without loading checkpoint state.", message)
        return False
    raise ValueError(f"{message} Re-run with --force-new-vfs to start a new VFS branch.")


def assert_checkpoint_identity(checkpoint: Mapping[str, Any], universe: CompiledUniverse, *, force_new_vfs: bool) -> bool:
    """The single identity gate every checkpoint consumer routes through.

    WS-1 task 5 (hamlet-1029f99f4b): both DemoRunner (training resume) and
    LiveInferenceServer (the serving path) call this, so a check added here is
    enforced on both paths at once. Do not hand-roll this chain at a call site.

    Composes, in order:
      1. format version — first, because a wrong-format checkpoint may lack
         ``vfs_hash`` entirely;
      2. ``assert_checkpoint_vfs_hash`` — the only leg that can return ``False``
         (the explicit force-new-VFS branch: start fresh, skip state load);
      3. ``assert_checkpoint_dimensions`` — dims, field UUIDs, ``drive_hash``,
         effective ``brain_hash``, and the four per-level content hashes;
      4. ``primary_level`` equality (D5) — the only field separating two levels
         that collide on every content hash (see
         ``test_two_levels_collide_on_almost_every_identity_field``).

    ``config_hash_warning`` is deliberately absent: a warning is the silent
    acceptance the Provenance-integrity guardrail forbids, and it was deleted
    per PDR-0022. The pack-level surfaces it loosely covered are tracked as a
    known divergence (hamlet-2dde1015fe).

    Returns True when the checkpoint may be resumed. Every mismatch raises
    ValueError except the explicit force-new-VFS branch, which returns False.
    """
    if universe is None:
        raise ValueError("universe parameter cannot be None - compiled universe required for identity validation")

    version = checkpoint.get("version")
    if version != CHECKPOINT_FORMAT_VERSION:
        raise ValueError(
            f"Unsupported checkpoint version: {version}\nExpected version {CHECKPOINT_FORMAT_VERSION}. Please retrain from scratch."
        )

    if not assert_checkpoint_vfs_hash(checkpoint, universe, force_new_vfs=force_new_vfs):
        return False

    assert_checkpoint_dimensions(checkpoint, universe)

    checkpoint_primary_level = checkpoint.get("primary_level")
    if checkpoint_primary_level is None:
        raise ValueError("Checkpoint missing primary_level; regenerate the checkpoint with the latest compiler.")
    if checkpoint_primary_level != universe.metadata.primary_level:
        raise ValueError(
            f"Checkpoint primary_level mismatch: checkpoint={checkpoint_primary_level}, "
            f"current={universe.metadata.primary_level}. "
            "A checkpoint trained at one level must not resume into a different level of the same pack."
        )

    return True


def _digest_path(checkpoint_path: Path) -> Path:
    return checkpoint_path.with_suffix(checkpoint_path.suffix + _DIGEST_SUFFIX)


def _compute_sha256(checkpoint_path: Path) -> str:
    digest = hashlib.sha256()
    with checkpoint_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_DIGEST_BUFFER_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def persist_checkpoint_digest(checkpoint_path: Path) -> str:
    """Compute and store the SHA256 digest alongside the checkpoint file."""

    digest = _compute_sha256(checkpoint_path)
    digest_path = _digest_path(checkpoint_path)
    digest_path.write_text(digest + "\n", encoding="utf-8")
    return digest


def verify_checkpoint_digest(checkpoint_path: Path, *, required: bool = True) -> bool:
    """Verify the checkpoint SHA256 digest.

    A digest sidecar (``<checkpoint>.sha256``) is required by default. The
    ``required=False`` path remains only for explicit local-dev tooling and
    logs a loud warning when the digest is absent.

    LOW-06: The digest file is expected to contain a SHA256 hex digest with optional
    trailing newline. The strip() call removes any trailing whitespace (including
    newlines) to ensure robust comparison with the computed hash.
    """

    digest_path = _digest_path(checkpoint_path)
    if not digest_path.exists():
        if required:
            raise FileNotFoundError(
                f"Missing checksum file for {checkpoint_path}. Expected {digest_path}. "
                "Untrusted checkpoints must ship with a SHA256 digest. "
                "Regenerate the checkpoint with the current Townlet version, or pass required=False "
                "if this is an explicit local-dev path."
            )
        logger.warning("Missing checksum for checkpoint %s (expected %s); skipping verification.", checkpoint_path, digest_path)
        return False

    # LOW-06: strip() removes trailing whitespace (including newline added during write)
    expected = digest_path.read_text(encoding="utf-8").strip()
    actual = _compute_sha256(checkpoint_path)
    if actual != expected:
        raise ValueError(
            f"Checkpoint digest mismatch for {checkpoint_path}. Expected {expected} but computed {actual}. "
            "The file may be corrupted or tampered."
        )
    return True


def safe_torch_load(
    checkpoint_path: Path | str,
    *,
    map_location: torch.device | str | None = None,
    allow_unsafe_pickle: bool = False,
) -> Any:
    """Load a checkpoint under the PyTorch weights-only safety guard.

    By default this loads with ``weights_only=True``: pickled Python objects
    inside the checkpoint cannot execute arbitrary code, and only the
    allowlisted tensor / numpy types are deserialised. This is the only path
    that is safe for checkpoints whose origin is not fully trusted.

    Args:
        checkpoint_path: Path to checkpoint file.
        map_location: Device to map tensors to.
        allow_unsafe_pickle: Explicit opt-in for ``weights_only=False``.
            **Use only for trusted, locally-produced checkpoints** that
            embed custom Python objects (curriculum state, replay buffers,
            etc.). When True, ``torch.load`` will deserialise arbitrary
            pickle payloads, which is equivalent to executing whatever code
            is in the file. A loud WARN is logged for audit visibility.

    Raises:
        RuntimeError: If a checkpoint contains custom Python objects but
            ``allow_unsafe_pickle`` is False (the safe default).

    Note:
        PyTorch 2.6+ requires explicit allowlisting of numpy types when
        ``weights_only=True``. Those types are registered here.
    """
    if allow_unsafe_pickle:
        logger.warning(
            "Loading %s with allow_unsafe_pickle=True (weights_only=False). "
            "This deserialises arbitrary Python objects from the checkpoint and is "
            "ONLY safe for trusted, locally-produced files.",
            checkpoint_path,
        )
        return torch.load(checkpoint_path, map_location=map_location, weights_only=False)

    try:
        # PyTorch 2.6+ requires explicit allowlisting of numpy types
        # Add numpy types to safe globals for PyTorch 2.6+ compatibility

        import numpy as np

        safe_globals: list[Any] = [np.dtype]

        try:
            from numpy._core.multiarray import scalar as np_scalar_new

            safe_globals.append(np_scalar_new)
        except (ImportError, AttributeError):
            # Older numpy versions use numpy.core.multiarray instead
            try:
                from numpy.core.multiarray import scalar as np_scalar_old  # type: ignore[attr-defined]

                safe_globals.append(np_scalar_old)
            except (ImportError, AttributeError):
                pass  # If neither import works, proceed without it

        torch.serialization.add_safe_globals(safe_globals)

        return torch.load(checkpoint_path, map_location=map_location, weights_only=True)
    except (pickle.UnpicklingError, ModuleNotFoundError, AttributeError) as exc:
        raise RuntimeError(
            f"Weights-only load failed for {checkpoint_path}: {type(exc).__name__}: {exc}. "
            "The checkpoint contains custom Python objects that cannot be safely deserialised. "
            "If this checkpoint is trusted and locally produced, pass allow_unsafe_pickle=True "
            "explicitly. Otherwise, regenerate it as a weights-only checkpoint."
        ) from exc
    except RuntimeError as exc:
        message = str(exc)
        if "weights_only" in message or "Weights only" in message:
            raise RuntimeError(
                f"Weights-only load failed for {checkpoint_path}: {message}. "
                "The checkpoint contains custom Python objects. "
                "If this checkpoint is trusted and locally produced, pass allow_unsafe_pickle=True "
                "explicitly. Otherwise, regenerate it as a weights-only checkpoint."
            ) from exc
        raise
