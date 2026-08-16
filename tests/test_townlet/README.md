# Townlet Test Suite

This directory contains the primary automated tests for the `townlet` package. The suite is much larger than the old refactoring-era notes in this file implied, so the counts below are intentionally tied to reproducible commands.

## Current Snapshot

Measured on 2026-05-16 from `/home/john/hamlet`:

| Measure | Current value | Evidence command |
|---|---:|---|
| Tests collected | 2,895 | `uv run pytest --collect-only -q tests/test_townlet --no-cov` |
| Tests selected by default | 2,862 | same command; the `slow` filter that deselected 33 of these **no longer exists** (2026-08-16, `hamlet-a0832f9004`) — today every collected test is selected |
| Test files | 284 | `find tests/test_townlet -type f -name 'test_*.py' \| wc -l` |
| Coverage artifact | 19% line coverage | `uv run python -m coverage report --rcfile=pyproject.toml` |
| Coverage denominator | 18,558 statements, 6,916 branches | same coverage report |

The 19% coverage number is measured from the existing local `.coverage` artifact. It is not proof that a fresh full test run currently passes or produces identical coverage. The repo currently has no `--cov-fail-under` threshold configured in `pyproject.toml`.

## Collection Breakdown

| Area | Collected | Selected by default | Notes |
|---|---:|---:|---|
| `unit/` | 2,420 | 2,420 | Component and DTO tests |
| `integration/` | 407 | 374 | the 33 `slow`-deselected tests in this 2026-05-16 count now run by default — the marker is gone |
| `properties/` | 49 | 49 | Hypothesis/property tests |
| `performance/` | 11 | 11 | Includes benchmark-marked tests; `benchmark` is not registered in `pyproject.toml` |
| `test_curriculum/` | 8 | 8 | Curriculum-stage tests outside the main `unit/` tree |
| `special/` | 0 | 0 | Directory currently contains no collected tests |
| **Total** | **2,895** | **2,862** | Default selection is controlled by `pyproject.toml` |

## Layout

```text
tests/test_townlet/
├── conftest.py
├── builders.py
├── fixtures/
├── helpers/
├── utils/
├── unit/
├── integration/
├── properties/
├── performance/
├── test_curriculum/
└── special/
```

Use the tree above as a navigation aid, not as a fixed taxonomy. New tests should live where their behavioral boundary is clearest:

- `unit/` for isolated package components, DTO validation, factories, parsers, and tensor helpers.
- `integration/` for compiler-to-runtime flows, environment/population handoffs, checkpointing, web metadata, and multi-component behavior.
- `properties/` for invariants that benefit from generated inputs.
- `performance/` for explicit timing or benchmark guardrails.

## Running Tests

The project-level pytest configuration already adds `--cov=townlet`, branch coverage, and `term-missing`. There is no marker-based deselection: `uv run pytest` is the complete suite.

```bash
# Default local suite: selected tests only, with coverage
uv run pytest

# Tests in this subtree only
uv run pytest tests/test_townlet

# Unit tests only
uv run pytest tests/test_townlet/unit

# Integration tests only
uv run pytest tests/test_townlet/integration

# Property tests only
uv run pytest tests/test_townlet/properties

# Collection without coverage
uv run pytest --collect-only -q tests/test_townlet --no-cov
```

For an HTML coverage report:

```bash
uv run pytest tests/test_townlet --cov=townlet --cov-report=html
```

## Shared Fixtures

The central fixture surface is `tests/test_townlet/conftest.py`, with additional helpers under `tests/test_townlet/_fixtures/`, `helpers/`, `utils/`, and `builders.py`.

Common fixtures include:

- `cpu_device` and `device` for deterministic CPU runs or CUDA-aware tests.
- `test_config_pack_path` for the canonical v2.1 test config pack.
- `config_pack_factory` / temporary config-pack helpers for isolated config mutations.
- Environment fixtures such as `basic_env`, `pomdp_env`, `temporal_env`, and `multi_agent_env`.
- Training fixtures such as replay buffers, curricula, exploration strategies, and vectorized populations.

Prefer existing fixtures and builders before adding new bespoke setup code.

## Writing Tests

Use behavioral assertions over brittle exact values unless the test is specifically validating a stable ABI, schema hash, or serialization contract.

```python
def test_component_behavior(cpu_device, test_config_pack_path):
    component = MyComponent(device=cpu_device)

    result = component.do_something()

    assert result > 0
    assert result < 1
```

For integration tests, use real components at the boundary under test and keep mocks close to external services or intentionally impossible states.

```python
def test_cross_component_flow(cpu_device, test_config_pack_path):
    env = make_test_env(test_config_pack_path, device=cpu_device)
    population = make_test_population(env, device=cpu_device)

    state = population.step_population(env)

    assert state.observations.shape[0] == env.num_agents
    assert state.rewards.shape == (env.num_agents,)
```

For property tests, keep strategies within valid domain bounds so failures point at invariants rather than invalid setup.

```python
from hypothesis import given, strategies as st


@given(st.integers(min_value=0, max_value=4))
def test_universal_property(action):
    result = component.process(action)

    assert 0 <= result <= 1
```

## Practices That Still Matter

- Use `cpu_device` for deterministic tests unless the test is explicitly about CUDA behavior.
- Control agent positions after reset when testing movement or local observations.
- Use `pytest.approx()` for floating-point comparisons.
- Add regression tests near the subsystem they protect; use `tests/test_townlet/regressions/` only when a bug needs a dedicated regression fixture set.
- Mark CUDA-only scenarios `gpu` (skipped without CUDA). There is no `slow` marker and no default deselection: if a test is too slow for the default suite, make it faster or delete it — a deselected test is an unread part of the gate (`hamlet-a0832f9004`).

## Markers

Registered markers live in `pyproject.toml`:

```python
@pytest.mark.gpu
@pytest.mark.integration
@pytest.mark.e2e
```

Useful marker commands:

```bash
uv run pytest -m gpu
uv run pytest -m integration
```

## Troubleshooting

If tests fail intermittently, first check for CUDA use, random spawn positions, or hidden shared state in fixtures.

If imports fail, run through `uv run pytest` from the repository root so `pythonpath = ["src"]` from `pyproject.toml` is active.

If coverage looks surprising, confirm whether you are reading a fresh report from the just-run test session or an existing `.coverage` artifact.
