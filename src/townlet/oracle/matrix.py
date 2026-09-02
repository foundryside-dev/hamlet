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
# test_differential_packs_vary_only_the_declared_axis). The cubic and rectangular
# packs entered as DIV-003 crash cells; boundary_wrap replaced the vacuous
# observation-encoding cell when that selector was deleted. These are plain
# standing cells because they exercise real substrate axes the default pack does not.
_DIFFERENTIAL_PACKS = (
    # (pack dir under configs/differential, level)
    ("boundary_wrap", "L1_full_observability"),
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


# DIV-006 is RETIRED at the token cut (2026-08-26, unit 3 Task 11). It declared the
# `obs_vfs` split into one `ObservationField` per exposed profile variable plus the
# `obs_item_slots` feature — a NEW-SIDE surface the cut deleted outright (`ObservationSpec`,
# `ObservationField`, `VFSObservationSpec` are gone). Its three declared hashes still move on
# the profile cells, but for DIV-008's cause now, and DIV-008 declares them uniformly on all
# twenty cells. Re-declaring them under a retired entry would certify a surface that no
# longer exists. See docs/oracle/known-divergences.md#div-006.
#
# Which packs' FROZEN fixture drifts from its live pack, and under which register entry.
# MEASURED at HEAD (`pack_drift`, 2026-08-26):
#   configs/default_curriculum           differing: vfs_profiles.yaml     -> DIV-008
#   configs/differential/*         (×3)  differing: vfs_profiles.yaml     -> DIV-008
#   configs/test/effects_smoke           differing: effects.yaml, vfs_profiles.yaml -> DIV-008
#   configs/test/items_smoke             only_in_frozen: levels/L0_smoke/brain.yaml (DIV-007)
#                                        + differing: effects.yaml (DIV-008)
# items_smoke keeps DIV-007 because that entry survives and still describes the stale
# never-loaded brain.yaml stub; DIV-008's entry enumerates the complete per-pack delta,
# including the row DIV-007 owns, so no drift is blessed by a declaration that does not
# describe it. effects_smoke moves to DIV-008 because DIV-006 (which held its fixture at the
# pre-`semantic_type` vfs_profiles schema) is retired. A pack absent here must be a byte copy
# of its fixture (a declaration with nothing to declare is a stale entry — test_pack_freeze
# pins both directions).
#
# COST, recorded not hidden (DIV-004's own): `pack_divergence` is a BOOLEAN gate. Declaring
# it blesses arbitrary drift between fixture and live pack, not merely the rows above — so
# the pack-freeze guard built at 49bdf28e is armed on ZERO of the twenty cells for as long
# as DIV-008 is open. That is the same cost DIV-004 recorded, and it dissolves the same way:
# a forward move of the oracle tag.
_PACK_DIVERGENCE = {
    "configs/default_curriculum": "DIV-008",
    "configs/differential/boundary_wrap": "DIV-008",
    "configs/differential/div003_cubic_partial": "DIV-008",
    "configs/differential/div003_rect": "DIV-008",
    "configs/test/effects_smoke": "DIV-008",
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

# DIV-012 (2026-09-02, unit 5 `day_phase`, hamlet-55b2826a02): four undeclared hash movers,
# each bisected to its own causing commit (full cpu-matrix run 20260902-100550) —
# `stratum_hash` at 94656527 (Task 1's `observation_mode` deletion: RAW hash over the whole
# StratumConfig, frozen fixture still declares the key), `affordances_hash` and
# `environment_hash` at c6c6b524 ("restore executable observation authority": the meter
# range_type migration narrows AffordanceParamConfig/EnvironmentConfig's schema — both RAW
# hashes move for the schema edit alone, neither pack's own YAML is touched), `brain_hash`
# at d554fb7f ("cut compact replay ABI": deletes the model_serializer that cbea580f had
# installed specifically to omit the always-None `token_set` key from the dump — reintroduces
# exactly the movement cbea580f fixed). Bound together under the union-exact rule, not
# because they share a cause. `_DIV012` (all four fields) covers the standing and
# differential blocks; `_DIV012_PROFILE` (three fields, `affordances_hash` excluded — it
# does not move on the profile packs, measured) covers items_smoke/effects_smoke. See
# docs/oracle/known-divergences.md#div-012 for the per-field bisection and full cell table.
_DIV012 = RegisteredHashDivergence(
    register_ref="DIV-012",
    hash_fields=("affordances_hash", "brain_hash", "environment_hash", "stratum_hash"),
)
_DIV012_PROFILE = RegisteredHashDivergence(
    register_ref="DIV-012",
    hash_fields=("brain_hash", "environment_hash", "stratum_hash"),
)

# DIV-011 is RETIRED into DIV-008 at the token cut (2026-08-26, unit 3 Task 11) — its own
# entry pre-registered exactly that condition ("retire when DIV-008 lands … the token hashes
# become part of that registered surface"). `token_type_schema_hash` and `layout_hash` are
# not a fact about an ALONGSIDE emission any more; they are the token observation ABI's own
# provenance, which is DIV-008's surface. Their declaration moves into `_DIV008_HASH` below,
# unchanged in content.

# DIV-008 (2026-08-26, unit 3 Task 10's cut, hamlet-fa6bb6da4a): the TokenSpec replaces the
# fixed-width superset + activity-mask ABI. MEASURED at HEAD by the DIV-009 worktree method
# — the oracle worktree at 4222a917 reading oracle_fixtures/<pack> versus the live tree
# reading configs/<pack>, which is exactly what the harness itself compares — on every one
# of the twenty cells. FIVE fields move, uniformly on all three blocks:
#
#   observation_schema_hash  redefined over the TokenSpec (spec §5); the artifact it was
#                            computed over no longer exists in its old form.
#   variable_schema_hash     a DIFFERENT deletion from the headline one, and easy to miss:
#                            `build_vfs_variables` stopped minting the engine-side
#                            observation primitives, so the canonical VariableDef list loses
#                            14 entries on default_curriculum (obs_grid_encoding,
#                            obs_local_window, obs_position, obs_velocity, eight
#                            obs_meter_*, obs_affordance_at_position, obs_temporal).
#                            Overlaps DIV-010's declaration, legally: two causes genuinely
#                            move this hash (DIV-010's tick injection ADDS an entry, this
#                            cut REMOVES fourteen), which is the DIV-010 composing shape,
#                            not the DIV-009 narrowing shape.
#   vfs_hash                 composite: slots 1 and 2 of compute_vfs_hash both move.
#   token_type_schema_hash   the transfer contract; `<absent>` on the oracle side.
#   layout_hash              the flat-net contract; `<absent>` on the oracle side.
#                            (Both inherited from the retired DIV-011.)
#
# Uniform across blocks, DIV-010's and DIV-011's pattern rather than DIV-009's: the cut is
# unconditional — it redefines the observation ABI for every compiled universe, whatever the
# pack declares.
_DIV008_HASH = RegisteredHashDivergence(
    register_ref="DIV-008",
    hash_fields=(
        "observation_schema_hash",
        "variable_schema_hash",
        "vfs_hash",
        "token_type_schema_hash",
        "layout_hash",
    ),
)
# The THIRD declaration axis, and the one this entry exists for: the `obs` stream diverges
# on every cell (tokens change the observation's shape and content), while `actions`,
# `dones` and `rewards` stay byte-exact — undeclared, so `compare_traces` holds them to the
# same byte-exact bar every undeclared stream gets. That is spec §5's adjudication criterion
# stated as a machine-checked declaration: tokens change what agents see, never what the
# world does.
_DIV008_STREAM = RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs",))


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
    unit 2 ("authored temporality") added the engine tick VariableDef (DIV-010),
    and unit 3's token cut replaced the observation ABI outright (DIV-008).

    Every one of the twenty cells now binds DIV-008 twice over — once as a
    hash declaration (`_DIV008_HASH`, five fields, uniform) and once as a
    STREAM declaration (`_DIV008_STREAM`, `obs` alone). That pairing is what
    makes spec §5 machine-checked rather than argued: the obs stream is
    permitted to diverge and REQUIRED to, while `actions` / `dones` /
    `rewards` are undeclared and therefore held byte-exact. DIV-008 is the
    first entry to carry both shapes under one register_ref, which
    `compare_traces` labels `"hash+stream"`.

    Standing and differential cells additionally bind `_DIV012` (2026-09-02, unit 5
    `day_phase`, full cpu-matrix run 20260902-100550): `stratum_hash` (Task 1's
    `observation_mode` deletion, bisected to 94656527), `affordances_hash` and
    `environment_hash` (both bisected to c6c6b524, the meter range_type schema
    migration), `brain_hash` (bisected to d554fb7f, which deleted the
    model_serializer cbea580f had installed to suppress exactly this movement).
    Profile cells bind the narrower `_DIV012_PROFILE` (same three causes, minus
    `affordances_hash`, which does not move on the profile packs — measured, not
    assumed). See docs/oracle/known-divergences.md#div-012 for the per-field
    bisection and the full ten-cpu-cell table.

    Standing cells bind `(_DIV009_STANDING, _DIV010, _DIV012, _DIV008_HASH)`;
    differential cells bind the identical tuple (measured — `_DIV012`'s field set
    matches the differential cells' undeclared movers exactly); profile cells
    bind `(_DIV009_PROFILE, _DIV010, _DIV012_PROFILE, _DIV008_HASH)`. DIV-006 and
    DIV-011 are RETIRED into DIV-008 at this cut (see their comments above) —
    DIV-006 because the new-side surface it described was deleted, DIV-011 by its
    own pre-registered condition. Overlapping fields between composing entries are
    legal where two causes genuinely move one hash (`variable_schema_hash`
    under DIV-010 and DIV-008; `vfs_hash` under DIV-009, DIV-010 and DIV-008);
    the union of every entry's declared fields must still equal the observed
    movers EXACTLY, and each entry's own fields must all move.

    Exit 0 now means "everything diverged exactly as registered", DIV-004's
    cost restated at this tag; see docs/oracle/known-divergences.md#div-008,
    #div-009, #div-010 and #div-012. Declarations return only when a register
    entry needs them (PDR-0037 record-then-bind).
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
            pack_divergence=_PACK_DIVERGENCE.get(_DEFAULT_PACK),
            hash_divergences=(_DIV009_STANDING, _DIV010, _DIV012, _DIV008_HASH),
            stream_divergence=_DIV008_STREAM,
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
            pack_divergence=_PACK_DIVERGENCE.get(f"configs/differential/{pack_dir}"),
            hash_divergences=(_DIV009_STANDING, _DIV010, _DIV012, _DIV008_HASH),
            stream_divergence=_DIV008_STREAM,
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
            hash_divergences=(_DIV009_PROFILE, _DIV010, _DIV012_PROFILE, _DIV008_HASH),
            stream_divergence=_DIV008_STREAM,
        )
        for device in ("cpu", "cuda")
        for pack, level in _PROFILE_VARIABLE_PACKS
    )
    return standing + differential + profile
