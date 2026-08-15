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

from townlet.oracle.trace_io import RunParams

_DEFAULT_PACK = "configs/default_curriculum"
_DEFAULT_LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)

# DIV-003 fixture cells (docs/oracle/known-divergences.md — the
# substrate→observation-dim seam, PDR-0035/PDR-0036). Each pack is
# default_curriculum with exactly one stratum axis moved (pinned by
# test_div003_fixture_packs_vary_only_the_declared_axis); each signature is
# the verbatim final-exception line re-verified at oracle-2026-08-13
# (0e875d7a) on 2026-08-15. The shape-mismatch messages embed num_agents in
# their first dim, so these signatures are stable only at num_agents=4 —
# change the cell params and the signatures must be re-verified at the tag.
_DIV003_FIXTURES = (
    # (pack dir under configs/differential, level, registered signature)
    (
        "div003_scaled",
        "L1_full_observability",
        "ValueError: Observation field 'obs_position' produced shape (4, 4), expected (4, 2).",
    ),
    (
        "div003_cubic_partial",
        "L2_partial_observability",
        "ValueError: Observation field 'obs_local_window' produced shape (4, 125), expected (4, 25).",
    ),
    (
        "div003_rect",
        "L1_full_observability",
        "ValueError: Non-square grids not yet supported: 8×6",
    ),
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
    sibling class sets for new shapes — not speculatively.

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


# DIV-004 — the normalization-vocabulary programme (WS-4, PDR-0054). MEASURED
# on all five default_curriculum levels by compiling the live tree against a
# worktree at the pre-change commit: exactly these three hashes move, and
# observation_spec.total_dims is unchanged at every level. `environment_hash`
# is RAW (_compute_pydantic_hash over the whole file) so it would move for any
# edit; the two DERIVED hashes are what the entry actually asserts.
_DIV004 = RegisteredHashDivergence(
    register_ref="DIV-004",
    hash_fields=("environment_hash", "observation_schema_hash", "vfs_hash"),
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
    # Names the entry under which this cell's compiled provenance hashes are
    # allowed — and required — to differ, with behaviour unchanged. Distinct
    # from pack_divergence on purpose: a declared INPUT delta and a declared
    # OUTPUT delta are two decisions (oracle_fixtures/README.md), and one does
    # not bless the other.
    hash_divergence: RegisteredHashDivergence | None = None

    @property
    def declares_pack_divergence(self) -> bool:
        return self.pack_divergence is not None

    @property
    def cell_id(self) -> str:
        p = self.params
        return f"{Path(p.pack).name}:{p.level}:{p.device}:seed{p.seed}"


def default_cells() -> tuple[Cell, ...]:
    """The full declared matrix: the standing block (all 5 default_curriculum
    levels on cpu, then all 5 on cuda), followed by the DIV-003 block (each
    fixture pack on cpu, then each on cuda).

    CUDA cells are always declared, never conditionally omitted — per spec,
    the RUN decision (whether to actually execute them) belongs to the
    harness, which reports them SKIPPED when --cuda is not passed. A matrix
    that drops CUDA cells entirely without the flag would make that skip
    silent instead of reported.

    No STANDING cell declares an expected CRASH divergence (pinned by test) —
    only the DIV-003 fixture cells do, each binding the register entry with its
    tag-verified signature. Pre-cut they land NEW_SIDE_ERROR (both sides
    crash — the divergence is not yet built); they flip to
    DIVERGED_AS_REGISTERED when the seam is cut.

    Every standing cell DOES declare DIV-004, the hash-only shape: WS-4 changes
    the authoring surface, so the frozen pack stays at the old schema, the two
    sides compile different `environment.yaml` files, and the compiled
    provenance moves by construction. The three fields are enumerated because
    they were MEASURED across all five levels, not predicted — and the cells
    still fail on any fourth mover or on any stream difference.
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
            pack_divergence="DIV-004",
            hash_divergence=_DIV004,
        )
        for device in ("cpu", "cuda")
        for level in _DEFAULT_LEVELS
    )
    div003 = tuple(
        Cell(
            RunParams(
                pack=f"configs/differential/{pack_dir}",
                level=level,
                num_agents=4,
                steps=100,
                seed=42,
                device=device,
            ),
            expected=RegisteredDivergence(register_ref="DIV-003", old_stderr_substring=signature),
            # These packs are copies of default_curriculum, so DIV-004's schema
            # change reaches them too and the frozen fixtures stay behind. No
            # hash_divergence: the old side crashes and writes no trace, so
            # there is nothing to compare hashes against.
            pack_divergence="DIV-004",
        )
        for device in ("cpu", "cuda")
        for pack_dir, level, signature in _DIV003_FIXTURES
    )
    return standing + div003
