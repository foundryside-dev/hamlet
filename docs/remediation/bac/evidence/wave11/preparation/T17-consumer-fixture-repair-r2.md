# T17 consumer fixture repair R2 — root remeasurement pending

2026-11-02 UTC; existing `/workspace/hamlet`. Root explicitly cleared this bounded repair after reporting both R1 runtime sessions CLOSED. Root-supplied results: affected exactly2 failed/407 passed in358.7037s; the second failure was the rollout-memory observation assertion at line216, matching the same constructor interception blind spot. Root also reports owned34 PASS, independent Astra12 PASS, six guardsPASS, and complete custody checks. Those results are attributed to root; this worker did not rerun or independently inspect those runtime gates.

## Exact change

Only `tests/test_townlet/integration/test_recurrent_bptt_runtime.py` was edited. In the gradient test (lines92–98) and rollout-memory test (lines184–196), save `RecurrentTokenQNetwork._initialize` as `original_initialize`, name the observer wrapper `instrumented_initialize`, call the saved method with the unchanged `self, *args, **kwargs`, and monkeypatch `_initialize` instead of `__init__`.

Each wrapper calls its saved original exactly once as its first statement. The existing recurrent-weight autograd hook and LSTM forward-pre-hook are unchanged and attach only after real initialization. Both legacy direct construction and `from_resolved_encoder` reach this common initializer. Production code, construction semantics and explicit interaction-MLP selection are unchanged. No manufactured gradients, replacement networks, sentinel observations, assertion removal, skip or xfail was added.

## Static assertion-preservation evidence

Before source mutation, Python standard-library `ast`, `hashlib`, `json` and `pathlib` parsed the existing test as text; no project module was imported or executed. The process retained only compact evidence, not a project-source copy. It recorded the original source SHA256 and computed an expected repaired AST from exactly these four textual substitutions, each occurring in the two existing observer blocks:

```text
original_init = RecurrentTokenQNetwork.__init__
  → original_initialize = RecurrentTokenQNetwork._initialize
def instrumented_init(self, *args, **kwargs):
  → def instrumented_initialize(self, *args, **kwargs):
original_init(self, *args, **kwargs)
  → original_initialize(self, *args, **kwargs)
monkeypatch.setattr(RecurrentTokenQNetwork, "__init__", instrumented_init)
  → monkeypatch.setattr(RecurrentTokenQNetwork, "_initialize", instrumented_initialize)
```

AST serialization used `ast.dump(..., include_attributes=False)` to exclude source positions. The assertion evidence hashes `json.dumps` of every `ast.Assert` dump in `ast.walk` order.

| Static evidence | Result |
| --- | --- |
| Original test source SHA256 | `2701678bcb442360eb2a860ea4e74bc7d5b8d4b9b2f639b78c21cd7db9f2494a` |
| Assertions before / after | **23 / 23** |
| Assertion AST SHA256 before / after, identical | `cafe1d69a70e3200f9bdba06b3f44b3f8fdb38b315ad1051f137be52141782f0` |
| Expected repaired complete AST SHA256, computed before editing | `da5f302b83a47e5338e97c4b1465f9e5d566629f2c60d3b48221f0bda7de4bbb` |
| Actual repaired complete AST SHA256, after editing/Black | `da5f302b83a47e5338e97c4b1465f9e5d566629f2c60d3b48221f0bda7de4bbb` |
| Exact expected AST match | True |
| Observer wrappers / original calls | Two wrappers; exactly one saved-original call per wrapper, first statement |

The post-edit static checker asserted all these equalities and exited0. This proves the complete executable AST differs only by the intended observer method/local-name substitutions. The complete three test functions, sequence-length parameterization `[2, 8]`, authored configuration/scenarios, `_run` real optimizer/counter/parameter-change checks, every nonempty/strictly-positive recurrent-gradient assertion, full-horizon finite/nonzero derivative checks and live/completed-lane memory conditions remain intact. Source diff readback showed only the two observer blocks changing.

Authorized formatter command:

```text
/workspace/hamlet/.venv/bin/black tests/test_townlet/integration/test_recurrent_bptt_runtime.py
```

Exit0, `1 file left unchanged.` No project runtime/import, pytest, collection, compiler, linter or format-check command ran. The standard-library AST checks are static evidence only and do not establish actual gradient or memory behavior.

## Exact complete-source inventory after repair

The inventory remains exactly the same three complete sources; no fourth helper/implementation source was opened. Physical line counts from `wc -l`; hashes from `sha256sum`:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/agent/networks.py` | 655 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| `src/townlet/agent/network_factory.py` | 179 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| `tests/test_townlet/integration/test_recurrent_bptt_runtime.py` | 222 | `105656e944001f44213e8c721bc98d7c99e8d8512aa1172eeabc93ea0f3df0a7` |
| Total | **1056** | NET/NF exactly unchanged |

## Custody and handback

Only the authorized existing test and this new ignored receipt were written in this repair phase. `git check-ignore` confirmed this receipt's ignored destination before writing. No production/config/fixture/protected artifact/index/commit/push, branch/worktree, source copy/deletion or delegation action occurred. All14 worktrees were left untouched. The earlier static audit and original R1 negative artifacts remain untouched.

Root owns actual R2 remeasurement, fresh independent review and integration. The real configured run must still prove nonempty strictly-positive recurrent-weight gradients, both full-horizon cases, and all rollout/completed-lane memory assertions. No runtime GREEN, fixed-behavior or full-qualification claim is made here. Worker returns stationary.
