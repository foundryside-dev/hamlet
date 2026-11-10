# Shared basic_env constructor identity repair

Status: SEALED, minimal fixture authoring and scoped Black/Ruff complete; executable qualification remains root-owned and OPEN. Only tests/test_townlet/_fixtures/environment.py changed among the four implementation/test files. No runtime, project import, pytest, Git/index action, repository copy, deletion, new test/helper, production change or subagent was used.

## Exact source inventory and custody

Whole-file accounting (targeted static reads/searches inside these files): initial 4 files / 4,529 lines; final 4 files / 4,535 lines. Within named caps 2,400 / 350 / 550 / 1,500 and aggregate 4,800.

| File | Access | Final lines | SHA256 |
| --- | --- | ---: | --- |
| src/townlet/environment/vectorized_env.py | Read only | 2399 | 5508110716c38d89497c6d3c0443d6eba15f7bd546b9f2231dd86a41f5b6c166 |
| src/townlet/config/world_roster.py | Read only | 312 | 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33 |
| tests/test_townlet/_fixtures/environment.py | Sole mutable source | 466 | 85467cd5cfe169306c2893944041c1e58d5fe21941498cca6cb2bd7ab9022180 |
| tests/test_townlet/unit/exploration/test_exploration_strategies.py | Read only | 1358 | 9dca12dcd0c58aef663b3287052fed40e3c233517e6010ad4513fe0cc7f43dc7 |

Fixture initial: 460 lines, SHA256 21bd79b1736efd53fdacb76ca6a6f4abaf3917340204aef74994ba20b6af745c. All three read-only hashes match their initial values, including the root-cleared, already-sealed greedy-test edit in strategies. The brief was read first. Allowed constructor-transport and world-identity prose contracts were read; historical direct-construction prose is superseded by the current transport receipt and actual ENV classmethod.

## Actual consumer uses and lifecycle phase

Static inspection of all 18 basic_env consumers in strategies lines 986–1358 found only basic_env.observation_dim reads: seven RND checkpoint completeness tests, seven AdaptiveIntrinsic completeness tests, two checkpoint round-trip tests and two strict-validation tests. Those tests exercise real providers, tensors, predictor training, network weights, optimizer state, epsilon/annealing/history, intrinsic rewards and malformed-state rejection. None calls ENV reset or step. No test body, expected result or provider path was changed.

Actual ENV declares observation_dim from the selected level's token_spec.total_dims during construction (line 380). Its world initializer validates declaration, exact seed, cardinality and membership, establishes fresh-unbound with zero cursors (lines 1940 onward), and construction creates the fresh VFS projection (lines 740 onward). Constructor completion does not reset/activate an episode. reset requires an issued reservation and step requires active phase. Therefore fresh construction is sufficient for these actual consumers; no bootstrap, role-owner declaration, synthetic observations, forged bank/learner receipts, old reset facade or lifecycle bypass is justified or introduced.

## Exact authored change and provenance

Added WorldRosterDeclaration import and a local declaration with the explicit test-owned ID tuple ("basic-env-world",). This literal is authored fixture data, not discovery of existing identity from lane indices or config labels. The same declaration's world_ids tuple is passed unchanged as lane_world_ids. num_agents remains 1.

Passed training_seed=universe.get_level("L0_test").training.seed. Root supplied a finite source-verified API prose receipt: TrainingV2Config.seed is a direct int field (training_v2_config.py line 347); no fifth source file was read by this owner. Both environment selection and seed lookup use the existing explicit L0_test level. There is no fallback, hardcoded seed, signature adapter or ambient RNG seed derivation.

Preserved compilation from test_config_pack_path, explicit device, one agent, all existing configuration/compiled features and real VectorizedHamletEnv.from_universe routing. Six lines added; no prior line removed. The caller remains responsible for public episode lifecycle when active simulation is required.

## Static verification

Post-edit wc -l and sha256sum returned the exact inventory above (exit 0). Post-edit source inspection confirms only the intended import and basic_env body additions.

Initial scoped command attempts from /workspace/hamlet:

```text
black --check --config pyproject.toml tests/test_townlet/_fixtures/environment.py
/bin/bash: line 1: black: command not found
exit 127

ruff check --config pyproject.toml tests/test_townlet/_fixtures/environment.py
/bin/bash: line 1: ruff: command not found
exit 127
```

Root supplied established executable paths; no installation, environment probe or project import attempted. Bare PATH misses were tool-path prerequisites, not code failures. Exact scoped follow-up from /workspace/hamlet:

```text
/workspace/hamlet/.venv/bin/black --config /workspace/hamlet/pyproject.toml /workspace/hamlet/tests/test_townlet/_fixtures/environment.py
All done! ✨ 🍰 ✨
1 file left unchanged.
exit 0

/workspace/hamlet/.venv/bin/black --check --config /workspace/hamlet/pyproject.toml /workspace/hamlet/tests/test_townlet/_fixtures/environment.py
All done! ✨ 🍰 ✨
1 file would be left unchanged.
exit 0

/workspace/hamlet/.venv/bin/ruff check --config /workspace/hamlet/pyproject.toml /workspace/hamlet/tests/test_townlet/_fixtures/environment.py
All checks passed!
exit 0
```

Post-check wc -l and sha256sum again returned exactly the final four-file inventory above (exit 0). Source is stationary and sealed for root qualification.

## Remaining required work

Root must freeze this fixture and execute the actual 18 checkpoint tests before broader repetition and fresh independent source review. No executable PASS is claimed by this owner.

The other nine from_universe call sites in this same fixture file retain missing constructor inputs: pomdp_env, temporal_env, multi_agent_env, env_factory, grid2d_3x3_env, grid2d_8x8_env, aspatial_env, continuous1d_env and continuous3d_env. cpu_env_factory and custom_env_builder route through env_factory. These remain OPEN outside this narrowly dispatched causal repair; none was silently rewritten or disabled.

Root's brief identifies actual runner.py:410 as a separate missing-input runtime path. This owner did not inspect or modify runner. Actual runner E2E, real bank/native integration, genuine lifecycle owners/activation and full BAC acceptance remain required OPEN. This constructor fixture patch neither stubs nor skips that obligation and does not establish broad suite or runtime success.
