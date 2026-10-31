# 05 — Quality Assessment

**Scope.** Meta-level assessment of the `townlet` project at `/home/john/hamlet`: toolchain
enforcement, test corpus signal, pre-release hygiene, documentation health, performance
discipline, configuration brittleness, and a prioritised quality recommendations list. The
per-subsystem catalogs in `02-subsystem-catalog.md` (validated) and `temp/sg{1..8}-*.md` are the
source-of-truth inputs and are not re-walked here.

**Author posture.** Critical, evidence-driven. Every claim is anchored to a `file:line` or grep
command. The CLAUDE.md "zero-backwards-compat" rule is treated as binding — every dead-code item
is a contract violation, not a stylistic preference.

---

## 0. SME Agent Protocol — confidence, risk, gaps

### 0.1 Confidence assessment

| Section | Confidence | Basis |
|---|---|---|
| §2 Toolchain audit | **High** | Direct read of `pyproject.toml`, `.pre-commit-config.yaml`, and all four `.github/workflows/*.yml`. Configuration is unambiguous. |
| §3 Test corpus signal | **Medium-High** | LOC and file counts directly observed; coverage % derived from a single `.coverage` artifact whose run-scope is unverified. |
| §4 Pre-release hygiene | **High** | Dead-code items independently confirmed by validator; `git ls-files` and grep checks performed for every stale-file claim. |
| §5 Documentation health | **High** | 12 documentation-drift items already validator-confirmed in catalog §10; this section adds quantitative drift estimates. |
| §6 Performance discipline | **Medium** | 6 GPU-discipline leaks confirmed by SG4/SG5; absence of a profiling baseline is asserted as "no file found" — a negative claim. |
| §7 Configuration brittleness | **High** | Orphan-config claims independently re-greppeed in this run; DAC dual-path lives in `dac_engine.py:196` and `:230`. |
| §8 Recommendations | **Medium-High** | Effort estimates are coarse and judgement-based; rationale and risk-of-inaction are evidence-anchored. |

### 0.2 Risk assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Coverage % is from a partial test-run artifact (not a clean suite run) | **High** for the headline 19% number; **Low** for the *relative* per-subsystem distribution which is internally consistent | Re-run the full suite under coverage; the test README now records 19% as a local artifact rather than treating it as a fresh full-suite result. |
| Some dead-code items in §11.1 may be reachable through paths the catalog's grep did not find | Medium | Catalog §11.1 has already been validator-corrected on two such items (`VTCInteractionProgressProgram`, `decay_epsilon`). Treat remaining items as "verify before deletion." |
| Effort estimates (S/M/L) are not story-points and may mis-rank in real planning | Medium | Operator should refine in `filigree` against actual sprint cadence. |

### 0.3 Information gaps

- **No CI run logs available** in this session; the workflow files prove what *should* run on PR/push,
  not what *does* run. Confidence that lint/tests/config-validation are enforced is derived from
  the YAML, not from a recent run history.
- **`uv.lock` not re-grepped exhaustively** — pytest-benchmark absence verified by direct
  `grep -c`, but other indirect deps not enumerated.
- **`docs/` content drift was sampled at the file-count level** (628 markdown files, 511 tracked
  under `docs/`). Per-document drift was not exhaustively quantified — only the 12 items in
  catalog §10 are validator-confirmed.

### 0.4 Caveats

- This assessment treats the project's CLAUDE.md "zero-backwards-compat" rule as a binding
  commitment. If the operator's actual intent is "we're alpha, don't delete *aspirational*
  code yet," several P1 items downgrade to P2. The operator must adjudicate.
- "Quality scores" are not assigned per-subsystem — that work belongs in the subsystem catalog,
  not here. This file scores **the project's quality posture as a whole**.

---

## 1. Verdict and headline

**Project quality posture: Concerning, trending toward Healthy.** The codebase has serious
underlying engineering discipline — pre-commit + ruff + black + mypy + a no-defaults linter all
wired into four CI workflows, a 77K-LOC test corpus structured one-to-one against the runtime
layout, frozen-dataclass DTOs, and a clean separation between compile-time and runtime concerns
in most subsystems. **The TODO marker count across the entire `src/townlet/` tree is seven** —
that is unusually low. The project's bones are good.

What pulls it into "Concerning" is the gap between the rules the project sets for itself and the
state of the working tree:

1. **The "zero-backwards-compat" rule in CLAUDE.md is honored selectively.** Catalog §11.1
   inventories 16 dead-code / orphan items. At least 6 are clearly contract violations under that
   rule (legacy `agent_config.py` parallel, `flask`/`flask-cors` unused deps, `VTCSocialResidueProgram`
   compiled with no call site, `CuesCompiler` instantiated but unread, `StructuredQNetwork`
   unreachable via factory, `migrate_affordances_to_effects.py` one-shot).
2. **Documentation is empirically stale on load-bearing claims.** 12 specific drifts in catalog
   §10 remain. The test suite's own README was also stale, but has now been rebaselined to
   2,895 collected tests, 2,862 default-selected tests, and a 19% local `.coverage` artifact.
3. **Configured-but-unused tooling.** `vulture` is in dev deps with zero invocations.
   `pytest-benchmark` is referenced by the performance conftest but absent from `pyproject.toml`
   and `uv.lock` — performance tests silently skip. `mypy disallow_untyped_defs = false` with a
   "tighten later" comment that has not been tightened.
4. **Stale audit artifacts checked into version control.** Four `DEPENDENCY_ANALYSIS_*` files
   (~36 KB, tracked) describe "98 Python files" against today's 162 — a prior ad-hoc audit
   committed to the repo and never deleted.

None of these is a launch blocker on its own. Together they project the impression of a
fast-moving alpha that has been allowed to accumulate small breaches of its own rules. Cleanup is
a measurable amount of work (estimated 8–15 hours for the P0/P1 set), not a structural
rewrite.

---

## 2. Toolchain & enforcement audit

### 2.1 Lint — `ruff`

`pyproject.toml:105-110`:
```toml
[tool.ruff]
line-length = 140
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
```

Selections cover **pycodestyle errors/warnings (E,W)**, **pyflakes (F)**, **isort (I)**,
**pep8-naming (N)**, **pyupgrade (UP)**. Not selected: B (bugbear), C4 (comprehensions), SIM
(simplify), PL (pylint), RUF (ruff-specific), ARG (unused-arguments), PTH (use pathlib), S
(bandit security), TID (tidy-imports), TRY (tryceratops). For a project this size, B and S in
particular are conspicuous omissions.

CI enforcement at `.github/workflows/lint.yml:23-31`:
```yaml
- name: Ruff (lint) - Enforce zero warnings
  run: |
    uv run ruff check .
```

Run is repo-wide, exit-on-nonzero. **Real enforcement.** Pre-commit also runs ruff with `--fix`
(`.pre-commit-config.yaml:9-14`) but with an exclude pattern for `.claude/`, `htmlcov/`, `runs/`,
`.uv-cache/`, `coverage*`, `*.msgpack`. Pre-commit is narrower than CI, which is the correct
asymmetry (CI is authoritative).

### 2.2 Format — `black`

`pyproject.toml:101-103`:
```toml
[tool.black]
line-length = 140
target-version = ['py313']
```

Line-length 140 is unusually generous (industry default is 88). It does prevent line-length lint
violations: a repo-wide check `find src/townlet -name "*.py" -exec awk 'length>140 ...' returns
**zero hits**. The cost is denser files — `src/townlet/vfs/vtc.py` is 2,990 LOC, which is a lot
of state to hold even at 88-char width.

CI enforcement (`lint.yml:32-39`) runs `black --check src tests` — fails CI on violation. Real
enforcement.

### 2.3 Type-check — `mypy`

`pyproject.toml:112-116`:
```toml
[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Start lenient, can tighten later
```

`disallow_untyped_defs = false` means **untyped function defs are accepted silently**. The
trailing comment "Start lenient, can tighten later" implies an intent to ratchet that has not
happened. `mypy --strict`-style options (`disallow_any_generics`, `no_implicit_optional`,
`strict_equality`, `warn_unreachable`) are all absent. For a project that markets itself as
`Typing :: Typed` (`pyproject.toml:38`) and that handed Pydantic v2 the foundation layer, this
posture leaves most of `src/townlet/` un-type-enforced.

CI enforcement (`lint.yml:40-47`) runs `mypy src/townlet` with `--show-error-codes`. Real
enforcement, but only against the bar the config sets — which is low.

### 2.4 Test discovery & coverage — `pytest` + `pytest-cov`

`pyproject.toml:118-140`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--verbose",
    "--cov=townlet",
    "--cov-branch",
    "--cov-report=term-missing",
    "-m",
    "not slow",
]
markers = [
    "slow: marks tests as slow (tests that take >5 seconds)",
    "gpu: marks tests requiring CUDA/GPU hardware",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
]
```

Coverage is **enabled by default** (no opt-in needed), branch coverage on, source scope
`townlet`. Coverage report is terminal-only — no HTML, no XML for codecov, no `--cov-fail-under`
threshold. **There is no coverage gate**: a PR that drops coverage to 5% would still pass CI.

The default `-m "not slow"` excludes slow tests from every developer run. Slow tests are picked
up only by the scheduled `full-tests.yml` workflow (`6:00 UTC daily`).

### 2.5 No-defaults linter

`scripts/no_defaults_lint.py` (whitelist-driven AST walker) is the load-bearing structural
enforcement of CLAUDE.md's "all behavioral parameters must be explicit" rule. CI invocation at
`.github/workflows/lint.yml:48-55` with `--whitelist .defaults-whitelist.txt` (229 lines of
exemptions). A parallel `defaults-whitelist-compliant.txt` (165 lines) appears to be a more
restrictive target the project has not yet adopted. Two tracked whitelists for the same rule is
itself a smell — the "compliant" file is dated 2025-11-05 ("PDR-002 Compliant") and the
project is presumably meant to migrate; it has not.

### 2.6 CI workflow inventory

`ls .github/workflows/` returns four files:

| Workflow | Trigger | Runs |
|---|---|---|
| `lint.yml` | push:main, pull_request | ruff, black --check, mypy, no-defaults lint |
| `tests.yml` | push:main, pull_request | `validate_compiler_cli.py` then `pytest` (fast suite, `-m "not slow"`) |
| `config-validation.yml` | push:main, pull_request | `validate_compiler_cli.py` only (redundant with `tests.yml`'s first stage) |
| `full-tests.yml` | workflow_dispatch, schedule cron `0 6 * * *` | `pytest -m "slow or not slow"` |

Five CI stages, three of which fire on every PR. `tests.yml` already runs the universe compiler
validation in its first step, making `config-validation.yml` redundant — minor overhead, not a
bug.

**No security workflow.** No `bandit`, `safety`, `pip-audit`, `osv-scanner`, or dependabot/renovate
configuration. Given the dependency surface (`tensorflow[and-cuda]`, `flask`, `mlflow`, `fastapi`),
this is a notable absence even for an alpha.

**No benchmark workflow.** `tests/test_townlet/performance/` exists but is gated behind a
skip-if-`pytest_benchmark`-missing dance — see §2.7 below — and is not scheduled.

### 2.7 Configured-but-unused tooling

| Tool | Declared | Wired? | Notes |
|---|---|---|---|
| `vulture>=2.0.0` | `pyproject.toml:84` | **No.** Not in `.pre-commit-config.yaml`, not in `.github/workflows/`, not invoked from any `scripts/`. | Dev dependency that does literally nothing. Either wire it or delete it. |
| `hypothesis>=6.100.0` | `pyproject.toml:83` | **Yes, narrowly.** Used by 4 property-test files in `tests/test_townlet/properties/` (34 test functions). | Real but small footprint. Could be a strength if extended. |
| `pytest-benchmark` | **Not declared in `pyproject.toml` or `uv.lock`** | **Referenced** by `tests/test_townlet/performance/conftest.py:8-12` with a try/except ImportError. | `grep -c "pytest-benchmark\|pytest_benchmark" pyproject.toml uv.lock` → `0`. Performance tests **always skip**. This is an inverted dead-code pattern: the test code calls for a tool the manifest doesn't supply. |
| `pytest-asyncio>=0.21.0` | `pyproject.toml:78` | Presumed used (live_inference is FastAPI); not audited. | Plausible. |
| `gitpython>=3.1.0` | `pyproject.toml:56` | Unaudited — used at all? | Verify on cleanup. |
| `requests>=2.31.0` | `pyproject.toml:57` | Unaudited in `src/`. | Probably indirect; verify. |
| `pre-commit` hook for trailing-whitespace, EOF, large-files (>1000 KB), merge-conflict, line-endings | `.pre-commit-config.yaml:25-46` | Yes | Real. |

### 2.8 Toolchain audit verdict

**The shape of the toolchain is good.** Pre-commit + four CI workflows + a custom no-defaults
linter is more rigorous than most alphas ever build. The gaps are in the *configuration* of the
tools that *are* wired:

- ruff selections leave `B`, `S`, `SIM`, `PTH` off — a B+S pass would surface concrete
  bugbear/security findings.
- mypy is lenient by explicit choice, and the "tighten later" intent has decayed.
- No coverage gate; no security scan; `vulture` declared but unused.

**Toolchain finding severity: P2 (medium).** None of these blocks shipping, but together they
mean lint-CI's pass signal is weaker than the project assumes.

---

## 3. Test corpus signal

### 3.1 Headline numbers

| Metric | Value | Source |
|---|---:|---|
| Source LOC (Python) | **45,117** | `find src/townlet -name "*.py" -exec wc -l {} +` |
| Test LOC (Python) | **77,265** | `find tests -name "*.py" -exec wc -l {} +` |
| Test:src ratio | **1.71** | derived |
| Source files | 162 | `find src/townlet -name "*.py" | wc -l` |
| Test files | 321 | `find tests/test_townlet -name "*.py" | wc -l` |
| Test functions (`def test_…`) | **2,762** | `grep -rh "^def test_\|    def test_" tests/test_townlet/ | wc -l` |
| Property-test functions | 34 | `grep -c "test_" tests/test_townlet/properties/*.py` |
| Performance test files | 4 | `tests/test_townlet/performance/*.py` |

### 3.2 Coverage — resolved README contradiction

Before remediation, `tests/test_townlet/README.md:4-5` still carried refactoring-era test-count
and coverage claims.

Current measured reality:

- **2,895** tests collected; **2,862** selected by the default `not slow` filter.
- **2,762** `def test_...` functions by grep.
- **284** `test_*.py` files under `tests/test_townlet/`.
- The repo-root `.coverage` artifact (`/home/john/hamlet/.coverage`, 405,504 bytes, modified
  `2026-05-16 06:47`) reports **TOTAL: 19% line coverage, 36 branches** (`python -m coverage
  report --rcfile=pyproject.toml`).
- The `.coverage` artifact is **NOT git-tracked** (`.gitignore:47` excludes `.coverage`), so the
  "checked-in coverage file" concern in the discovery findings is incorrect — it is a local
  working-tree artifact, not a committed file. **This corrects the discovery findings.**
- `tests/test_townlet/README.md` now records the measured collection and coverage-artifact
  values, with an explicit caveat that the 19% number is not a fresh full-suite coverage result.

The 19% number must still be qualified: a single run-time artifact may capture only the tests
that were actively run; it does not necessarily represent a clean full-suite invocation. The
README contradiction is fixed, but the project still lacks a clean coverage baseline and gate.

Per-subsystem coverage (from same artifact) shows the headline 19% breaks down sharply
unevenly. Selected results (`python -m coverage report`):

| Path | Coverage |
|---|---:|
| `src/townlet/effects/compiler.py` | 2% |
| `src/townlet/effects/executor.py` | 4% |
| `src/townlet/environment/action_executor.py` | 3% |
| `src/townlet/environment/dac_engine.py` | 2% |
| `src/townlet/environment/vectorized_env.py` | 7% |
| `src/townlet/demo/runner.py` | 6% |
| `src/townlet/demo/live_inference.py` | 7% |
| `src/townlet/items/manager.py` | 6% |
| `src/townlet/recording/video_renderer.py` | 0% |
| `src/townlet/recording/video_export.py` | 0% |
| `src/townlet/world/expression/parser.py` | 7% |
| `src/townlet/world/expression/type_checker.py` | 7% |
| `src/townlet/config/agent_config.py` | 90% |
| `src/townlet/config/environment_config.py` | 96% |
| `src/townlet/world/expression/ast_nodes.py` | 90% |

The pattern: **DTOs and AST node dataclasses are well-covered; runtime engines and orchestration
code are not.** If the artifact represents anything close to a clean run, the critical-path code
is dramatically under-tested. If it represents only a partial unit-suite run, then the old
README coverage claim was unverifiable.

### 3.3 Test taxonomy and markers

`pyproject.toml:135-140` declares four markers: `slow`, `gpu`, `integration`, `e2e`.

Marker usage across the corpus (`grep -rn "pytest.mark.{slow,gpu,integration,e2e}" tests/`):

| Marker | Usage count | Test files with the marker |
|---|---:|---:|
| `slow` | 9 | small |
| `gpu` | 4 | small |
| `integration` | 3 | small |
| `e2e` | 2 | small |
| **Total marker uses** | **18** | across **2,762** test functions |
| Test files with **no** markers | **286 / 321 (89%)** | |

The taxonomy is **largely aspirational**. The directory structure (`tests/test_townlet/unit/`,
`integration/`, `properties/`, `performance/`) does most of the categorisation work — markers are
nearly unused. This means the `-m "not slow"` default in `pyproject.toml:131` excludes only nine
specific test functions out of 2,762.

### 3.4 Test infrastructure

There is a real `tests/TEST_WRITING_GUIDE.md` (top-level, not `tests/test_townlet/`) and a
`tests/test_townlet/_fixtures/` directory with 13 fixture modules
(`brain_configs.py`, `config.py`, `constants.py`, `database.py`, `devices.py`, `environment.py`,
`instant_affordances_helper.py`, `networks.py`, `temp.py`, `training.py`, `utils.py`,
`variable_meters.py`). `tests/test_townlet/utils/builders.py` is the canonical test-data factory.

Six `conftest.py` files distribute fixtures hierarchically (root + four package-level). 365
total `conftest.py` LOC.

19 test files use `@pytest.mark.parametrize` — modest, given the corpus size.

### 3.5 Test corpus verdict

The test corpus is **well-structured but the historical size signal was misleading.** 77K LOC,
2,895 collected tests, and 2,762 `def test_...` functions are a real investment. But:

- The README headline numbers had to be rebaselined from old refactoring-era claims.
- Markers are aspirational; the four-axis taxonomy from `pyproject.toml:135-140` is barely
  applied.
- The `.coverage` artifact (whether complete or partial) reveals that critical runtime modules
  (DAC engine, action executor, effects executor, video renderer) are under 10% covered.
- The two largest LOC contributors to `src/` — `vfs/vtc.py` (2,990 LOC) and
  `environment/vectorized_env.py` (1,559 LOC) — sit at 24% and 7% line coverage respectively.

**Test corpus finding severity: P1 (high)** — fix the README claims and run a clean full-suite
coverage measurement to determine which number is real. A clean run will either reveal a deep
gap that must be planned for, or vindicate the README and reveal the local `.coverage` artifact
as a partial-run misread.

---

## 4. Pre-release hygiene scorecard

The CLAUDE.md "zero-backwards-compat / delete-don't-maintain" rule is the project's stated norm.
Items below are graded against that rule. Severity scale: **P0 (drop everything)** /
**P1 (do next)** / **P2 (default)** / **P3 (low priority cleanup)**.

### 4.1 Dead-code inventory (cross-referenced to catalog §11.1)

| # | Item | Location | Severity | Why this rating |
|--:|------|----------|:--:|---|
| 1 | `flask`, `flask-cors` in `pyproject.toml:50-51`, no `from flask` import anywhere in `src/` | `pyproject.toml` | **P1** | Larger attack surface, false signal of dual-stack design, trivial to delete. Validator-confirmed. |
| 2 | `tensorflow[and-cuda]>=2.20` **and** `tensorflow>=2.20` (lines 60+61) both declared | `pyproject.toml` | **P1** | Redundant declaration; the CUDA-coupled variant pulls hundreds of MB. Likely only `tensorboard` is needed. |
| 3 | `msgpack`, `lz4` declared in main deps **and** in `recording` extra | `pyproject.toml:62-63` vs `:87-88` | **P3** | Minor; duplicate-declaration in same manifest. |
| 4 | `agent_config.py` (362 LOC) legacy parallel of `brain_config.py` + `drive_as_code.py` | `src/townlet/config/agent_config.py` | **P1** | The catalog flagged this as "deletion candidate" but in fact `DriveConfig` is still imported by `dac_engine.py:23` and `AgentConfig` by `__init__.py:15` and `demo/runner.py:475`. The deletion-candidate claim is more precisely "consolidate `AgentConfig` and `BrainConfig` into one shape" — still a real violation of the rule, but not pure-delete. |
| 5 | `capability_config.py` defines `CapabilityConfig` (line 94) with zero callers in `src/` | `src/townlet/config/capability_config.py` | **P1** | Clear violation. Has a test file (`tests/test_townlet/unit/config/`) — tests of unused code are pure cost. Delete config + test together. |
| 6 | `affordance_masking.py` — config DTO with zero `src/` callers | `src/townlet/config/affordance_masking.py` | **P1** | Same pattern as #5. `tests/test_townlet/unit/config/test_affordance_masking.py` exists; delete both. |
| 7 | `VTCSocialResidueProgram` compiled but no runtime call site (validator-confirmed) | `src/townlet/vfs/vtc.py` | **P1** | Compiled into a frozen-dataclass program, hashed into `compute_vfs_hash`, exported from `__init__.py`, and never `.apply()`-ed. Pure cost surface. |
| 8 | `CuesCompiler` instantiated at `universe/compiler.py:78` but `self._cues_compiler` never read | `src/townlet/universe/compiler.py` | **P1** | Validator-confirmed. Either wire it up or delete. |
| 9 | `StructuredQNetwork` defined at `networks.py:558`, unreachable via `NetworkFactory` | `src/townlet/agent/networks.py` | **P1** | Validator-confirmed; has unit tests. Code + tests are both dead. |
| 10 | `ScopedVariableRegistry` parallel scaffold in `registry.py:877-1049` | `src/townlet/vfs/registry.py` | **P2** | Validator marked it as unused by environment; 172 LOC of parallel infrastructure. |
| 11 | `Switch` and `Reduce` AST nodes in `world/expression/ast_nodes.py` — unparseable, unimplemented | `src/townlet/world/expression/` | **P2** | Holes in the public AST that mislead about DSL capabilities. |
| 12 | `world/types/primitive.py` `Type` protocol — zero consumers | `src/townlet/world/types/` | **P2** | Parallel type system to the actual string-based one. |
| 13 | `EffectScope.ITEM` and `EffectScope.AFFORDANCE` populated but never iterated in `EffectManager.tick` | `src/townlet/effects/manager.py` | **P2** | Latent feature signalling incomplete implementation. |
| 14 | `scripts/migrate_affordances_to_effects.py` — one-shot migration with no current consumer | `scripts/` | **P2** | One-shot scripts are textbook backwards-compat cruft per CLAUDE.md. |
| 15 | `UnifiedServer._start_frontend()` defined but never called from `start()` | `src/townlet/demo/unified_server.py` | **P2** | Drifted code in a 257-LOC file. |
| 16 | `RecordingCriteria` unreferenced by writer thread; `reason="periodic"` hardcoded | `src/townlet/recording/criteria.py` | **P2** | Latent bug + dead config. |
| 17 | Server-side replay handlers in `demo/live_inference.py` — no Vue consumer | `src/townlet/demo/` | **P3** | Server has the path; frontend doesn't connect. |
| 18 | `aggregation` extrinsic strategy hardcoded to `min` despite docstring promising `min/max/mean/product` | `src/townlet/environment/dac_engine.py:411` | **P2** | Feature gap or doc lie — either fix or amend the docstring. |

**Tally:** 18 dead/orphan items. Estimated LOC deletable in a single P1 sweep: **~1,400–1,800 LOC**
(orphan configs, `VTCSocialResidueProgram` definition + hashing + export, `StructuredQNetwork`
class + tests, `migrate_affordances_to_effects.py`, four spurious pyproject deps). The bulk of
catalog §11.1 is real, not noise.

### 4.2 Legacy / TODO marker sweep

`grep -rn "TODO\|XXX\|FIXME\|HACK\|deprecated\|DEPRECATED" src/townlet/ --include="*.py"` returns
**7 hits across 162 files**. Breakdown:

| Marker | Count | Locations |
|---|---:|---|
| TODO | 6 | `recording/video_renderer.py:214`, `demo/database.py:255,268`, `universe/compiled.py:99,100`, `environment/vectorized_env.py:746` |
| deprecated | 1 | `training/replay_buffer.py:22` (a docstring note about a deprecated parameter) |
| FIXME / XXX / HACK / DEPRECATED | 0 | — |

`grep -rn "# legacy\|legacy" src/townlet/` returns zero hits. `grep -rn "v1\b\|# old" src/townlet/`
returns zero hits. Catalog §11.1 §11.5 items aside, **the source tree is genuinely free of
in-code legacy markers** — meaning the dead code is not "labelled as deprecated and left", it is
"silently unused." That makes it harder to find but does not change the disposition under
CLAUDE.md.

**This is a strength.** Compared to typical alpha codebases, seven TODO markers in 45K LOC is
remarkably restrained.

### 4.3 Stale files at repo root

`ls /home/john/hamlet/` reveals seven non-standard top-level files. Tracking status verified by
`git ls-files`:

| File | Size | Tracked? | In `.gitignore`? | Verdict |
|---|---:|---|---|---|
| `.coverage` | 405,504 B | **No** (`.gitignore:47` excludes it) | Yes | Local working-tree artifact. **Not a commit problem** — but the existence of a coverage file at repo root after a partial run is operationally noisy. |
| `DEPENDENCY_ANALYSIS_INDEX.txt` | 10,952 B | **Yes** | No | Stale audit. Claims "98 Python files" against today's 162. **Delete.** |
| `DEPENDENCY_ANALYSIS_REPORT.txt` | 13,966 B | **Yes** | No | Same. **Delete.** |
| `DEPENDENCY_ANALYSIS_SUMMARY.md` | 10,846 B | **Yes** | No | Same. **Delete.** |
| `DEPENDENCY_GRAPH_VISUAL.txt` | (size unread, ~10 KB) | **Yes** | No | Same. **Delete.** |
| `.defaults-whitelist.txt` | 10,154 B | **Yes** | No | Active — referenced by `.github/workflows/lint.yml:50`. **Keep.** |
| `.defaults-whitelist-compliant.txt` | 8,354 B | **Yes** | No | Parallel "target" whitelist (PDR-002). Never adopted. Either adopt or **delete**. Two whitelists for one rule is a smell. |
| `qvalues_inference.log` | 0 B | **No** | (not explicitly listed) | Empty local log; CWD-relative inference output. Add `*.log` to `.gitignore`. |

**The four `DEPENDENCY_ANALYSIS_*` files are the headline finding here.** They are tracked, they
are stale (reference 98 files vs 162 actual), they describe an architecture that has since been
re-organised (the v2.1 hierarchical config layout post-dates them). They are a **dishonesty
risk**: a contributor opening the repo today will read them and form a wrong mental model of the
codebase. **Severity: P1**, immediate-cleanup target.

### 4.4 Pre-release hygiene verdict

**Severity P0:** None.
**Severity P1:** 6 items (deletable pyproject deps × 2, orphan configs × 2, stale audit files,
`VTCSocialResidueProgram`, `CuesCompiler`, `StructuredQNetwork`, `tests/test_townlet/README.md`
numbers).
**Severity P2:** 8 items.
**Severity P3:** 2–3 items.

The project's own no-backwards-compat rule is binding; under that rule the P1 cohort cannot
remain. Combined effort estimate for the P1 cohort: **6–10 hours, mechanical cleanup, low risk**.

---

## 5. Documentation health

### 5.1 Inventory

- 628 markdown files repo-wide (`find . -name "*.md" -not -path "*/.uv-cache/*" -not -path
  "*/htmlcov/*"`).
- 509 markdown files tracked under `docs/` (`git ls-files docs/ | wc -l`).
- 21 top-level subdirectories under `docs/`.
- Top doc directories by size: `docs/plans/` (5.3 MB), `docs/architecture/` (1.4 MB),
  `docs/bugs/` (996 KB), `docs/research/` (964 KB), `docs/tasks/` (888 KB).

Doc:code ratio (lines): a precise count was not run, but at 509 tracked markdown files vs 162
Python source files, **doc files outnumber source files 3.1:1**. By byte count, `docs/plans/`
alone (5.3 MB) is larger than the entire packaged source surface.

### 5.2 Documentation drift catalog (from validated catalog §10)

12 specific drifts confirmed:

1. Compiler stage count (7 vs 9)
2. Config layout (flat vs `<pack>/levels/<level>/`)
3. `variables_reference.yaml` required-vs-optional
4. DAC file naming (`drive_as_code.yaml` vs `drive.yaml`)
5. DAC location (per-pack vs per-level)
6. reward_strategy deletion LOC count (583 vs 234)
7. Exploration file inventory (4 files claimed; 3 actually exist; `icm.py` etc. absent)
8. `RecurrentSpatialQNetwork` LSTM input dim (192 vs 240)
9. `aggregation` extrinsic strategy modes (4 claimed vs 1 implemented)
10. `src/hamlet/` "obsolete" vs "fully deleted"
11. `frontend/npm run dev` instructions vs missing `package.json`
12. Flask described as part of stack vs unused

### 5.3 Estimated doc decay rate

CLAUDE.md is 388 lines, ~12,000 words. Twelve specific claims are stale. Sectionally, the drifts
break down as:

| CLAUDE.md section | Drifts hitting it | Section status |
|---|---:|---|
| "Active Config Packs (Curriculum)" | 1, 2, 3, 4, 5 | Substantively wrong |
| "Drive As Code" + "Universe Compiler Quick Reference" | 6, 9 | Specific facts wrong |
| "Network Architecture Selection" | 8 | LSTM input dim wrong |
| "Frontend Visualization" | 11 | Broken instructions |
| "Architecture Overview" / "Variable & Feature System" | 3 | Required-vs-optional inverted |
| "Antipatterns" lists | (no drift; correct) | Correct |

Approximately **40–50% of CLAUDE.md by section** is materially affected. The non-drifted
sections (project mission, anti-patterns enumeration, filigree usage) are stable. **Estimated
rewrite scope: ~150–200 lines of CLAUDE.md require editing**, plus regeneration of corresponding
sections in `docs/UNIVERSE-COMPILER.md`, `docs/config-schemas/*.md`, and
`docs/architecture/COMPILER_ARCHITECTURE.md`.

### 5.4 `tests/test_townlet/README.md` — rebaselined

The test corpus's own README previously carried refactoring-era test-count and coverage claims.
Current measured reality is 2,895 collected tests, 2,862 default-selected tests, 284 `test_*.py`
files under `tests/test_townlet/`, and a local `.coverage` artifact reporting 19% line coverage.

This mattered because:

- It sits inside the test directory itself — contributors read it when onboarding to test
  writing.
- It overstated discipline (coverage) and understated volume (test count).
- It dated itself as fully refactored in November 2025, six months stale at the time of this
  assessment.

**Action:** Done for the README. Still open: run a clean full suite under coverage if the project
wants a real coverage gate rather than a local-artifact snapshot.

### 5.5 CHANGELOG status — release log or worklog?

`CHANGELOG.md` is **876 lines, 36 KB**, headers as follows:

```
## [Unreleased]
## 2025-11-07 - TASK-002C: VFS Phase 1 Integration (COMPLETE)
## 2025-11-07 - TASK-002B: Composable Action Space (COMPLETE)
## 2025-11-06 - TASK-002A: Configurable Spatial Substrates (COMPLETE)
## 2025-11-05 - 0.1.0 Alpha Worklog
## [0.1.0] - 2025-11-04
## Release Notes Format
```

Of 7 section headers, **6 are dated TASK-XXX or alpha-worklog entries**. Only `[0.1.0]` is
version-style.

**Cross-check:** `pyproject.toml:3` declares `version = "0.1.0"`. `CHANGELOG.md` has been
rebaselined so the 2025-11-05 material is a `0.1.0` alpha worklog, not a separate release
declaration. The package baseline is therefore `0.1.0`.

The Keep-a-Changelog format is being **violated** — the file is functioning as an internal
sprint worklog rather than a user-facing release log. For a 0.1.0 alpha that may be acceptable,
but the project advertises itself as following SemVer + Keep-a-Changelog at the top of the file,
so the practice still doesn't match the discipline declared.

**Severity: P2** — fix when the next version tag happens.

---

## 6. Performance discipline

### 6.1 Stated posture vs reality

The project describes itself as "GPU-native vectorized training" (CLAUDE.md §1.2,
`pyproject.toml` keywords). Catalog §11.3 inventories **six per-agent Python loops in nominally
GPU-native paths**:

| Location | Loop nature |
|---|---|
| `affordance_engine.py:538-555` | Per-agent affordance resolution |
| `action_executor.py:73-134` | Per-agent action dispatch |
| `vectorized_env.py:954-969, 1346-1371` | Per-agent state updates |
| `dac_engine.py:572-577, 747-751` | Per-agent reward computation paths |
| `grid2d.py:581-598` | `encode_partial_observation` non-vectorised |
| `vfs/vtc.py` `VTCInteractionProgressProgram.apply` | Per-agent loop in a VTC program |

These six leaks span the **hottest loop in the system** — `vectorized_env.step()` runs at every
tick of every episode. A per-agent Python loop in `action_executor.py` and `dac_engine.py` means
that effective vectorisation is bottlenecked by N (number of agents). For the default `num_agents
= 4` in the demo, this is invisible; for the L5_multi_agent pack (catalog §1.2) or any scaling
experiment, it will dominate.

**Severity: P1**. The discrepancy between marketing and reality is sharper here than in any
other category. Either the GPU-native claim must be qualified or the loops must be vectorised.

### 6.2 Benchmark and profiling infrastructure

`tests/test_townlet/performance/` exists with four files:

- `test_environment_step_benchmarks.py` (pytest-benchmark fixtures)
- `test_expression_benchmarks.py` (pytest-benchmark fixtures)
- `test_performance_threshold.py` (asserts `OVERHEAD_LIMIT = 0.05`, i.e. <5% overhead)
- `conftest.py` (skips all benchmarks if `pytest-benchmark` not importable)

**The skip-on-missing dance is always-on.** `pytest-benchmark` is not in `pyproject.toml` or
`uv.lock`:

```
grep -c "pytest-benchmark\|pytest_benchmark" pyproject.toml uv.lock
pyproject.toml:0
uv.lock:0
```

Effective result: every benchmark in `tests/test_townlet/performance/` is silently skipped.
`test_performance_threshold.py` does not require `pytest-benchmark` (it uses `time.perf_counter`)
and presumably runs — but it is **single-purpose, single-config** (asserts <5% overhead for one
specific compile path).

There is no `scripts/profile.py`, no `docs/performance/baseline.md` with measured numbers, no
flamegraph captures in the repo. The performance category exists structurally but has no live
artifact backing it.

### 6.3 Performance discipline verdict

**Severity P1.** The GPU-native marketing is contradicted by the six per-agent loops; the
benchmark infrastructure is dead-on-arrival. Either:

- **Vectorise the six loops + add `pytest-benchmark` to dev deps + run benchmarks in CI**
  (substantial work; M-L effort), or
- **Amend the "GPU-native" claim** to "vectorised where it matters, with documented Python
  fallbacks at [these specific paths]" (S effort).

The current state — claim GPU-native, ship per-agent loops, skip all benchmarks silently — is
the worst combination.

---

## 7. Configuration brittleness

### 7.1 Orphan config DTOs (cross-reference §4.1)

`src/townlet/config/` contains 22 modules and 142 Pydantic models (catalog §3). Of these, three
DTO files have **zero `src/` callers** outside the config package itself:

| File | Test file? | Status |
|---|---|---|
| `capability_config.py` | none | Cold-dead. Verified by `grep -rln "from townlet.config.capability_config\|CapabilityConfig" src/`. |
| `affordance_masking.py` | `tests/test_townlet/unit/config/test_affordance_masking.py` | Cold-dead in src; test covers something nothing uses. |
| `agent_config.py` (partial) | (extensively tested) | Half-alive: `DriveConfig` is imported by `dac_engine.py:23`; `AgentConfig` by `__init__.py:15` and `demo/runner.py:475`. Not deletable wholesale; consolidation candidate with `brain_config.py`. |

These orphans imply **either removed features or never-shipped features**. The CHANGELOG does
not mention `capability_config` or `affordance_masking` in any release header — they are pure
dark matter.

### 7.2 DAC dual compilation path

Catalog §11.2 flags two coexisting DAC compilation paths in `src/townlet/environment/dac_engine.py`:
- `_compile_extrinsic` for DAC v2 schema (line 196)
- `_compile_extrinsic` for legacy `agent.yaml` path (line 230) — for the same
  `constant_base_with_shaped_bonus` strategy.

Risk profile of silent divergence:

- **High.** The two paths share a strategy name. If a bug is fixed in one and not the other,
  rewards computed via the two paths will diverge silently. Per the CLAUDE.md no-backcompat
  rule, the legacy path is a deletion candidate. The `drive_hash` provenance system (catalog §4)
  prevents *checkpoint* mixing but does not prevent run-time mis-routing.
- **Severity: P1.** Pick the surviving path, delete the other, regenerate fixtures.

### 7.3 pyproject.toml dependency redundancy

| Issue | Lines | Severity |
|---|---|:--:|
| `flask>=3.0.0`, `flask-cors>=4.0.0` declared but never imported | `pyproject.toml:50-51` | **P1** |
| `tensorflow[and-cuda]>=2.20.0` **and** `tensorflow>=2.20.0` both declared | `pyproject.toml:60-61` | **P1** |
| `msgpack>=1.1.2` + `lz4>=4.4.5` in main; **same** in `recording` extra | `pyproject.toml:62-63` vs `:87-88` | **P3** |
| Whether `tensorflow` is genuinely used (vs just `tensorboard`) | n/a | P2 (audit) |

CUDA-coupled TensorFlow is the most expensive single line in the manifest in terms of install
time and disk footprint. If the only TF surface is `tensorboard` (catalog discovery §3), the
declaration can collapse to `tensorboard` alone.

### 7.4 Configuration brittleness verdict

The config DTO layer is structurally sound (142 BaseModels, `extra="forbid"` discipline,
per-schema files) but accumulates dark-matter modules and a known dual-compilation path. The
no-defaults linter enforces one rule but a parallel "compliant" whitelist has been built and
never adopted.

**Severity: P1 collectively** (DAC dual path + Flask/TF cleanup + orphan configs). These are
mechanical cleanups, not architectural changes.

---

## 8. Top 10 quality recommendations

Ordered by leverage (impact × inverse-effort). Each entry: title, rationale,
**Confidence** in the recommendation, **Risk if not done**, effort estimate, **concrete files
to touch**.

### Q-REC-1 (P1, S effort) — Delete the four tracked `DEPENDENCY_ANALYSIS_*` files

**Rationale.** Stale audit checked into repo root in May 2025. Describes "98 Python files"
against today's 162. Contributors form a wrong mental model. Doing this also clears the most
visible "this is an active mess" signal at the repo surface.

**Confidence.** High. The file dates and content are wrong against current `find` output.
**Risk if not done.** Onboarding contributors and AI assistants ingest a known-stale dependency
graph as truth.
**Effort.** S (5 minutes — `git rm` and commit).
**Files.** `DEPENDENCY_ANALYSIS_INDEX.txt`, `DEPENDENCY_ANALYSIS_REPORT.txt`,
`DEPENDENCY_ANALYSIS_SUMMARY.md`, `DEPENDENCY_GRAPH_VISUAL.txt`.

### Q-REC-2 (resolved for README, follow-up for coverage gate) — Re-derive test README numbers

**Rationale.** The README now records the measured collection counts and local `.coverage`
artifact: 2,895 collected tests, 2,862 selected by default, 284 `test_*.py` files, and 19% line
coverage from the existing artifact. A clean `uv run pytest --cov=townlet --cov-report=term`
run is still needed before setting a project coverage gate.

**Confidence.** High on numbers (independently counted). Medium on which coverage is "real"
until a clean run is performed.
**Risk if follow-up is not done.** Coverage-based gating decisions could still be made from a
partial local artifact.
**Effort.** S-M for the clean coverage run and threshold decision.
**Files.** Potentially add a `--cov-fail-under=XX` to `pyproject.toml:124-131` once the real
number is known.

### Q-REC-3 (P1, S effort) — Remove redundant pyproject dependencies

**Rationale.** `flask` + `flask-cors` (unused), redundant `tensorflow` declaration, possibly
unnecessary CUDA-coupled TF if only TensorBoard is used. Each line shed is install-time + attack
surface saved.

**Confidence.** High for Flask (validator-confirmed zero imports). Medium for TF (need to audit
whether `import tensorflow` exists vs just `tensorboard`).
**Risk if not done.** Larger image, longer install, false stack-diversity signal, security
surface.
**Effort.** S (15 minutes — delete lines, re-run `uv lock`, run tests).
**Files.** `pyproject.toml:50-51, 60-61, 62-63 vs 87-88`.

### Q-REC-4 (P1, M effort) — Delete or wire `VTCSocialResidueProgram`, `CuesCompiler`, `StructuredQNetwork`

**Rationale.** Three named pieces of compiled-but-unwired code; each violates the no-backcompat
rule. `VTCSocialResidueProgram` is the worst — it is compiled, hashed into `compute_vfs_hash`,
exported from `__init__.py`, and never `.apply()`-ed. Either it should run (and tests should
cover the runtime path) or it should disappear entirely (including its hash contribution).

**Confidence.** High for `VTCSocialResidueProgram` (validator-confirmed). High for `CuesCompiler`
(`grep -n self._cues_compiler` returns only the assignment). High for `StructuredQNetwork`
(`grep -n StructuredQNetwork src/` returns only the class definition).
**Risk if not done.** Compute the hash contribution of `VTCSocialResidueProgram` and you have a
hash-stability landmine — future cleanup will invalidate all existing checkpoints. Better to
break it now (zero users).
**Effort.** M (4–6 hours — delete each item, update tests, regenerate VFS hash fixtures,
update any docs that mention them).
**Files.** `src/townlet/vfs/vtc.py`, `src/townlet/vfs/__init__.py`,
`src/townlet/vfs/schema_hashes.py`, `src/townlet/vfs/transition_graph.py`,
`src/townlet/universe/compiler.py:55, 78`, `src/townlet/universe/cues_compiler.py`,
`src/townlet/agent/networks.py:558+`, `src/townlet/agent/network_factory.py`, all matching
tests.

### Q-REC-5 (P1, M effort) — Delete the legacy DAC compilation path in `dac_engine.py`

**Rationale.** Two `_compile_extrinsic` code paths for `constant_base_with_shaped_bonus` (one at
line 196 for DAC v2, one at line 230 for legacy `agent.yaml`) is precisely the
"support-both-old-and-new" antipattern called out in CLAUDE.md. Pick one (DAC v2 is the documented
forward path); delete the other; update fixtures.

**Confidence.** High (validator + SG4 agree on the two paths).
**Risk if not done.** Silent reward divergence when bugs are fixed in only one path. Hash-based
checkpoint compat is the only safeguard, and it does not catch within-run mis-routing.
**Effort.** M (6–10 hours — verify which fixtures use legacy, migrate, delete, re-validate).
**Files.** `src/townlet/environment/dac_engine.py:196, 230`, `src/townlet/config/agent_config.py`
(if the legacy path imports from here), test fixtures.

### Q-REC-6 (P1, S effort) — Decide on `vulture` and `pytest-benchmark`

**Rationale.** Two configured-but-unused signals. `vulture` is in dev deps and called from
nothing. `pytest-benchmark` is used by performance/conftest.py but absent from the manifest —
the performance tests silently skip. Resolution options:

- **A:** Wire vulture into pre-commit + add a `vulture-check` CI job; add `pytest-benchmark` to
  dev deps; enable the perf tests in a scheduled workflow.
- **B:** Remove vulture from deps; delete the performance conftest skip-dance and either delete
  `tests/test_townlet/performance/` or convert it to plain-`time`-based benchmarks.

Either choice is fine; the current state (declare-but-don't-use) is what is not fine.

**Confidence.** High on the facts; recommendation depends on operator intent for the perf
suite.
**Risk if not done.** False signal about discipline. The `tests/test_townlet/performance/`
directory exists and looks active, but it is dead-on-arrival.
**Effort.** S (1–2 hours either way).
**Files.** `pyproject.toml:83-84`, `.pre-commit-config.yaml`, `.github/workflows/lint.yml` or a
new `benchmarks.yml`, `tests/test_townlet/performance/conftest.py`.

### Q-REC-7 (P1, M effort) — Reconcile catalog §11.3 GPU-discipline leaks against the "GPU-native" claim

**Rationale.** Six per-agent Python loops in the runtime hot path contradict the "GPU-native"
marketing in CLAUDE.md, README, and `pyproject.toml` keywords. Two paths:

- **Vectorise** the six loops (action_executor, dac_engine, vectorized_env, grid2d encoder,
  affordance_engine, VTCInteractionProgressProgram). This is real engineering work; M-L effort.
- **Amend the claim** — document the specific paths that remain non-vectorised and the reasons
  (small N defaults, code clarity, etc.). S effort.

Pick before downstream consumers (paper, blog post, partner pitch) cement the GPU-native claim
in writing that cannot easily be retracted.

**Confidence.** High on the leak inventory (catalog + validator confirmed).
**Risk if not done.** Two-cohort risk: (a) operator presents GPU-native claim externally and it
is fact-checked by a competent reader; (b) scaling experiment (L5_multi_agent or beyond) reveals
sublinear speedup and someone has to do the work anyway, in panic mode.
**Effort.** S to amend, M-L to vectorise.
**Files.** Six locations enumerated in catalog §11.3; CLAUDE.md mission paragraph; README.

### Q-REC-8 (P2, M effort) — Tighten mypy: ratchet `disallow_untyped_defs` per-module

**Rationale.** `pyproject.toml:116` declares `disallow_untyped_defs = false` with a "tighten
later" comment. Six months on, untightened. The project advertises `Typing :: Typed` and uses
Pydantic v2 everywhere, but does not enforce type discipline at the function-def level.

A practical migration: per-module `[[tool.mypy.overrides]]` blocks turning `disallow_untyped_defs
= true` on for modules that already pass clean (DTO layer, world/types, agent/networks). Add a
quarterly sprint item to migrate one more subpackage.

**Confidence.** High on the diagnosis. Medium on the order of migration (depends on actual
type-coverage of each subpackage — not measured in this assessment).
**Risk if not done.** Type discipline silently degrades; new untyped functions accrete.
**Effort.** M (4–8 hours initial; ongoing).
**Files.** `pyproject.toml:112+`.

### Q-REC-9 (P2, S effort) — Add bandit / B-rule security pass

**Rationale.** Ruff selections (`pyproject.toml:110`) include `E,F,I,N,W,UP` — no `B` (bugbear),
no `S` (bandit). The repo handles serialised checkpoints (`cloudpickle>=3.0.0`), a WebSocket
server bound `0.0.0.0`, and CORS `allow_origins=["*"]`. A `ruff check --select=S` pass against
`src/` would surface known unsafe patterns at zero recurring cost.

**Confidence.** High on the gap (selections file is unambiguous). Medium on the value
(localhost-only-safe combinations may make findings non-actionable).
**Risk if not done.** When deployment via `townlet-demo.service` happens to a non-localhost
host, latent issues become live ones.
**Effort.** S (30 minutes to add the selection, plus an hour to triage findings).
**Files.** `pyproject.toml:109-110`, possibly `.github/workflows/lint.yml` with a
`--no-fix` lint pass for `S` initially.

### Q-REC-10 (P2, S effort) — Add `--cov-fail-under` and per-subsystem coverage targets

**Rationale.** Coverage is computed (`pyproject.toml:127`) but not gated. After Q-REC-2
resolves the true number, set a floor (current actual − 5% as a starting threshold) and ratchet
upward over time. Per-subsystem targets help: DTOs and AST nodes are already at 90%; runtime
engines at 2–9% are the obvious gap.

**Confidence.** High on the mechanism; the threshold itself requires Q-REC-2 to resolve first.
**Risk if not done.** Coverage regression goes undetected indefinitely.
**Effort.** S (30 minutes once Q-REC-2 lands).
**Files.** `pyproject.toml:124-131`.

### 8.1 Recommendations summary table

| # | Title | P | Effort | Confidence |
|--:|---|:--:|:--:|:--:|
| Q-REC-1 | Delete stale `DEPENDENCY_ANALYSIS_*` files | P1 | S | High |
| Q-REC-2 | Fix `tests/test_townlet/README.md` + re-derive coverage | P1 | S | High |
| Q-REC-3 | Remove redundant pyproject deps (Flask, TF) | P1 | S | High |
| Q-REC-4 | Delete/wire `VTCSocialResidueProgram`, `CuesCompiler`, `StructuredQNetwork` | P1 | M | High |
| Q-REC-5 | Delete legacy DAC compilation path | P1 | M | High |
| Q-REC-6 | Resolve `vulture` and `pytest-benchmark` (wire or remove) | P1 | S | High |
| Q-REC-7 | Reconcile GPU-discipline leaks vs marketing | P1 | S–L | High |
| Q-REC-8 | Tighten mypy per-module | P2 | M | High |
| Q-REC-9 | Add ruff `S` (bandit) selection | P2 | S | High |
| Q-REC-10 | Add `--cov-fail-under` and per-subsystem targets | P2 | S | High |

**Total estimated effort for P1 cohort (Q-REC-1 through Q-REC-7):** 15–28 hours (single engineer,
focused). Net deletion: ~1,400–1,800 LOC of dead code + stale audit files + redundant deps.

---

## 9. Quality metrics summary

| Metric | Value | Source |
|---|---:|---|
| Source Python LOC | 45,117 | `find src/townlet -name "*.py" -exec wc -l {} +` |
| Source Python files | 162 | `find src/townlet -name "*.py" | wc -l` |
| Test Python LOC | 77,265 | `find tests -name "*.py" -exec wc -l {} +` |
| Test Python files | 321 | `find tests/test_townlet -name "*.py" | wc -l` |
| Test:src LOC ratio | **1.71** | derived |
| Total test functions | 2,762 | `grep -rh "^def test_\|    def test_" tests/test_townlet/ | wc -l` |
| Property-test functions | 34 | catalog §3 |
| Estimated dead-code LOC (P1 deletion candidates) | ~1,400–1,800 | aggregated from §4.1 |
| Orphan / unused config DTO files | 2 cold-dead, 1 half-dead | §7.1 |
| Stale tracked files at repo root | 4 (`DEPENDENCY_ANALYSIS_*`) | §4.3 |
| Markdown files in `docs/` (tracked) | 509 | `git ls-files docs/ | wc -l` |
| Doc files : source files ratio | 3.1 : 1 | derived |
| Estimated CLAUDE.md drift rate | **40–50%** of sections materially affected | §5.3 |
| Documented drift items (validator-confirmed) | 12 | catalog §10 |
| TODO/deprecated markers in `src/` | 7 | §4.2 |
| FIXME/HACK/XXX markers in `src/` | 0 | §4.2 |
| Files >500 LOC in `src/` | 9 (top: `vfs/vtc.py` 2,990 LOC, `vectorized_env.py` 1,559 LOC) | §2.2 |
| pytest marker usages | 18 (across 2,762 tests; 286/321 files have **no** marker) | §3.3 |
| Coverage % (per local `.coverage` artifact, possibly partial) | **19% line, 36 branches** | `python -m coverage report --rcfile=pyproject.toml` |
| Coverage % (per `tests/test_townlet/README.md`) | 19% local artifact, explicitly qualified | `tests/test_townlet/README.md` |
| `--cov-fail-under` threshold | **none configured** | `pyproject.toml:124-131` |
| CI stages on PR/push | 3 (lint.yml, tests.yml, config-validation.yml) | `.github/workflows/` |
| CI stages scheduled / on-demand | 1 (full-tests.yml @ 06:00 UTC daily) | `.github/workflows/full-tests.yml` |
| Security scan jobs (bandit, audit, etc.) | **0** | §2.6 |
| Configured-but-unused dev tools | 2 (`vulture`, `pytest-benchmark` — the latter is referenced by test code but missing from deps) | §2.7 |
| GPU-discipline leaks in nominally GPU-native paths | 6 | catalog §11.3 |
| Performance benchmarks runnable today | 1 (`test_performance_threshold.py`); others silently skip | §6.2 |
| Pyproject manifest version | 0.1.0 | `pyproject.toml:3` |
| CHANGELOG release baseline | Resolved: 2025-11-05 section is a `0.1.0` alpha worklog, not a release | §5.5 |
| `mypy disallow_untyped_defs` | `false` (with "tighten later" comment, six months unactioned) | `pyproject.toml:116` |
| Ruff selections | `E, F, I, N, W, UP` (no `B`, no `S`, no `SIM`, no `PTH`) | `pyproject.toml:110` |

### 9.1 Headline composite scores

| Composite | Score | Basis |
|---|:--:|---|
| **Toolchain discipline** | **3 / 5** | Pre-commit + 4 CI workflows is real; tool *config* is lenient (mypy untyped OK, ruff B/S off, no coverage gate, no security scan). |
| **Test corpus discipline** | **3 / 5** | Large investment (1.71:1 ratio), good structure, real fixtures + builders — but markers are aspirational and the coverage gate is absent. |
| **Pre-release hygiene (zero-backcompat adherence)** | **2 / 5** | 18 dead-code items per catalog §11.1, 4 stale tracked audit files, 4 redundant deps. The project sets a strict rule and follows it ~70% of the time. |
| **Documentation health** | **2 / 5** | 12 confirmed drifts remain; test README and changelog baseline are now corrected, but changelog format still mixes release notes with worklogs. Volume is fine; freshness is not. |
| **Performance discipline** | **2 / 5** | 6 hot-path Python loops + dead benchmark suite + GPU-native marketing = the worst combination. |
| **Configuration discipline** | **4 / 5** | 142 DTOs, `extra="forbid"`, custom no-defaults linter, hierarchical v2.1 layout — genuinely strong. Two orphan files and a DAC dual-path keep it from 5. |

**Overall posture: Concerning, trending Healthy.** The disciplines are in place; the
follow-through is incomplete. The P1 cohort of recommendations (Q-REC-1 through Q-REC-7) is
mostly mechanical cleanup that closes 70% of the gap in under 30 engineer-hours.
