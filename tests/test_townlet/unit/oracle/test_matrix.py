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

# Deliberately DUPLICATED from matrix.py, not imported: these are pins. The
# signatures are the verbatim final-exception lines re-verified at
# oracle-2026-08-13 (0e875d7a) on 2026-08-15 — see DIV-003 in
# docs/oracle/known-divergences.md. A matrix edit that moves a signature must
# consciously move the pin too.
_DIV003_SIGNATURES = {
    "div003_scaled": ("ValueError: Observation field 'obs_position' produced shape (4, 4), expected (4, 2)."),
    "div003_cubic_partial": ("ValueError: Observation field 'obs_local_window' produced shape (4, 125), expected (4, 25)."),
    "div003_rect": "ValueError: Non-square grids not yet supported: 8×6",
}
_DIV003_LEVELS = {
    "div003_scaled": "L1_full_observability",
    "div003_cubic_partial": "L2_partial_observability",
    "div003_rect": "L1_full_observability",
}


def test_matrix_declares_sixteen_cells() -> None:
    """CUDA duplicates of each cell are always declared — never absent from
    the matrix — so the harness can report them SKIPPED instead of silently
    omitting them when --cuda is not passed (spec: 'never silent'). 16 =
    the 10 standing default_curriculum cells + 3 DIV-003 fixture packs x 2
    devices (content 5 step 3)."""
    cells: tuple[Cell, ...] = default_cells()
    assert len(cells) == 16
    standing = [c for c in cells if c.params.pack == "configs/default_curriculum"]
    div003 = [c for c in cells if c.params.pack.startswith("configs/differential/")]
    assert len(standing) == 10
    assert len(div003) == 6
    assert len(standing) + len(div003) == len(cells)
    assert all(c.params.num_agents == 4 for c in cells)
    assert all(c.params.steps == 100 for c in cells)
    assert all(c.params.seed == 42 for c in cells)


def test_cpu_block_precedes_cuda_block() -> None:
    cells = default_cells()
    assert tuple(c.params.device for c in cells[:5]) == ("cpu",) * 5
    assert tuple(c.params.device for c in cells[5:10]) == ("cuda",) * 5
    assert tuple(c.params.level for c in cells[:5]) == LEVELS
    assert tuple(c.params.level for c in cells[5:10]) == LEVELS
    # DIV-003 block appended after the standing matrix, same cpu-then-cuda rule
    assert tuple(c.params.device for c in cells[10:13]) == ("cpu",) * 3
    assert tuple(c.params.device for c in cells[13:16]) == ("cuda",) * 3


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


def test_standing_cells_declare_no_expectations() -> None:
    """Pin: the standing default_curriculum cells still certify bare
    agreement. Expectations live ONLY on the DIV-003 fixture cells — a
    standing cell sprouting one silently would change what exit 0 certifies
    for the whole standing matrix."""
    for c in default_cells():
        if c.params.pack == "configs/default_curriculum":
            assert c.expected is None, f"standing cell {c.cell_id} declares an expectation"


def test_div003_cells_bind_the_registered_signatures() -> None:
    """Every DIV-003 cell binds DIV-003 with the verbatim final-exception
    line re-verified at the oracle tag, on the level whose crash it is. A
    drifted signature would quietly turn DIVERGED_AS_REGISTERED into
    OLD_SIDE_ERROR (fail-closed, but for the wrong stated reason) — or, if
    loosened, widen what the suppression can match (PDR-0040: loosen nothing
    without a new adversarial pass)."""
    div003 = [c for c in default_cells() if c.params.pack.startswith("configs/differential/")]
    assert {Path(c.params.pack).name for c in div003} == set(_DIV003_SIGNATURES)
    for c in div003:
        name = Path(c.params.pack).name
        assert c.expected is not None, f"{c.cell_id} declares no expectation"
        assert c.expected.register_ref == "DIV-003"
        assert c.expected.old_stderr_substring == _DIV003_SIGNATURES[name]
        assert c.params.level == _DIV003_LEVELS[name]


def test_div003_fixture_packs_vary_only_the_declared_axis() -> None:
    """Trial-001 discipline: a fixture pack is default_curriculum with ONE
    axis moved. Every yaml except stratum.yaml (the moved axis) and
    experiment.yaml (name + single-level list) must be byte-identical to its
    default_curriculum counterpart, and the pack carries exactly its declared
    level. A fixture that drifted measures something other than the
    registered crash."""
    root = Path(__file__).resolve().parents[4]
    base = root / "configs" / "default_curriculum"
    for pack_name, level in _DIV003_LEVELS.items():
        pack = root / "configs" / "differential" / pack_name
        yamls = sorted(p.relative_to(pack) for p in pack.rglob("*.yaml"))
        assert yamls, f"{pack_name}: pack missing or empty"
        level_dirs = {p.parts[1] for p in yamls if p.parts[0] == "levels"}
        assert level_dirs == {level}, f"{pack_name}: levels {level_dirs} != {{{level!r}}}"
        for rel in yamls:
            counterpart = base / rel
            assert counterpart.exists(), f"{pack_name}/{rel} has no default_curriculum counterpart"
            if rel.name in ("stratum.yaml", "experiment.yaml"):
                continue
            assert (pack / rel).read_bytes() == counterpart.read_bytes(), f"{pack_name}/{rel} drifted from default_curriculum"
        assert (pack / "stratum.yaml").read_bytes() != (
            base / "stratum.yaml"
        ).read_bytes(), f"{pack_name}: stratum.yaml does not move the declared axis"


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
