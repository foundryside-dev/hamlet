# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 (latest) · seventeenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). **Both merge gates to
`main` are now SATISFIED** (`PDR-0048`) — gate 1 at `dd94e122`, gate 2 (README re-verification
*by method*) at `1b25c99d`. **Neither is banked**: `PDR-0039` fires the sweep again at the merge,
unconditionally, and three commits have landed since. The merge itself is the owner's call.

The session's other half was the compiler's authoring grammar, and it produced **an owner ruling**
(`PDR-0047`) that now governs the Next bet's first concrete unit.

**READ `docs/architecture/vfs.md` AND `docs/architecture/vfs-current-implementation.md` BEFORE
TOUCHING VFS** (binding; the owner named both this session, and following them corrected a claim
this session had just written).

## Owner state (2026-08-15)

- **Grant re-confirmed, scope unchanged**, at this session's `/own-product`. `vision.md`'s stamp
  is now correct — `Last reviewed: 2026-08-15`, owner-approved, amendment-logged (`PDR-0050`).
  The two-checkpoint bookkeeping debt is **closed**. Next review due **2026-09-15**.
- **`PDR-0046` stands**: the agent may commit and push `project-recovery` without asking. The
  merge to `main` and anything outward-facing still stop for the owner.
- **Owner rulings this session, both load-bearing:**
  1. *"It should work like a regular compiler, the author defines it from a list of pre-approved
     types, scalings and so on"* — `PDR-0047`, resolving the `semantic_type` fork to option (a).
  2. The scope-setting example: *"money might be an int between 1 and 100 capped for an
     individual, or it might be a log float that models a GDP multiplied by through sin(time)."*
     Both are `money`; neither is more correct; the palette must express both without Python.
- **Owner directed, in-flight now:** run **Trial 002** (author both money designs as config, zero
  lines under `src/townlet/`) **before** building the fix. *"and then move straight into the
  trial."*

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **`hamlet-2fe1c34ebb`** (P1, the decided direction) — `semantic_type` has three disagreeing
  vocabularies and no authority; the authored declaration is never consulted; `default="custom"`
  violates No-Defaults on a parameter that feeds a provenance hash. Governed by `PDR-0047`'s four
  rules (comment 145). **Hash-moving → takes the `PDR-0037` register-first order**, with
  `PDR-0041` as the worked example. Also governs `hamlet-365e996511` (`range_type`) per the
  ruling's *"and so on"* — coordinate, do not solve them differently.
- **`hamlet-cbb747a51e`** (P2, new) — a pack compiles, prints `Compilation succeeded`, exits 0,
  and silently writes **no cache artifact**. CI cannot see it: the gate runs `validate`, which
  writes no cache. *The covered command and the broken command are not the same command.*
- **`hamlet-f9090ec3e8`** (P2, new) — `test_vfs_overhead_under_limit` is flaky by construction
  (5% wall-clock ratio under always-on coverage) and sits in the CI gate.
- **`hamlet-c4ce5515cc`** (P2) — still owns the `hasattr` antipattern at `metadata.py:83`; that
  line was reclassified, not fixed, by `PDR-0049`.
- **WS-7** `hamlet-e3af412673` (P0, in progress, claude — claim to 2026-08-17 00:49 UTC). Open
  DECIDE unchanged: close now, or keep as the standing knockdown home.
- **WS-3** `hamlet-1f89714685` still gates WS-4 `hamlet-15050f280a` (`PDR-0034`). **WS-6**,
  **WS-0**, **WS-5** (`hamlet-7a52a63e0b`, body still gated by its own notes) ready, untouched.
- ~~`hamlet-60dd3c4b53`~~ — **CLOSED** by deletion+correction; its headline was falsified by
  execution. Do not re-derive the observation-hash claim.

## What this checkpoint did

- **Closed merge gate 2** (`PDR-0048`). Ten README claims had gone stale in one day, every one
  because the recovery fixed what was described. Filed `hamlet-cbb747a51e` from the sweep.
- **Falsified `PDR-0045`'s two cited violations by executing them** (`PDR-0049`). `vfs_adapter.py`
  was **dead code** — zero callers, not even imported by the compiler — so the "currency name
  changes the observation schema hash" claim is false in the shipped compiler; `metadata.py:83`
  runs but nothing consumes its output. Deleted the module and its tests, **proved inert** by a
  byte-identical hash diff across all five levels and five hash fields. **The principle is
  untouched; the instances were struck by pointer** (`PDR-0020` practice). The
  `Demo dogfooding` metric's counting rule changed with it: **count executed behaviour, not grep
  hits.**
- **Recorded the owner's authoring-grammar ruling** (`PDR-0047`), and — following the owner's
  pointer to `vfs.md` — found that **`vfs.md` §9.2's ten normalisation kinds are all declarable,
  all implemented, and wired since WS-1(e)**. The scalings palette the ruling describes already
  exists. The real gaps are three *bindings*: `range_type` inert, no integer type, no expression
  slot on a bar.
- **Closed the `vision.md` grant-stamp debt** with owner approval (`PDR-0050`).

## Next session, start here

1. **Trial 002 is in flight and owner-directed** — author both money designs as config, zero lines
   under `src/townlet/`. `PDR-0047` records the *predicted* outcome (money A fails on the missing
   integer type; money B fails on the absent bar-level expression binding) **so the trial can
   falsify it**. Report what actually happens, not what was predicted.
2. **Then `hamlet-2fe1c34ebb`**, register-first. Do not start with the code.
3. **The merge is available but not taken.** Both gates satisfied; gate 2 re-fires at the merge;
   `PDR-0043` trigger 2 (nightly cron) rides the checklist.

**Harness gate contract** (carry): `uv run python -m townlet.oracle.harness` — exit 0 iff every
cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its register entry; empty and all-SKIPPED
runs fail. NOT safe to run concurrently with itself in one checkout.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before measurements; verify red by
mutation; a green test is not evidence; a correction is not self-verifying; a verifier is not
self-verifying. **New (`PDR-0049`), and the sharpest of this session:** *a red found by reading is
not a defect until it executes* — this project already knew a green tool is not evidence
(`PDR-0033`) and a recorded green is not a green (`PDR-0010`); this is the mirror, and **the
cheapest fix would have been indistinguishable from progress**. Also: *when two quantities share a
name, say which*; *count executed behaviour, not grep hits*; *a gate that reddens at random is how
a verified gate becomes a waved-through gate*; and — three times this session — ***the false claim
was in this workspace's own files, including one written earlier in the same session***.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0032`, `PDR-0034`–`PDR-0042`,
`PDR-0043` (nightly deferral), `PDR-0044`, `PDR-0045` (principle intact — only its two cited
instances are struck, per `PDR-0049`), `PDR-0046` (the boundary is the merge, not the push),
`PDR-0047` (owner ruling — reverse only via its three triggers), `PDR-0048`, `PDR-0049`, `PDR-0050`.
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-15, unchanged; changing it escalates.
