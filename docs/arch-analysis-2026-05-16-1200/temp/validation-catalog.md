# Validation Report — 02-subsystem-catalog.md

## Verdict

**NEEDS_REVISION (warnings only)** — the catalog is structurally sound, all
eight subsystems present, dependency matrix internally consistent, and 8 of
10 high-risk spot-check claims confirmed verbatim against source. However
**two claims in §11.1 and §11.2 are refuted** by wider-scope greps that
SG6 and SG2 explicitly asked the validator to perform; both must be edited
before the catalog is used to drive document recreation. Neither rises to a
critical block — they are tech-debt-class precision fixes.

The "RecurrentSpatialQNetwork input dim is 240 not 192" claim in §10 row 8
was not requested for ground-truthing and is left to the SG6 author; flagged
as a follow-up.

## Coverage check

`ls /home/john/hamlet/src/townlet/` returns 15 child entries (excluding
`__init__.py`, `__pycache__`, `py.typed`):

| Subdir | Catalog coverage |
|--------|------------------|
| `agent/` | SG6 |
| `config/` | SG3 |
| `curriculum/` | SG6 |
| `demo/` | SG8 |
| `effects/` | SG7 |
| `environment/` | SG4 |
| `exploration/` | SG6 |
| `items/` | SG7 |
| `population/` | SG6 |
| `recording/` | SG8 |
| `substrate/` | SG5 |
| `training/` | SG6 |
| `universe/` | SG1 |
| `vfs/` | SG2 |
| `world/` | SG5 (DSL) |

All 15 covered. No subsystem missed.

## Contract compliance

| Required section | Present | Notes |
|---|---|---|
| Per-subsystem summary (8 entries) | ✓ | §§1-8, one for each SG |
| Cross-subsystem dependency matrix | ✓ | §9, 11×11 matrix |
| Documentation drift catalog | ✓ | §10, 12 rows |
| Aggregated concerns (dead code, latent bugs, perf, doc, structural, security) | ✓ | §11.1-11.6 |
| Coordinator notes for downstream phases | ✓ | §12 |
| Confidence summary | ✓ | Per-SG confidence table |
| Per-claim citations | ✓ (delegated) | Catalog defers to `temp/sgN-*.md`; spot-checked 10 |

Section ordering matches the system-archaeologist contract.

## Spot-check results

### A. SG6: `icm.py`, `count_based.py`, `adaptive_rnd.py` do not exist in `exploration/`

**Command**: `ls /home/john/hamlet/src/townlet/exploration/`
**Output**:
```
action_selection.py  adaptive_intrinsic.py  base.py
epsilon_greedy.py  __init__.py  __pycache__  rnd.py
```

**Verdict: CONFIRMED.** None of the three CLAUDE.md-named files exist.
Catalog §10 row 7 and §6 are correct.

### B. SG6: `decay_epsilon()` never called within SG6 scope

**Command**: `grep -rn "decay_epsilon" src/townlet/{agent,population,training,exploration,curriculum}`
**Output**:
```
src/townlet/exploration/epsilon_greedy.py:92:    def decay_epsilon(self) -> None:
src/townlet/exploration/adaptive_intrinsic.py:191: def decay_epsilon(self) -> None:
src/townlet/exploration/adaptive_intrinsic.py:193:     self.rnd.decay_epsilon()
src/townlet/exploration/rnd.py:302:    def decay_epsilon(self) -> None:
```

The only callers within SG6 scope are the strategy's own internal
self-delegation (`adaptive_intrinsic.py:193` calls its inner `rnd`). No
external SG6 caller. **Within SG6 scope: CONFIRMED.**

**However**, broadening the grep to all of `src/townlet/`:
```
src/townlet/demo/runner.py:933:    self.exploration.decay_epsilon()
```

The demo runner — which IS the actual training driver invoked by
`scripts/run_demo.py` — calls `decay_epsilon()` once per episode at
`runner.py:933`. SG6's own report (`temp/sg6-training.md:649`) **explicitly
asked the validator to perform this wider-repo grep**.

**Verdict on §11.2 "Epsilon schedule may be dead": REFUTED.** The schedule
is alive at the demo runner. The §11.1 row "`decay_epsilon()` defined but
never called from training loop" is **imprecise**: it IS called from the
training driver (`DemoRunner.run`), just not from `VectorizedPopulation`.
**Required revision** — see below.

### C. SG6: `StructuredQNetwork` unreachable via `NetworkFactory`

**Command**: enumerated `build_*` methods in `network_factory.py`
**Output**:
```
build_feedforward (line 24)
build_recurrent  (line 73)
build_dueling    (line 139)
build_set_encoder (line 181)
```

No `build_structured`. `grep "StructuredQNetwork" src/` returns only the
class definition at `networks.py:558`; zero usage outside its own file.

**Verdict: CONFIRMED.** Catalog §11.1 entry is correct.

### D. SG2: VTCInteractionProgress / VTCSocialResidue runtime call sites

**Command**: `grep -rn "VTCInteractionProgressProgram|VTCSocialResidueProgram|interaction_progress_program|social_residue_program" src/townlet/`

**Findings:**

`VTCInteractionProgressProgram` IS wired at runtime:
```
src/townlet/environment/action_executor.py:153  has_multi_tick_affordances()
src/townlet/environment/action_executor.py:182  contains_affordance(...)
src/townlet/environment/action_executor.py:239  env.vtc_interaction_progress_program.apply(...)
src/townlet/universe/compiler.py:406  interaction_progress_program=transition_interaction_progress
```

`apply()` is called per-tick from `ActionExecutor._advance_vtc_interaction_progress`
at `action_executor.py:239`.

`VTCSocialResidueProgram`: full search across `src/townlet/` shows it
referenced **only** in `vfs/vtc.py` (definition + compile helpers),
`vfs/__init__.py` (export), `vfs/schema_hashes.py` (hashing input), and
`vfs/transition_graph.py:20` (phase label `"apply_social_residue_effects"`).
**No `apply()` call site exists anywhere in `src/townlet/environment/`** or
in any runtime path.

**Verdict on InteractionProgress: REFUTED.** The catalog claim "call sites
could not be found" is wrong — `action_executor.py:239` is the call site
and SG2's own narrative (sg2-vfs.md:62) explicitly hedges "runtime caller
not located in this scan — see Concerns", inviting validator re-grep.

**Verdict on SocialResidue: CONFIRMED.** It is compiled but never executed
at runtime. Genuinely dead.

The catalog §11.1 row lumps both together; this row must be split.

### E. SG8: `frontend/package.json` missing

**Command**: `ls /home/john/hamlet/frontend/package.json`
**Output**: `ls: cannot access '/home/john/hamlet/frontend/package.json': No such file or directory`
`ls /home/john/hamlet/frontend/` shows: `demo.html  index.html  RECOMMENDATIONS_P0-1.md  src  vite.config.js`.

**Verdict: CONFIRMED.** Catalog §8C and §10 row 11 are correct. This is a
critical user-facing breakage (CLAUDE.md instructs `npm run dev`).

### F. SG8: `flask`/`flask-cors` unused in `src/`

**Command**: `grep -rn "from flask\|import flask" src/`
**Output**: (empty; exit code 1 — no matches)

`grep -n "flask" pyproject.toml` shows:
```
50: "flask>=3.0.0",
51: "flask-cors>=4.0.0",
```

**Verdict: CONFIRMED.** Catalog §10 row 12 and §11.1 last row correct.

### G. SG4: `reward_strategy.py` fully deleted

**Command**: `find src -name "reward_strategy*"` → empty.
`grep -rn "RewardStrategy\b" src/` → empty (exit 1).

**Verdict: CONFIRMED.** Catalog §4 verification claim correct. Note: the
SG4 sub-claim that the CLAUDE.md "583 lines" figure should actually be 234
deletions (catalog §10 row 6) was NOT independently re-verified here —
trusting SG4's `git log -p` reading.

### H. SG3: Config layout is `configs/<pack>/levels/<level>/`

**Command**: `find configs -maxdepth 3 -type d`
**Output (excerpt)**:
```
configs/default_curriculum/levels/L0_0_minimal
configs/default_curriculum/levels/L0_5_dual_resource
configs/default_curriculum/levels/L1_full_observability
configs/default_curriculum/levels/L2_partial_observability
configs/default_curriculum/levels/L3_temporal_mechanics
configs/aspatial_test/levels/L0
configs/L5_multi_agent/levels/L5_multi_agent
configs/simple/levels/L0_simple
configs/reference/model_pack/levels
configs/test/<various>/levels
```

No flat `configs/L0_0_minimal/` directly. The hierarchical
`<pack>/levels/<level>/` layout is universal.

**Verdict: CONFIRMED.** Catalog §10 row 2 correct; CLAUDE.md is stale.

### I. SG1: `CuesCompiler` never called from `compiler.py`

**Command**: `grep -n "CuesCompiler\b" src/townlet/universe/compiler.py`
**Output**:
```
55: from .cues_compiler import CuesCompiler
78:        self._cues_compiler = CuesCompiler()
```

Followup: `grep -n "self._cues_compiler\b" src/townlet/universe/compiler.py`
returns only line 78 (the assignment). The instance attribute is
constructed but **never read** elsewhere in the file.

**Verdict: CONFIRMED.** Catalog §1 and §11.1 entry correct.

### J. SG4: `aggregation` extrinsic hardcoded to `min`

**Source**: `dac_engine.py` lines 400-425, read directly.

Relevant lines:
```python
def compute_aggregation(meters, dones):
    """Aggregation: reward = base + min(bars)"""
    ...
    # Apply min aggregation (could be extended to max/mean/product)
    aggregated = torch.min(bar_values, dim=1).values
```

The closure name (`compute_aggregation`), its docstring (`min(bars)`), and
the inline comment (`could be extended to max/mean/product`) all confirm:
the strategy promises four modes but implements only `min`.

**Verdict: CONFIRMED.** Catalog §4 and §10 row 9 correct.

## Other findings

### Internal contradictions

1. **§11.1 row "`decay_epsilon()` defined but never called from training loop"** vs SG6's own
   `temp/sg6-training.md:556` and `:649`, which explicitly call out "warrants a grep over the
   wider repo to confirm". The catalog promoted SG6's hedged concern to a flat dead-code
   assertion. Wider grep shows it IS called at `src/townlet/demo/runner.py:933`. The catalog
   row over-claims.

2. **§11.1 row "VTCInteractionProgressProgram, VTCSocialResidueProgram — compiled but call
   sites not found"** vs SG2's own `temp/sg2-vfs.md:130` and `:141`, which hedge "in this
   scan" and "needs confirmation". Validator grep confirms InteractionProgress is wired at
   `action_executor.py:239`; only SocialResidue is genuinely unwired. The catalog row
   over-aggregates two distinct findings (one true, one refuted).

3. **§11.2 row "Epsilon schedule may be dead"** — refuted by finding 1. The schedule IS
   driven by `DemoRunner.run` once per episode. This row should be deleted; what remains is
   a *structural* concern that the schedule lives in the demo driver rather than in
   `VectorizedPopulation`, which is a layering observation, not a latent bug.

### Overclaiming

The catalog's confidence column ("High" for all 8) is *not* the issue here. The issue is
that two cross-subsystem aggregations in §11.1-§11.2 strip the hedge that the underlying
`temp/sgN-*.md` carried, and present them as confirmed dead code. The subagent reports
themselves were honest and explicitly invited validator re-grepping.

### Internal consistency (dependency matrix vs per-subsystem)

Spot-checked four edges against the underlying `sgN` reports:

- SG2 → SG5 DSL: matrix says "imports parser, type-checker, history". sg2-vfs.md §"Inbound
  dependencies / Outbound dependencies" confirms (line 35: `history.py` import from
  `townlet.world.expression.history`). ✓
- SG6 → SG4: matrix says "constructs and steps VectorizedHamletEnv". sg6 §"step_population"
  flow at vectorized.py:606 confirms. ✓
- SG7 effects → SG5 DSL: matrix says "imports parser+evaluator". sg7's effects compiler
  description confirms expression ASTs are parsed at compile time. ✓
- SG1 → SG7: matrix says "imports EffectCatalog". sg1 confirms in its outbound list. ✓

No contradictions found in the four edges checked.

### Coverage of catalog §12 verifications

§12 asks the validator to (a) re-grep VTC programs, (b) confirm exploration files. Both
done. (a) yielded the refutation in finding 2 above; (b) confirmed exactly. The §12
self-instruction is honoured.

## Required revisions

### Warnings (must fix before downstream phases use catalog as source of truth)

W1. **§11.1, row "`VTCInteractionProgressProgram`, `VTCSocialResidueProgram` — compiled but
    call sites not found"**: split into two rows. Keep `VTCSocialResidueProgram` as dead
    (no runtime call site). Remove `VTCInteractionProgressProgram` — it is called from
    `src/townlet/environment/action_executor.py:239`. The SG2 source report's hedge
    ("in this scan") was lost in aggregation.

W2. **§11.1, row "`decay_epsilon()` defined but never called from training loop"**: revise
    to "`decay_epsilon()` is called only from `demo/runner.py:933`, not from
    `VectorizedPopulation` where the rest of the per-step exploration coordination lives —
    a layering concern, not dead code". Citation: `src/townlet/demo/runner.py:933`.

W3. **§11.2, row "Epsilon schedule may be dead — `decay_epsilon()` never called"**:
    **delete this row.** It is refuted by W2. The schedule is alive at the demo runner.

W4. **§2 prose ("VTCInteractionProgressProgram and VTCSocialResidueProgram are compiled but
    the explorer could not find their runtime call sites")**: revise to mention only
    `VTCSocialResidueProgram`. Add citation `action_executor.py:239` for the
    InteractionProgress call site.

W5. **§6 prose ("`decay_epsilon()` is defined on the exploration strategies but never
    called anywhere in SG6 — the ε schedule may be dead")**: revise per W2 — drop "may be
    dead", keep the SG6-scope structural observation that the schedule is driven from
    `demo/runner.py`, not `VectorizedPopulation`.

### Critical

None. The five W-items are precision corrections; the catalog's overall structure,
confidence, and coverage remain sound.

## Sign-off

Confidence in this verdict: **High**.

- Coverage: independently verified against `ls src/townlet/` — 15/15.
- Spot checks: 10 of 10 high-risk claims independently re-run; 8 confirmed verbatim, 2
  refuted (InteractionProgress runtime call, `decay_epsilon` repo-wide call).
- Cross-document consistency: 4 dependency-matrix edges re-checked against per-SG
  reports; no contradictions.
- The two refutations are tech-debt-class (over-aggregation in §11) and easily fixed by
  the catalog author; they do not invalidate downstream phases (diagrams, security,
  quality) because the affected items appear only in the concerns aggregation, not in the
  per-subsystem summaries that feed C4 diagrams.

The catalog may proceed to downstream phases **after W1–W5 are applied**. If time-boxed,
W1 and W3 alone are the load-bearing edits (one false positive in dead-code list, one
false positive in latent-bug list); W2/W4/W5 are prose-level precision improvements on
the same underlying facts.
