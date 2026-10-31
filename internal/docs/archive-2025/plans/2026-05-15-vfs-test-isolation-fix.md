# Fix the VFS test-isolation leak

> **For Claude:** Read this top to bottom before touching anything. Use the systematic-debugging discipline — find the offending writer before proposing a fix. Filigree issue: `hamlet-c1260e52ab`.

## Goal

Make the full pytest suite pass — currently exactly **one** test fails, and only because of cross-test state leakage. After the fix, `uv run pytest --no-cov -p no:faulthandler` should report **0 failed** instead of 1 failed out of 2655.

## The bug, in one paragraph

`tests/test_townlet/integration/test_item_vfs_observations.py::test_item_vfs_masking_with_different_profiles` **passes in isolation** (0.28 s) and **fails in the full suite**. Its first assertion is a deliberate test-isolation check:

```python
assert torch.all(
    env.vfs_registry.item_vfs == 0.0
), f"VFS registry not clean at test start! Non-zero values found: {env.vfs_registry.item_vfs[env.vfs_registry.item_vfs != 0.0]}"
```

A prior test in the suite leaves non-zero values in the `item_vfs` tensor of a `VFSRegistry`, and this test correctly detects it. The test is honest; the *production code* (or a prior test's teardown) is the bug.

## Hypotheses (ranked)

1. **Most likely — `item_vfs` is module/class-level state on `VFSRegistry`.** Construction of a new `VectorizedHamletEnv` does not give a fresh tensor; it reuses a shared one. Check `src/townlet/vfs/registry.py` for class-level tensor allocation, `@classmethod`-style caches, or module-level singletons.
2. **Possible — `CompiledUniverse`'s VFS profiles share the tensor.** If `compiled_vfs_profiles` carries `item_vfs` storage, two envs built from the same compiled universe see each other's writes. Check `src/townlet/vfs/profiles.py` and `src/townlet/universe/compiler.py` around `_compile_vfs_profiles` / `_stage_5_prepare_shared_artifacts`.
3. **Possible — the compiler cache.** If `use_cache=True` rehydrates a `CompiledUniverse` from disk and the registry tensor is stored on it (not freshly built per env), every test sharing that cache picks up the bytes of the last writer. Look at `CompiledUniverse.load_from_cache` and the compiler at `src/townlet/universe/compiler.py:412`.
4. **Less likely — a singleton GPU allocator.** Pre-allocated tensor pools that survive teardown.

## What we already know (don't re-do)

- ✅ `torch>=2.9,<2.12` is **required** — torch 2.12 + triton 3.7 segfaults inside pytest on Adam construction. Don't waste time bisecting against torch 2.12. If your `uv sync` pulls 2.12, the `pyproject.toml` pin is wrong; check first.
- ✅ Full-suite reproducer: `uv run pytest --no-cov -p no:faulthandler` → 1 failed, 2629 passed.
- ✅ Isolation reproducer: `uv run pytest tests/test_townlet/integration/test_item_vfs_observations.py::test_item_vfs_masking_with_different_profiles --no-cov` → 1 passed.
- ✅ The golden-path smoke (`tests/test_townlet/integration/test_golden_path_smoke.py`) passes on the rescue config — Hamlet's runtime is healthy in isolation.
- ✅ The recent VFS work landed in `c321103e` (TASK-004C: reward_strategy migration, VFS integration). Earlier VFS commits: `8dee690b` (VFS direct storage), and prior. `git log -- src/townlet/vfs/ | head -20` for the timeline.

## Required: find the offending predecessor BEFORE proposing a fix

The plan's failure mode would be: "patch the symptom in `test_item_vfs_observations.py` by resetting state before the assert" — **don't**. The test is correctly reporting a real leak. Fix the source.

**Bisect strategy:**

```bash
# Get the list of tests that ran before the failing one in suite order:
uv run pytest --collect-only -q --no-cov -p no:faulthandler 2>/dev/null \
  | grep -B 999 "test_item_vfs_masking_with_different_profiles" > /tmp/before.txt

# Binary-bisect: run halves until you isolate the offender.
# Easier: drop the failing test into its own session with one predecessor file at a time:
uv run pytest tests/test_townlet/integration/test_<candidate>.py \
              tests/test_townlet/integration/test_item_vfs_observations.py::test_item_vfs_masking_with_different_profiles \
              --no-cov -p no:faulthandler
```

Start with the obvious suspects (other tests in `test_item_vfs_observations.py`, `test_item_vfs_integration.py`, `test_item_observations.py`, `test_effects_compilation_pipeline.py`). Each one of those constructs a VFS-bearing env and may leak.

Once you find the smallest pair `(test_X, test_item_vfs_masking)` that fails, you have the writer. Now read what `test_X` did to the registry that didn't get torn down.

## Fix shape (only after the writer is identified)

The right fix depends on which hypothesis wins:

- **If it's class-level state (H1):** move `item_vfs` to instance state on `VFSRegistry`, and ensure `VectorizedHamletEnv.__init__` constructs a fresh registry rather than borrowing one.
- **If it's shared-via-compiled-universe (H2):** keep the *spec* shared (cheap to hash), but allocate the runtime tensor per env in `VFSRegistry`'s constructor.
- **If it's the cache (H3):** ensure `CompiledUniverse.load_from_cache` does not deserialize live runtime state into a shared object. The cache should only hold static, deterministic configuration — never per-env tensors.

**In all cases, add a regression test** that constructs two `VectorizedHamletEnv` instances from the same universe, writes to one's `item_vfs`, and asserts the other's is still zero. Place it next to the failing test.

## Constraints — read before you touch anything

- **Pre-release, zero users, zero downloads.** No backwards compat. Delete obsolete paths; do not "support both old and new."
- **Work only in `src/townlet/`.** `src/hamlet/` is obsolete legacy code.
- **No defaults** — all behavioural parameters must be explicit. If you add a field, add it to the relevant DTO Config class.
- **CLAUDE.md is authoritative** on project rules. Re-read its "ANTIPATTERNS" section before adding any `try/except` or `hasattr` checks.
- **Filigree mandatory** — claim `hamlet-c1260e52ab` with `mcp__filigree__claim_issue` before starting, and close it when done with a comment summarising root cause.

## Acceptance criteria

1. `uv run pytest --no-cov -p no:faulthandler` → 0 failed.
2. A new regression test exists that would catch this leak even if pytest's test ordering changes.
3. `uv run mypy src/townlet --show-error-codes` → still clean (currently 0 errors in 136 files).
4. `uv run ruff check .` and `uv run black --check src tests` → still clean.
5. Filigree issue `hamlet-c1260e52ab` closed with a comment naming the offending test, the root cause class, and the line of code that fixed it.

## Verification commands (run all before declaring done)

```bash
uv run pytest --no-cov -p no:faulthandler                          # must show 0 failed
uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py  # must still pass
uv run mypy src/townlet --show-error-codes
uv run ruff check .
uv run black --check src tests
python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
```

## Anti-goals (do NOT do these)

- Don't patch the assertion in `test_item_vfs_masking_with_different_profiles` to make the symptom go away.
- Don't add a `setUp`/fixture that resets the registry just for this one test — fix the source so *every* test starts clean by construction.
- Don't disable the test, mark it `@pytest.mark.skip`, or change its ordering.
- Don't refactor VFS broadly while you're here. One bug, one fix, one commit. The rescue session is over; this is targeted repair.

## Useful pointers

- Implementation: `src/townlet/vfs/registry.py`, `src/townlet/vfs/profiles.py`, `src/townlet/universe/compiler.py`.
- Failing test: `tests/test_townlet/integration/test_item_vfs_observations.py:test_item_vfs_masking_with_different_profiles`.
- Companion tests likely involved: `tests/test_townlet/integration/test_item_vfs_integration.py`, `test_item_observations.py`, `test_effects_compilation_pipeline.py`.
- Rescue context: `docs/plans/2026-05-14-hamlet-rescue-recovery-plan.md`, recent commits `06a1c8c8` through `4798b803`.

## First commit shape

Either:
- `fix(vfs): allocate item_vfs per env to stop cross-test leakage`, **or**
- `test(vfs): add cross-env isolation regression test` (if you found the writer but want to land the regression test before the fix).

Do not combine the bisect work, the fix, and a broader VFS refactor in one commit.
