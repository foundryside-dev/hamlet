# T15 finite interface technical review — Astra medium r1

Verdict: **APPROVE** the complete R1 technical proposal. The sole r0 constructor-preservation finding is resolved. No further proposal amendment, user permission, task/lens expansion or source search is required. This approves the finite interface design, not implementation, predecessor release or executable acceptance.

Reviewed proposal: `T15-interface-proposal-r1.md`, SHA256 **70b155234f553855675a235d980674afdc3588d92e71dd054bba5b69f0e56d0a**. Observed HEAD **b3003550b7c1dad76a52e596b2af01658fa2b92d**. Original proposal and r0 review remain unchanged; r0 review hash is `25f1524240071ee9c14341078929dc768a9d9f210b2415e09cb093f4e06b90ba`.

## Same exact bounded source context

Existing `/workspace/hamlet` only; unchanged charged inventory **4 files/2450 lines**:

| Alias | Complete source | Lines | SHA256 |
|---|---|---:|---|
| POP | `src/townlet/population/vectorized.py` | 1854 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| RC | `src/townlet/training/replay_contract.py` | 222 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| QT | `src/townlet/training/q_targets.py` | 80 | `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f` |
| OP | `src/townlet/config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |

The reserved learner test remains absent. Future ceilings POP3000/RC250/QT100/OP600/test1000 remain5/4950. No fifth implementation source, SB/PB/RB/runner/provider/brain/network/helper/test source was opened. Previously read guidance and owner preservation/History A rulings remain applicable. All14 worktrees were preserved.

Consumed the new runtime/unit/supplier/factory-bridge receipts as **prose only**, at their proposal-listed hashes `9048ba713a2540bc8a8e7bf9e45ebbc01ba619b3732a32663dc0049c1104d23c`, `3d4b45239fa0eed2c7a5a87995b5143137eed1a67927e81d06ecb48958490e41`, `0ce1d3732ba2ff231495dbecbe8f2f73c04da18cf5f2bb850bb71fb5a2793f19`, and `ffe98bb8fa69aef0c1f338d4816375530e69499956999bb2351ace574e81b789`. Their source inventories are their owners' inventories, not extra sources for this review.

## Why r0 R1 is closed

The receipts establish actual runtime RR/EL learner paths, LI serving, and named successful real fixture suppliers. The source-verified ENV initializer retains the selected level and already consumes `level.training`; the separately counted81-line factory bridge calls that initializer directly. No demonstrated carrierless learner remains. This is supplier evidence, not inference from annotations or fixture names.

The proposal now gives exact normal compiled-adapter, explicit factory, and construction/serving roles. Normal learning uses central OP resolution and actual declared minimum/seed/limits; the explicit factory retains required inputs and the passed effective brain. Serving/inspection preserves nullable limits and legacy/global sampler roles without requesting learner inputs merely for construction. Actual low-level/manual fixture purposes are distinguished from successful learning. The named capture/warmup/eligible-selector fixture adjustments belong to existing bounded owners; they do not excuse incorrect optimizer behavior or narrow acceptance.

## Lazy setup: binding existing state, not resetting it

I checked the new lazy mechanism against actual POP storage and load behavior. POP244–284 constructs and publicly exposes replay before the first step; POP456–484 can store collector data; POP1178–1197 serializes that replay; POP1737–1778 validates/materializes and installs replay and cumulative clocks before any later step. The runtime receipt confirms RR loads after constructing and before stepping. Therefore “first step” is not evidence that replay is fresh, empty, unconfigured or at tick0.

R1 already expressly disallows dropping owned data, reseeding/reconfiguring restored state and live pre-load clock mutation. Those requirements make the mechanism sound. The concrete implementation interpretation, carried forward into authoring/review, is:

- The eager factory binds its complete setup once. The lazy adapter resolves/binds learner policy before first experience admission, but does not rerun the common object initializer, replace learned network/optimizer state, clear collector lists, or reconstruct replay merely because its own setup marker was unset.
- Fresh replay configuration is legal only for the genuinely pristine, population-owned constructor buffer. Zero retained rows alone is insufficient: empty buffers can still own archives, next-ID counters, beta/RNG state, selected modes or prior clock history. A current loaded or externally attached qualified buffer must be adopted/validated with its existing state, not treated as a blank factory target. Preserve applicable low-level inspection roles independently of whether learning has been entered.
- A successful raw POP load installs its replay and restored total_steps consistently with the learner setup/binding. Its first later step preserves current rows, stable IDs/domains, priorities, sampler state and beta, then paces from restored total_steps to the next actual vector tick. It does not supply fresh tick0 or rerun configure_sampling. A setup marker alone cannot override the actual installed buffer's ownership/configuration. Existing qualification checks and supplied matching configuration govern; no silent policy switch is allowed.
- Where an accepted old/current adaptation genuinely needs a different target, use the already specified offside prepare/validate/materialize/install path. In particular, captured6-to-prioritized7 uses the known restored tick before installation. Preserve active captured history and approved old archives as specified; do not mutate the live target's tick to make fallible preparation succeed. Unknown-legality manual data never becomes optimizer input through lazy setup.

These are direct consequences of R1's explicit preservation/restore requirements, not a new state format, public API, task or additional design decision. The exact private setup representation is an implementation choice. Existing T15 current-restore/constructor tests must cover load-before-first-step and already-owned qualified state so a superficially plausible unconditional setup call cannot pass. No broader native guarantee is inferred: T24/T25 still own the complete native10/7 envelope and configuration/atomic/stochastic continuation acceptance.

## Retained technical acceptance and limits

The other mechanisms accepted in r0 remain accepted: actual selected recurrent PER with one common initializer; explicit separate PCG64 training-seed policy and truthful per-leaf/horizon provenance; exact stored successors under each network's own real prefix with connected online BPTT; exclusion of padding; once-weighted unit objectives and stable priority feedback; strict eligible provider filter/select/scatter preserving nonselection effects; all-real-row unweighted float64 X04 telemetry; vector-tick beta and successful-update LR/target clocks; archive/new-row warmup/current captured preservation. C01/C02/C05/C06/C07/C12/C13 obligations are not closed by this proposal review.

All finite causal controls, existing owner/B03 gates, actual recurrent-PER construction, two real finite X04 updates, changed-source full G2 trigger, six guards and fresh implementation review remain required. No optional scope churn, hidden warmup/seed, false-brain/manual-attachment production proof, unmasked optimizer fallback or capability removal is approved.

## Custody and stationary return

Read-only checks verified the proposal/r0 review/four source hashes, observed HEAD and clean tracked status. Only this ignored prose review was written. No project imports/runtime, pytest/collection, probes, compiler/linter/gate, source/tests/index/tracker edits, branch/worktree/source-tree copy/deletion, subagent, commit or publication occurred. No durable user-only permission rule is claimed.

Root reports corrected T14 R2 full qualification active at68% with no failure at this review's dispatch. That is attributed progress, not PASS; T14 remains unqualified/unreleased until its actual full gate closes. This approval alone does not authorize premature T15 implementation. Return stationary for root's qualified bounded dispatch and later implementation verification.
