"""Helpers for checkpoint metadata and secure loading."""

from __future__ import annotations

import hashlib
import logging
import math
import pickle
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from townlet.universe.compiled import CompiledUniverse

_DIGEST_SUFFIX = ".sha256"
_DIGEST_BUFFER_SIZE = 1024 * 1024  # 1 MiB chunks keep memory bounded

# WS-1 task 5: the single source of truth for the checkpoint payload format.
# Previously hardcoded as a magic `3` at two sites in demo/runner.py.
# 4: THE TOKEN CUT (unit 3 Task 10). `observation_field_uuids` and `observation_dim`
# are DROPPED with their producer (the compiled ObservationSpec, deleted); token nets gate
# on `token_type_schema_hash` and flat nets on `layout_hash`. A version-3 checkpoint
# describes a different observation ABI entirely and refuses loudly (zero backcompat).
CHECKPOINT_FORMAT_VERSION = 4

# The complete DemoRunner artifact. Producers and both consumers share this one
# closed schema: pre-release checkpoints are regenerated, never migrated.
DEMO_CHECKPOINT_KEYS = frozenset(
    {
        "version",
        "episode",
        "timestamp",
        "substrate_metadata",
        "population_state",
        "curriculum_state",
        "affordance_layout",
        "agent_ids",
        "epsilon",
        "training_config",
        "config_dir",
        "config_hash",
        "primary_level",
        "action_dim",
        "meter_count",
        "observation_schema_hash",
        "drive_hash",
        "curriculum_hash",
        "bars_hash",
        "affordances_hash",
        "training_hash",
        "brain_hash",
        "pack_brain_hash",
        "vfs_hash",
        "token_type_schema_hash",
        "layout_hash",
    }
)
SUBSTRATE_METADATA_KEYS = frozenset({"position_dim", "substrate_type"})

logger = logging.getLogger(__name__)


def validate_demo_checkpoint_payload(checkpoint: Mapping[str, Any]) -> None:
    """Validate the exact current outer DemoRunner checkpoint schema."""
    if not isinstance(checkpoint, Mapping):
        raise ValueError(f"Demo checkpoint payload must be a mapping; got {type(checkpoint).__name__}.")

    checkpoint_keys = set(checkpoint)
    if checkpoint_keys != DEMO_CHECKPOINT_KEYS:
        missing = sorted(DEMO_CHECKPOINT_KEYS - checkpoint_keys)
        unknown = sorted(checkpoint_keys - DEMO_CHECKPOINT_KEYS)
        raise ValueError(
            "Demo checkpoint key set mismatch: "
            f"missing={missing}, unknown={unknown}. "
            "This checkpoint payload is no longer supported; retrain from scratch."
        )


def validate_demo_checkpoint_runtime_fields(
    checkpoint: Mapping[str, Any],
    *,
    position_dim: int,
    substrate_type: str,
    num_agents: int,
) -> None:
    """Validate exact outer fields bound to the initialized runtime."""
    substrate_metadata = checkpoint["substrate_metadata"]
    if not isinstance(substrate_metadata, dict):
        raise ValueError("Demo checkpoint substrate_metadata must be a dictionary; " f"got {type(substrate_metadata).__name__}.")
    metadata_keys = set(substrate_metadata)
    if metadata_keys != SUBSTRATE_METADATA_KEYS:
        missing = sorted(SUBSTRATE_METADATA_KEYS - metadata_keys)
        unknown = sorted(metadata_keys - SUBSTRATE_METADATA_KEYS)
        raise ValueError(f"Demo checkpoint substrate_metadata key set mismatch: missing={missing}, unknown={unknown}.")

    checkpoint_position_dim = substrate_metadata["position_dim"]
    if isinstance(checkpoint_position_dim, bool) or not isinstance(checkpoint_position_dim, int):
        raise ValueError("Demo checkpoint substrate_metadata.position_dim must be an integer.")
    if checkpoint_position_dim != position_dim:
        raise ValueError(
            "Demo checkpoint substrate position_dim mismatch: " f"checkpoint={checkpoint_position_dim}, current={position_dim}."
        )

    checkpoint_substrate_type = substrate_metadata["substrate_type"]
    if not isinstance(checkpoint_substrate_type, str):
        raise ValueError("Demo checkpoint substrate_metadata.substrate_type must be a string.")
    if checkpoint_substrate_type != substrate_type:
        raise ValueError(
            "Demo checkpoint substrate type mismatch: " f"checkpoint={checkpoint_substrate_type!r}, current={substrate_type!r}."
        )

    agent_ids = checkpoint["agent_ids"]
    if not isinstance(agent_ids, list) or any(not isinstance(agent_id, str) for agent_id in agent_ids):
        raise ValueError("Demo checkpoint agent_ids must be a list of strings.")
    if len(agent_ids) != num_agents:
        raise ValueError(f"Demo checkpoint agent_ids length mismatch: checkpoint={len(agent_ids)}, current population={num_agents}.")

    epsilon = checkpoint["epsilon"]
    if isinstance(epsilon, bool) or not isinstance(epsilon, int | float) or not math.isfinite(float(epsilon)):
        raise ValueError("Demo checkpoint epsilon must be a finite number.")


def attach_universe_metadata(checkpoint: dict[str, Any], universe: CompiledUniverse) -> None:
    """Add config hash and dimension metadata to a checkpoint payload.

    HIGH-05: Now includes brain_hash for network architecture validation.

    Raises:
        ValueError: If universe is None
    """
    # LOW-05: Explicit None check for universe parameter
    if universe is None:
        raise ValueError("universe parameter cannot be None - compiled universe required for metadata attachment")

    level = universe.get_level(universe.metadata.primary_level)

    checkpoint["config_hash"] = universe.metadata.config_hash
    # D5. The only field separating two levels that collide on every content hash.
    # Stamped here; compared on resume by assert_checkpoint_identity (task 5).
    checkpoint["primary_level"] = universe.metadata.primary_level
    checkpoint["action_dim"] = level.action_metadata.total_actions
    checkpoint["meter_count"] = len(level.meter_metadata.meters)
    checkpoint["observation_schema_hash"] = level.observation_schema_hash
    checkpoint["drive_hash"] = level.drive_hash
    checkpoint["curriculum_hash"] = level.curriculum_hash
    checkpoint["bars_hash"] = level.bars_hash
    checkpoint["affordances_hash"] = level.affordances_hash
    checkpoint["training_hash"] = level.training_hash
    checkpoint["brain_hash"] = universe.brain_hash
    # PDR-0027: the pack baseline beside the effective hash, so a lineage fork (a per-level
    # brain.yaml override) is stated at load time instead of discovered at runtime.
    checkpoint["pack_brain_hash"] = universe.pack_brain_hash
    checkpoint["vfs_hash"] = level.vfs_hash
    # The two TokenSpec hashes ARE the observation identity since the unit-3 cut.
    # `token_type_schema_hash` is the token-net transfer contract (payload-schema
    # contents, MAX_POSITION_RANK, VALUE_BLOCK_WIDTH via the feature names);
    # `layout_hash` is the flat-net contract (capacities, slot bindings, total_dims).
    checkpoint["token_type_schema_hash"] = level.token_type_schema_hash
    checkpoint["layout_hash"] = level.layout_hash


def assert_checkpoint_token_type_schema_hash(checkpoint: Mapping[str, Any], universe: CompiledUniverse) -> None:
    """The TOKEN-NET checkpoint gate (token-obs spec §4): compare the TokenSpec
    type-schema hash — payload-schema CONTENTS (closed-vocabulary members,
    MAX_POSITION_RANK, VALUE_BLOCK_WIDTH, spelled out through the feature names) —
    so an engine vocabulary bump produces this banner, not a shape error deep in
    ``load_state_dict``. Deliberately NOT the layout hash: capacities and slot
    bindings are entity variation, which a token net absorbs by design.

    Used by token nets (``architecture.type='token_set'``).
    """
    level = universe.get_level(universe.metadata.primary_level)
    checkpoint_hash = checkpoint.get("token_type_schema_hash")
    if checkpoint_hash is None:
        raise ValueError("Checkpoint missing token_type_schema_hash; regenerate the checkpoint with the latest compiler.")
    if checkpoint_hash != level.token_type_schema_hash:
        raise ValueError(
            f"Checkpoint token_type_schema_hash mismatch: checkpoint={str(checkpoint_hash)[:16]}..., "
            f"current={level.token_type_schema_hash[:16]}... "
            "The engine's token payload schemas have changed since the checkpoint was created "
            "(a closed-vocabulary member, MAX_POSITION_RANK, or VALUE_BLOCK_WIDTH moved). "
            "Per-type encoder weights are not exchangeable across this boundary; retrain."
        )


def assert_checkpoint_layout_hash(checkpoint: Mapping[str, Any], universe: CompiledUniverse) -> None:
    """The FLAT-NET checkpoint gate capability (token-obs spec §5): compare the
    TokenSpec serialization-layout hash — type order, capacities, slot-binding
    identity, ``total_dims``. A flat reader's dims are positional, so a re-bound
    slot changes what a dim MEANS even at equal width; this hash is the contract
    that catches it. Since the unit-3 cut this is THE flat-reader observation gate:
    the obs-dim and field-uuid legs retired with their producer.
    """
    level = universe.get_level(universe.metadata.primary_level)
    checkpoint_hash = checkpoint.get("layout_hash")
    if checkpoint_hash is None:
        raise ValueError("Checkpoint missing layout_hash; regenerate the checkpoint with the latest compiler.")
    if checkpoint_hash != level.layout_hash:
        raise ValueError(
            f"Checkpoint layout_hash mismatch: checkpoint={str(checkpoint_hash)[:16]}..., "
            f"current={level.layout_hash[:16]}... "
            "The token serialization layout (type order, capacities, slot bindings, total_dims) "
            "has changed since the checkpoint was created. A flat network reads dims positionally "
            "and cannot ride a moved layout."
        )


def assert_checkpoint_dimensions(
    checkpoint: Mapping[str, Any],
    universe: CompiledUniverse,
    *,
    architecture_type: str | None = None,
) -> None:
    """Raise ValueError when checkpoint observation/action dims mismatch universe.

    ``architecture_type`` selects the observation gate (unit-3 cut):

    - ``"token_set"``: the TokenSpec TYPE-SCHEMA hash — the transfer contract.
      Capacities and slot bindings are entity variation a token net absorbs by design,
      so they are deliberately excluded.
    - anything else (a flat reader, ``None`` included): the LAYOUT hash — type order,
      capacities, slot-binding identity, ``total_dims``. A flat reader's dims are
      positional, so a re-bound slot changes what a dim MEANS at equal width.

    The obs-dim and order-sensitive field-uuid legs are GONE: their producer (the
    compiled ``ObservationSpec``) was deleted at the cut.

    Raises:
        ValueError: If universe is None or dimensions mismatch
    """
    # LOW-05: Explicit None check for universe parameter
    if universe is None:
        raise ValueError("universe parameter cannot be None - compiled universe required for dimension validation")

    level = universe.get_level(universe.metadata.primary_level)

    action_dim = checkpoint.get("action_dim")
    if action_dim is not None and action_dim != level.action_metadata.total_actions:
        raise ValueError(f"Checkpoint action_dim mismatch: checkpoint={action_dim}, current={level.action_metadata.total_actions}")

    if architecture_type == "token_set":
        assert_checkpoint_token_type_schema_hash(checkpoint, universe)
    else:
        assert_checkpoint_layout_hash(checkpoint, universe)

    # CRIT-06: Validate drive_hash to ensure reward function consistency
    checkpoint_drive_hash = checkpoint.get("drive_hash")
    if checkpoint_drive_hash is None:
        raise ValueError("Checkpoint missing drive_hash; regenerate the checkpoint with the latest compiler.")
    if level.drive_hash is None:
        raise ValueError("Universe missing drive_hash; ensure DAC config is compiled.")
    if checkpoint_drive_hash != level.drive_hash:
        raise ValueError(
            f"Checkpoint drive_hash mismatch: checkpoint={checkpoint_drive_hash[:16]}..., "
            f"current={level.drive_hash[:16]}... "
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
    if level.curriculum_hash is None:
        raise ValueError("Universe missing curriculum_hash; recompile the config pack.")
    if checkpoint_curriculum_hash != level.curriculum_hash:
        raise ValueError(
            f"Checkpoint curriculum_hash mismatch: checkpoint={checkpoint_curriculum_hash[:16]}..., "
            f"current={level.curriculum_hash[:16]}... "
            "The curriculum configuration has changed since the checkpoint was created."
        )

    checkpoint_bars_hash = checkpoint.get("bars_hash")
    if checkpoint_bars_hash is None:
        raise ValueError("Checkpoint missing bars_hash; regenerate the checkpoint with the latest compiler.")
    if level.bars_hash is None:
        raise ValueError("Universe missing bars_hash; recompile the config pack.")
    if checkpoint_bars_hash != level.bars_hash:
        raise ValueError(
            f"Checkpoint bars_hash mismatch: checkpoint={checkpoint_bars_hash[:16]}..., "
            f"current={level.bars_hash[:16]}... "
            "The bars configuration has changed since the checkpoint was created."
        )

    checkpoint_affordances_hash = checkpoint.get("affordances_hash")
    if checkpoint_affordances_hash is None:
        raise ValueError("Checkpoint missing affordances_hash; regenerate the checkpoint with the latest compiler.")
    if level.affordances_hash is None:
        raise ValueError("Universe missing affordances_hash; recompile the config pack.")
    if checkpoint_affordances_hash != level.affordances_hash:
        raise ValueError(
            f"Checkpoint affordances_hash mismatch: checkpoint={checkpoint_affordances_hash[:16]}..., "
            f"current={level.affordances_hash[:16]}... "
            "The affordances configuration has changed since the checkpoint was created."
        )

    checkpoint_training_hash = checkpoint.get("training_hash")
    if checkpoint_training_hash is None:
        raise ValueError("Checkpoint missing training_hash; regenerate the checkpoint with the latest compiler.")
    if level.training_hash is None:
        raise ValueError("Universe missing training_hash; recompile the config pack.")
    if checkpoint_training_hash != level.training_hash:
        raise ValueError(
            f"Checkpoint training_hash mismatch: checkpoint={checkpoint_training_hash[:16]}..., "
            f"current={level.training_hash[:16]}... "
            "The training configuration has changed since the checkpoint was created."
        )


def surface_brain_lineage(checkpoint: Mapping[str, Any]) -> None:
    """State a brain-lineage fork BEFORE the artifact is used (PDR-0027).

    Legibility, not validation: assert_checkpoint_dimensions still enforces effective
    brain_hash equality for resume. This makes the fork visible to a human loading an
    artifact whose brain diverges from its pack baseline.

    A checkpoint missing pack_brain_hash predates this stamp and RAISES — same rule as
    every other hash here (see the WS-1 task 4 comment in assert_checkpoint_dimensions:
    no `is not None` escapes). Pre-release, zero users: old checkpoints are regenerated,
    not accommodated.
    """
    pack_hash = checkpoint.get("pack_brain_hash")
    effective_hash = checkpoint.get("brain_hash")
    if pack_hash is None:
        raise ValueError("Checkpoint missing pack_brain_hash; regenerate the checkpoint with the latest compiler.")
    if pack_hash != effective_hash:
        logger.warning(
            "brain lineage fork: this checkpoint's effective brain (%s...) diverges from its "
            "pack baseline (%s...) at level %s — a per-level brain.yaml override. It is NOT "
            "interchangeable with unforked artifacts of the same pack (PDR-0027).",
            str(effective_hash)[:16],
            str(pack_hash)[:16],
            checkpoint.get("primary_level"),
        )


def assert_checkpoint_vfs_hash(checkpoint: Mapping[str, Any], universe: CompiledUniverse, *, force_new_vfs: bool) -> bool:
    """Validate checkpoint VFS identity before resume.

    Returns True when the checkpoint may be resumed. Returns False only for an explicit
    force-new-VFS branch request, meaning callers must start fresh and skip state load.
    """
    if universe is None:
        raise ValueError("universe parameter cannot be None - compiled universe required for VFS hash validation")

    level = universe.get_level(universe.metadata.primary_level)

    checkpoint_vfs_hash = checkpoint.get("vfs_hash")
    if checkpoint_vfs_hash is None:
        raise ValueError("Checkpoint missing vfs_hash; regenerate the checkpoint with the latest compiler.")

    if checkpoint_vfs_hash == level.vfs_hash:
        return True

    message = (
        f"Checkpoint vfs_hash mismatch: checkpoint={str(checkpoint_vfs_hash)[:16]}..., "
        f"current={level.vfs_hash[:16]}... "
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
      1b. ``surface_brain_lineage`` (PDR-0027) — states a brain fork before any
         hash leg can raise; requires the ``pack_brain_hash`` stamp;
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

    # PDR-0027: state a lineage fork before any hash leg can raise about it. Placed after
    # the format gate on purpose — a wrong-format checkpoint lacks the stamp entirely, and
    # "unsupported version" is the honest first error there.
    surface_brain_lineage(checkpoint)

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


@dataclass(frozen=True)
class TokenRosterReport:
    """The loud cross-universe roster report (token-obs spec §4): what a token-net
    load actually did, both directions, never silently."""

    #: Type keys present on both sides — their encoder + type-embedding weights loaded.
    loaded_types: tuple[str, ...]
    #: Types the TARGET network has that the checkpoint lacks — left at fresh init.
    cold_started_types: tuple[str, ...]
    #: Types the CHECKPOINT has that the target network lacks — their weights dropped.
    dropped_types: tuple[str, ...]
    #: Non-per-type parameter keys (Q-head, aggregator projections) skipped because
    #: their shapes differ (e.g. a different action_dim) — left at fresh init.
    cold_started_modules: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.cold_started_types and not self.dropped_types and not self.cold_started_modules


def load_token_network_state_by_type(
    network: torch.nn.Module,
    source_state: Mapping[str, torch.Tensor],
) -> TokenRosterReport:
    """Load a TokenSetQNetwork state dict BY TYPE KEY (token-obs spec §4).

    Per-type encoders and type embeddings load for the INTERSECTION of type keys —
    the ``nn.ModuleDict`` keying is the transfer contract (a list indexed by roster
    position would re-bind weights silently). Both mismatch directions are reported
    loudly (warning log + the returned report). A shape mismatch on a SHARED type is
    a payload-schema mismatch — the checkpoint was written by an engine with
    different payload schemas — and REFUSES.

    Non-per-type parameters (aggregator projections, Q-head) transfer mechanically
    when shapes match; a shape mismatch there (a different action_dim or embed dim)
    cold-starts that module and is reported, because the Q-head's values encode the
    source universe's rewards and must be relearned anyway.
    """
    from townlet.agent.networks import TokenSetQNetwork

    if not isinstance(network, TokenSetQNetwork):
        raise ValueError(f"load_token_network_state_by_type requires a TokenSetQNetwork, got {type(network).__name__}")

    def _type_of(key: str) -> str | None:
        for prefix in ("encoders.", "type_embeddings."):
            if key.startswith(prefix):
                return key[len(prefix) :].split(".", 1)[0]
        return None

    target_state = network.state_dict()
    target_types = set(network.token_type_names)
    source_types = {t for key in source_state if (t := _type_of(key)) is not None}

    loaded_types = tuple(sorted(target_types & source_types))
    cold_started_types = tuple(sorted(target_types - source_types))
    dropped_types = tuple(sorted(source_types - target_types))

    merged: dict[str, torch.Tensor] = dict(target_state)
    cold_started_modules: list[str] = []
    for key, source_tensor in source_state.items():
        key_type = _type_of(key)
        if key_type is not None:
            if key_type not in target_types:
                continue  # dropped type — reported below
            target_tensor = target_state[key]
            if target_tensor.shape != source_tensor.shape:
                raise ValueError(
                    f"Token payload-schema mismatch on shared type {key_type!r}: parameter {key!r} is "
                    f"{tuple(source_tensor.shape)} in the checkpoint but {tuple(target_tensor.shape)} in the "
                    "current network. Payload widths are engine constants (spec §1: width is fixed per type "
                    "across all universes), so this checkpoint was written by an engine with different token "
                    "payload schemas. Refusing to load; retrain."
                )
            merged[key] = source_tensor
        else:
            target_tensor_or_none = target_state.get(key)
            if target_tensor_or_none is None or target_tensor_or_none.shape != source_tensor.shape:
                cold_started_modules.append(key)
                continue
            merged[key] = source_tensor

    # Two-way module loudness (task-9 review M2): a non-per-type parameter the TARGET
    # has but the checkpoint does not (e.g. attention projections loading from a mean
    # checkpoint) keeps its fresh init — that is a cold start and must be reported,
    # not silent.
    source_keys = set(source_state)
    for key in target_state:
        if _type_of(key) is None and key not in source_keys:
            cold_started_modules.append(key)
    cold_started_modules.sort()

    network.load_state_dict(merged)
    report = TokenRosterReport(
        loaded_types=loaded_types,
        cold_started_types=cold_started_types,
        dropped_types=dropped_types,
        cold_started_modules=tuple(cold_started_modules),
    )
    if not report.is_clean:
        logger.warning(
            "token-net roster mismatch at cross-universe load: loaded types %s; cold-started types "
            "(in network, not in checkpoint — fresh init) %s; dropped types (in checkpoint, not in "
            "network — weights discarded) %s; cold-started modules (shape mismatch, fresh init) %s.",
            list(report.loaded_types),
            list(report.cold_started_types),
            list(report.dropped_types),
            list(report.cold_started_modules),
        )
    return report


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
