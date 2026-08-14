"""The declared comparison matrix — explicit cells, no discovery magic (WS-7)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from townlet.oracle.matrix import Cell, RegisteredDivergence, default_cells

LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)


def test_default_matrix_declares_all_ten_cells() -> None:
    """CUDA duplicates of each cell are always declared — never absent from
    the matrix — so the harness can report them SKIPPED instead of silently
    omitting them when --cuda is not passed (spec: 'never silent')."""
    cells: tuple[Cell, ...] = default_cells()
    assert len(cells) == 10
    assert all(c.params.pack == "configs/default_curriculum" for c in cells)
    assert all(c.params.num_agents == 4 for c in cells)
    assert all(c.params.steps == 100 for c in cells)
    assert all(c.params.seed == 42 for c in cells)


def test_cpu_block_precedes_cuda_block() -> None:
    cells = default_cells()
    assert tuple(c.params.device for c in cells[:5]) == ("cpu",) * 5
    assert tuple(c.params.device for c in cells[5:]) == ("cuda",) * 5
    assert tuple(c.params.level for c in cells[:5]) == LEVELS
    assert tuple(c.params.level for c in cells[5:]) == LEVELS


def test_cell_id_is_unique_and_readable() -> None:
    cells = default_cells()
    ids = [c.cell_id for c in cells]
    assert len(set(ids)) == len(ids)
    assert "default_curriculum:L0_0_minimal:cpu:seed42" in ids


# --- RegisteredDivergence: the declared binding to a register entry ----------
#
# hamlet-56ec575ae2 / PDR-0037: a suppression mechanism is a machine for
# manufacturing false AGREEs if it is loose. Narrowness is enforced at
# DECLARATION time — a weak binding must be unconstructable, not merely
# discouraged.

_GOOD_SIGNATURE = "RuntimeError: oracle cannot reset this substrate"


def test_registered_divergence_accepts_a_narrow_declaration() -> None:
    expected = RegisteredDivergence(register_ref="DIV-003", old_stderr_substring=_GOOD_SIGNATURE)
    assert expected.register_ref == "DIV-003"


@pytest.mark.parametrize("bad_ref", ["", "DIV-3", "div-003", "DIV-0034", "hamlet-56ec575ae2", "DIV-003 "])
def test_registered_divergence_rejects_malformed_refs(bad_ref: str) -> None:
    with pytest.raises(ValueError, match="register_ref"):
        RegisteredDivergence(register_ref=bad_ref, old_stderr_substring=_GOOD_SIGNATURE)


@pytest.mark.parametrize(
    "weak",
    [
        "",
        "   ",
        "Error",
        "RuntimeError",
        "RuntimeError:",  # adversarial finding: the colon defeated the bare-identifier regex
        "AttributeError :",
        "NotImplementedError:",
        "E: x",  # short but not an identifier — pins the length floor itself
        "              ",  # 14 chars of whitespace — pins the strip before the floor
    ],
)
def test_registered_divergence_rejects_short_signatures(weak: str) -> None:
    """An empty, near-empty, or exception-type-only signature matches every
    crash (of that type) — the exact false-pass machine the adversarial brief
    exists to prevent."""
    with pytest.raises(ValueError, match="signature"):
        RegisteredDivergence(register_ref="DIV-003", old_stderr_substring=weak)


@pytest.mark.parametrize(
    "boilerplate",
    [
        "Traceback (most",
        "most recent call last",
        "Traceback (most recent call last):",
        # adversarial finding: a SUPERSTRING containing the whole header also
        # appears in every multi-line traceback; `sig in BP` alone missed it
        "XX Traceback (most recent call last): YY",
    ],
)
def test_registered_divergence_rejects_traceback_boilerplate(boilerplate: str) -> None:
    """A signature present in EVERY Python traceback cannot distinguish the
    registered crash from any crash; it must be unconstructable."""
    with pytest.raises(ValueError, match="boilerplate"):
        RegisteredDivergence(register_ref="DIV-003", old_stderr_substring=boilerplate)


def test_registered_divergence_rejects_unicode_digit_refs() -> None:
    """\\d alone matches Unicode decimal digits; a ref like 'DIV-٠٠٣' would
    construct a binding no ASCII register heading can ever satisfy."""
    with pytest.raises(ValueError, match="register_ref"):
        RegisteredDivergence(register_ref="DIV-٠٠٣", old_stderr_substring=_GOOD_SIGNATURE)


def test_default_cells_declare_no_expectations_yet() -> None:
    """Pin: expectations arrive with the DIV-003 matrix cells (content 5 step 3),
    not before. A default cell sprouting one silently would change what exit 0
    certifies for the whole standing matrix."""
    assert all(c.expected is None for c in default_cells())


def _register_sections() -> dict[str, str]:
    """known-divergences.md split into {DIV-NNN: section body}."""
    register = Path(__file__).resolve().parents[4] / "docs" / "oracle" / "known-divergences.md"
    sections: dict[str, str] = {}
    current: str | None = None
    for line in register.read_text().splitlines():
        m = re.match(r"^## (DIV-\d{3})\b", line)
        if m:
            current = m.group(1)
            sections[current] = ""
        elif line.startswith("## "):
            current = None
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def test_declared_register_refs_exist_in_the_register() -> None:
    """Every RegisteredDivergence declared in the matrix must point at a real
    `## DIV-NNN` entry in docs/oracle/known-divergences.md — a ref to a
    nonexistent entry is filing to /dev/null (PDR-0028). Vacuous while no cell
    declares one; arms itself the moment DIV-003 cells land."""
    entries = set(_register_sections())
    declared = {c.expected.register_ref for c in default_cells() if c.expected is not None}
    assert declared <= entries, f"matrix declares refs with no register entry: {sorted(declared - entries)}"


def test_declared_register_refs_bind_entries_with_the_matching_harness_shape() -> None:
    """A binding certifies ONE diff shape (old side crashes, no trace; new
    side runs), so the entry it names must declare that same shape via a
    machine-readable `Harness shape: old-side-crash` line. Prevents the
    typo-bind: certifying 'DIVERGED_AS_REGISTERED (DIV-001)' where DIV-001's
    registered shape is checkpoint-boundary and cannot manifest in a trace.
    Vacuous while no cell declares an expectation; arms with DIV-003."""
    sections = _register_sections()
    for cell in default_cells():
        if cell.expected is None:
            continue
        ref = cell.expected.register_ref
        assert ref in sections, f"{ref} has no register entry"
        assert "Harness shape: old-side-crash" in sections[ref], (
            f"cell {cell.cell_id} binds {ref}, but that entry does not declare "
            f"`Harness shape: old-side-crash` — either the binding names the wrong "
            f"entry, or the entry predicts a diff shape this binding cannot certify"
        )
