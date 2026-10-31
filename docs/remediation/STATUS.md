# Remediation status and handoff

**Written:** 2026-10-31.
**Branch:** `fix/vfs-compiler-remediation-2` (tracks `origin`).
**State recorded at:** the green commit, the one that last touched this file (`git log -1 -- docs/remediation/STATUS.md`). VFS and the compiler are **green**.

Read this first when resuming on another machine or in a cloud session. It is self-contained:
everything that used to live only in a local session scratchpad is in the repo now (see
[§9 Records](#9-records-in-the-repo)).

> **Update this file at the end of the current section.** When VFS and the compiler are called
> green, fill in [§5](#5-the-current-section-vfs--compiler-to-green), set "State recorded at" to
> the green SHA, and move the closed rows of [§7](#7-open-items-register) to §8.

---

## 1. Resume checklist

```bash
git fetch origin && git checkout fix/vfs-compiler-remediation-2 && git pull
uv sync --extra dev --extra recording
git log --oneline main..HEAD          # the sprint's commits, newest first
```

Then:

1. Read §3 (rulings and rules) and §4 (method). They are binding.
2. Read §5. It says exactly what is left before VFS and the compiler are green.
3. Run the gate (§4.3) once at the tip to confirm the environment matches.

---

## 2. The plan and where we are

The owner approved this order (2026-10-24, "lock subsystems before integration"). A subsystem
is **done when a fresh review finds nothing material** (§5.1 defines "material").

| # | Phase | Status |
|---|---|---|
| 1 | VFS + compiler sprint: VFS round-2 WP9–WP17, compiler WP5–WP7 folded in | **Done** |
| 2 | VFS + compiler re-review, then call VFS and the compiler green | **Done: green (2026-10-31)** |
| 3 | Open a PR to `main`, every CI row green at the tip, merge | **Next / in progress** |
| 4 | Training-loop review (BaC layer 2) | Queued |
| 5 | UaC: items, affordances, rewards (`uac-items-affordances-rewards.md`) | Queued |
| 6 | Strata (`strata.md`) | Queued |
| 7 | Effects and expressions (`uac-effects-expressions.md`) | Queued |
| 8 | End-to-end shakedown: config in, behaviour out, a training run | Queued |

The per-subsystem plans for phases 5–7 are in this directory. Their source review is in
`review-2026-10-24/`.

**Deferred owner rulings: not to be implemented until the owner confirms.**
- Meters become pointers to VFS variables (bars.yaml becomes a survival-role binding; the meter
  token type, the cascade DTOs and the `bar.` spelling go).
- Bounds and breach policy.
- The nine-field variable declaration redesign.

Sources: `design-review-vfs.md`, `design-review-compiler.md`.

### Commits on the branch since `main` (`11c74398`)

| SHA | Content |
|---|---|
| `b4bd60a0` | Compiler WP6/7: CLI never tracebacks; cache keyed on pack path and compiler source; residue deleted |
| `e7113e15` | WP10: expression identity; `variables_hash` checkpoint-gated |
| `46ca2372` | Token-spec refusals located; identity rule only where the encoder is blind |
| `67b6dc5e` | WP12: writes and rules shape-proved; writes to expression-owned variables refuse |
| `58e0a475` | WP9: every clock agrees; reset evaluates expressions; one spawn-predicate resolver |
| `4906e23a` | WP11: item-state rows share the item token's visibility mask |
| `9afa4184` | WP16: persistent-lifetime VFS state survives resume (checkpoint format 7) |
| `c76c1bed` | WP15: pair, message and agent_private deleted (S1) |
| `2a7ead8d` | CLAUDE.md corrections (owner-authorized) |
| `cfee624c` | WP13: `global` is per world |
| `de821e29` | Items are per world |
| `f045ffcb` | CI: no-defaults ratchet |
| `381cfb07` | Every effect lives in one world |
| `d3de07e8` | Affordance state, references and reductions are world-local |
| `76a3060e` | WP14 history operators, S4 same-tick expressions, S8 derived rule reads, dead features deleted |
| `ca2eeab5` | WP17 S5: one spelling per reference, one resolver for every consumer |
| `2e0d1622` | Reserved engine names, per-profile item state, compile-time refusals for runtime crashes |
| `dcf09db1` | Architecture docs match the one-spelling grammar, Cut B and the token cut |
| `559dd0f9` | Typed switch cases, located item-profile refusal, `self`/`target` reserved |
| `39825727` | Re-review repairs R1 and R2 (see §5) |

At `39825727`:
- the full suite gives `5415 passed, 17 skipped`;
- `COMPILED_SCHEMA_VERSION` is 1.40;
- `CHECKPOINT_FORMAT_VERSION` is 8;
- the no-defaults ratchet is at 618 (653 at the start of the sprint).

**No PR is open yet.** CI workflows trigger on `project-recovery*` branches, so this branch has
had no CI run. The first one will be the PR's. Do not read the absence of a red row as green.

---

## 3. Owner rulings and standing rules (binding)

**Rulings made in this sprint**
- **S1 (2026-10-25): the batch is N independent single-agent worlds.**
  - `global` is per world, shape `[num_worlds]`.
  - The item arena is flat `[N*C, V]`, with row = `w*C + slot`.
  - Effect stores and RNG are per world. Affordance storage is `[N, A, ...]`. `agent_ref` and
    `item_ref` are world-local.
  - The `pair`, `message`, `group`, `zone` and `agent_private` scopes are deleted until
    agents-per-world is declarable.
  - The check: a world-0 differential. Two runs differ only in world 0's actions, and worlds
    1..N-1 must stay bitwise identical.
- **One spelling per reference (WP17).**
  - `x` is a registry variable, read in this world by its declared scope.
  - `bar.m` is a meter, including as a write target.
  - `item.x` is the bound item's state.
  - Engine names are `tick` (everywhere, read-only), `agent_id` (in writes and rules,
    read-only), and `intensity`/`elapsed_ticks`/`duration_remaining` (in effects only).
  - These are reserved, together with `self`, `target` and the expression keywords.
  - Every other spelling refuses at compile, naming the one to use.
- **The token identity rule is brain-gated (S3).** Two entities identical in every declared
  parameter are refused only for `token_set`/`recurrent` brains.
- **Hash movement is free.** No checkpoints exist; note moved hashes in the commit message.

**Standing rules (CLAUDE.md)**
- **Zero backwards compatibility.** Delete; never dual-path. Old configs fail loudly.
- **No-defaults.** `extra="forbid"`, everything explicit. The ratchet
  (`scripts/no_defaults_lint.py --ratchet .defaults-ratchet`) fails if the whitelisted count
  rises *or falls* without the file being lowered. Lower `.defaults-ratchet` whenever the count
  drops.
- **Never branch on a variable's name (PDR-0045).**
- **Work only in `src/townlet/`.** Never edit `.oracle/`.
- **Merging.** Run `gh pr merge <n> --merge` as a plain command, never in a `;`/`&&` compound.
  Autonomous merge to `main` is allowed under PDR-0101 once every CI row at the tip is green and
  the README is re-verified. Tags, releases and `gh pr close` escalate to the owner.
- **`git stash` is hard-blocked by an operator hook,** even inside a compound or as
  `git stash list`.
- **Check `git status --short` before committing.** The index is shared with any parallel agent.
- **Commit attribution:** `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

---

## 4. Working method

### 4.1 Coordinator and packages
- One coordinator session plans, gates, commits and pushes. Subagents implement work packages.
- Implementers alternate between two models, and each package gets an **adversarial verifier on
  the other model**.
- **The verifier works in a detached worktree** at the commit
  (`git worktree add --detach <dir> <sha>`, `PYTHONPATH=<wt>/src`, confirm `townlet.__file__`).
  It never edits the main tree, and it removes the worktree at the end.
- **Briefs name file ownership** whenever two implementers share the tree.
- **The verifier attacks the claims:** it reruns every filed repro, writes authored-pack probes,
  runs a world-0 differential over every compilable `configs/` level, compares behaviour tick by
  tick against the previous commit, and reports defects first with P1/P2/P3 severity.
- **Every defect routes to a repair pass** before the next package builds on it. So far every
  verifier has found something; budget a repair round per package.

### 4.2 Severity bar
- **P1:** wrong behaviour, a crash or silent corruption reachable from an authored pack, or a
  broken determinism or isolation contract.
- **P2:**
  - a claimed contract that doesn't hold;
  - a compile that accepts what the runtime can't serve (a crash at step);
  - a missing refusal;
  - a no-defaults or name-branch violation;
  - an unlocated error.
- **P3:** nits, doc drift, dead code, perf. Logged, never blocking.

### 4.3 The gate, run before every commit

```bash
CUDA_VISIBLE_DEVICES= uv run pytest tests -q --no-cov -p no:cacheprovider -n auto --dist worksteal   # under 10 minutes even on 4 workers
uv run ruff check .
uv run black --check src tests scripts
uv run mypy src/townlet
uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet
uv run python scripts/validate_compiler_cli.py
uv run python scripts/gen_expression_functions_doc.py --check
```

Invariants checked alongside the gate:
- **`token_type_schema_hash` starts with `de093a6e9f59924e` on every compilable shipped level.**
  It is the transfer contract; any change that moves it is wrong.
- If a shipped pack's files change, run `uv run python scripts/regen_frozen_live_inputs.py` and
  commit the inventory diff. The drift test pins input digests.

---

## 5. The current section: VFS + compiler to green

### 5.1 How the re-review works
- Three fresh reviewers, one per lens, review a fixed SHA against the bar in
  `rereview-2026-10-31/BRIEF.md`:
  - `vfs_runtime` (step-time correctness and isolation);
  - `compiler` (stages, hashes, cache, artifact, CLI; owns the full gate);
  - `authoring` (docs vs DTOs vs behaviour; 15 designer mechanics; principle violations).
- Each lens classifies every known item and closes out the original 2026-10-24 findings.
- **Green means:** no P1, no P2, and no gap in VFS or compiler scope that makes a reasonable
  mechanic unauthorable without Python.

### 5.2 First pass at `559dd0f9`: all three lenses NOT GREEN
The contracts held in every lens:
- world isolation (differential over 33/33 compilable levels; RNG never diverged);
- same-seed determinism;
- cache round-trip (a 40-step run bitwise equal from a fresh and a cached artifact);
- the access policy on every write path;
- reset ordering;
- dying-agent freezing;
- persistent save/restore.

Almost all of the original review's VFS and compiler findings are closed (closure tables are in
each lens's `REVIEW.md`).

The blocking findings, and where they went:

| Lens:id | Severity | Finding | Fix |
|---|---|---|---|
| authoring:A1 | P1 | A transition rule on a meter compiled and crashed at step | **R2:** implemented through the existing bars commit path |
| runtime:N1 | P2 | bool/ref item state read through the float32 arena; `not item.flag` crashed | **R2** |
| runtime:N2 | P2 | A vector target written with a per-row expression crashed (actions) or broadcast (rules) | **R2:** constant-only in both |
| runtime:N3 | P2 | `clamp` on a ref or bool target corrupted it | **R2:** refused |
| compiler:N1 | P2 | Compile accepted packs that env construction refused (action name, item arena, positions, deployment) | **R1** |
| compiler:N2 | P2 | Substrate rank refusals were a bare ValueError | **R1:** in the DTOs |
| compiler:N3 | P2 | A custom action named like a substrate action was silently dropped | **R1:** refused |
| compiler:N4 | P2 | Infinite continuous bounds gave NaN positions | **R1** |
| compiler:N5 | P2 | Effects and `items_appearance` were outside checkpoint identity | **R1:** `effects_hash`, `items_appearance_hash` |
| compiler:N6 | P2 | `true`/`false` and non-identifiers were declarable as ids | **R1:** identifier grammar from the parser |
| authoring:A4 | P2 | `time_in_window` hardcodes a 24-tick day | **R1:** refuse opening hours when period ≠ 24 (minimal; full design in §7) |
| authoring:A2 | P2 gap | No random draw can reach VFS state | **R3 (in flight)** |
| authoring:A3 | P2 gap | Spatial and vector functions refused in variable expressions ("distance to nearest food" unauthorable) | **R3 (in flight)** |
| authoring:A5 | P2 gap | An affordance closed by a variable | **moved to UaC** (§7.1) |
| authoring:A6 | P2 gap | An action masked unless a condition holds | **moved to UaC** (§7.1) |

R1 and R2 also closed P3s: located diagnostics, dotfile discovery, sorted evaluation marks,
error codes, and doc examples made loadable. The authoring lens's doc-example test now
**steps** every example in a real pack. Before, it compiled against a mock, which is how four
doc examples shipped as crashes.

### 5.3 State of the remaining steps

| Step | State at the time of writing |
|---|---|
| R1 + R2 committed (`39825727`) | ✅ full suite green |
| **Verifier of `39825727`** | ✅ done; record in `rereview-2026-10-31/verify_R12/RESULTS.md`. 4 defects, **repaired in R4** |
| **R3 expressions** (`636192e0`) | ✅ full suite green on exactly that tree (`5438 passed`) |

**R1+R2 verifier defects (repaired in R4; kept here for the record):**
- **D1, P1: keyword prefixes misparse.** The parser matches `not`, `true` and `false` with
  `Literal`, not `Keyword` (`world/expression/parser.py:61-62`, plus the unary `not`).
  - Effect: an id `notable` parses as `not able` and silently reads the wrong value, and
    `true_count` is accepted and then fails at first use.
  - Fix: use `Keyword` for those tokens. Don't refuse keyword prefixes in `is_identifier`, since
    `order` is legal.
- **D2, P2: placement silently falls back to declared positions.**
  `vectorized_env.py:1630-1650` switches randomization off and uses declared positions when
  affordances + `num_agents` exceed capacity. It counts every world's agent on one grid, a
  pre-S1 assumption.
  - Effect: off-grid positions are used, and shipped `static_epistemic_access` crashes at
    `num_agents=61`.
  - Fix: delete the fallback, and check capacity at compile as affordances + 1 agent per world.
    R1's randomize-conditional position check is then correct.
- **D3, P2: a meter rule can leave a meter out of bounds.** A meter rule before
  `clamp_and_validate` leaves an out-of-bounds meter for the rest of the tick, and cascades
  read it raw.
  - Fix: clamp `bar.` rule targets to the meter's declared bounds at commit, as depletion and
    cascades do.
- **D4, P2: one substrate refusal is still unlocated.** `interaction_radius` larger than the
  bounds raises a bare ValueError from `substrate/continuous.py:79` (and `continuousnd.py:99`),
  via stage 3's `SubstrateFactory.build`.
  - Fix: move it into the stratum DTO validator.
- **P3s:**
  - the stratum DTO says ranks 4–100, but the token spec caps at `MAX_POSITION_RANK=8`;
  - `DAC-REF-001` and `CLOCK_REFERENCE` locations moved one line up;
  - `effects_hash` moves when a fragment moves to an earlier-sorting file, and on `1.0` vs `1`;
  - `checkpoint_utils.py:473-476` docstring counts are stale;
  - action writes commit before rules within a phase, which is undocumented;
  - leftover doc nits: `variables.md:370`, `expressions.md:585/785/980`, VFS.md illustrative
    names.

**R3 verifier defects (repaired in R4):**
- **V1, P1:** a draw on an affordance-scope target filled `[W]` and broadcast along the affordance axis
  (cross-world leak at N == A, crash otherwise).
- **V2, P2:** compile-time constant folding evaluated draws from torch's global generator.
- **V3, P2:** draw order followed declaration order, so moving a declaration or adding an
  unrelated random variable re-rolled every draw.
- **V4–V6, P2:** three things compiled and crashed at reset: `gather` over a `tensor1d` static
  with an initializer mode, vector `==` into a bool, and a position function naming an unknown
  affordance.

**R4 design calls (the owner endorsed the placement and undeployed-affordance calls on 2026-10-31):**
- **Counter-based randomness** (`vfs/random_draws.py`). Each value is splitmix64(seed, episode,
  tick, site, world, element), vectorised, keyed on a stable draw-site identity
  (`var:<id>`, `rule:<id>:<write>`, `action:<name>:<write>`).
  - There is no generator state: checkpoints carry `vfs_random_state = {seed, episode}`, and
    `CHECKPOINT_FORMAT_VERSION` is 9.
  - The effects and items generators capture the seed at construction but are still stateful
    and not checkpointed (§7.4).
- **Placement is per world (S1).** The capacity check is affordances + 1 per world, at compile
  (`GRID_CAPACITY_EXCEEDED`). The joint-draw fallback is deleted, so same-seed trajectories of
  `randomize_affordances: true` packs differ from `636192e0`.
- **Undeployed affordances refuse in position functions.** A position function naming an
  affordance that some level of the pack does not deploy refuses at compile
  (`EXPRESSION-AFFORDANCE-UNDEPLOYED`).
  - This is stricter than the old documented "infinity".
  - It bites a curriculum whose early levels deploy fewer affordances than a pack-scope variable
    names. Revisit in UaC if that pattern is wanted.
- **One canonical form for the effects hash.** `effects_hash` sorts definitions by id, and
  `1` vs `1.0` still moves it, as in every other canonical-AST hash, because the type checker
  distinguishes them.

| Step | State at the time of writing |
|---|---|
| R3 verifier | ✅ done; record in `rereview-2026-10-31/verify_R3/RESULTS.md`. 1 P1 and 5 P2s, **repaired in R4** (below) |
| **R4 repair** (D1–D4, aspatial position functions, V1–V6, P3s) | ✅ `f3a6d115` |
| R4 verifier | ✅ **no P1, no P2**; all eight areas hold, including resume through a real `DemoRunner.run()` and statistical checks of the counter-based draws. Record: `rereview-2026-10-31/verify_R4/RESULTS.md` |
| **Green call** at `f3a6d115` | ✅ runtime lens **GREEN**; authoring lens **GREEN** after A9; compiler lens NOT GREEN on R1/R2 only. Records: `rereview-2026-10-31/<lens>/RERUN.md` |
| Final fixes, then **GREEN** | ✅ in the green commit (below) |

**The final fixes (green commit):**
- **A9 (authoring, P2):** `if (c) then …` refused, because `if (` parsed as a call to a function
  named `if`. The parser's identifier rule now excludes every keyword.
- **R1 (compiler, P2):** an empty `experiment_name` compiled and failed at env construction; it
  now has `min_length=1`.
- **R2 (compiler, P2):** continuous bounds beyond float32 range compiled and overflowed on step
  1. Each bound and the span must fit in float32 (`FLOAT32_MAX` in `config/stratum_config.py`).
- **PDR-0045 (found by the CLAUDE.md audit):** `compilers/actions.py` labelled WAIT passive
  because of its name. The label now comes from the declaration: no writes and no source
  affordance means passive. Nothing at runtime reads the label.

**Verdict: VFS and the universe compiler are green.** No P1 or P2 remains in either, and no
mechanic in VFS or compiler scope is unauthorable without Python.

R3 covers:
- `uniform`/`normal_dist` admitted in variable expressions, rules and writes, with one draw per
  row from each world's own generator;
- function output shapes derived from `FUNCTION_SPECS` instead of the hand list in
  `vfs/profiles.py`, so spatial and vector functions work in variable expressions;
- a defined value for spatial expressions at the reset instant (reset evaluates profiles before
  spawn; WP9);
- `elapsed_ticks()` deleted;
- refusal messages that name the fix.

**If you resume and R3 is not on the branch,** the session ended before it was committed. Its
brief is reproduced in §5.4; re-run it from `39825727`.

Then phase 3: open the PR, read every CI row at the tip, re-verify the README, and merge with
the plain `gh pr merge <n> --merge`.

### 5.4 R3 brief (reproduced in case it must be re-run)

**A2: random draws in VFS**
- Admit `uniform` and `normal_dist` in global and agent profile expressions, transition rules
  and action writes.
- Each draw is one independent value per row of the expression's shape.
- Draws must come from each world's own generator; never `torch.rand` or the global generator.
- Tests:
  - a world-0 differential (N≥4, 64 steps, random global plus random agent expression plus a
    rule writing a random value);
  - same-seed A/A bitwise identity;
  - whether per-world RNG state is checkpointed.

**A3: shapes from the registry**
- Replace the hand allow-list in `vfs/profiles.py` (`pointwise`) with a declared shape rule on
  each `FUNCTION_SPECS` entry.
- Admit spatial and vector functions wherever the consumer's `ReadContext` serves positions.
- Make the first observation after reset carry the correct `distance_to_affordance`.
- Delete `elapsed_ticks()`.
- Make the shape refusals name the fix.

**Acceptance**
- An exposed "distance to nearest food" variable is correct from the first observation.
- Per-world random weather is authorable and reproducible per seed.
- Re-run `rereview-2026-10-31/authoring/probes/f_matrix.py` and report the delta.

---

## 6. Designer-mechanics scorecard (the product number)

The authoring lens tried 15 mechanics in YAML only, at `559dd0f9` and again at `f3a6d115`:

| Mechanic | At `559dd0f9` | At green (`f3a6d115`, measured) |
|---|---|---|
| Ticks since the agent last ate | works | works |
| Resource regenerates toward a cap | works | works |
| Reward on a rising edge | works | works |
| Variable persists across episodes | works | works |
| Private variable drives a reward | works | works |
| Moving average of a meter, exposed | works | works |
| Item state decays while held | awkward (through effects) | awkward |
| Per-world weather every K ticks | awkward (deterministic) / gap (random) | works (per world, per seed) |
| Hunger decays faster at night | gap (A1) | works |
| Terminal condition on a variable | gap (A1) | awkward (a rule zeroing a lethal meter) |
| Distance to nearest food, observed | gap (A3) | works (correct from the first observation) |
| Opening hours on a declared non-24 clock | gap (wrong silently) | refused at compile; full fix in §7.2 |
| Cooldown on an action | awkward / gap (no mask) | awkward; the mask half is UaC (A6) |
| Action masked unless a condition | gap | UaC (A6) |
| Affordance closed by a variable | gap | UaC (A5) |

At green: 9 work directly, 3 work awkwardly, 1 is refused by design, and 2 are UaC items. At
`559dd0f9`, 6 worked directly.

---

## 7. Open items register

Items still open at green, grouped by the phase that owns them. "Owner" marks a decision
only the owner can make.

### 7.1 UaC phase (phase 5): first items
- **A5: an affordance closed by a variable.**
  - Add a declared field on the affordance DTO (e.g. `available_when: <bool expression>`),
    lowering to the existing VTC affordance-gate rules.
  - Context: the old runtime store `affordance.<NAME>.available` and its `affordance_overrides`
    plumbing were deleted at `2e0d1622` because no authored spelling reached them. This is a
    capability gap, not a cleanup.
- **A6: an action masked unless a condition holds.**
  - Add a declared predicate on `CustomActionConfig`, lowering to the existing
    `compute_action_legality_masks` phase. A cooldown needs this.
  - Moving A5 and A6 here was a coordinator call, reversible by the owner.
- **Fixed affordance positions are ignored at runtime** under `deployment.type: fixed` (config
  `[0,0]`/`[6,6]` ran at `[2,3]`/`[5,7]`).
  - R1 checks position rank and bounds only under `randomize_affordances: false`.
  - The differential packs `div003_rect`/`div003_cubic_partial` carry out-of-substrate positions
    byte-identical to `default_curriculum` (by design of `test_matrix.py`). Unconditional checking
    needs a differential-pack decision.
- **Items, carried state:**
  - a carried EXCLUSIVE item has no item token and no state row;
  - a shared carried item reports its ground position, not its holder's;
  - items never spawn on continuous substrates.
- **DAC role fields** (`money_bar`, etc.) don't go through the one-spelling resolver. Decide
  whether they should.
- **Hidden defaults reachable from YAML behind blanket waivers.**
  - `config/drive_as_code.py:573-610`: e.g. a drive without `composition:` silently gets
    `normalize: false`.
  - `config/items_config.py:266-362`: spawn schedule and placement defaults.

### 7.2 Strata phase (phase 6)
- **Opening hours on a declared clock period (A4, full fix).**
  - Proposed design: an hour is 1/24 of the declared day, `hour = floor(tick_in_day * 24 /
    period)`. This keeps `OPENING_HOURS_FEATURES` (24 lanes) and `token_type_schema_hash` stable.
  - Sibling 24-tick sites: `universe/dto/token_spec.py:390`,
    `effects/affordance_identity.py:162-184`, `config/affordances_v2_config.py:44`.
  - R1 refuses period ≠ 24 until then.
- No `docs/config-schemas/` page states the substrate rank rules now in the stratum DTOs.

### 7.3 Effects phase (phase 7)
- **Identical effects alias:** effects with identical payloads but different writes alias under
  every brain. Depends on "declared dynamics in the descriptor" (`design-review-vfs.md`,
  change 3).
- **Budget 0:** an effect scope with budget 0 silently refuses every spawn. Candidate for a
  compile refusal.
- **Unbounded capacity:** `max_active_effects` has no upper bound (1e6 takes 21 s and 3.9 GB at
  compile).
- **Structural defaults** remain in `config/effects_config.py:119-159` (original C12).
- **Unreachable lanes:** `affordance_identity` self/all lanes are always zero; cutting them is a
  token-schema change.

### 7.4 Training-loop phase (phase 4)
- The torch global RNG is not checkpointed: spawn positions, affordance randomization,
  `random_*` initializers and epsilon-greedy. "Exact checkpoint resume" is therefore not
  literally true. Check this against what R3 finds for per-world RNG.

- After R4, VFS draws are counter-based and resume from `{seed, episode}`. Still stateful
  and not checkpointed: the effects and items generators, `random_*` initializers and spawn
  positions (the last two also draw from the global stream, so their values depend on N).
- Bar writes made by `effects.tick` are not clamped at commit (R4's D3 clamp covers VTC action
  writes and rules only). Effects phase, or here.

### 7.5 P3 backlog (non-blocking)

**Found at the green call (the P3 sweep after green takes the cheap ones):**
- The `EXPRESSION-AFFORDANCE-UNDEPLOYED` check ignores declaration scope. A level-scoped
  interaction is refused when some *other* level doesn't deploy the affordance
  (`semantics.py:282`).
- The stage-3 static-facts pass parses every string leaf, descriptions included, so a
  description reading `distance_to_affordance("NOPE")` is refused (`semantics.py:241`).
- Expression-produced vector widths and computed `gather` indices are checked only at reset
  (documented at `expressions.md:484`).
- `uniform(5.0, 2.0)` and `normal_dist(0, -2)` are admitted.
- DemoRunner saves its final checkpoint after `current_episode += 1`, so a resume skips one
  runner episode index (the draw counter stays consistent).
- Continuous affordance positions are `list[list[int]]`
  (`affordances_v2_config.py:81`), so a fractional position is refused (UaC).
- A negative `max_active_effects` is refused at `effects.yaml:1`, not at the budget's own line.
- `max_active_effects` has no upper bound (compiler N7).
- Provenance ignores pyyaml/msgpack/numpy versions.
- From the CLAUDE.md audit:
  - `substrate/base.py:143-162` docstring claims INTERACT is at `[-2]` and WAIT at `[-1]`
    (false; WAIT is custom). STRATA.md §5 and the enabled_actions.md banner repeat it.
  - Two DAC shaping classes share `type: vfs_variable` (`drive_as_code.py:362`, `:536`).
  - `StructuredQNetwork` (`agent/networks.py:478`) has no references.
  - Annealing is declared in both `drive.yaml` and `training.yaml`; only `training.yaml` is read.
  - `enabled_actions.md` says "omit the field to enable the entire vocabulary" (a default).
- The runtime-lens P3s carried from 559dd0f9:
  - N4: references can't be compared to null;
  - N5: a rule at `evaluate_terminal_conditions` is seen one tick late;
  - N6: exposure composes through expressions (now documented);
  - N7: dead-world expressions shift once, and random ones keep drawing;
  - N9: boolean compositions;
  - the division-by-zero-at-publish doc sentence.

**Carried from earlier:**
**Hashing and the artifact**
- Hash false moves:
  - `initial_value: 2` vs `2.0`;
  - `affordances_hash`/`items_hash` hash expression text (respacing moves them), not the
    canonical AST.

  No semantic edit fails to move a hash.
- `CompiledUniverse.from_dict` ignores unknown payload keys.
- Artifacts are not byte-identical across processes (`compiled_at`).

**References and variables**
- References can't be compared to null or `agent_id` (`aref == -1` refuses). A global
  `agent_ref` sentinel works. "Is this claim mine" becomes real once agents-per-world exists.
- `effect_ref`/`affordance_ref` with `lifetime: persistent` are not refused (the same dangling
  shape as `item_ref`, which is refused).
- Bool compositions are boolean algebra (additive = OR, multiplicative = AND).
- `semantic_type` is required but consumed only at exposure and in the hash for hidden
  variables.
- An agent-shaped read into a global target refuses, while global into agent runs world-locally
  (consistent under S1).

**Runtime**
- A dead world's expressions shift once after death, then freeze.
- The WP11 visibility mask is computed twice per tick (cache it on `TokenPublishContext`).

**Diagnostics and dead code**
- The namespace's undeclared-target message is ungrammatical ("targets 'x' names no variable").
- `ActionSpaceBuilder.get_enabled_actions` has zero callers.
- Docstrings in `test_content_hash_checkpoint_guard.py`/`test_meter_bounds_runtime.py` say
  provenance uses `git rev-parse HEAD` (stale).
- The namespace's `_LEGACY_*` table feeds refusal text only (acceptable).

**Moot under S1**
- The expression language has no cross-agent reduction. A global can't aggregate agent
  quantities, but with one agent per world that's moot until agents-per-world exists.

---

## 8. Closed in this sprint (summary)

The detail is in the commit messages and the lens closure tables.
- **Original review, VFS:** phase-graph truth, eager evaluation deleted, shape-proved writes, the
  extents/zone/group/pair/message/agent_private deletions, `vfs_hash` coverage, same-tick
  expressions, typed registry/VTC/effects storage, meter-name collisions.
- **Original review, compiler:** `items_appearance` round-trip, pack hashes stamped and compared,
  CLI tracebacks, the cache fingerprint, located refusals.
- **S1 complete:**
  - per-world globals, items, effects, affordance state and references;
  - per-world RNG;
  - `for_each all_agents` world-local;
  - dead-world freezing on the dying step.

  The world-0 differential holds over every compilable level.
- **WP17:**
  - one spelling, one resolver;
  - interactions and item hooks compile at stage 6 with locations;
  - spawn predicates inline pure expressions;
  - history operators refuse in spawn predicates;
  - one temporal-function list derived from `FUNCTION_SPECS`;
  - profile refusals located at the declaration.
- **The B4 verifier's defects:**
  - the reserved-name clash between compile and runtime;
  - cross-profile `item.x`;
  - writable `tick`;
  - `additive_delta` on references;
  - `delay` on timeless levels;
  - switch case bodies;
  - the unlocated item-profile refusal.
- **Docs:** the architecture docs (`VFS.md`, `UAC.md`, `STRATA.md`, `COMPILER.md`) match the
  grammar, Cut B and the token cut. Every loadable example is validated, and the transition-rule
  examples are stepped by a test.
- **Other:** `velocity_*` name branch deleted; `exclusive` hidden default made required; the
  CLAUDE.md identity rule confirmed by the owner.

---

## 9. Records in the repo

| Path | Content |
|---|---|
| `docs/remediation/README.md` and the per-subsystem plans | The 2026-10-24 gap analysis and work packages for every phase |
| `docs/remediation/design-review-{vfs,compiler}.md` | Design reviews behind the deferred owner rulings |
| `docs/remediation/review-2026-10-24/` | The original review: `REVIEW_SYNTHESIS.md`, `findings_*.md`, `gaps_*.md` |
| `docs/remediation/rereview-2026-10-31/BRIEF.md` | The re-review bar, scope and method |
| `docs/remediation/rereview-2026-10-31/<lens>/REVIEW.md` | Each lens's full record: findings, known-item classification, closure tables |
| `docs/remediation/rereview-2026-10-31/<lens>/probes/*.py` | The lens probes used for the green call |
| `scripts/regen_frozen_live_inputs.py` | Regenerates the pinned input digests after a pack change |

About the probes:
- They are frozen evidence, excluded from ruff.
- Several hard-code paths from the original session, such as
  `/tmp/claude-1000/.../scratchpad/...` worktree and pack paths. Repoint `ROOT`/worktree
  constants before re-running.
- The `review-2026-10-24/` reproduction scripts cited by the per-subsystem plans were not copied
  (only the findings were). Each plan states its repro inline well enough to rebuild it.
