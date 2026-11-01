# T18 independent review — NOT GREEN

Two P2 findings block release of this candidate. The bounded FIFO implementation and valid native tail continuation passed independent checks; optimizer checkpoint refusal is incomplete.

## Immutable identity and inspection inventory

- Base HEAD: `050a1a70e979aa03724219b81e848093820f044f`.
- Selected staged tree: `7901753a30d08f6bbea78670cb71241e8f784d2e`.
- Detached snapshot: `/tmp/bac-verify-T18-7901753a30`; HEAD alone is the base, not the implementation.
- Actual `townlet.__file__` asserted inside that snapshot for the probe and pytest run.
- Source hashes verified before and after execution, all unchanged and identical to `task-T18-candidate.json`:

| File | Lines | SHA256 |
|---|---:|---|
| `src/townlet/exploration/rnd.py` | 604 | `e55f9f39e723f822fa6225f9d3010b36c6eac1cf48da2a3d8cdc9416fdbd78f0` |
| `src/townlet/population/vectorized.py` | 1854 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| `src/townlet/config/bac_options.py` | 243 | `1de08a7cc36c49772254d8b9dc2d8adf3cac76533eecba5c36568745bc48c8f1` |
| `tests/test_townlet/regressions/bac/test_rnd_service.py` | 334 | `b00f61416f5f5808b961aee256f69ed1637e962e286b4eeee766b549d2cfb6da` |

These are the only four project implementation/test sources inspected, charged as 3035 whole-file lines. The sole additional authored source is sibling `task-T18-review-probe.py`, 187 lines; total five sources/3222 lines. References include AGENTS.md, brief/report/package/manifest/patch, STATUS/BRIEF methodology, and authored training YAML. Existing owner tests and imported runner/checkpoint/compiler APIs were executed without opening their implementation. No project source, candidate index, configs, or artifacts were edited by the probe; its configs and run artifacts are temporary copies.

The review honors the newer additive user rule and historical Option A. Existing direct APIs and exact historical dictionaries remain required capabilities. No capability removal is requested.

## Findings

### T18-R1 — P2: incomplete or reset Adam history passes the real population restore gate

Location: snapshot `src/townlet/exploration/rnd.py:488–513`, `:563–576`; consumer `src/townlet/population/vectorized.py:1515–1524`.

The new validator checks that optimizer-state IDs are a **subset** of declared parameter IDs, then validates only moments still present. It never requires all dense RND predictor parameters to have Adam state after a successful update, nor checks each Adam step against the versioned service `optimizer_updates`. The service checks its own row/update arithmetic without connecting it to optimizer history. In this dense network every successful minibatch supplies every parameter a gradient; after two successful updates each parameter must have its complete moment state and step 2.

Independent actual-consumer reproduction, `native_consumer()` in the probe:

1. Copy the complete authored feedforward pack; run `DemoRunner.run()` for two lanes/two episodes/three steps, predictor batch 5. The actual producer state contains admitted=12, consumed=10, optimizer_updates=2, pending shape `[2, obs_dim]`.
2. Establish a valid control: advance with three nonconstant successor rows, reload the ordinary runner artifact, assert the saved state is exact, advance with the same rows, and assert the entire resulting RND checkpoint equals the control.
3. Deep-copy the actual saved population payload. Delete only `payload['exploration_state']['rnd_state']['optimizer']['state'][0]`. All service counts, tails, networks, remaining moment tensors, and authored configuration remain intact.
4. Both `population.validate_checkpoint_state(bad)` and `population.load_checkpoint_state(bad)` succeed. Advance the same three rows. Predictor `net.0.weight` differs from the valid continuation because Adam silently creates fresh moments for that parameter.
5. Independent variant: retain all moments but zero every `moment['step']` while service `optimizer_updates` remains 2. Both public population gates again accept the payload; the same next update differs from the valid control.

This is a missing refusal at the current native checkpoint consumer under the complete/validated future-state contract. It is not deferred production-service wiring or a DTO-only artifact. Require full moment coverage and per-parameter step consistency for versioned RND continuation; reject before installation. Keep exact historical available-state import as its separately identified, supported path.

### T18-R2 — P2: standalone RND installs an optimizer configuration its destination cannot execute

Location: snapshot `src/townlet/exploration/rnd.py:491–494`, `:516–517`.

Only lr/eps/weight-decay/beta ranges are checked after preparing the copied optimizer. Destination compatibility of execution flags is not validated. On CPU, take a valid configured provider checkpoint after a successful minibatch, change only `state['optimizer']['param_groups'][0]['capturable'] = True`, then call `validate_state` and `load_state`. Both succeed and install the payload. The next admitted row completes a batch and fails inside Adam with:

```text
AssertionError: If capturable=True, params and state_steps must be on supported devices:
['cuda', 'xpu', 'hpu', 'privateuseone', 'xla'].
```

The probe asserts this exact causal sequence against the actual candidate. The population's existing exact configuration validator rejects this particular flag change; this finding belongs to the public standalone backend validation/load contract, which is separately promised and intended for reuse. Validate optimizer group schema/types and destination-supported execution configuration before installation, preserving valid supported optimizer settings.

No P1 or separate P3 finding is asserted.

## Positive evidence and limits

The independent probe exits 0 after asserting the passing controls **and reproducing the two defects**. Its exit code therefore does not indicate a green verdict. Command:

```bash
PYTHONPATH=/tmp/bac-verify-T18-7901753a30/src CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /workspace/hamlet/.venv/bin/python /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T18-review-probe.py
```

Captured output: `/tmp/bac-t18-review-probe.log`.

- FIFO model: **144 calls** across both service modes and all three overflow policies; capacity 5/batch 3/budget 2; oversized, empty, same-tick and later-tick inputs. Exact consumed-row order, pending row identities, receipts, conservation, budget/overflow split, and periodic full-state restoration all pass.
- Actual runner artifact: valid two-row tail reload and identical next complete RND checkpoint pass, independent of DTO-only tests.
- Candidate regression plus four B05 exploration owner suites: **106 passed in 16.26s**. Command uses `/workspace/hamlet/.venv/bin/python`, `PYTHONPATH` pinned to snapshot `/src`, CUDA disabled, OMP/MKL=1, `torch.set_num_threads(1)`, and `pytest.main(['--no-cov','-p','no:cacheprovider', ...,'-q'])`. Selections are `tests/test_townlet/regressions/bac/test_rnd_service.py`, plus `tests/test_townlet/unit/exploration/{test_epsilon_greedy_selection.py,test_exploration_strategies.py,test_rnd_normalization.py,test_rnd_stats_update_timing.py}`. Captured output: `/tmp/bac-t18-review-tests.log`.
- Existing regression suite verifies frozen target, normalization separation, owned snapshots, exact historical import/direct operation, malformed tail/config/count/normalization/network/selected optimizer refusal, valid private-instance continuation, native corrupt-tail atomic refusal, and fresh-runner restore. These are real passing controls; they do not cover missing/reset optimizer history or incompatible execution flags.

Source review finds the POP change narrow: exact historical keys or that exact set plus `predictor_service`, existing strict checks retained, provider validation called before applying population fields. No broad unknown-key or fallback bypass was introduced. The service supports lossless overflow service and separately counted explicit drops; direct one-minibatch behavior is retained. Code structure is understandable, with preparation preceding installation. The incomplete optimizer validation is the material quality and contract gap.

Strict per-world state bank/lifecycle/isolation and production bounded-service wiring are explicitly unimplemented and remain open acceptance work, not new findings in this scoped reusable-backend review. No GPU, slow, coverage, repository-wide static, or full pytest qualification was run here; the coordinator owns the required repaired-snapshot full gate. No whole-BAC, G03/G04, S1 or repository-green claim is made.
