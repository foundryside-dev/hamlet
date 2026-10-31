# WS-1 pinning-test sources of record

Working copies of pinning tests written and measured during WS-1 planning, kept here
because the plan cites them and the original location did not survive.

**Why this directory exists.** `docs/plans/2026-08-11-ws1-fix-set.md` originally cited these
as `scratchpad/…`. No `scratchpad/` directory exists in the repo or in git — the files lived
in a prior session's `/tmp`, which is ephemeral. The second review (`PDR-0015`) flagged the
citation as dead. They are committed here so the plan's references resolve.

These are **not** live tests. Nothing collects them — the filenames are deliberately not all
`test_*.py`-under-`tests/`, and they are excluded from the pytest testpaths. Each becomes a
real test file when its unit is implemented, at the path its task names.

| file | destination | task |
|---|---|---|
| `PINNING_TEST_b_FINAL_test_recurrent_bptt_runtime.py` | `tests/test_townlet/integration/test_recurrent_bptt_runtime.py` | 6 |
| `b_amended_test.py` | *(amendment donor only — see below)* | 7 |
| `c_test_recurrent_bootstrap_runtime.py` | `tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py` | 7 |
| `test_dead_agent_interaction_gating.py` | `tests/test_townlet/integration/test_dead_agent_interaction_gating.py` | 3b |

## `b_amended_test.py` is a donor, not a base

It carries the H6 amendment that task 7 needs, but it is **not** a newer version of
`PINNING_TEST_b_FINAL`. Diffed, it makes three changes and only two are wanted:

- ✅ `expected_run_length = sequence_length + 1` — the H6 amendment itself
- ✅ explicit `q_learning.use_double_dqn = True` in `_make_pack` — double-DQN gives
  `{T+1, T+1}`; vanilla would give `{T, T+1}` and make the assertion ambiguous
- ❌ **drops** `shutil.rmtree(target / ".compiled")` — task 7's trap 3 requires it, and
  WS-1(a) is precisely why inheriting a source pack's compile cache is unsafe
- ❌ **rewrites** pinning test 3 from the `nn.LSTM` forward-pre-hook onto
  `population.rollout_hidden` — which defeats the point of that test. Hooking `nn.LSTM`
  itself means it names neither the old nor the new townlet API, so it discriminates a
  correct fix from a plausible-looking wrong one. Keep the `nn.LSTM` form.

**Take the amendment from it; take the file from `PINNING_TEST_b_FINAL`.**

Both the second review and an independent read reached this conclusion separately.
