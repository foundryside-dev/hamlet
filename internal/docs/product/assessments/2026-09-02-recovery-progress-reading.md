# Recovery progress reading — 2026-09-02

**What this is:** a point-in-time reading of how much of the recovery program (`hamlet-1ade187dcc`,
the 2026-08-11 maturity assessment) is done, and how far the tree is from the vision's
destination. Requested by the owner at the fifty-third checkpoint; taken by reading the product
workspace, the tracker, and `src/townlet/` at `ca0378ac` (`project-recovery-4`, `main` at
`ea3648db`). It is a **reading, not a decision** — it changes no bet and no horizon.
Method: tracker state from filigree, workstream and WS-4 child status by query, ledger items
spot-checked against source by grep and by reading the call sites, not from the tracker's text.

## 1. Headline

Recovery is roughly at its midpoint by the program's own yardsticks. The enabling
infrastructure is finished and banked on `main`; the product work it was built to enable is
essentially unstarted. The Now bet's exit (`PDR-0058`: retire the oracle) has three conditions
and none is met.

## 2. Workstreams

| Workstream | Status | Note |
|---|---|---|
| WS-1 correctness defects (`hamlet-67ffbd282a`) | closed | cache keyed on level, LSTM gradient flow, economy clamps |
| WS-7 freeze and oracle (`hamlet-e3af412673`) | closed | pinned oracle, differential harness, divergence register |
| Token observation umbrella (`hamlet-fa6bb6da4a`) | closed | five checkpointed milestones, M4 four cells pass |
| WS-0 unblock (`hamlet-8eeaba1461`) | open | frontend metadata, pre-filigree ticket migration |
| WS-6 plan reconciliation (`hamlet-5e39fcccb0`) | open | head of the critical path, no children filed |
| WS-2 deletion (`hamlet-337b9e80fb`) | open | `src/townlet/recording/` and `config/capability_config.py` still in tree; `source_map.py` was deliberately resurrected (`PDR-0121`) and is no longer dead |
| WS-3 wiring harness (`hamlet-1f89714685`) | open | one seed child only; `test_pack_smoke.py` and 76 YAML-driven tests exist but no per-surface category |
| WS-4 authoring surface (`hamlet-15050f280a`) | open | 54 children: 11 closed, 35 triage, 7 proposed, 1 open |
| WS-5 doc truth (`hamlet-ad2773718a`) | open | gated on WS-4 (`PDR-0125`) |

The milestone itself is still `planning`. Two of eight workstreams are closed; the critical path
(WS-6 → WS-2 → WS-3 → WS-4) has not started.

**Milestone success criteria, read one by one:** zero declared-but-inert surfaces — no;
a config-in/behaviour-out test per declarative surface — partial (pack smoke + token-type
exercises, not per surface); compile cache keyed on `primary_level` — done (WS-1); recurrent
path threads LSTM state — done (WS-1); markdown ticket stratum migrated — not done (WS-0 open);
canonical docs source-derived — gated (WS-5 behind WS-4).

## 3. Scale of what moved

| Reading | Value |
|---|---|
| Commits since 2026-08-11 | 335 |
| `src/townlet` diff vs `oracle-2026-08-13` | 111 files, +12,738 / −6,374 |
| `src/townlet` size | 52,053 lines |
| Merges to `main` | 5; latest `ea3648db`, Lint / Tests / Config Validation all green |
| Tests | 332 files; 3,846 pass / 11 skip at the last local reading (`a07b889b`) |
| Divergence register | 12 entries: 6 `built`, 4 `retired`, 2 `tag-stamped`; 0 closed by an adjudicated rebuild |

## 4. Bet exit (`PDR-0058`) — none of three conditions met

1. Every register entry terminal — **no**: six `built` entries are live divergences.
2. Harness verdict vocabulary re-earned — **no**: `AGREE` is unreachable matrix-wide since
   `PDR-0056`; green certifies "diverged exactly as registered".
3. Gates read on a suite that hides nothing — **yes** since `hamlet-a0832f9004` closed.

## 5. Gap to the final implementation — the seven config surfaces

Against the seven surfaces `metrics.md` tracks (VFS variables, VTC transitions, DAC rewards,
effects, items, substrate topology, curriculum), verified at source:

| Surface | Reading | Evidence |
|---|---|---|
| DAC rewards | **closed** | all strategy types real; `money_bar` is a required role binding, not a name branch (`config/drive_as_code.py`); `hybrid` is self-described "simplified" (`dac_engine.py:409`) |
| VTC action writes | **wired, unproven** | `CustomActionConfig.writes` compiles (`compilers/actions.py:125`, landed `7cbfbff8` 2026-08-21) and reaches VTC (`vectorized_env.py:548` → `vtc.py:2257`); **no shipped pack declares `writes:`** and `test_custom_actions.py` only covers REST *without* writes; occupancy claims are the one exercised path (`test_occupancy_wiring.py`) |
| VFS variables | **half-real** | three declaration surfaces (`environment.yaml`, `vfs_profiles.yaml`, `variables_reference.yaml`); reference-file variables absent from the symbol table (`hamlet-33e520cebd`); `lifetime` hardcoded (`hamlet-4597fd5d04`); access roles have no authoring field (`hamlet-1a520475f4`) — this is the declaration-store unit, `PDR-0147` |
| Effects | **partly wired** | declared scope now reaches spawn (`executor.py:596-631` reads `context.effect.scope`; `manager.py` dispatches on all four); effects still cannot read position or time (`hamlet-a737e444c0`); `spawn_item` unreachable end-to-end (`hamlet-1b9af9088c`) |
| Items | **partly wired** | pickup/use work; `on_drop` compiled and never invoked from a live path (`hamlet-628e202bf7`); no destruction surface (`hamlet-83806979f7`); held items invisible to the `item` token type (`hamlet-4b931faaf4`) |
| Substrate topology | **selection only** | 6-D witness passed (Trial 001); a new topology is still a Python edit |
| Curriculum | **not started** | `STAGE_CONFIGS` Python literal (`curriculum/adversarial.py:28`), `max_length=6` (`training/state.py:157`), life-sim meter names hardcoded (`curriculum/static.py:47`, `adversarial.py:45-59`) |

**Count: 2 closed, 3 partly wired, 2 not started.** The scoreboard row still read "~2 of 7" from
2026-08-17 and had not been re-read since the token cut; that reading undercounted the
VTC and effects movement and is refreshed at this checkpoint.

Beyond UAC: Brain as Code is 1 of 3 layers live (layer 2 only); the model-export path the
prototyping-modeller audience depends on has no entry point (`hamlet-0cdb8a6d1a`). Neither is in
any workstream.

## 6. Why it feels further along than the counts say

The strangler front-loads instruments — oracle, harness, hashes, token ABI — so each later cut is
checkable in one diff. That is why five merges landed with zero regressions, and why the product
metric has barely moved: instrument work protects surfaces without opening them. The next unit
(`PDR-0147`) is the first that closes a whole surface rather than widening a working one.

## 7. Loose ends surfaced by this reading

1. **The tracker lags the code on at least one WS-4 item.** `hamlet-3381043d2e` claims the
   compiler hardcodes `writes=()`; that was true when filed (2026-08-19) and false since
   `7cbfbff8` (2026-08-21). Annotated on the issue at this checkpoint, not closed — the runtime
   half is unproven by any committed pack. A pass over the 35 triage items against source is owed
   before WS-6 assigns causes.
2. **The config-surface metric was unread for sixteen days.** Refreshed here; it should be re-read
   at every unit acceptance, not only at merges.
3. **WS-2's confirmed-dead list is partly still in tree** — `recording/` and
   `capability_config.py` unchanged since the assessment; `affordance_masking.py` is gone.
