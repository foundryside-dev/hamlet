# T09a independent SPEC + QUALITY review

Verdict: **PASS for the bounded X03 repair, both specification and quality. No material P1/P2 finding remains in the reviewed physical-action admission change.** This does not approve the joint release or establish an exhaustive frozen-world invariant. Release requires zero outstanding P1/P2 findings, the final actual-wave identity refresh, and root's required exact-tree gates.

Fresh independent other-model review of the Astra-implemented packet. Read the T09a brief first. User capability-preservation instructions override AGENTS blanket deletion guidance. No production/permanent test source, index, git state, or other packet was mutated; only this receipt and the one ignored review probe were written. No delegation or broad full pytest was performed.

## Fixed identity and source boundary

- Snapshot: `/tmp/bac-verify-T09a-63beed0c8d`.
- Base HEAD: `050a1a70e979aa03724219b81e848093820f044f`.
- Actual staged candidate tree: `63beed0c8d85c3cbfb3d438982630f413eee4023`.
- Before and after execution, `git diff --cached 63beed0c8d85c3cbfb3d438982630f413eee4023 --exit-code --quiet` and `git diff --exit-code --quiet` passed, and HEAD matched the base. HEAD alone was not used as candidate identity.
- Import before/after the final execution was asserted to be `/tmp/bac-verify-T09a-63beed0c8d/src/townlet/__init__.py`; direct installed `/workspace/hamlet/.venv/bin/python`, CPU, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, explicit Torch threads 1.

Four candidate implementation/test sources, **2469 lines**:

| Source | Lines | Verified SHA256 before and after |
| --- | ---: | --- |
| `src/townlet/environment/action_executor.py` | 299 | `c0f1c2ee2396e35e192d11d81d79f5a25f1112d3ef8143adbff367011dbbe980` |
| `src/townlet/environment/vectorized_env.py` | 1714 | `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d` |
| `tests/test_townlet/regressions/bac/test_successor_producer.py` | 212 | `c88043817f6996f02a1a7cb732e96b1afdc1a70c548b7b956c7da125eb605670` |
| `tests/test_townlet/regressions/bac/test_inactive_action_execution.py` | 244 | `851986aa7f17350c8c769b939a400207ac718c97acfaf23ed0e657e3f41bab67` |

One fifth source is my own `task-T09a-review-probe.py`, **201 lines**, SHA256 `d76c94abb19bf628c3fd6dc48edd8ad42e2ca00c17854b429d3411d081f2492b`. The original 291-line revision of the same approved AE logical source was additionally loaded only for the isolated causal comparison; its SHA256 was asserted as `fafc6e34c8806cf9f681a5b6eb797828b1309953aa7efbe03a1635c3375e3161`. Conservatively charging both AE revisions: **2961 source lines, five logical files**. No sixth implementation/test/helper, item-handler, action-builder, conftest, or old external T09 probe source was opened. Additional owner tests were execute-only. Other reads were task/report/manifest/patch/AGENTS material and authored YAML, including the published END_LANE action shape.

## Specification assessment

The original X03 was real on both base and prior candidate: completed DROP changed inventory after authored death. The old report's red evidence has not been reinterpreted as green. The permanent exact regression now passes on the reviewed fixed snapshot.

At AE line 42, a fresh boolean `~env.dones` tensor captures entry eligibility. ENV captures entry activity at lines 1089–1090, calls AE at 1096, and evaluates terminal conditions only at 1149. This admits a live final action and rejects completed rows without manufacturing legality or changing the submitted vector. ENV still forwards that actual vector with its explicit activity mask to VTC at 1097–1101.

Physical gates cover substrate movement and movement debit (AE 47–67), GET (78), every USE slot (98), every DROP slot (117), and each authored custom-item action (132). They filter before per-row item-handler dispatch. Completed velocity is retained at line 53; live WAIT/item actions continue to publish zero displacement, and live movement publishes its real final displacement. No signature, default, action vocabulary, feature, or live selection policy is removed. Existing illegal-live/empty-successor diagnostics remain in place; the tests check predecessor legality for every live submitted action.

The new regression module uses actual compiler/reset/step and authored pack/item rules; it does not inject runtime done/mask/position/inventory/meter state. Its 22 passing cases cover exact completed DROP, live GET/USE/DROP/custom actions, dead WAIT and item intents, movement debit and retained terminal velocity, both authored and lifespan completion, eligible final actions, two completed plus two continuing rows, canonical/historical successor masks, and all-complete extra steps. These are meaningful causal state assertions rather than mask-only checks.

## Independent adversarial evidence

The fifth-source probe authors a six-world pack through the counted producer helper, modifies YAML, recompiles, resets, and drives supported actions. It adds these independent positive/negative cases:

1. **Interleaved completed worlds and mixed action IDs.** Worlds 1, 3, 5 die through an authored tick condition while 0, 2, 4 live. The eligible final batch mixes USE, DROP, and inventory POLISH. Following batches mix inactive USE/GET/DROP/POLISH with different live actions. Exclusive items exercise actual slot 1, shared items slot 0. Live literal effects are 7 and 11 money, live GET restores the dropped inventory, completed item identity/position/holder and observation/meter/position/velocity/inventory witnesses remain equal, counts diverge correctly, and siblings later retire once. Historical canonical masks survive continuing steps and an all-complete extra step.
2. **The item action itself causes death.** Authored USE_SLOT_1 both adds 7 money and writes lethal energy zero. Alternating rows die through that actual item action; the effect is visible on the final eligible step. Repeating USE_SLOT_1 in the next batch leaves them at 7 while the previously live siblings execute it once and also finish. This checks entry gating independently of the worker's tick-caused final actions.
3. **Actual INTERACT intent versus actual active interaction.** All six worlds first interact with Bed, each gaining the authored 17 money. END_LANE, a real custom VTC action, then terminates alternating rows, corroborating that the vector still reaches VTC. An observational wrapper preserves the original tracking method. An all-WAIT batch makes no tracking call; a batch with only completed-row INTERACT intents calls tracking once with `{}`, applies no physical interaction effect, and clears the prior `_last_affordances` exactly as the old implementation does. Subsequent live-row INTERACT gives only live rows another 17 money and reports their actual successes.

The last distinction is intentional and material: AE's intent-only `substrate_mask` and `interact_intent.any()` trigger are preserved, while `interact_mask` gates actual interaction/debit. The original comment at AE 148–156 remains, with a narrowly added explanation for physical movement. The probe verifies unchanged tracking timing on both original and fixed AE. It does **not** treat all tracking fields as frozen completed-world state.

## Executed evidence and reproducibility

All executions used cwd snapshot, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=/tmp/bac-verify-T09a-63beed0c8d/src`, and `/workspace/hamlet/.venv/bin/python`. The runner preimports and asserts `townlet` from the snapshot before invoking pytest:

```python
import pathlib, torch, townlet, pytest
torch.set_num_threads(1)
assert pathlib.Path(townlet.__file__).resolve() == pathlib.Path(
    '/tmp/bac-verify-T09a-63beed0c8d/src/townlet/__init__.py'
)
raise SystemExit(pytest.main(['--no-cov', '-p', 'no:cacheprovider', '-q', *paths]))
```

Selected candidate `paths`:

```text
tests/test_townlet/regressions/bac/test_inactive_action_execution.py
tests/test_townlet/regressions/bac/test_successor_producer.py
tests/test_townlet/regressions/test_episode_lane_environment.py
tests/test_townlet/unit/environment/test_action_masking.py
tests/test_townlet/unit/training/test_episode_accounting.py
tests/test_townlet/integration/test_authored_episode_lanes.py
```

Result: **107 collected / 107 passed in 36.75s**, exit 0; `/tmp/t09a-review-owners.log`. This is the new 22, producer 5 and B11 80. No skipped, xfailed, or failed results.

Own-probe `paths` is the single absolute `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T09a-review-probe.py`:

- Candidate: **4 passed in 3.17s**, exit 0; `/tmp/t09a-review-probe-green.log`.
- Same command with `T09A_ORIGINAL_EXECUTOR=1`: **3 failed / 1 passed in 3.19s**, expected exit 1; `/tmp/t09a-review-probe-original.log`. That fixture obtains the exact base AE with `git show`, hash-checks it, compiles it in a private namespace, and monkeypatches only `_execute_actions` within that process. Both interleaved cases fail at the intended item-holder freeze assertion (inactive GET reclaims the dropped item); self-caused death fails at the intended observation/meter freeze assertion (money 7 becomes 14). The INTERACT intent/timing control passes. This is an executor-delta comparison against current dependencies, not a full base-tree reconstruction.
- Fresh final candidate rerun after that original-method comparison: **4 passed in 3.53s**, exit 0. A single-process `verify()` before and after pytest asserted all four source hashes, HEAD, staged tree, unstaged cleanliness, and snapshot import identity. No source/index changes occurred.

Calibration was kept separate from causal results. The first exploratory shared case assumed repeated GET would fill shared slot 1; the real API retained the first shared instance in slot 0. The shared witness now exercises that actual held slot; exclusive coverage exercises slot 1. No shared slot-1 capability conclusion follows. A direct `python -m pytest` invocation for the external ignored probe also exposed pytest root-path import precedence; its snapshot-import assertion deliberately refused the live workspace import at collection. The reported runs use the asserted preimport wrapper above. Neither setup failure is counted as vulnerability evidence.

The worker receipt separately reports 313 owner tests, scoped Ruff/Black/mypy and unchanged whole no-defaults 614 ceiling passing. Those additional 206 owners and static checks were not independently rerun here and are attributed to that receipt. This review did not run repository-wide pytest/coverage or assert whole-BAC green.

## Findings, limits and release conditions

No P1/P2 defect or capability reduction was found in the reviewed repair. Specification and quality both pass within the stated boundary. The implementation is a localized, consistent eligibility intersection at the physical dispatch sites, with no test-oracle weakening or hidden action replacement.

Witnesses are bounded to the observed interfaces and authored actions. PW12 still owns the complete simulator-state inventory. Preserved INTERACT tracking timing itself illustrates why a blanket all-state-freeze claim would be false. GPU, every substrate, arbitrary malformed external input, all shared-item temporal state, population/learner internals, and full lifecycle integration beyond executed owners were not qualified.

Before dependent release (including T15/T18e), root must verify these same four owned byte hashes against the **actual final fixed wave**, including if an unused RP module commits first and changes the base/tree. Refresh the identity linkage explicitly; do not silently transfer the old staged-tree label to a new candidate. Root must then complete the exact-wave collection, owners, six standing guards and full suite, and disposition any remaining P1/P2 finding to zero. This scoped PASS is not a waiver of those conditions.

## Final actual wave02 identity refresh

Root supplied the actual joint candidate after the initial review: snapshot `/tmp/bac-verify-wave02-3d1d21cff5`, base `050a1a70e979aa03724219b81e848093820f044f`, staged tree **`3d1d21cff5abdf60b630f97da0cdb09bf8ccd036`**. Read the new `task-T09a-wave02-candidate.json` and `task-T09a-wave02-review-package.md`. Their four owned source mappings equal the original review manifest exactly; all four bytes/hashes in the table above were independently rechecked before and after fresh execution on wave02. No additional source file was opened. The authored `configs/aspatial_test` fixture subtree and `configs/test/episode_lanes/actions.yaml` were also verified unchanged between the two candidate trees using `git diff OLD_TREE NEW_TREE --exit-code --quiet -- PATHS`.

The same single own probe now selects its snapshot root through `T09A_REVIEW_SNAPSHOT` (one-line adapter only, still 201 lines). Its final SHA256 is **`36cb25c2d220d5b7e9b082c8b729adff79ac2d2947a8b1aea81a33193e0d6e26`**; the previous probe hash above identifies the initial-snapshot runs. No test assertions or authored scenarios changed during the refresh.

Fresh execution set `T09A_REVIEW_SNAPSHOT=/tmp/bac-verify-wave02-3d1d21cff5`, `PYTHONPATH=/tmp/bac-verify-wave02-3d1d21cff5/src`, and the same OMP/MKL/Torch thread limits. The installed Python wrapper preimported and asserted `townlet` from **wave02**, verified HEAD and both staged/unstaged diffs, verified the four source hashes and fixture YAML equality, invoked pytest on the own-probe absolute path with `--no-cov -p no:cacheprovider -q`, then repeated all identity checks **after** pytest in the same process.

Result: **4 collected / 4 passed in 3.46s**, exit 0; `/tmp/t09a-review-wave02.log`. Both before/after import checks resolved to `/tmp/bac-verify-wave02-3d1d21cff5/src/townlet/__init__.py`; Torch threads 1. The staged tree equals `3d1d21cff5abdf60b630f97da0cdb09bf8ccd036`, unstaged diff is empty, and all four source hashes remain identical. The earlier 107-pass owner selection and original-executor 3-fail/1-pass comparison remain explicitly attributed to the initial `63beed...` snapshot; they are not relabeled as wave02 executions.

**SPEC PASS and QUALITY PASS are refreshed for these unchanged T09a bytes on actual wave02; zero scoped P1/P2 findings.** The identity-refresh condition is satisfied for this actual tree. Root still owns wave02's collection/owner gates, six standing guards, full suite and global zero-P1/P2 release decision. Off-scope RP work was not source-reviewed here. All PW12/exhaustiveness and preserved INTERACT tracking limits above remain in force.
