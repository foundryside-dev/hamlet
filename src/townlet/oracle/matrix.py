"""The declared comparison matrix.

Cells are DECLARED, not discovered — per the no-defaults principle, every
parameter of every cell is explicit here. The five default_curriculum levels
are three distinct universes (PDR-0018); all five are cells anyway, because
the harness compares runtimes, not curricula.

Expected divergences are declared here too (hamlet-56ec575ae2 / PDR-0037): a
cell that is REGISTERED to diverge binds to its known-divergences entry via
RegisteredDivergence, and the harness passes it only when the observed outcome
matches that declaration narrowly. Extend by declaration, never by discovery.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from townlet.oracle.trace_io import _TRACE_STREAMS, RunParams

_DEFAULT_PACK = "configs/default_curriculum"
_DEFAULT_LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)

# Differential packs (configs/differential/): default_curriculum with exactly
# one stratum axis moved (pinned by
# test_differential_packs_vary_only_the_declared_axis). They entered the matrix
# as the DIV-003 crash cells — at oracle-2026-08-13 (0e875d7a) each crashed on
# the old side with a signature re-verified at that tag. DIV-003 was cut and
# adjudicated (PDR-0041), and at oracle-2026-08-17 (4222a917, PDR-0074) the
# oracle itself runs them, so the entry is `retired` and these are plain
# standing cells expected to AGREE. They stay because they exercise the
# substrate axes the default pack does not.
_DIFFERENTIAL_PACKS = (
    # (pack dir under configs/differential, level)
    ("div003_scaled", "L1_full_observability"),
    ("div003_cubic_partial", "L2_partial_observability"),
    ("div003_rect", "L1_full_observability"),
)

# Profile-variable packs: the only runnable packs whose `vfs_profiles.yaml`
# declares variables, so the only cells in which the compiled `obs_vfs` block
# has any width (items_smoke: 3 dims, item scope; effects_smoke: 1 dim, global
# scope). Added at oracle-2026-08-17 (PDR-0074) because unit 3
# (hamlet-f0ed709ecf) splits that block, and default_curriculum + the
# differential packs declare `variables: []` — without these cells the matrix
# would read green about that cut while measuring nothing (PDR-0052's shape).
# Their AGREE at the new tag is what proves they can see, before the cut asks.
_PROFILE_VARIABLE_PACKS = (
    ("configs/test/items_smoke", "L0_smoke"),
    ("configs/test/effects_smoke", "L0_effects"),
)


# ASCII: \d alone also matches Unicode decimal digits ('DIV-٠٠٣'), which would
# construct a ref no register heading can ever carry.
_REGISTER_REF_RE = re.compile(r"DIV-\d{3}", re.ASCII)
_TRACEBACK_BOILERPLATE = "Traceback (most recent call last):"
# Shorter than this cannot name an exception type plus any distinguishing
# context; it exists to make lazily-weak signatures unconstructable, not to
# guarantee distinctiveness (that is the declarer's job, reviewed).
_MIN_SIGNATURE_LEN = 12


@dataclass(frozen=True)
class RegisteredDivergence:
    """One cell's declared binding to a known-divergences register entry.

    Supports exactly one divergence shape — the ORACLE side crashes without
    producing a trace, the registered signature appearing in its final
    exception text, while the REBUILD runs and produces a valid one — because
    that is DIV-003's shape (PDR-0036), the only trace-visible entry. New
    shapes are added when a register entry needs them, not speculatively
    (PDR-0037 reversal trigger 3: unexercised machinery in a verdict-emitting
    tool is itself a risk).

    Narrowness is enforced twice (PDR-0033: a suppression mechanism is a
    machine for manufacturing false AGREEs if it is loose):

    - At construction, the cheaply-decidable weak classes are rejected:
      empty/short signatures, a bare exception-type name (with or without a
      trailing colon), and anything containing — or contained in — the
      universal traceback header line.
    - At adjudication, the harness matches the signature only against the
      FINAL EXCEPTION TEXT of the old side's stderr (harness.py), so frame
      paths, warnings, log noise, stdout, and harness-authored diagnostics
      can never satisfy it regardless of what was declared.

    What construction canNOT decide is left to the declarer and review: a
    syntactically strong signature that happens to be generic for THIS
    codebase's exceptions (a config value, a common message fragment) will
    still match every crash whose final exception contains it. Declare the
    most specific stable fragment of the registered crash's message.
    """

    register_ref: str  # e.g. "DIV-003" — must name a docs/oracle/known-divergences.md entry
    old_stderr_substring: str  # distinctive text of the registered crash's final exception

    def __post_init__(self) -> None:
        if not _REGISTER_REF_RE.fullmatch(self.register_ref):
            raise ValueError(f"register_ref must look like 'DIV-003', got {self.register_ref!r}")
        signature = self.old_stderr_substring.strip()
        if len(signature) < _MIN_SIGNATURE_LEN:
            raise ValueError(
                f"old_stderr_substring must be a distinctive failure signature "
                f"(>= {_MIN_SIGNATURE_LEN} chars after strip), got {self.old_stderr_substring!r} — "
                f"a short signature matches unrelated crashes and manufactures false passes"
            )
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\s*:?", signature):
            raise ValueError(
                f"old_stderr_substring {self.old_stderr_substring!r} is a bare identifier "
                f"(an exception-type name, with or without a colon) — not a distinctive "
                f"failure signature: it matches EVERY crash of that type, not the registered one"
            )
        if signature in _TRACEBACK_BOILERPLATE or _TRACEBACK_BOILERPLATE in signature:
            raise ValueError(
                f"old_stderr_substring {self.old_stderr_substring!r} contains or is contained in "
                f"traceback boilerplate — present in every Python traceback, it cannot "
                f"distinguish the registered crash from any crash"
            )


@dataclass(frozen=True)
class RegisteredHashDivergence:
    """One cell's declared binding for the SECOND divergence shape: provenance
    moved as intended, behaviour did not.

    `RegisteredDivergence` above covers old-side-crash. This covers the shape
    WS-4 produces by construction: the authoring surface changes, so the
    compiled artifact hashes differently, while every observable byte of the
    run is unchanged. Without it the harness cannot express that at all —
    `compare_traces` returns HASH_MISMATCH and short-circuits BEFORE comparing
    a single stream, so the oracle goes blind on exactly the surface WS-4
    exists to change. Same failure as `hamlet-2090c9f16d` one layer up:
    the harness stops answering at the moment of use.

    Added because a register entry needs it (DIV-004), which is the bar the
    sibling class sets for new shapes — not speculatively. DIV-004 and DIV-005
    retired when the oracle moved forward to oracle-2026-08-17 (PDR-0074); the
    shape stays because the next authoring cut (DIV-006, unit 3) binds it, and
    the harness's compare path and its tests exercise it regardless.

    Narrowness (PDR-0033 — a suppression mechanism is a machine for
    manufacturing false AGREEs if it is loose):

    - `hash_fields` is an ENUMERATED set, never a wildcard. A hash moving
      outside it keeps the cell red, and the verdict detail separates the
      declared movers from the undeclared ones.
    - The declared set must match the observed set EXACTLY. A declared field
      that did NOT move is a stale entry and lands
      `REGISTERED_DIVERGENCE_ABSENT`, the same treatment the crash shape gets
      when the oracle stops crashing.
    - Streams are still compared in full, byte-exact. The declaration
      suppresses nothing about behaviour; it only stops provenance inequality
      from pre-empting the comparison that matters.

    What construction cannot decide is left to the declarer and review: RAW
    hashes (`environment_hash`, `stratum_hash`, … — `_compute_pydantic_hash`
    over a whole config file) move for ANY edit to that file, so listing one
    is far weaker evidence than listing a DERIVED hash
    (`observation_schema_hash`, `vfs_hash`, …) that names what the compiler
    actually built. Declare the derived ones deliberately; the raw one is a
    consequence.
    """

    register_ref: str  # e.g. "DIV-004" — must name a docs/oracle/known-divergences.md entry
    hash_fields: tuple[str, ...]  # exact set of *_hash fields permitted (and required) to differ

    def __post_init__(self) -> None:
        if not _REGISTER_REF_RE.fullmatch(self.register_ref):
            raise ValueError(f"register_ref must look like 'DIV-004', got {self.register_ref!r}")
        if not self.hash_fields:
            raise ValueError(
                "hash_fields must enumerate at least one *_hash field — an empty set is a wildcard "
                "by another name, and would let any provenance movement pass unremarked"
            )
        if len(set(self.hash_fields)) != len(self.hash_fields):
            raise ValueError(f"hash_fields contains duplicates: {self.hash_fields!r}")
        for name in self.hash_fields:
            if not name.endswith("_hash"):
                raise ValueError(
                    f"hash_fields entry {name!r} is not a provenance hash field — entries must end in '_hash', "
                    f"so a typo cannot silently widen the declaration to something that never matches"
                )

    @property
    def declared(self) -> frozenset[str]:
        return frozenset(self.hash_fields)


@dataclass(frozen=True)
class RegisteredStreamDivergence:
    """One cell's declared binding for the THIRD divergence shape: a named trace
    stream diverges as intended, everything else does not.

    Built for DIV-008 (the token-observation cut, spec
    docs/superpowers/specs/2026-08-22-token-observation-representation-design.md §5):
    the observation representation changes, so the `obs` stream diverges on every
    cell, while world dynamics under scripted actions — `actions`, `dones`,
    `rewards` — must stay byte-exact. Added because that register entry needs it,
    the bar the sibling classes set.

    Narrowness (PDR-0033, both directions, enforced in compare_traces):
    - `streams` is an ENUMERATED set from the closed trace-stream vocabulary,
      never a wildcard. An undeclared stream diverging keeps the cell red.
    - Every declared stream must ACTUALLY diverge somewhere in the trace; one
      that does not is a stale entry and lands REGISTERED_DIVERGENCE_ABSENT.
    - Hash movement is a separate declaration (`RegisteredHashDivergence`) —
      a declared OUTPUT-stream delta does not bless provenance movement, and
      vice versa. DIV-008 binds both, under one register_ref.
    """

    register_ref: str
    streams: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _REGISTER_REF_RE.fullmatch(self.register_ref):
            raise ValueError(f"register_ref must look like 'DIV-008', got {self.register_ref!r}")
        if not self.streams:
            raise ValueError("streams must enumerate at least one trace stream — an empty set is a wildcard by another name")
        if len(set(self.streams)) != len(self.streams):
            raise ValueError(f"streams contains duplicates: {self.streams!r}")
        for name in self.streams:
            if name not in _TRACE_STREAMS:
                raise ValueError(f"streams entry {name!r} is not a trace stream (one of {_TRACE_STREAMS})")

    @property
    def declared(self) -> frozenset[str]:
        return frozenset(self.streams)


# DIV-006 — unit 3 (hamlet-f0ed709ecf, PDR-0075): the `obs_vfs` block became one field per
# exposed global/agent profile variable plus the `obs_item_slots` feature. MEASURED on both
# profile packs by compiling the pre-cut tree (the oracle worktree at 4222a917) beside the
# live tree: exactly these three DERIVED hashes move; `environment_hash` does not
# (environment.yaml is untouched), and neither does anything else. `default_curriculum` and
# the differential packs declare no profile variables, so nothing moves there and their
# sixteen cells stay undeclared.
_DIV006 = RegisteredHashDivergence(
    register_ref="DIV-006",
    hash_fields=(
        "observation_schema_hash",
        "variable_schema_hash",
        "vfs_hash",
    ),
)
# Which profile packs' FROZEN fixture drifts from its live pack, and under which register
# entry. effects_smoke: the DIV-006 cut requires `semantic_type` on global/agent profile
# variables, so its fixture is held at the pre-cut vfs_profiles.yaml schema. items_smoke:
# DIV-007 — levels/*/brain.yaml became a loaded surface (PDR-0027) and the live pack's
# stale, never-loaded L0_smoke stub was deleted; the fixture keeps it and the old loader
# ignores it. A pack absent here must be a byte copy of its fixture (a declaration with
# nothing to declare is a stale entry — test_pack_freeze pins both directions).
_PACK_DIVERGENCE = {
    "configs/test/effects_smoke": "DIV-006",
    "configs/test/items_smoke": "DIV-007",
}

# DIV-009 (2026-08-23, hamlet-5cc071f4b6): six Phase B landings after the oracle tag moved
# provenance hashes with no register entry — measured per-commit with the DIV-004 worktree
# method (old code + oracle_fixtures vs each commit's code + live pack, matching what the
# harness itself compares). Only three of the six commits actually move a hash on any of
# the three probed packs (default_curriculum L1, div003_rect L1, items_smoke L0_smoke);
# the other three (8868f237, 03764c6b, and the first half of the brain-fork landing,
# d60104f0) add no mover. See docs/oracle/known-divergences.md#div-009 for the full table
# and the composite-hash reasoning (`vfs_hash` picks up `transition_graph_hash` via
# `compute_vfs_hash`, not directly).
_DIV009_STANDING = RegisteredHashDivergence(
    register_ref="DIV-009",
    hash_fields=("actions_hash", "pack_brain_hash", "transition_graph_hash", "vfs_hash"),
)
# The profile packs' obs-side derived hashes (`observation_schema_hash`,
# `variable_schema_hash`, `vfs_hash`) are already accounted for exactly by `_DIV006` —
# measured to confirm DIV-006 alone covers them, so DIV-009's own field set here stays
# disjoint from DIV-006's rather than re-declaring `vfs_hash` a second time. `vfs_hash`
# itself moves on these cells for both causes (DIV-006's obs-side inputs AND DIV-009's
# transition_graph_hash input to `compute_vfs_hash`), but the union of the two entries'
# fields already equals the observed set without duplicating it.
_DIV009_PROFILE = RegisteredHashDivergence(
    register_ref="DIV-009",
    hash_fields=("actions_hash", "pack_brain_hash", "transition_graph_hash"),
)

# DIV-010 (2026-08-23, unit 2 "authored temporality", hamlet-fa6bb6da4a): the engine tick
# VariableDef injected into every compiled universe (always-on, global scope) moves
# `variable_schema_hash` directly and `vfs_hash` as a consequence — measured by two-worktree
# probe (baseline 11dee204, head HEAD) and confirmed per-commit: only the tick-injection
# commit (2d14d5f7) moves anything; the other five unit-2 landings (marks rename+content,
# agent-profile evaluation, item-profile refusal, time_of_day derivation, write-back statics
# fix) move no hash. Identical two-field set on all three blocks — the injection is
# unconditional, unlike DIV-009's profile-block narrowing. See
# docs/oracle/known-divergences.md#div-010 for the full table and why streams cannot move.
_DIV010 = RegisteredHashDivergence(
    register_ref="DIV-010",
    hash_fields=("variable_schema_hash", "vfs_hash"),
)

# DIV-011 (2026-08-25, unit 3 Task 7, hamlet-fa6bb6da4a): the TokenSpec artifact is
# compiled ALONGSIDE the ObservationSpec family and stamps two NEW hashes on every
# compiled universe — `token_type_schema_hash` (transfer contract) and `layout_hash`
# (flat-net contract). The oracle side predates the fields (old reads `<absent>`), so
# they surface as movers on every cell; everything pre-existing is byte-identical
# (measured: BASE-vs-tree compile probe over all five default_curriculum levels, 95
# pre-existing hash lines unchanged). Neither field enters config_hash or the vfs_hash
# composition — that movement is Task 10's, registered as DIV-008. Uniform two-field set
# on all blocks, DIV-010's pattern: the emission is unconditional.
_DIV011 = RegisteredHashDivergence(
    register_ref="DIV-011",
    hash_fields=("token_type_schema_hash", "layout_hash"),
)


@dataclass(frozen=True)
class Cell:
    params: RunParams
    # None for the overwhelming default: the cell is expected to AGREE.
    expected: RegisteredDivergence | None = None
    # Names the known-divergences entry under which this cell's FROZEN oracle
    # pack is allowed to differ from the live pack (hamlet-2090c9f16d).
    #
    # Default None is the load-bearing choice: with no declaration, any drift
    # between oracle_fixtures/<pack> and configs/<pack> fails the cell. Silent
    # drift is the failure PDR-0052's reversal trigger names — a frozen pack
    # that has rotted into a different universe still compiles, and then every
    # cell AGREEs about nothing. Setting this is the recorded human judgement
    # that the two packs still describe the SAME universe in two schemas; it is
    # never inferred from the fact that they differ.
    pack_divergence: str | None = None
    # Names the entries under which this cell's compiled provenance hashes are
    # allowed — and required — to differ, with behaviour unchanged. Distinct
    # from pack_divergence on purpose: a declared INPUT delta and a declared
    # OUTPUT delta are two decisions (oracle_fixtures/README.md), and one does
    # not bless the other. A TUPLE, not one entry: two register entries can
    # bind the same cells (DIV-006 + DIV-009 on the profile cells) when two
    # distinct causes move the same hash. The union of every entry's declared
    # fields must match the observed movers exactly; each entry's own fields
    # must all move, or that entry alone is stale (hamlet-fa6bb6da4a).
    hash_divergences: tuple[RegisteredHashDivergence, ...] = ()
    # Names the entry under which named trace STREAMS are allowed — and
    # required — to diverge, everything else byte-exact. The third declaration
    # axis, orthogonal to pack_divergence (inputs) and hash_divergences
    # (provenance): DIV-008 binds stream + hash together at the token cut.
    stream_divergence: RegisteredStreamDivergence | None = None
    # Run this cell's trace with harness-scripted actions (old side records,
    # new side replays) instead of per-side seeded draws. DIV-008 cells declare
    # it; --scripted forces it matrix-wide for verification runs.
    scripted_actions: bool = False

    @property
    def declares_pack_divergence(self) -> bool:
        return self.pack_divergence is not None

    @property
    def cell_id(self) -> str:
        p = self.params
        return f"{Path(p.pack).name}:{p.level}:{p.device}:seed{p.seed}"


def default_cells() -> tuple[Cell, ...]:
    """The full declared matrix, in three blocks, each cpu-then-cuda:

    1. standing — all 5 default_curriculum levels (10 cells);
    2. differential — the three one-axis-moved packs (6 cells);
    3. profile-variable — items_smoke and effects_smoke (4 cells).

    CUDA cells are always declared, never conditionally omitted — per spec,
    the RUN decision (whether to actually execute them) belongs to the
    harness, which reports them SKIPPED when --cuda is not passed. A matrix
    that drops CUDA cells entirely without the flag would make that skip
    silent instead of reported.

    At oracle-2026-08-17 the fixtures under oracle_fixtures/ were byte copies
    of the live packs and no cell declared anything, so exit 0 meant old and
    new AGREE (PDR-0074). That is no longer true: six Phase B landings after
    the tag moved provenance with no register entry (DIV-009, hamlet-5cc071f4b6),
    and unit 2 ("authored temporality") then added its own compiler-surface
    movement (DIV-010, hamlet-fa6bb6da4a) — the engine tick VariableDef
    injected into every compiled universe. All sixteen standing + differential
    cells now bind `(_DIV009_STANDING, _DIV010, _DIV011)` (hash-only:
    `actions_hash`, `pack_brain_hash`, `transition_graph_hash`, `vfs_hash` from
    DIV-009, plus `variable_schema_hash`, `vfs_hash` from DIV-010 — `vfs_hash`
    moves for both causes but is declared once per composing entry, per
    hamlet-fa6bb6da4a's union-exact rule — plus `token_type_schema_hash`,
    `layout_hash` from DIV-011: unit 3 Task 7's alongside TokenSpec emission,
    absent on the oracle side by construction) and the four profile-variable
    cells bind `(_DIV006, _DIV009_PROFILE, _DIV010, _DIV011)` — DIV-006's
    obs-side split (PDR-0075), DIV-009's disjoint field set, and DIV-010's /
    DIV-011's uniform two-field sets. Exit 0 now means "everything diverged
    exactly as registered", DIV-004's cost restated twice at this tag; see
    docs/oracle/known-divergences.md#div-009, #div-010 and #div-011.
    Declarations return only when a register entry needs them (PDR-0037
    record-then-bind).
    """
    standing = tuple(
        Cell(
            RunParams(
                pack=_DEFAULT_PACK,
                level=level,
                num_agents=4,
                steps=100,
                seed=42,
                device=device,
            ),
            hash_divergences=(_DIV009_STANDING, _DIV010, _DIV011),
        )
        for device in ("cpu", "cuda")
        for level in _DEFAULT_LEVELS
    )
    differential = tuple(
        Cell(
            RunParams(
                pack=f"configs/differential/{pack_dir}",
                level=level,
                num_agents=4,
                steps=100,
                seed=42,
                device=device,
            ),
            hash_divergences=(_DIV009_STANDING, _DIV010, _DIV011),
        )
        for device in ("cpu", "cuda")
        for pack_dir, level in _DIFFERENTIAL_PACKS
    )
    profile = tuple(
        Cell(
            RunParams(
                pack=pack,
                level=level,
                num_agents=4,
                steps=100,
                seed=42,
                device=device,
            ),
            pack_divergence=_PACK_DIVERGENCE.get(pack),
            hash_divergences=(_DIV006, _DIV009_PROFILE, _DIV010, _DIV011),
        )
        for device in ("cpu", "cuda")
        for pack, level in _PROFILE_VARIABLE_PACKS
    )
    return standing + differential + profile
