"""The declared comparison matrix — explicit cells, no discovery magic (WS-7)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from townlet.oracle.matrix import Cell, RegisteredDivergence, RegisteredHashDivergence, default_cells

LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)

# Deliberately DUPLICATED from matrix.py, not imported: these are pins. A
# matrix edit that changes a block must consciously move the pin too.
# The differential packs entered as the DIV-003 crash cells (signatures
# re-verified at oracle-2026-08-13); DIV-003 retired when the oracle moved
# forward to oracle-2026-08-17 (4222a917, PDR-0074), so they are now plain
# standing cells and carry no signature.
_DIFFERENTIAL_LEVELS = {
    "div003_scaled": "L1_full_observability",
    "div003_cubic_partial": "L2_partial_observability",
    "div003_rect": "L1_full_observability",
}
# The only runnable packs whose vfs_profiles.yaml declares variables — the
# cells that can see unit 3 (hamlet-f0ed709ecf) split the obs_vfs block.
_PROFILE_VARIABLE_CELLS = {
    "configs/test/items_smoke": "L0_smoke",
    "configs/test/effects_smoke": "L0_effects",
}


def test_matrix_declares_twenty_cells() -> None:
    """CUDA duplicates of each cell are always declared — never absent from
    the matrix — so the harness can report them SKIPPED instead of silently
    omitting them when --cuda is not passed (spec: 'never silent'). 20 =
    the 10 standing default_curriculum cells + 3 differential packs x 2
    devices + 2 profile-variable packs x 2 devices (PDR-0074)."""
    cells: tuple[Cell, ...] = default_cells()
    assert len(cells) == 20
    standing = [c for c in cells if c.params.pack == "configs/default_curriculum"]
    differential = [c for c in cells if c.params.pack.startswith("configs/differential/")]
    profile = [c for c in cells if c.params.pack in _PROFILE_VARIABLE_CELLS]
    assert len(standing) == 10
    assert len(differential) == 6
    assert len(profile) == 4
    assert len(standing) + len(differential) + len(profile) == len(cells)
    assert all(c.params.num_agents == 4 for c in cells)
    assert all(c.params.steps == 100 for c in cells)
    assert all(c.params.seed == 42 for c in cells)


def test_cpu_block_precedes_cuda_block() -> None:
    cells = default_cells()
    assert tuple(c.params.device for c in cells[:5]) == ("cpu",) * 5
    assert tuple(c.params.device for c in cells[5:10]) == ("cuda",) * 5
    assert tuple(c.params.level for c in cells[:5]) == LEVELS
    assert tuple(c.params.level for c in cells[5:10]) == LEVELS
    # differential block appended after the standing matrix, same cpu-then-cuda rule
    assert tuple(c.params.device for c in cells[10:13]) == ("cpu",) * 3
    assert tuple(c.params.device for c in cells[13:16]) == ("cuda",) * 3
    # profile-variable block last, same rule
    assert tuple(c.params.device for c in cells[16:18]) == ("cpu",) * 2
    assert tuple(c.params.device for c in cells[18:20]) == ("cuda",) * 2


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


def test_standing_and_differential_cells_declare_nothing_at_this_tag() -> None:
    """Pin (PDR-0074): the sixteen non-profile cells certify bare agreement —
    no `expected`, no `pack_divergence`, no `hash_divergence` — so for them
    exit 0 means AGREE, not "diverged exactly as registered". A declaration
    sprouting on one of them silently changes what exit 0 certifies; it
    returns only with a register entry that needs it (PDR-0037)."""
    for c in default_cells():
        if c.params.pack in _PROFILE_VARIABLE_CELLS:
            continue
        assert c.expected is None, f"{c.cell_id} declares an old-side-crash expectation"
        assert c.pack_divergence is None, f"{c.cell_id} declares a pack divergence"
        assert c.hash_divergence is None, f"{c.cell_id} declares a hash divergence"


def test_profile_variable_cells_bind_div006_narrowly() -> None:
    """DIV-006 (PDR-0075) is hash-only on the four profile-variable cells: exactly the
    three DERIVED hashes measured to move, no RAW hash, and a pack divergence only where
    the frozen fixture actually differs — effects_smoke under DIV-006 (its fixture is held
    at the pre-`semantic_type` schema), items_smoke under DIV-007 (its fixture keeps the
    stale, never-loaded levels/L0_smoke/brain.yaml stub the PDR-0027 cut deleted from the
    live pack)."""
    profile = [c for c in default_cells() if c.params.pack in _PROFILE_VARIABLE_CELLS]
    assert len(profile) == 4
    for c in profile:
        assert c.expected is None
        assert c.hash_divergence is not None and c.hash_divergence.register_ref == "DIV-006"
        assert c.hash_divergence.declared == {"observation_schema_hash", "variable_schema_hash", "vfs_hash"}
        if c.params.pack == "configs/test/effects_smoke":
            assert c.pack_divergence == "DIV-006"
        else:
            assert c.pack_divergence == "DIV-007", f"{c.cell_id}: items_smoke's fixture keeps the deleted brain.yaml stub (DIV-007)"


def test_differential_cells_run_their_declared_levels() -> None:
    differential = [c for c in default_cells() if c.params.pack.startswith("configs/differential/")]
    assert {Path(c.params.pack).name for c in differential} == set(_DIFFERENTIAL_LEVELS)
    for c in differential:
        assert c.params.level == _DIFFERENTIAL_LEVELS[Path(c.params.pack).name]


def test_profile_variable_cells_are_the_packs_with_a_populated_obs_vfs_block() -> None:
    """The profile-variable cells exist to see unit 3 (hamlet-f0ed709ecf). A
    pack in this block whose vfs_profiles.yaml declares no variables would be
    a cell that reads green about that cut while measuring nothing — the
    silent-and-green failure PDR-0052 names. So each declared pack must
    actually declare at least one profile variable, at the level the cell
    runs."""
    import yaml

    root = Path(__file__).resolve().parents[4]
    profile = [c for c in default_cells() if c.params.pack in _PROFILE_VARIABLE_CELLS]
    assert {c.params.pack for c in profile} == set(_PROFILE_VARIABLE_CELLS)
    for c in profile:
        assert c.params.level == _PROFILE_VARIABLE_CELLS[c.params.pack]
        doc = yaml.safe_load((root / c.params.pack / "vfs_profiles.yaml").read_text())

        def count(node: object) -> int:
            if isinstance(node, dict):
                own = len(node["variables"]) if isinstance(node.get("variables"), list) else 0
                return own + sum(count(v) for v in node.values())
            if isinstance(node, list):
                return sum(count(v) for v in node)
            return 0

        assert count(doc) > 0, f"{c.params.pack} declares no profile variables — it cannot see the obs_vfs split"


def test_differential_packs_vary_only_the_declared_axis() -> None:
    """Trial-001 discipline: a fixture pack is default_curriculum with ONE
    axis moved. Every yaml except stratum.yaml (the moved axis) and
    experiment.yaml (name + single-level list) must be byte-identical to its
    default_curriculum counterpart, and the pack carries exactly its declared
    level. A fixture that drifted measures something other than the
    registered crash (DIV-003, retired) and now something other than the
    substrate axis the cell exists to exercise."""
    root = Path(__file__).resolve().parents[4]
    base = root / "configs" / "default_curriculum"
    for pack_name, level in _DIFFERENTIAL_LEVELS.items():
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
    declares one (as at oracle-2026-08-17); armed the moment a cell binds."""
    entries = set(_register_sections())
    declared = {c.expected.register_ref for c in default_cells() if c.expected is not None}
    declared |= {c.hash_divergence.register_ref for c in default_cells() if c.hash_divergence is not None}
    declared |= {c.pack_divergence for c in default_cells() if c.pack_divergence is not None}
    assert declared <= entries, f"matrix declares refs with no register entry: {sorted(declared - entries)}"


def test_declared_register_refs_bind_entries_with_the_matching_harness_shape() -> None:
    """A binding certifies ONE diff shape (old side crashes, no trace; new
    side runs), so the entry it names must declare that same shape via a
    machine-readable `Harness shape: old-side-crash` line. Prevents the
    typo-bind: certifying 'DIVERGED_AS_REGISTERED (DIV-001)' where DIV-001's
    registered shape is checkpoint-boundary and cannot manifest in a trace.
    Vacuous while no cell declares an expectation; arms the moment one does."""
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


def test_hash_divergence_bindings_bind_entries_with_the_hash_only_shape() -> None:
    """The second shape gets the same typo-bind guard as the first.

    A `RegisteredHashDivergence` certifies "provenance moved as registered,
    behaviour did not". Binding it to an entry that predicts an old-side crash
    (or a checkpoint-boundary entry that cannot manifest in a trace at all)
    would certify the wrong thing, so the entry must say `Harness shape:
    hash-only` in its own text.
    """
    sections = _register_sections()
    for cell in default_cells():
        if cell.hash_divergence is None:
            continue
        ref = cell.hash_divergence.register_ref
        assert ref in sections, f"{ref} has no register entry"
        assert "Harness shape: hash-only" in sections[ref], (
            f"cell {cell.cell_id} binds {ref} as a hash-only divergence, but that entry " f"does not declare `Harness shape: hash-only`"
        )


def test_a_cell_never_declares_both_divergence_shapes() -> None:
    """The two shapes are mutually exclusive by construction, and saying both
    would be incoherent rather than merely redundant: the crash shape asserts
    the old side produced NO trace, and the hash shape adjudicates the hashes
    of a trace the old side DID produce. A cell claiming both is a declaration
    error, not a stricter cell.
    """
    for cell in default_cells():
        assert not (
            cell.expected is not None and cell.hash_divergence is not None
        ), f"cell {cell.cell_id} declares both an old-side-crash divergence and a hash-only one"


def test_hash_divergence_declarations_are_enumerated_not_wildcards() -> None:
    """PDR-0033: a suppression mechanism is a machine for manufacturing false
    AGREEs if it is loose. Construction rejects the loose forms — an empty
    field set (a wildcard by another name), duplicates, and any entry that is
    not a provenance hash field.
    """
    with pytest.raises(ValueError, match="at least one"):
        RegisteredHashDivergence(register_ref="DIV-004", hash_fields=())
    with pytest.raises(ValueError, match="duplicates"):
        RegisteredHashDivergence(register_ref="DIV-004", hash_fields=("vfs_hash", "vfs_hash"))
    with pytest.raises(ValueError, match="not a provenance hash field"):
        RegisteredHashDivergence(register_ref="DIV-004", hash_fields=("vfs_hash", "observation_schema"))
    with pytest.raises(ValueError, match="DIV-004"):
        RegisteredHashDivergence(register_ref="div-4", hash_fields=("vfs_hash",))


# --- RegisteredStreamDivergence: the third declared shape, built for DIV-008 ---
#
# DIV-008 (the token-observation cut) changes the obs stream while keeping
# actions/dones/rewards byte-exact under scripted actions. This declares WHICH
# streams are permitted to diverge; undeclared streams diverging keeps the cell red.


def test_stream_divergence_validates_ref_and_streams() -> None:
    from townlet.oracle.matrix import RegisteredStreamDivergence

    d = RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs",))
    assert d.declared == frozenset({"obs"})

    with pytest.raises(ValueError, match="register_ref"):
        RegisteredStreamDivergence(register_ref="div8", streams=("obs",))
    with pytest.raises(ValueError, match="at least one"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=())
    with pytest.raises(ValueError, match="duplicates"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs", "obs"))
    with pytest.raises(ValueError, match="not a trace stream"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=("observations",))


def test_cell_defaults_declare_nothing_new() -> None:
    from townlet.oracle.matrix import default_cells

    for cell in default_cells():
        assert cell.stream_divergence is None
        assert cell.scripted_actions is False
