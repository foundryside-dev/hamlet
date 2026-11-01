"""Immutable results for accepted recording work and durable drain failures."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

LEGACY_RECORDING_RUN = "townlet:legacy-recording:v1"
StorageMode = Literal["file_only", "indexed"]


class RecordingPublicationError(RuntimeError):
    """Read-only observations of a failed, non-atomic publication."""

    def __init__(self, *, phase, cause, path, legacy_alias_path, generation, index_id, alias_state, canonical_state, index_state):
        self._phase, self._cause = phase, cause
        self._path, self._legacy_alias_path = path, legacy_alias_path
        self._generation, self._index_id = generation, index_id
        self._alias_state, self._canonical_state, self._index_state = alias_state, canonical_state, index_state
        super().__init__(
            f"Recording publication failed during {phase}: {cause}; artifact={path}; alias={legacy_alias_path}; generation={generation}"
        )

    @property
    def phase(self):
        return self._phase

    @property
    def cause(self):
        return self._cause

    @property
    def path(self):
        return self._path

    @property
    def legacy_alias_path(self):
        return self._legacy_alias_path

    @property
    def generation(self):
        return self._generation

    @property
    def index_id(self):
        return self._index_id

    @property
    def alias_state(self):
        return self._alias_state

    @property
    def canonical_state(self):
        return self._canonical_state

    @property
    def index_state(self):
        return self._index_state


@dataclass(frozen=True)
class RecordingTicket:
    sequence: int
    episode: int
    lane: int


@dataclass(frozen=True)
class RecordingReceipt:
    ticket: RecordingTicket
    status: Literal["persisted", "not_selected", "failed"]
    path: Path | None
    index_id: int | None
    error: Exception | None
    storage_mode: StorageMode


class RecordingDrainError(RuntimeError):
    """Retain all resolutions, actual failures and honest unbound sequences.

    ``receipts`` contains failed tickets; ``resolved_receipts`` also retains
    successful tickets from the same closed admission set. Provisional legacy
    frames have no episode identity until their real end marker arrives.
    """

    def __init__(self, run_id, receipts, errors, unbound_sequences):
        self._run_id = run_id
        self._resolved_receipts = tuple(receipts)
        self._receipts = tuple(receipt for receipt in receipts if receipt.status == "failed")
        self._errors = tuple(errors)
        self._unbound_sequences = tuple(unbound_sequences)
        identities = "; ".join(f"{receipt.ticket}: {receipt.path}: {receipt.error}" for receipt in self._receipts)
        super().__init__(
            f"Recording drain failed for run {run_id!r}; {identities}; unbound sequences={self._unbound_sequences}; {self._errors}"
        )

    @property
    def run_id(self):
        return self._run_id

    @property
    def receipts(self):
        return self._receipts

    @property
    def resolved_receipts(self):
        return self._resolved_receipts

    @property
    def errors(self):
        return self._errors

    @property
    def unbound_sequences(self):
        return self._unbound_sequences
