# Current State — HAMLET / Townlet        Checkpoint: 2026-08-11 · second checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — freeze the current
system as an oracle, then knock down and rebuild one design-space unit at a time against it.
Guarded by **Provenance integrity**, which this session measured as **BREACHED**.

## In flight

Recovery milestone **`hamlet-1ade187dcc`**, work streams WS-0…WS-7.

- **WS-1** `hamlet-67ffbd282a` (P0) — **ready, gates the oracle freeze.** All four defects now
  **confirmed by execution** (`PDR-0008`), plus two new provenance issues split out:
  `hamlet-ae6601e463` (four per-level hashes stamped by nobody — cheapest high-value fix in the
  set) and `hamlet-1029f99f4b` (serving path runs zero identity guards).
- **WS-7** `hamlet-e3af412673` (P0) — the strangler's enabling stream. Blocked by WS-1. Contains
  `hamlet-834108b55a` (no seeding API).
- **WS-6** `hamlet-5e39fcccb0` — **ready.** Head of the critical path.
- **WS-0** `hamlet-8eeaba1461` — **ready.** `frontend/package.json` confirmed still missing.
- **WS-2/3/4/5** — `hamlet-337b9e80fb`, `1f89714685`, `15050f280a`, `ad2773718a`. Blocked.
  WS-4 gained `hamlet-0d0115383e` (per-level `architecture` unauthorable, `PDR-0009`).

Tracker drift from last session is resolved: `hamlet-7a932c4e40` closed `cancelled`,
`hamlet-f2c7439b63` closed superseded.

## Open questions / blocked-on-owner

- ⚠️ **A poisoned compile cache is in the working tree right now.**
  `configs/default_curriculum/.compiled/universe.msgpack` holds **L0's** projection. Any run at
  L0_5/L1/L2/L3 before WS-1(a) lands silently resumes the wrong weights *and* writes checkpoints
  stamped with the wrong identity. `rm -rf configs/*/.compiled` before the next run. It is
  deliberately **not** deleted — it is the standing repro.
- ~~Owner decision — audit `runs/`?~~ **CLOSED, `PDR-0011`.** Audited on owner authorisation:
  `runs/` holds only `.gitkeep`, **zero `.pt` files exist anywhere in the tree**, and no tensorboard
  or run-database artifacts exist. Nothing to cut loose; no deletion was required or performed. The
  provenance breach did **zero historical damage** — it is a live hazard, not a legacy one. Policy
  recorded: no artifact predating the WS-1 provenance fixes is trusted evidence, and any that
  surfaces later is discarded rather than re-stamped.
- ~~Owner decision — promote no-tech-debt into `vision.md`?~~ **CLOSED, `PDR-0013`.** Owner
  approved (*"absolutely load bearing"*). Added as a distinct anti-goal that **generalises** the
  backwards-compatibility one rather than replacing it — the older entry's enumerated patterns
  (fallbacks, deprecation warnings, "support both") are what make it enforceable in review and
  would have been lost in a merge. `vision.md` now carries an **amendment log**; the authority
  grant is untouched.
- **Which knockdown is first?** Terrain/substrate remains the strongest candidate — three of four
  substrate crashes collapse to one change, and it is where the 6-D demo hits its only wall.
- **Determinism beyond CPU** — GPU float nondeterminism and the `vtc_kernels.py` TorchScript-JIT
  path remain untested. Note: this machine's CUDA is currently broken
  (`nvrtc: failed to open libnvrtc-builtins.so.13.0`), so GPU verification is blocked on that.
- **Design fork inside `PDR-0009`** — per-level `architecture` override, or make `brain.yaml`
  level-overridable the way `training.yaml` is? The second is more coherent with the grammar.
  Decide before implementing.
- **README push** remains the owner's call; drafting and committing locally is already endorsed.

Closed this session: *"what is the real test coverage?"* — **81%** (`PDR-0010`).

## Last checkpoint did

- **Verified WS-1 by execution** — 20 agents, adversarial lenses per verdict, plus a completeness
  critic. (b), (c), (d) and both session findings **confirmed**; (d) narrowed to its affordability
  leg; **four claims retired as false alarms**; fix order changed on reachability grounds — (b)/(c)
  are correct but unreachable on all 21 shipped packs. `PDR-0008`.
- **Filed three new issues** — two provenance defects under WS-1, and the authorability gap under
  WS-4. `PDR-0009` classifies the last of these as *an option not yet enabled*, not a bug.
- **Read the guardrails for the first time since 2026-05-16.** Coverage resolves to **81%** and the
  disputed 19% is *diagnosed* as a partial-run artefact (reproduced deliberately). `Gates green` is
  **1 of 4**, not 4 of 4 — recorded green for three months while three were red. `PDR-0010`.
- **Resolved the workspace's contradiction with itself** — `roadmap.md` now matches `PDR-0006` §2b
  on EnvFactory and states the Now bet in strangler/oracle terms.

## Next session, start here

**Execute the WS-1 fix plan: `docs/plans/2026-08-11-ws1-fix-set.md`.** Nine tasks, reviewed by four
`axiom-planning` lenses (zero hallucinations across ~45 checked claims; sequencing and pinning-test
discipline clean), with three blockers resolved in the plan's §0 by `PDR-0014`. **Read §0 first —
it overrides the task text where they conflict.** Order per `PDR-0008`: gates → (a) cache key +
`primary_level` → (d) affordability → four-hash stamp → serving guards → (b) → (c), plus
`hamlet-88acec4bb5` (dead-agent filter) and the `bars.*.bounds` wiring.

The plan's own review does **not** carry forward — re-review after the amendments land.

Two traps recorded on `hamlet-67ffbd282a`, both of which will bite silently:
1. **(c)'s spec does not compile against (b)'s** — (b) makes `hidden` a required positional and
   deletes `self.hidden_state`, which (c)'s pinning-test mitigation depends on. Rewrite (c) against
   (b)'s post-fix API; do not extend it.
2. **(a)'s spec does not touch `compiled.py:487-499`**, where `from_dict` rebuilds the transition
   schedule by scanning for the *first* level matching a hash triple, with no primary-level check.
   Sound-by-construction today, but it survives (a) unless someone adds the lookup.

Do not re-litigate `PDR-0006` (strangler) or `PDR-0007` (universality + definition-of-done); both
were decided with the owner on evidence. Read `vision.md` first — it is ENDORSED, and changing it
escalates.
