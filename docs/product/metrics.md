# Metrics — HAMLET / Townlet             Last read: 2026-08-11 (post WS-1 verification sweep)

> **Partly measured.** The bootstrap seed was superseded the same session: the maturity assessment
> (`wf_4ca82820-274`) executed compiles, `env.reset()`, and stepping, and **Trial 001** was run by
> hand. Rows now carry a mix of *executed*, *source-traced*, and `UNMEASURED` readings — each says
> which. Targets marked `<owner sets>` still need a real number and date before they can gate
> acceptance or fire a PDR reversal trigger. A target without a number and a date is not
> falsifiable and must be rejected.
>
> **Scale note:** `src/townlet/` is **45,274 LOC** across 14 packages (assessment §7). Earlier
> figures in this session said ~37k — a ~20% underestimate. No conclusion depends on it.

## North-star

The vision says the product is **trivial authoring**: idea → running DRL gym without Python. The
north-star must therefore measure *authoring cost*, not runtime quality. Runtime quality is a
guardrail — a fast, correct substrate nobody can author against has failed at the thing it is for.

| Metric | Target (falsifiable) | Current | Read on | Trend |
|--------|----------------------|---------|---------|-------|
| **Zero-Python authoring rate (world)** — of N representative new mechanic/interaction ideas, the fraction expressible as a config pack alone, with **zero lines changed under `src/townlet/`** | ≥ `<owner sets>` of N by `<owner sets date>` | **1 of 1** — first trial passed (see below). Corpus not yet defined, so N=1 and this is an existence proof, not a rate. | 2026-08-11 | — |

### Trial 001 — "Sims in six dimensions" (PASSED, 2026-08-11)

Owner's proposed demo: take the Sims universe and re-substrate it into a 6-dimensional world.
**Executed and verified end-to-end. Zero lines changed under `src/townlet/`.**

- **Diff: one file, ~6 lines** — `stratum.yaml` `type: grid` → `gridnd`, `width/height` →
  `dimension_sizes: [4,4,4,4,4,4]`, `topology: square` → `hypercube`.
- Compiles; `env.reset()` OK; **50 `env.step()` calls OK**; agents carry 6-D positions
  (`positions` shape `(4, 6)`, e.g. `[0,3,3,1,0,3]`).
- The action vocabulary **auto-expanded from the dimensionality**: `DIM0_NEG … DIM5_POS`
  (12 movement actions) + `INTERACT, WAIT, REST, MEDITATE, GET, USE_SLOT_0, DROP_SLOT_0` = 19.
- The **entire Sims domain carried over untouched** — bars, affordances, items, effects, DAC
  rewards, curriculum. Only the substrate changed.

**One caveat, and it is a real authorability gap:** gridnd does **not** support partial vision, so
the pack's POMDP levels (L2/L3) must be switched to `active_vision: global` or the whole-pack
compile fails — the compiler builds *all* levels, not just the primary. The failure is loud and
precise, which is the good news; the limitation is genuine, and belongs in the authorability
ledger. Also noted: `grid3d` is in the `stratum.yaml` type Literal but has **no factory branch**
(`substrate/factory.py` handles grid, continuous, gridnd, continuousnd, aspatial only), so 3-D
specifically is the broken case while 4-D-and-up works.

This is the strongest available evidence for the substrate axis of the grammar, and it satisfies
`PDR-0003` obligation B (generality needs a second witness) better than a from-scratch universe
would, because holding the domain fixed isolates the variable being demonstrated.

**Scope note:** this measures authoring a *world* (UAC). Authoring a *mind* (BAC) is measured
separately in the input metrics below, because BAC Layers 1 and 3 are unbuilt — folding them into
one rate would hide which half of the thesis is failing.

**Best available proxy until the N-idea corpus exists:** the **Demo dogfooding** input metric.
Townlet Town is the first-class tech demo and is bound by the dogfooding rule in `vision.md` — it
must be authored through the same door as any user. Every privileged Python path it relies on is a
proven-load-bearing authorability gap. Unlike the N-idea corpus, this is measurable **today**
against code that already exists, which makes it the cheapest honest read on the central claim.

**Why this and not "students taught" or "coverage":** it is the only number that falsifies the
central claim. If a new mechanic still needs Python, the substrate-as-code thesis is false for that
mechanic, regardless of how green the gates are. It is measurable today with a fixed corpus of
candidate ideas and a `git diff --stat src/townlet/` check after each authoring attempt.

**Instrumentation still not built.** Trial 001 was run by hand. Defining the N-idea corpus and a
repeatable trial protocol remains a bet (`roadmap.md` → Next). Until it exists, `1 of 1` is an
existence proof, not a rate — it proves the substrate axis works, and proves nothing about the
other axes. No bet may be accepted on north-star grounds from a single hand-run trial.

## Input metrics (the levers that move the north-star)

| Metric | Target | Current | Read on |
|--------|--------|---------|---------|
| **Time-to-first-training-step** for a brand-new config pack authored from a template | ≤ `<owner sets>` min by `<owner sets date>` | `UNMEASURED` | — |
| **Config-surface coverage** — declarative subsystems needing no Python to extend (VFS variables, VTC transitions, DAC rewards, effects, items, substrate topology, curriculum) | 7 of 7 by `<owner sets date>` | **~2 of 7** — the earlier `6 of 7` estimate was wrong. Assessment §4 ledger: VTC action-writes have no YAML path at all (`compilers/actions.py:205` hardcodes `writes=()`); custom actions are structural no-ops; 3 of 4 effect scopes inert; curriculum stages are a Python literal; a new topology is a documented 4-step Python edit. Substrate *selection* works (Trial 001); substrate *authoring* does not. **2026-08-11 — the cognition surface is revealed narrower still, not improved:** per-level `architecture` selection was assumed authorable and is not (`PDR-0009`, `hamlet-0d0115383e`). Curriculum remains the weakest of the seven. **2026-08-11 (later) — FIRST MOVEMENT, and it is real.** Task 3 (`30c433e3`) made every declared affordance cost gate the live interaction; previously only a hardcoded `money` index was consulted, so `energy`/`mood`/`satiation` costs were validated and ignored. Measured shift: 35-58% of interactions that used to complete now correctly do not. **2026-08-12 — second movement.** Task 3a (`7065729a`) wired `bars.*.bounds` at all six runtime sites **and** gave the VFS observation-normalization ABI its first production callers. An author can now change a meter's runtime ceiling *and* its observation scaling from `bars.yaml` alone. Measured on L1: money `1.000000 → 22.500000` per tick, money affordances `1 of 7 → 7 of 7`. Still not 7 of 7 overall — curriculum remains the weakest, and `hamlet-e979f2ba37` now records that the five shipped levels are three universes. | 2026-08-12 |
| **Failure loudness** — an authoring mistake (missing variable, stale artefact, hash mismatch) produces a clear compile-time error rather than a silent no-op | 100% of known classes | Partially enforced, **now with measured evidence on both sides**. LOUD: VTC missing-target and checkpoint hash mismatch (`hamlet-2254316f44` / `hamlet-d5cb2dd4e7`); the item-VFS unresolved-profile guard raises rather than emitting zeros — it is loud enough that a *stale benchmark fixture* predating it now fails the suite, which is the metric working, not breaking. SILENT: the three provenance paths in the guardrail below, plus the gridnd/`grid3d` gaps. | 2026-08-11 |
| **Mind-authoring surface (BAC)** — Brain-as-Code layers declarable and *live*, of the 3 specified in `hld/02-brain-as-code.md` | 3 of 3 by `<owner sets date>` | **1 of 3, and narrower than that reads (`PDR-0009`).** Layer 2 is live **at pack scope only** — `apply_training_overrides` merges exactly five fields and `architecture` is not one, so the most basic cognitive choice in a curriculum (*does this agent have memory?*) is not authorable per level at all. Every shipped pack is feedforward; the documented L0-MLP → L2-LSTM progression is inexpressible. Layers 1 and 3 remain **unbuilt**. Tracker `hamlet-0d0115383e`. | 2026-08-11 |
| **Declared-but-inert config surfaces** — schema fields that validate and are documented but do not drive runtime behaviour | 0 | **~40 confirmed** across all 8 subsystems (assessment §3 P1). Highest-consequence: `drive.composition.normalize`/`clip`; `bars.recovery.natural` (**ships at `0.001`**, zero readers); `replay_buffer.min_size` (2 validators, real gate hardcoded); the whole `curriculum.adversarial:` block (in every shipped level, read by nobody); the recurrent encoder spec; `effects.yaml` `scope:`; `recording.enabled`. Nearly all ship at their **no-op value** — which is why it was invisible. **Count unchanged 2026-08-11, but a sibling category is now named:** four per-level content hashes (`bars`, `affordances`, `curriculum`, `training`) are computed, serialized and consumed by nobody (`hamlet-ae6601e463`). These are inert **outputs**, not inert config fields, so they are deliberately *not* added to this count — but the failure shape is identical and the fix is cheaper than any item above it. **2026-08-11 (later) — the count GREW before it shrank, and the new entries are larger than the old ones.** Newly confirmed inert: (1) the entire **VFS normalization ABI** — `apply_normalization` implements `minmax`/`zscore`/`log_scaled`/`one_hot`/`cyclical_sin_cos`, is tested, is hashed into the schema hashes, and has **zero production callers**, while the compiled `obs_meters` field description literally reads *"8 meter values (normalized)"*; (2) `clamp_and_validate`, a **declared-but-empty transition phase** — it appears exactly once in the codebase, as a string in `DEFAULT_TRANSITION_PHASES` (`hamlet-f46e2b381a`); (3) **2 of 4 brain architectures** (`recurrent`, `set_encoder`) implemented, authorable, documented, used by zero of 21 packs (`hamlet-fa6bb6da4a`, `PDR-0017`). Against that, `bars.*.bounds` was worse than inert — **contradicted**: L1 declares `money.bounds.max: 999999.0` and the runtime held it at `1.0`, killing the entire declared economy. **2026-08-12 — TWO CLOSED, ONE ADDED.** Task 3a (`7065729a`) closed both `bars.*.bounds` (contradicted → enforced at six sites) and the VFS normalization ABI (zero production callers → applied to every field that declares a spec). Newly confirmed inert in the same pass: `deficit_energy`, `deficit_satiation`, `time_since_last_eat`, `time_since_last_sleep` are declared observation fields with declared normalization and **zero writers anywhere in `src/`** — 4 of 124 observation dimensions are permanently `0.0` (`hamlet-dc8f887cd5`). The pattern `PDR-0016` named holds again: **an inert declared surface is rarely inert alone.** | 2026-08-12 |
| **Subsystem maturity established** — subsystems with an evidence-backed disposition (KEEP / REPAIR / RESPEC / REBUILD / DELETE) rather than an unknown state | 8 of 8 | **8 of 8 — COMPLETE.** All eight assessed REPAIR (run `wf_4ca82820-274`, `PDR-0004`) | 2026-08-11 |
| **Demo dogfooding — privileged-Python count** — places where Townlet Town (the first-class tech demo) uses a Python path an outside author could not use | 0 | `UNMEASURED` | — |

## Guardrails (must NOT degrade while chasing authorability)

| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| **Gates green** — `ruff check`, `black --check`, `mypy src`, `pytest` | all 4 pass | **4 of 4 — RESTORED 2026-08-11 (`c2f61beb`).** ruff pass; black 0 files; mypy `Success: no issues found in 163 source files`; pytest **2935 passed, 16 skipped, 0 failed**. The gate now also *stays* green by construction: pre-commit pinned black 25.11.0 / ruff v0.14.5 against a lock resolving 26.3.1 / 0.15.12, so every commit was formatted by a different binary than CI checked with — replaced with `repo: local` hooks running `uv run`. Prior reading, for the record: **1 of 4 — MEASURED, `PDR-0010`.** ruff **pass**; black **fail** (`environment/dac_engine.py`, +3 under `tests/`); mypy **fail** (3 errors in 2 files); pytest **fail** (1 of 2942 — a stale benchmark fixture, not a product defect). Recorded green since 2026-05-16 while three of four were red. Nothing here is deep; it went unnoticed *because the workspace said it was green*. | 2026-08-11 |
| **Test coverage** | ≥ `<owner sets>`% by `<owner sets date>` | **81% — RESOLVED, `PDR-0010`.** One clean full-suite run (`--cov=townlet`, 2942 tests, 7m53s). Both disputed figures retired. The **19%** is now *explained*, not merely superseded: re-running a single test overwrote `.coverage` and reported `TOTAL 16%` — the same artefact the 2026-05-16 report suspected of its own number. Needs one replication before it is cited publicly. | 2026-08-11 |
| **Documentation truth** — count of confirmed false architecture claims in canonical docs | 0 | **≥ 14 confirmed** and growing: `configs/L0_*`–`L3_*` packs documented in `README.md`/`CLAUDE.md` **do not exist**; `frontend/package.json` documented as runnable but **missing**; README's **70% coverage badge is false** (real: 81% — errs low, still wrong on a public repo); `CLAUDE.md`'s **29/54 observation dims are false** (measured 124 for *both* L0 and L2); `CLAUDE.md` documents **L2/L3 as LSTM/`RecurrentSpatialQNetwork`** while every shipped pack is feedforward and per-level architecture is unauthorable (`PDR-0009`). Note `caf404b8` rewrote `CLAUDE.md`/`AGENTS.md` on 2026-08-11 *without* fixing any of these — shorter, not truer, and the mtime signal is reset again. **2026-08-11 (later) — three MORE confirmed false, all in CLAUDE.md, all measured:** (1) the architecture claims — no pack constructs `SimpleQNetwork` (zero production sites; it is dead code) or `RecurrentSpatialQNetwork`; the shipped brain is `feedforward` with `layer_norm: false`, so the documented "MLP with LayerNorm" does not exist; (2) `drive_as_code.yaml` is stated REQUIRED for all packs **in two places** — every shipped pack uses `drive.yaml`, and a grep written against the documented filename returns zero hits and falsely "confirms" that no level references `money` (two packs' `drive.yaml` do); (3) "L0_0_minimal: 1 affordance / 29 dims" — measured 14 affordances and 124 dims. The second is the dangerous class: a doc error that makes a *verification* silently vacuous. **2026-08-12 — three MORE confirmed false, all measured by `diff`, all in CLAUDE.md (`PDR-0018`):** (1) the **"Low Energy Delirium" curriculum is not implemented** — `L0_0_minimal/drive.yaml` and `L0_5_dual_resource/drive.yaml` are byte-identical, both `constant_base_with_shaped_bonus`, and **no shipped level declares a `multiplicative` extrinsic**, so the documented contrast cannot be demonstrated; this is the claim `vision.md:94` calls *"the flagship demonstrator of the substrate"*; (2) the **per-level grids (3×3, 7×7) do not exist** — 8×8 is set once in pack-level `stratum.yaml` with no override path; (3) **the five levels are three universes** — `bars`/`affordances`/`drive` byte-identical across all five, `L0_5` and `L1` `training.yaml` identical but for `output_subdir`, `L0_0` vs `L0_5` `curriculum.yaml` differing only in comments. **All four of the sites this row has been tracking are now CORRECTED in CLAUDE.md** (this commit) — the first repair to this guardrail, after `PDR-0016` committed to it and `30c433e3`/`9a6de69e` did not deliver it. | 2026-08-12 |
| **Runtime throughput** — env steps/sec at the benchmarked scale axes | ≥ baseline, no regression | **Runnable, but no recorded baseline artifact is on disk** (`PDR-0011`). The benchmarks execute (the 2026-08-11 suite ran `env-step`, `env-step-scale`, `action-mask`, `reward`, `vtc-runner`) and the commits exist (`7868dba7`/`3311bc00`, `hamlet-2b92152ac9`), but `runs/` is empty, so the comparison baseline must be **re-run to be cited**. Do not quote the hot-path report's numbers as current. **2026-08-11 (later) — GPU is no longer blocked.** `torch.cuda.is_available()` was `False` with `nvrtc: failed to open libnvrtc-builtins.so.13.0`; cause was the duplicate CUDA stack above, now removed. Full suite wall-clock roughly halved (10m42s → ~5m15s). Still **no recorded env-steps/sec baseline artifact** — that gap is unchanged. | 2026-08-11 |
| **Provenance integrity** — a change to variables / observation / actions / transitions changes the corresponding hash, and a mismatched checkpoint is rejected | no silent acceptance | **BREACHED — measured end-to-end, `PDR-0008`.** Three independent silent-acceptance paths: (1) ~~the compile cache is not keyed on `primary_level`~~ **CLOSED 2026-08-11 (`22b7616d`)** — cache keyed per level, `from_dict` resolves by name rather than by a colliding hash triple, and `primary_level` is stamped into every checkpoint (D5); previously `assert_checkpoint_vfs_hash` was *satisfied by a corrupted comparand* and an L0-trained network resumed into a live L2 run with no error — then wrote a checkpoint stamped with L0's identity, so the mislabelling is **inverted and permanent**; (2) four per-level content hashes (`bars`, `affordances`, `curriculum`, `training`) are computed and read by **nobody** — `hamlet-ae6601e463`; (3) the live-inference serving path invokes **zero** identity guards — `hamlet-1029f99f4b`. `hamlet-d5cb2dd4e7`'s enforcement is real but only on the honest path. Hash-boundary tests still unwritten (`hamlet-c8c316ba03`). | 2026-08-11 |
| **Pre-release hygiene** — dead-code / orphan items outstanding against the zero-backwards-compat rule | 0 | ~15 at 2026-05-16; several removed since (`4124ab5f`, `4360148d`, `fdc08611`) — **uncounted since**. Scope widened by `PDR-0012` (strict no-tech-debt until 1.0, no research-code exemption): this row now also covers failing gates, inert surfaces, computed-but-unconsumed outputs, and broken-but-unreachable code. Needs a recount. **2026-08-11 — first recount since May, and a large one.** Removed: 13 runtime dependencies with **zero references anywhere** in the repo (`tensorflow` declared *twice*, plus `mlflow`, `pettingzoo`, `gymnasium`, `pandas`, `scikit-learn`, `flask`, `flask-cors`, `cloudpickle`, `gitpython`, `requests`, `python-dotenv`, `rich`), `apply_interaction`, `get_affordance_cost`, `check_affordability`, `money_idx`. Dependency floors corrected from fiction (`ruff>=0.0.280` against 0.15.12 running) to what is exercised. Side effect worth recording: removing `tensorflow` **restored CUDA on this machine** — it dragged a duplicate `nvidia-cudnn-cu12` stack alongside torch's `cu13`. | 2026-08-11 |

## Reading notes

- **The coverage row is resolved (`PDR-0010`) and the finding it carried still stands.** The real
  figure is **81%**; the README advertises **70%**. Being wrong in the *safe* direction does not
  make an unverified quality claim on a public repo acceptable — that is what the guardrail is for.
  The 19% is diagnosed as a partial-run `.coverage` artefact, reproduced deliberately. **Do not
  cite 81% publicly until a second full-suite run replicates it** (`PDR-0010` reversal trigger).
- **A guardrail that is not re-read is not a guardrail.** `Gates green` sat recorded as green from
  2026-05-16 to 2026-08-11 while three of its four gates were red, and every failure is trivial.
  The cost was not the failures; it was three months of false confidence. Re-read the guardrails at
  every checkpoint that touches code, not at milestones.
- **No metric has fired a PDR reversal trigger yet.** `PDR-0007`'s trigger (inert-surface count
  *rises*) is the one to watch and cannot fire until an option is enabled under it — `PDR-0009`'s
  work is the first, so the next reading of the inert count is the real test of that principle.
- **`Provenance integrity` is now the most degraded guardrail on the board**, and it guards the
  claim the whole product rests on. It is also the only row whose breach is *inverted* — a
  mislabelled checkpoint is accepted by the wrong universe and rejected by the right one — so the
  damage is not merely missing provenance but actively false provenance.
