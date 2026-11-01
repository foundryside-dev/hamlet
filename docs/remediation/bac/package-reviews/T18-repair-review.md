# T18 repair round 1 independent re-review — scoped GREEN

**T18-R1 addressed. T18-R2 addressed.** No new P1/P2/P3 finding in this repair. The reusable single-provider backend meets this packet's scoped contracts; release remains conditional on coordinator-owned selected-wave integration/full gates. Strict per-world ownership and real production bounded-service wiring remain unimplemented acceptance work.

## Fixed candidate and bounded inspection

- Snapshot: `/tmp/bac-verify-wave01-6881a7488a`.
- Base HEAD: `050a1a70e979aa03724219b81e848093820f044f`.
- Selected joint-wave tree: `6881a7488a110adbd94c689b67b5241fb094d10e`. HEAD alone is the base. The probe compares the complete index entry metadata against this exact tree using read-only `ls-files --stage` / `ls-tree -r`; it does not inspect other packets' source contents.
- `task-T18-r1-candidate.patch` exactly equals `git diff --cached --binary` restricted to the three T18 changed files. The repair diff and updated receipt/package/manifest were reviewed against the original requirements and both prior findings.
- Four source hashes verified before and after all executions; actual import path asserted inside this snapshot:

| Source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/exploration/rnd.py` | 661 | `3a774dfb042cdbf20b66555c41f75c2d537b6ff49472395877dfcf5595e26e72` |
| `src/townlet/population/vectorized.py` | 1854 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| `src/townlet/config/bac_options.py` | 243 | `1de08a7cc36c49772254d8b9dc2d8adf3cac76533eecba5c36568745bc48c8f1` |
| `tests/test_townlet/regressions/bac/test_rnd_service.py` | 422 | `ecd2db6e72de5fba9453a6fff217d68113f6ff138c3c7a6cc9b5548e9e340c74` |

Inventory: those four project sources, charged as 3180 whole-file lines, plus the existing independent probe rewritten in place, **265 lines**: five sources/3445 lines. No sixth source, AS/ENV implementation, conftest or other test/helper implementation was inspected. POP and OP bytes are unchanged from the initial review. No project source/index mutation, subagents or broad pytest run was performed. The original failed-candidate review remains historical evidence; this review concerns only the new fixed candidate.

## Finding closure and quality

**R1 — complete optimizer continuation: addressed.** `rnd.py:524–555` now requires complete parameter-state coverage when any moments exist and a common integral Adam clock. `:618–622` compares that clock to the **saved** service update count plus saved signed offset. Empty/reset history cannot be accepted by deriving replacement metadata from the incoming moments. `:439–441` captures the offset from trusted live state, preserving supported external manual optimizer steps and historical available-state imports without fabricating consumed rows.

Independent actual native-consumer check: the authored runner produces admitted=12, consumed=10, two service updates, offset=0 and a two-row tail. Starting from that captured payload, delete one Adam parameter state, clear all moments, reset all steps, or change one parameter step. Each malformed payload retains the original service metadata and also changes Q tensors to 99 and total_steps by 100. **Both** public population validation and load reject every payload with ValueError, and the entire live population checkpoint remains equal to its pre-operation snapshot. Original next-update divergence is therefore prevented before any Q/counter installation. The same standalone and delegated provider checks also pass. Native consumer delegation remains narrow and unchanged in this repair.

**R2 — optimizer destination compatibility: addressed.** `rnd.py:468–490` validates group schema/IDs/scalar and flag types. `:556–565` performs the destination execution check on a disposable deep-copied optimizer and parameters, returning the untouched prepared optimizer for installation. The exact original CPU `capturable=True` corruption now refuses in standalone validate/load; live state and global torch RNG remain unchanged. Population refuses it as well. No unsupported flag restriction was inferred from its name alone.

The independent probe additionally verifies supported `amsgrad=True`, `maximize=True`, `foreach=True`, CPU `fused=True`, and scalar-tensor learning rate with `foreach=False`: each validates without changing destination state, loads without advancing moments or drawing RNG, and matches the source's next real update exactly. Manual one/five-step optimizer histories retain their positive offsets and next-update equality. Historical available-state imports with zero and three Adam updates into an existing two-update service retain signed offsets -2/+1, preserve the pending tail and direct one-minibatch API, and match restored next updates.

The repair is cohesive: metadata records the two clocks' relationship, preparation rejects corrupt history, and the execution preflight remains separate from the object installed. No capability removal is required by either fix. No additional material quality finding was established.

## Executed evidence

The sole adversarial source is sibling `task-T18-review-probe.py`. Its assertions now require refusal of the old defects. Command, exit 0:

```bash
PYTHONPATH=/tmp/bac-verify-wave01-6881a7488a/src CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /workspace/hamlet/.venv/bin/python -u /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T18-review-probe.py
```

Actual output `/tmp/bac-t18-r1-review-probe.log` confirms:

- 144 FIFO calls across six mode/overflow combinations pass exact consumption order, retained identities, receipts, conservation, same-tick budgets, overflow classification and full-state restoration controls.
- Original malformed optimizer cases plus empty and unequal-step variants refuse atomically in standalone and delegated population-provider validation.
- Manual history, signed historical offsets, supported optimizer settings and no validation/load RNG draws pass.
- Actual ordinary runner artifact restores the exact two-row tail and produces the identical complete next RND state; actual public population gates reject malformed optimizer payloads before changed Q/counter installation.
- Exact base/tree/source identity checks remain unchanged after execution.

Independent regression/owner rerun: **117 passed in 11.87s** (43 task cases + 74 B05 owner cases), exit 0. Command:

```bash
PYTHONPATH=/tmp/bac-verify-wave01-6881a7488a/src CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /workspace/hamlet/.venv/bin/python -c 'import pathlib, townlet, torch, pytest; torch.set_num_threads(1); assert pathlib.Path(townlet.__file__).resolve() == pathlib.Path("/tmp/bac-verify-wave01-6881a7488a/src/townlet/__init__.py"); raise SystemExit(pytest.main(["--no-cov", "-p", "no:cacheprovider", "tests/test_townlet/regressions/bac/test_rnd_service.py", "tests/test_townlet/unit/exploration/test_epsilon_greedy_selection.py", "tests/test_townlet/unit/exploration/test_exploration_strategies.py", "tests/test_townlet/unit/exploration/test_rnd_normalization.py", "tests/test_townlet/unit/exploration/test_rnd_stats_update_timing.py", "-q"]))'
```

Captured output: `/tmp/bac-t18-r1-review-tests.log`. The permanent suite also covers fresh-runner artifact restoration, existing direct APIs, exact historical import, corrupt tails/config/counts and owner normalization/action-selection behavior. The authored probe and pytest ran serially, one torch thread each.

Limits: CPU only; no GPU/slow/coverage/full pytest or whole-repository static qualification in this review. Other wave implementation sources were not inspected. Coordinator-owned integration/full gates are still required for release; this scoped GREEN does not claim G03/G04 closure, strict per-world S1 qualification, whole-BAC acceptance or repository green. The additive preservation rule and historical Option A remain binding.
