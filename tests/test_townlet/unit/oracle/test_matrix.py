"""The declared comparison matrix — explicit cells, no discovery magic (WS-7)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from townlet.oracle.matrix import Cell, RegisteredDivergence, RegisteredHashDivergence, default_cells
from townlet.oracle.trace_io import RunParams

LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)

# Deliberately DUPLICATED from matrix.py, not imported: these are pins. A
# matrix edit that changes a block must consciously move the pin too.
# The cubic and rectangular differential packs entered as DIV-003 crash cells.
# boundary_wrap replaced the deleted observation-encoding axis; all three are
# plain standing cells and carry no signature.
_DIFFERENTIAL_LEVELS = {
    "boundary_wrap": "L1_full_observability",
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


def test_standing_and_differential_cells_bind_div009_narrowly() -> None:
    """Pin (hamlet-5cc071f4b6, DIV-009): the sixteen non-profile cells no longer
    certify bare agreement. Six Phase B landings after the oracle tag moved
    provenance with no register entry (measured 2026-08-23); every standing and
    differential cell binds a hash-only DIV-009 entry over exactly the four
    measured fields — no crash expectation, and no wider or narrower hash_fields
    set than measurement showed. DIV-010 (hamlet-fa6bb6da4a, unit 2) and DIV-008
    (unit 3's token cut) compose alongside it on these same cells — checked here
    as "DIV-009 is present and still narrow", leaving their own field sets to
    test_standing_and_differential_cells_bind_div010_and_div008_narrowly.

    These sixteen cells DO declare a pack divergence since 2026-08-26: their
    live vfs_profiles.yaml carries the L3 temporal declaration
    (hamlet-02684be106) and their frozen fixtures do not. That is DIV-008's
    row — see docs/oracle/known-divergences.md#div-008's per-pack drift table."""
    for c in default_cells():
        if c.params.pack in _PROFILE_VARIABLE_CELLS:
            continue
        assert c.expected is None, f"{c.cell_id} declares an old-side-crash expectation"
        assert c.pack_divergence == "DIV-008", f"{c.cell_id}: the vfs_profiles.yaml drift is DIV-008's row"
        div009 = [d for d in c.hash_divergences if d.register_ref == "DIV-009"]
        assert len(div009) == 1, f"{c.cell_id} does not bind exactly one DIV-009 entry"
        assert div009[0].declared == {
            "actions_hash",
            "pack_brain_hash",
            "transition_graph_hash",
            "vfs_hash",
        }, f"{c.cell_id}: DIV-009 hash_fields do not match measurement"


def test_standing_and_differential_cells_bind_div010_and_div008_narrowly() -> None:
    """Pin (hamlet-fa6bb6da4a, DIV-010, unit 2 "authored temporality"): the engine tick
    VariableDef injected into every compiled universe moves exactly `variable_schema_hash`
    and `vfs_hash` — measured by two-worktree probe (11dee204 vs HEAD) and confirmed
    per-commit as the tick-injection commit's own movement. Every standing and differential
    cell binds this as a second, composing entry alongside DIV-009, and unit 3's token cut
    (DIV-008) composes third, plus a fourth (DIV-012) on all sixteen standing+differential
    cells (2026-09-02, unit 5 `day_phase`, full cpu-matrix run 20260902-100802):
    `affordances_hash`, `brain_hash`, `environment_hash`, `stratum_hash`, each bisected to
    its own causing commit (94656527, c6c6b524 twice, d554fb7f) — see
    docs/oracle/known-divergences.md#div-012 for the per-field bisection and cell table.
    Four entries total on all sixteen cells.

    DIV-011 is GONE from the binding: it retired into DIV-008 by its own pre-registered
    condition, and its two token hashes are declared under DIV-008 now (2026-08-26)."""
    for c in default_cells():
        if c.params.pack in _PROFILE_VARIABLE_CELLS:
            continue
        div010 = [d for d in c.hash_divergences if d.register_ref == "DIV-010"]
        assert len(div010) == 1, f"{c.cell_id} does not bind exactly one DIV-010 entry"
        assert div010[0].declared == {"variable_schema_hash", "vfs_hash"}, f"{c.cell_id}: DIV-010 hash_fields do not match measurement"
        assert not [
            d for d in c.hash_divergences if d.register_ref == "DIV-011"
        ], f"{c.cell_id} still binds DIV-011, which retired into DIV-008"
        div012 = [d for d in c.hash_divergences if d.register_ref == "DIV-012"]
        assert len(div012) == 1, f"{c.cell_id} does not bind exactly one DIV-012 entry"
        assert div012[0].declared == {
            "affordances_hash",
            "brain_hash",
            "environment_hash",
            "stratum_hash",
        }, f"{c.cell_id}: DIV-012 hash_fields do not match measurement"
        assert len(c.hash_divergences) == 4, f"{c.cell_id} should bind exactly DIV-009 + DIV-010 + DIV-012 + DIV-008"


def test_every_cell_binds_div008_hash_and_stream_narrowly() -> None:
    """Pin (hamlet-fa6bb6da4a, DIV-008, unit 3 Task 11): the token cut. Every one of the
    twenty cells binds DIV-008 TWICE over — once as a hash declaration (five fields, uniform
    across all three blocks because the cut is unconditional) and once as a stream
    declaration naming `obs` alone. That pairing is what makes spec §5 machine-checked:
    `obs` is permitted to diverge and REQUIRED to, while `actions`/`dones`/`rewards` stay
    undeclared and are therefore held byte-exact.

    The five fields are the MEASURED set (matrix runs 20260826-171622 scripted /
    20260826-171731 plain, both exit 0), not the entry's original prediction — which named
    three and left `variable_schema_hash` explicitly open. It moves, and its cause is the
    fourteen engine-minted `obs_*` registry primitives dying with `build_vfs_variables`, a
    different deletion from the entry's headline. Two of the five (`token_type_schema_hash`,
    `layout_hash`) are inherited from the retired DIV-011.

    `scripted_actions` stays False on every cell: plain mode was measured green too, so
    forcing it would make a plain-mode run unexpressible for no gain."""
    for cell in default_cells():
        div008 = [d for d in cell.hash_divergences if d.register_ref == "DIV-008"]
        assert len(div008) == 1, f"{cell.cell_id} does not bind exactly one DIV-008 hash entry"
        assert div008[0].declared == {
            "observation_schema_hash",
            "variable_schema_hash",
            "vfs_hash",
            "token_type_schema_hash",
            "layout_hash",
        }, f"{cell.cell_id}: DIV-008 hash_fields do not match measurement"
        assert cell.stream_divergence is not None, f"{cell.cell_id} declares no stream divergence"
        assert cell.stream_divergence.register_ref == "DIV-008"
        assert cell.stream_divergence.declared == {"obs"}, (
            f"{cell.cell_id}: only `obs` may diverge — declaring another stream would stop " f"spec §5's criterion being adjudicated at all"
        )
        assert cell.scripted_actions is False, f"{cell.cell_id}: plain mode measured green, so the criterion is not forced matrix-wide"


def test_all_cells_bind_the_drift_and_unit2_and_token_entries() -> None:
    """Pin (hamlet-5cc071f4b6, hamlet-fa6bb6da4a): every one of the twenty cells names
    DIV-009 (the pre-unit-2 drift), DIV-010 (unit 2's compiler-surface movement) and DIV-008
    (unit 3's token cut) in its hash_divergences, with no duplicate register refs on a cell
    — the matrix-wide binding that brings the matrix back to exit 0. DIV-006 and DIV-011
    both retired into DIV-008 at the cut and must appear nowhere."""
    for cell in default_cells():
        refs = [d.register_ref for d in cell.hash_divergences]
        assert "DIV-009" in refs
        assert "DIV-010" in refs
        assert "DIV-008" in refs
        assert "DIV-011" not in refs, f"{cell.cell_id}: DIV-011 retired into DIV-008"
        assert "DIV-006" not in refs, f"{cell.cell_id}: DIV-006 retired into DIV-008"
        assert refs == sorted(set(refs), key=refs.index)  # no duplicate entries


def test_profile_variable_cells_declare_their_pack_drift() -> None:
    """DIV-006 is RETIRED at the token cut (2026-08-26): its new-side surface — the obs_vfs
    split into per-variable ObservationFields plus obs_item_slots — was deleted with the
    whole ObservationSpec family, so binding it would certify a ghost. Its three hashes are
    declared under DIV-008 now, uniformly on all twenty cells.

    What survives is the pack-drift declaration, re-pointed by measurement:
    effects_smoke drifts on effects.yaml (Task 10's required max_active_effects) AND
    vfs_profiles.yaml (DIV-006's old schema hold) -> DIV-008, which enumerates both rows.
    items_smoke keeps DIV-007 — its fixture still carries the stale, never-loaded
    levels/L0_smoke/brain.yaml stub the PDR-0027 cut deleted from the live pack; its own
    effects.yaml row is enumerated in DIV-008's table, since pack_divergence is one string."""
    profile = [c for c in default_cells() if c.params.pack in _PROFILE_VARIABLE_CELLS]
    assert len(profile) == 4
    for c in profile:
        assert c.expected is None
        assert not [
            d for d in c.hash_divergences if d.register_ref == "DIV-006"
        ], f"{c.cell_id} still binds DIV-006, which retired into DIV-008"
        if c.params.pack == "configs/test/effects_smoke":
            assert c.pack_divergence == "DIV-008"
        else:
            assert c.pack_divergence == "DIV-007", f"{c.cell_id}: items_smoke's fixture keeps the deleted brain.yaml stub (DIV-007)"


def test_profile_variable_cells_bind_div009_narrowly() -> None:
    """DIV-009's own field set on the four profile cells stays narrowed to exactly the three
    fields on its own (VTC / actions DTO / brain-fork) surface: `actions_hash`,
    `pack_brain_hash`, `transition_graph_hash`. It was narrowed to be disjoint from DIV-006's
    fields; DIV-006 has retired into DIV-008, whose field set it is disjoint from too, so the
    narrowing stands unchanged."""
    profile = [c for c in default_cells() if c.params.pack in _PROFILE_VARIABLE_CELLS]
    assert len(profile) == 4
    for c in profile:
        div009 = [d for d in c.hash_divergences if d.register_ref == "DIV-009"]
        assert len(div009) == 1, f"{c.cell_id} does not bind exactly one DIV-009 entry"
        assert div009[0].declared == {"actions_hash", "pack_brain_hash", "transition_graph_hash"}


def test_profile_variable_cells_bind_div010_narrowly() -> None:
    """DIV-010's field set on the four profile cells overlaps DIV-008's on
    `variable_schema_hash` and `vfs_hash` — both move for both causes (DIV-010's tick
    injection ADDS one VariableDef; the token cut REMOVES fourteen engine-minted `obs_*`
    primitives), declared under both entries, legal per the union-exact composing rule since
    each entry's own fields still all move. The tick injection is unconditional, so DIV-010's
    set here is identical to its set on the standing/differential cells, unlike DIV-009's
    profile-narrowed set; so is DIV-008's. Each profile cell additionally binds
    `_DIV012_PROFILE` (2026-09-02, unit 5 `day_phase`, full cpu-matrix run 20260902-100802):
    `brain_hash`, `environment_hash`, `stratum_hash` — the same three of DIV-012's four causes
    that move here; `affordances_hash` measurably does NOT move on these two packs, so the
    narrower object (not `_DIV012`) is bound, per the union-exact rule. Four entries total:
    DIV-009, DIV-010, DIV-012, DIV-008."""
    profile = [c for c in default_cells() if c.params.pack in _PROFILE_VARIABLE_CELLS]
    assert len(profile) == 4
    for c in profile:
        div010 = [d for d in c.hash_divergences if d.register_ref == "DIV-010"]
        assert len(div010) == 1, f"{c.cell_id} does not bind exactly one DIV-010 entry"
        assert div010[0].declared == {"variable_schema_hash", "vfs_hash"}
        div012 = [d for d in c.hash_divergences if d.register_ref == "DIV-012"]
        assert len(div012) == 1, f"{c.cell_id} does not bind exactly one DIV-012 entry"
        assert div012[0].declared == {
            "brain_hash",
            "environment_hash",
            "stratum_hash",
        }, f"{c.cell_id}: DIV-012 hash_fields do not match measurement (profile cells exclude affordances_hash)"
        assert len(c.hash_divergences) == 4, f"{c.cell_id} should bind exactly DIV-009 + DIV-010 + DIV-012 + DIV-008"


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
    declared |= {hd.register_ref for c in default_cells() for hd in c.hash_divergences}
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
        for hd in cell.hash_divergences:
            ref = hd.register_ref
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
            cell.expected is not None and cell.hash_divergences
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


def test_profile_cells_bind_hash_divergences_tuple() -> None:
    for cell in default_cells():
        assert isinstance(cell.hash_divergences, tuple)
        assert not hasattr(cell, "hash_divergence")  # old field is gone, not dual-carried


# --- RegisteredStreamDivergence: the third declared shape, built for DIV-008 ---
#
# DIV-008 (the token-observation cut) changes the obs stream while keeping
# actions/dones/rewards byte-exact under scripted actions. This declares WHICH
# streams are permitted to diverge; undeclared streams diverging keeps the cell red.


def test_stream_divergence_validates_ref_and_streams() -> None:
    from townlet.oracle.matrix import RegisteredStreamDivergence

    d = RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs",))
    assert d.declared == frozenset({"obs"})

    # Pin the full trace-stream vocabulary: all four members must be constructible
    # (not just "obs"). A typo like "reward" in _TRACE_STREAMS would pass if only
    # "obs" is tested, breaking Tasks 4/5.
    d_all = RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs", "actions", "dones", "rewards"))
    assert d_all.declared == frozenset({"obs", "actions", "dones", "rewards"})

    with pytest.raises(ValueError, match="register_ref"):
        RegisteredStreamDivergence(register_ref="div8", streams=("obs",))
    with pytest.raises(ValueError, match="at least one"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=())
    with pytest.raises(ValueError, match="duplicates"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs", "obs"))
    with pytest.raises(ValueError, match="not a trace stream"):
        RegisteredStreamDivergence(register_ref="DIV-008", streams=("observations",))


def test_cell_defaults_declare_nothing_new() -> None:
    """The two new axes stay OPT-IN at the dataclass level: a cell that names neither gets
    neither. (The twenty matrix cells all opt in to `stream_divergence` since DIV-008 was
    bound; what is pinned here is that the DEFAULT is still silence, so a cell added without
    thinking cannot inherit a suppression.)"""
    from townlet.oracle.matrix import Cell

    bare = Cell(RunParams(pack="configs/x", level="L0", num_agents=1, steps=1, seed=1, device="cpu"))
    assert bare.stream_divergence is None
    assert bare.scripted_actions is False


def test_stream_divergence_bindings_bind_entries_with_the_stream_scoped_shape() -> None:
    """The THIRD shape gets the same typo-bind guard as the first two.

    A `RegisteredStreamDivergence` certifies "this named stream diverged as registered,
    every other stream is byte-exact". Binding it to an entry that predicts an old-side
    crash, or a checkpoint-boundary entry that cannot manifest in a trace at all, would
    certify the wrong thing — so the entry must say `Harness shape: stream-scoped` in its
    own text. Without this, DIV-008's stream binding was the only one of the three
    declaration axes with no register-side check."""
    sections = _register_sections()
    for cell in default_cells():
        sd = cell.stream_divergence
        if sd is None:
            continue
        assert sd.register_ref in sections, f"{sd.register_ref} has no register entry"
        assert "Harness shape: stream-scoped" in sections[sd.register_ref], (
            f"cell {cell.cell_id} binds {sd.register_ref} as a stream-scoped divergence, but "
            f"that entry does not declare `Harness shape: stream-scoped`"
        )
