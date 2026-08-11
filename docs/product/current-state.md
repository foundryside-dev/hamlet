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

- ~~⚠️ **A poisoned compile cache is in the working tree right now.**~~ **CLOSED — WS-1(a) landed
  (`22b7616d`).** Before the fix, four of five levels were served L0's projection
  (`9ddda35aebfb2357`). The cache is now keyed on `primary_level`, one artifact per level, with a
  hard guard outside the defensive read. The stale artifacts are deleted; the repro lives in
  `tests/test_townlet/integration/test_compile_cache_level_identity.py` instead of the working tree.
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
  path remain untested. **No longer blocked**: this machine's CUDA was broken with
  `nvrtc: failed to open libnvrtc-builtins.so.13.0`; the cause was `tensorflow[and-cuda]` — an
  entirely unused dependency — dragging a duplicate `nvidia-cudnn-cu12` stack alongside torch's
  `cu13`. Removed in `e082afd5`; `torch.cuda.is_available()` is now `True` and the suite runs
  ~2× faster. GPU determinism work can proceed.
- **Design fork inside `PDR-0009`** — per-level `architecture` override, or make `brain.yaml`
  level-overridable the way `training.yaml` is? The second is more coherent with the grammar.
  Decide before implementing.
- **README push** remains the owner's call; drafting and committing locally is already endorsed.

Closed this session: *"what is the real test coverage?"* — **81%** (`PDR-0010`).

## This session did (implementation)

- **Task 1 — the four gates are green** (`c2f61beb`). black 4→0, mypy 3 errors→0, benchmark
  1 failed→3 passed with value assertions. Root-caused *why* the black gate kept re-breaking:
  pre-commit pinned black 25.11.0 / ruff v0.14.5 while the lock resolved 26.3.1 / 0.15.12, so every
  commit was formatted by a different binary than CI checked with. Now `repo: local` hooks.
- **Dependencies brought back to reality** (`e082afd5`). **Thirteen** runtime dependencies had zero
  references anywhere — including `tensorflow`, declared *twice*. Removing it **fixed CUDA on this
  machine**. `uv.lock` is now tracked (it was gitignored — untenable for a provenance product).
  Floors were fiction (`ruff>=0.0.280` against 0.15.12 running) and now state what is exercised.
- **Found WS-0's root cause.** `.gitignore` carries a blanket `*.json` under a "# Data" heading;
  it is global and silently excluded `frontend/package.json`. `hamlet-d892e161c0` reads as
  "package metadata is missing" when the truth is **it was never committable**. Manifests are now
  negated explicitly; narrowing the rule fully is WS-0's call (it also catches `.mcp.json`).
- **Task 2 — WS-1(a) closed** (`22b7616d`), including the `from_dict` hash-triple scan that
  survives the filename fix on its own.
- **Second review + `PDR-0015`** (`2a63b95f`): `PDR-0014`'s bounds site list was an undercount and
  the omitted site was the only one that binds. Filed `hamlet-f46e2b381a` for the architecture half.

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

**Continue the WS-1 fix plan: `docs/plans/2026-08-11-ws1-fix-set.md`.** Re-reviewed and cleared
**APPROVED_WITH_AMENDMENTS** (`PDR-0015`). **Read §0 AND §0.1 first — §0.1 overrides both the task
text and §0 where they conflict.**

Order: ~~gates(1)~~ → ~~a(2)~~ → **d(3) ← next** → bounds(3a) → new1(4) → new2(5) → b(6) → c(7) →
close(8), plus sibling `3b` (`hamlet-88acec4bb5`) after 3a and before the freeze.

**Landed:** task 1 (`c2f61beb`, four gates green), dependencies (`e082afd5`), task 2
(`22b7616d`, cache keyed on `primary_level` + `from_dict` by-name lookup + D5 stamp pulled
forward). Suite **2935 passed, 0 failed**; ruff/black/mypy green.

**Next up — task 3 (WS-1(d), declared non-money costs gate the interaction).** Note §0.1's task 3
edits: do **not** delete the clamp (reversed), and its pinning literals now carry an explicit
scenario (all meters seeded to `0.5`) without which `successful_interactions == {}` fails at step 1.

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
