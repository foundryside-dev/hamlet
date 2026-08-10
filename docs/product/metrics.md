# Metrics — HAMLET / Townlet             Last read: 2026-08-11 (post-assessment)

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
| **Config-surface coverage** — declarative subsystems needing no Python to extend (VFS variables, VTC transitions, DAC rewards, effects, items, substrate topology, curriculum) | 7 of 7 by `<owner sets date>` | **~2 of 7** — the earlier `6 of 7` estimate was wrong. Assessment §4 ledger: VTC action-writes have no YAML path at all (`compilers/actions.py:205` hardcodes `writes=()`); custom actions are structural no-ops; 3 of 4 effect scopes inert; curriculum stages are a Python literal; a new topology is a documented 4-step Python edit. Substrate *selection* works (Trial 001); substrate *authoring* does not. | 2026-08-11 |
| **Failure loudness** — an authoring mistake (missing variable, stale artefact, hash mismatch) produces a clear compile-time error rather than a silent no-op | 100% of known classes | Partially enforced — VTC missing-target and checkpoint hash mismatch fail loudly per `hamlet-2254316f44` / `hamlet-d5cb2dd4e7` | 2026-08-11 |
| **Mind-authoring surface (BAC)** — Brain-as-Code layers declarable and *live*, of the 3 specified in `hld/02-brain-as-code.md` | 3 of 3 by `<owner sets date>` | **1 of 3** — Layer 2 (architecture/optimizer/loss/replay) is live in `brain.yaml` + `config/brain_config.py` + the agent factories. Layer 1 (behaviour contract, ethics, panic, personality) and Layer 3 (think-loop execution graph) are **unbuilt**. | 2026-08-11 |
| **Declared-but-inert config surfaces** — schema fields that validate and are documented but do not drive runtime behaviour | 0 | **~40 confirmed** across all 8 subsystems (assessment §3 P1). Highest-consequence: `drive.composition.normalize`/`clip`; `bars.recovery.natural` (**ships at `0.001`**, zero readers); `replay_buffer.min_size` (2 validators, real gate hardcoded); the whole `curriculum.adversarial:` block (in every shipped level, read by nobody); the recurrent encoder spec; `effects.yaml` `scope:`; `recording.enabled`. Nearly all ship at their **no-op value** — which is why it was invisible. | 2026-08-11 |
| **Subsystem maturity established** — subsystems with an evidence-backed disposition (KEEP / REPAIR / RESPEC / REBUILD / DELETE) rather than an unknown state | 8 of 8 | **8 of 8 — COMPLETE.** All eight assessed REPAIR (run `wf_4ca82820-274`, `PDR-0004`) | 2026-08-11 |
| **Demo dogfooding — privileged-Python count** — places where Townlet Town (the first-class tech demo) uses a Python path an outside author could not use | 0 | `UNMEASURED` | — |

## Guardrails (must NOT degrade while chasing authorability)

| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| **Gates green** — `ruff check`, `black --check`, `mypy src`, `pytest` | all 4 pass | Passed at milestone baseline (`hamlet-c994a795e9`, comment 93); **not re-run this session** | 2026-05-16 |
| **Test coverage** | ≥ `<owner sets>`% by `<owner sets date>` | **DISPUTED — 19% vs 70%.** `README.md` badge claims 70%; the 2026-05-16 quality assessment measured **19%** from a single `.coverage` artefact of unverified run-scope and rated the headline number **High-risk unreliable** in its own §0.2. Neither figure is currently trustworthy. | 2026-05-16 |
| **Documentation truth** — count of confirmed false architecture claims in canonical docs | 0 | **≥ 12 confirmed** (2026-05-16 report §catalog-10) and growing: `configs/L0_*`–`L3_*` packs documented in `README.md`/`CLAUDE.md` **do not exist** (actual: `aspatial_test`, `default_curriculum`, `L5_multi_agent`, `reference`, `simple`, `test`); `frontend/package.json` documented as runnable but **missing**. | 2026-08-11 (verified this session) |
| **Runtime throughput** — env steps/sec at the benchmarked scale axes | ≥ baseline, no regression | Baseline is **runnable and recorded** (`hamlet-2b92152ac9`, commits `7868dba7`/`3311bc00`); exact numbers live in the hot-path report, not duplicated here | 2026-05-16 |
| **Provenance integrity** — a change to variables / observation / actions / transitions changes the corresponding hash, and a mismatched checkpoint is rejected | no silent acceptance | Enforced for checkpoints (`hamlet-d5cb2dd4e7`); **hash-boundary tests not yet written** — open as `hamlet-c8c316ba03` | 2026-08-11 |
| **Pre-release hygiene** — dead-code / orphan items outstanding against the zero-backwards-compat rule | 0 | ~15 at 2026-05-16; several removed since (`4124ab5f`, `4360148d`, `fdc08611`) — **uncounted since** | 2026-05-16 |

## Reading notes

- **The coverage row is a finding, not just a metric.** The product currently advertises a number
  (70%) that its own architecture audit contradicts (19%, itself untrusted). Publishing an
  unverified quality claim on a public repo is the kind of thing the guardrail exists to catch.
  Resolving it needs one clean full-suite run under coverage — see `current-state.md` open
  questions. Until then, treat **both** numbers as unusable and do not cite either.
- No metric here has ever fired a reversal trigger, because no PDR predates this bootstrap.
