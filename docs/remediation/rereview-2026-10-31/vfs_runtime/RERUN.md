# Green-call rerun — lens `vfs_runtime` — f3a6d115

Worktree `rereview/vfs_runtime/wt2` (detached at f3a6d115; removed at the end). Interpreter `/home/john/hamlet/.venv/bin/python`,
`PYTHONPATH=wt2/src` (`townlet.__file__` confirmed under wt2/src), CPU. /home/john/hamlet untouched, no `git stash`.
Probes: the 559dd0f9 set repointed (`probes/harness.py` → wt2), `p_isolation.py` extended with VFS random draws (global expression
`rg: uniform(0,1)`, agent expression `ra: normal_dist(0,1) + bar.energy` exposed, affordance rule `aff_r <- uniform()` gated by a rule-level
`uniform() > 0.3`, global rule `g += normal_dist(0, 0.01)`, action write `av2 += uniform()`, and `dist: distance_to_affordance("SLEEP")`),
plus a new resume probe. Logs: `out2/`.

## VERDICT: GREEN for this lens

No P1, no P2, no VFS/compiler-scope spec gap left in my findings. Residual P3s listed below.

## New findings N1–N10 at f3a6d115

| id | at 559dd0f9 | at f3a6d115 | evidence |
|---|---|---|---|
| N1 bool/ref item state through float32 arena, `not item.flag` crashed | P2 | **repaired** | `p_access.py a2`: `if: not item.flag` → `modify item.flag value: not item.flag` compiles and runs; arena row `[100, 100, 1.0, -1.0]` after USE; `item.flag and …` branch also runs (`USE 0..2`) |
| N2 vector target + agent-shaped expression (action crash / rule broadcast) | P2 | **repaired** (constant-only) | `p_writes.py w1`: `vec <- av`, `vec <- bar.energy`, `t1 <- av` refuse `[VTC-WRITE-TYPE]` at `actions.yaml:9` / `transition_rules.yaml:3` in both action writes and rules; literals still run |
| N3 `clamp` on ref/bool target | P2 | **repaired** | `w2`, `p_claim2.py c3`: `aref … clamp`, `flag … clamp [0,1]`, `flag … clamp [0,0]` refuse at compile in actions and rules |
| N4 refs write-only w.r.t. identity (null test via sentinel, release via global bool) | P3 | unchanged P3 | `p_access.py a3`, `p_claim.py`, `p_claim2.py c2`: sentinel null test and global-bool release still compile and run world-locally; `occ == agent_id` / `occ == me` still refuse (type / shape). Moot under S1 |
| N5 rule at `evaluate_terminal_conditions` seen one tick late | P3 | unchanged P3 | `w5`: `(1,0),(2,2),(3,4)` at that phase; every other phase `(1,2),(2,4),(3,6)` |
| N6 exposure composes through expressions over engine-only inputs | P3 | unchanged P3 | `w4b` compiles and publishes 0.1; still undocumented in variables.md (grep) |
| N7 dead-world expressions shift once then freeze; tick-derived keep moving | P3 | unchanged P3, **plus** random expression variables (`rg`, `ra`) re-draw every step in a dead world (draws are keyed on tick, expressions keep evaluating) — the dead world's exposed `ra` row changes every step, reward 0 | `p_dying.py d1` (`out2/p_dying_d1.log`) |
| N8 persistent `item_ref` across reset | P3 | **repaired** | `p_misc.py m3`: `[LOAD_ERROR] variables.yaml:113 … 'held' is an item_ref with lifetime persistent, but item rows are episode-lifetime …` |
| N9 bool compositions are torch boolean algebra; `composition: clamp, clamp: null` = overwrite | P3 | unchanged P3 | `w2`, `w6` |
| N10 doc drift | P3 | mostly repaired: VFS.md:272/1141 now say one evaluation mode; variables.md:382 `get_global`/`get_agent` gone; phase-entry snapshot now documented (variables.md:319) | greps; the division-by-zero-at-publish sentence is still absent (P3) |

## Contracts that held before — rerun at f3a6d115 (no regression)

- **World-0 differential** (perturbed world 0 vs not; 40 steps + reset + 4 steps; every world's obs/reward/done/meters/pos/every registry
  variable incl. the four random ones/effects): **NO DIVERGENCE in worlds 1..N-1** at N=2, N=4 (= affordance count), N=5; global RNG
  stream never diverges (`out2/iso_*.pt`, `compare2.py`).
- **A/A determinism**: same seed, two runs, N=4: bitwise identical on every world and key (`compare2.py … all`).
- **N=1 vs N=4 vs N=5**, world 0: every registry variable identical except `noise_t`/`noise_e` (torch-global-RNG initializers, stream
  length) and `dist` (random placement); the counter-based draws `rg`, `ra`, `aff_r`, `av2` are **identical across N** — the S1 claim in
  `vfs/random_draws.py` holds; meters identical every step.
- **Random-draw resume** (`out2/p_random_resume.log`): `vfs_random_state()` = `{seed, episode}`; a fresh env with
  `restore_persistent_state` + `restore_vfs_random_state` + `reset()` reproduces episode 2's `rg`/`aff_r`/`av2` trace of the original
  bitwise; an un-restored env draws episode 1's values (different).
- **Dying agent** (`p_dying.py d1/d2`): writes apply on the dying step (entry mask); afterwards globals, affordance rows, agent vars, meters,
  effect writes frozen; live worlds unaffected.
- **Reset ordering** (`p_reset_ckpt.py r1/r3`): instant-0 persistent expressions from carried values (`pacc` 6 → 7), tick 0 in every row,
  tick-lifetime writes visible in that step's obs then reset, episode random initializers redraw per reset / tick ones per step, reset after
  partial deaths clears dones and re-seeds history, double reset fine.
- **Persistent save/restore** (`r2`): exact persistent id set, dtype-preserving, `pexp` re-evaluated from the restored value after reset,
  cross-world ref and N-mismatch refused before any write.
- **Access policy** (`p_access.py a1/a2`): every authored write path (effect modify / sample / for_each body, rule, action write,
  interaction, item hook) refuses `writable_by: []` at compile with `file:line`; agent read of engine-only and any agent write refuse at
  runtime; exposure without read access refuses at the declaration (registry and item); item-state publisher per world.
- **Phase graph, meter-name collision, rule ordering, hashes, for_each world-locality, claim_if_free per world/idempotent/frozen on death**:
  all as at 559dd0f9 (`w5`, `w6`, `m1`, `m2`, `m4`, `p_claim.py`).

## Noticed in passing (not blocking)
- `distance_to_affordance` takes a quoted literal (`"SLEEP"`); a bare `SLEEP` refuses with the generic "names no variable" text — a
  refusal that could name the quoted form (P3, authoring lens).
- `VFSRandomness(torch.initial_seed())` is captured at env construction (`vectorized_env.py:588`): `seed_all` must precede env
  construction, as the training loop does; a caller that seeds afterwards gets draws from the pre-seed value. Documented contract, noted.
- N7's dead-world random re-draws: harmless for training (reward 0, dones masked) but worth one sentence next to variables.md:328.

## Not covered
Same as REVIEW.md §5: CUDA, `capacity_claim`, interaction `delay`, `effect_ref`/`affordance_ref` write paths, DemoRunner end to end,
POMDP masking of `variable_element`, the full suite (compiler lens).
