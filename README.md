# Townlet

The repository directory is named `hamlet`; the Python distribution and live source tree are
`townlet`. Same project.

Townlet is a deep reinforcement-learning substrate expressed as configuration. World variables,
spatial topology, meters, actions, affordances, effects, items and rewards are authored in YAML,
compiled into a hash-carrying `CompiledUniverse`, and executed through a torch-tensor runtime.
The training runner chooses CUDA when it is available and otherwise uses CPU.

The point is authoring: *from game as experience to writing a game as experience*. The
[product vision](docs/product/vision.md) is that an author can turn an idea for a mechanic into a
running, trainable experiment without writing an environment subclass, observation plumbing or
reward-function class. The currently supported declarations implement part of that vision;
broader cognition, world modeling and authoring experiences remain unfinished.

The survival world in `configs/default_curriculum` — eight meters, fourteen affordances and an
8×8 grid — is the demonstration, rather than the limit of the intended product.

## Status and verification

Townlet is pre-release: version 0.1.0, classified Alpha, with no backwards-compatibility contract.
Removed declarations and artifact versions fail loudly; there are no compatibility readers or
migration paths.

**Source review:** `project-recovery-4` at
`ea9fc5fafe451cd59e7231ccef06d221e73ff99d`, 2026-10-01 Australia/Canberra.
Its execution files match the qualified implementation
`b70fda104e5061ed2735e8b31b7f8f9caaf99f19`. This README's source review and that implementation's
executed qualification are separate records. Full local tests, Ruff, Black, mypy, no-defaults,
compiler-fleet validation, direct-parent comparison and frozen CPU qualification passed at the
qualified source. Commands, terminal outcomes and scope are retained in the
[static-access evidence](docs/product/evidence/static-epistemic-access/acceptance.md) and
[local integration receipt](docs/product/evidence/static-epistemic-access/local-integration.json).

At this review, hosted CI for the consolidation into GitHub `main` is pending. Local success and
historical hosted success are not results for a new published head. The eventual main landing
and exact-head hosted checks belong in the [current-state record](docs/product/current-state.md).
No fresh browser, CUDA or learned-policy convergence campaign is claimed by this source review.

The project remains a rewrite behind a pinned oracle. `oracle-2026-08-17` at
`4222a9176e68e232a0e46c7004183440e27f22c3` is the preserved-behavior reference;
`oracle-2026-08-13` remains history. Frozen source, tags and fixtures do not change to make a
comparison pass. Intended differences belong in the
[divergence register](docs/oracle/known-divergences.md). See [Oracle rules](docs/oracle/ORACLE.md).

## Author a universe

Declarations are identified by content, including nested YAML files. Filenames are transport:
renaming a file does not select a different declaration family. Pack declarations live outside
`levels/`; declarations under `levels/<id>/` belong to that level. Unknown and conflicting
families refuse. See the [declaration contract](docs/config-schemas/declarations.md).

A conventional pack layout is:

```text
configs/default_curriculum/
  experiment.yaml       # declared levels and experiment identity
  stratum.yaml          # pack-wide spatial topology and capabilities
  environment.yaml      # meter observation types and cascade graph
  actions.yaml          # substrate/custom actions, writes and labels
  brain.yaml            # architecture, optimizer, loss, Q-learning and replay
  variables.yaml        # canonical state, policies, profiles and scope extents
  items.yaml            # item catalog
  effects.yaml          # effect catalog
  transition_rules.yaml # optional transition declarations
  presentation.yaml     # optional display metadata
  levels/<level>/
    curriculum.yaml     # vision and temporal configuration
    bars.yaml           # meters, bounds and cascades
    affordances.yaml    # costs, interactions, hours and placement
    drive.yaml          # reward declarations
    training.yaml       # training controls and enabled actions
    brain.yaml          # optional COMPLETE replacement brain
    items.yaml          # optional level item appearances
```

This tree is a convention, not the compiler's discovery rule. The required level families are
curriculum, bars, affordances, drive and training. Pack catalogs cannot be moved to level scope.
A level brain replaces the complete pack brain; partial patches are not supported. Training
overrides five effective-brain scalars: gamma, target-update frequency, Double DQN, learning
rate and replay capacity.

### Spatial configuration

The current `configs/default_curriculum/stratum.yaml` is:

```yaml
stratum:
  version: "1.0"

  substrate:
    type: grid

    grid:
      topology: square
      width: 8
      height: 8

      boundary: clamp

      distance_metric: manhattan

      diagonals: true

  vision_support: both

  temporal_support: enabled
```

The stratum is pack-wide. Changing it changes every level's spatial execution; a level-local
stratum is not a separate world. The current vocabulary includes square/cubic grids, GridND,
continuous spaces and aspatial worlds, with family-specific support boundaries. Coordinate and
egocentric normalization are canonical; the deleted `observation_encoding` and
`observation_mode` selectors are not accepted. The live viewer supports a narrower surface than
the compiler; a declared spatial mode does not imply that it has a complete renderer.

Trial 001 records a historical substrate-swap witness: the survival rules were moved to a
six-dimensional grid through configuration, without source changes. That establishes a specific
compile/reset/step witness, not full support for every topology or a learning result. See
[metrics](docs/product/metrics.md) and [Strata](docs/architecture/STRATA.md).

### Canonical variables and static access

Cut B replaced the separate environment/profile/overlay authoring surfaces with one canonical
variable roster. Each declaration specifies scope, lifetime, initialization, semantic type and
exposure. `variables.extents` supplies the sizes of zone, group, message and affordance storage;
item state uses the same contract, qualified by its declared item profile. The authored day
clock is derived from engine `tick`, and a curriculum can refer to its period with
`day_length: {period_of: day_phase}`. See [variables](docs/config-schemas/variables.md).

Read and write policies are required. This is a declaration from the committed
`configs/static_epistemic_access/variables.yaml` witness:

```yaml
- id: hidden_score
  scope: agent
  type: scalar
  lifetime: episode
  semantic_type: custom
  readable_by: [engine]
  writable_by: [engine]
  exposed_to: []
  initial_value: 2.0
```

Readers are exactly `engine` and optional `agent`, with engine read required. Writers are
`[engine]` or `[]`; an empty writer policy makes the state runtime-immutable. Exposure is
independent: agent-readable state is not directly observed unless `exposed_to: [agent]` is also
declared. Exposure without read permission, missing policies, duplicate roles and unknown actors
refuse. Initialization/reset can initialize immutable storage according to its declared lifetime.

The engine executes actions, effects, expressions, rewards and spawn predicates. Choosing an
action does not grant the policy an agent-write role. Accessors and observation publishers use
one registry-owned immutable policy snapshot; permission changes require a new runtime instance.
Known denied authored targets refuse at compilation, and dynamic operations retain checked
write paths. VTC carries attempted write targets independently of value equality: writing the
old value is still a write. Each VTC commit authorizes its complete VFS target set before publishing
transition bars, dones and state; spawn overrides authorize before allocation/registration.

The witness's actual ADVANCE action changes both public and hidden state. Its named hidden-state
reward remains usable by the engine while direct agent access denies, through direct and
cache-loaded artifacts, two rows and two episodes. Qualified item probes are separately retained.
Static roles do not implement ownership or spatial privacy, engine confidentiality, a Python
sandbox or information-theoretic noninterference: rewards and public derived values can reveal
hidden inputs. See [static-access acceptance](docs/product/evidence/static-epistemic-access/acceptance.md).

### Rewards

The current L1 `drive.yaml` is:

```yaml
drive:
  version: '1.0'
  modifiers:
    energy_crisis:
      bar: energy
      ranges:
      - name: range_0
        min: 0.0
        max: 0.2
        multiplier: 0.0
      - name: range_1
        min: 0.2
        max: 1.0
        multiplier: 1.0
  extrinsic:
    type: constant_base_with_shaped_bonus
    base_reward: 0.01
    bar_bonuses:
    - bar: energy
      center: 0.0
      scale: 0.5
    - bar: health
      center: 0.0
      scale: 0.5
    variable_bonuses: []
    apply_modifiers: []
  intrinsic:
    strategy: adaptive_rnd
    base_weight: 0.1
    apply_modifiers:
    - energy_crisis
    adaptive_config:
      enabled: true
      threshold: 100.0
      decay_rate: 0.995
      min_weight: 0.01
  shaping:
  - type: approach_reward
    weight: 0.01
    target_affordance: EAT
    max_distance: 5.0
  - type: completion_bonus
    weight: 0.1
    affordance: SLEEP
  composition:
    normalize: false
    clip: null
    log_components: true
    log_modifiers: true
```

Rewards are configured rather than supplied through a `RewardStrategy` subclass. This declared
surface is not fully implemented: `composition.normalize` and `composition.clip` are accepted
but inert, and intrinsic strategy selection has unfinished integration. A parsed declaration is
not proof that every field affects execution. See [DAC](docs/config-schemas/drive_as_code.md).

The five default levels share meter, affordance and reward declarations. Partial visibility in
L2 and active time in L3 change runtime behavior while preserving the compiled token layout.
Their names do not establish five distinct curricula or five qualified learning outcomes.

## Install

The package requires Python 3.13 or newer; `.python-version` pins 3.13. The retained qualification
used Python 3.13.1, Torch 2.11.0+cu130 and Pydantic 2.13.4. Those are actual execution versions,
not a cross-platform or CUDA qualification claim.

```bash
git clone https://github.com/foundryside-dev/hamlet
cd hamlet
uv sync --all-extras --locked
```

Use `--all-extras` for the development tools: pytest, Ruff, Black and mypy are in the `dev` extra.
The installed project provides `townlet`; no `PYTHONPATH` export is needed. There are no declared
console-script entry points, so use Python modules and repository scripts.

## Compile, train and inspect

Validate without reading or writing a compiled cache:

```bash
uv run python -m townlet.universe validate configs/default_curriculum \
    --primary-level L1_full_observability
```

Compile and inspect:

```bash
uv run python -m townlet.universe compile configs/default_curriculum \
    --primary-level L1_full_observability
uv run python -m townlet.universe inspect configs/default_curriculum \
    --primary-level L1_full_observability --format json
```

`--primary-level` is required for compile/validate and directory inspection. Compilation builds
all world levels, with one cache artifact per selected primary level:
`<pack>/.compiled/universe-<level>.msgpack`. The top-level effective brain is primary-level scoped.
The current compiled artifact schema is **1.29**; older versions and missing policies refuse.
This is separate from authored declaration versions and checkpoint format **6**.

Train using the pack root:

```bash
uv run scripts/run_demo.py --config configs/default_curriculum \
    --level L1_full_observability --episodes 10000 --inference-port 8766
```

`--level` and `--inference-port` are required. The unified launcher runs training and a WebSocket
viewer backend in one process. Artifacts go under
`runs/<run_metadata.output_subdir>/<timestamp>/`: checkpoints with digest sidecars, a metrics
database, TensorBoard data, logs and a config snapshot. This command is a wired entry point;
the current checkpoint did not run a new end-to-end training/browser campaign.

The frontend runs separately:

```bash
cd frontend
npm ci
npm run dev
```

The live viewer still has model-readiness, checkpoint freshness and control/transport gaps;
watching agents move is not evaluation or convergence evidence.

Serve a checkpoint separately:

```bash
uv run python -m townlet.demo.live_inference <checkpoint_dir> 8766 0.2 10000 \
    configs/default_curriculum L1_full_observability
```

Training resume and serving share an identity gate. They check selected world, effective brain,
VFS and architecture-appropriate token/layout contracts before loading weights. Permission-only
changes in ordinary or qualified item state move variable/VFS identity and refuse exact resume.
Transfer is a distinct operation. Some broader pack-level identity fields are recorded without
being independent checkpoint gates; this is not a guarantee that every pack edit is incompatible.

## Architecture and completion

| Area | Present implementation | Remaining boundary |
| --- | --- | --- |
| Compiler | Nested declaration discovery, typed/scoped validation, compiled token and transition products, cache and CLI | Not every authored failure is yet a complete structured diagnostic; some command lowering remains runtime-owned |
| Strata | Multiple spatial families and vectorized torch state | Edge/action/renderer semantics are uneven across families |
| Universe as Code | Meters, affordances, effects, items, variables, rewards and transition programs | Some accepted settings and lifecycle/item semantics remain incomplete |
| Brain as Code | `feedforward`, `dueling`, `token_set`, token-native `recurrent`; optimizer/loss/replay factories | Cognitive topology, personality, goals, panic/compliance and think-loop graph are not implemented |
| Observation | Seven typed token families, compact serialization, masked publishers, policy-authorized registry/item plans | Agent-token capacity remains zero in shipped packs; held-item/locality relationships are incomplete |
| Integration/UX | Training, checkpoints, live server, Vue observer and recording machinery | Experiment controls, terminal lanes, randomness isolation, model handoff and browser journeys need further qualification |

`CompiledUniverse` is a frozen dataclass, not a deeply immutable object graph. World products and
runtime state remain separate concerns. The completed static-access work seals permission
authority for a runtime instance; it does not close whole-artifact immutability.

The declaration-store work is accepted in two bounded cuts:
[Cut A](docs/product/evidence/declaration-cut-a/acceptance.md) implements files-as-transport;
[Cut B](docs/product/evidence/declaration-cut-b/acceptance.md) unifies canonical variable
semantics and typed scope. [Static epistemic access](docs/product/evidence/static-epistemic-access/acceptance.md)
adds the checked finite policy contract and its identity/evidence closure. Those acceptances do
not complete the entire authoring product.

The token-recovery milestones and their historical learning witness remain retained. M4 is a
versioned deterministic engineering qualification at `9d4e942f`, not a multi-seed statistical
convergence study of the current default scenarios: four token architecture/aggregation cells
passed their prescribed L2 survival floor under a fixed budget. See the
[M4 evidence](docs/product/baselines/2026-09-m4-token-regression/) and
[metrics](docs/product/metrics.md). No new learning result is inferred from local unit tests or
static-access qualification.

## Differential qualification

The public harness compares the preserved oracle and current implementation using declared
pack/level/seed/device inputs:

```bash
uv run python -m townlet.oracle.harness --cell default_curriculum:L0_0_minimal
```

It creates or verifies a detached oracle worktree under `.oracle/`, runs both sides in separate
processes, and writes reports under `runs/differential/<run-id>/`. The sides read different
explicit pack roots: frozen `oracle_fixtures/` and live `configs/`. `--scripted` replays the old
side's actions on the new side.

The matrix declares ten CPU cells and ten CUDA cells. CUDA rows explicitly skip when not enabled.
Acceptance compares observation, action, reward and done streams plus provenance hashes. A
registered divergence must match its declared field/stream/crash shape; unexplained differences,
stale allowances and empty or all-skipped runs fail. A registered observation difference does
not authorize changing actions, rewards or dones.

The register now contains DIV-001 through DIV-015. Cut B's DIV-014 and static access's DIV-015
append measured variable/VFS causes without widening historical stream allowances. DIV-015
also binds a complete frozen/live byte inventory for the six matrix packs. The direct-parent
static-access comparison independently requires unchanged streams and resets; it does not
inherit historical observation suppression. The qualified implementation's parent and frozen
CPU reports, attributions and raw-evidence reconstruction are linked in its
[acceptance record](docs/product/evidence/static-epistemic-access/acceptance.md).

## Checks and CI

Run locally:

```bash
uv run ruff check .
uv run black --check src tests
uv run mypy src/townlet --show-error-codes
uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
uv run python scripts/validate_compiler_cli.py
uv run pytest
```

Bare pytest runs the default complete selection; no `slow` deselection remains. Hardware skips
remain possible. The pack smoke test discovers current positive packs, constructs two CPU lanes,
resets and steps them; this is a finite-output/contract gate, not a training qualification.

Four GitHub Actions workflows are configured with Python 3.13 and `uv sync --all-extras`:

| Workflow | Configured trigger and checks |
| --- | --- |
| Lint | Push to `main`/`project-recovery*`, PR; Ruff, Black, mypy, no-defaults |
| Config Validation | Push to `main`/`project-recovery*`, PR; public compiler CLI fleet |
| Tests | Push to `main`/`project-recovery*`, PR; config validation then bare pytest |
| Full Test Suite | Dispatch and nightly `0 6 * * *`; config validation then bare pytest |

The compiler-fleet script excludes `aspatial_test`; the pytest pack smoke gate exercises that
pack separately. The three named negative VFS fixtures are expected compiler refusals.
No workflow installs Node, runs frontend tests/build, runs the oracle, launches the unified demo
or qualifies learning. `frontend/package.json` provides local `npm test` and `npm run build`
scripts; their presence is not a new browser/build acceptance result.

Workflow files describe what is configured. A hosted success claim requires terminal checks at
the exact published head, and a main-merge success requires its actual landing record. Historical
hosted readings are retained in [product decisions](docs/product/decisions/), including
[PDR-0145](docs/product/decisions/0145-gate-2-executed-for-the-fifth-merge-29-stale-claims-22-omissions-and-nine-defects-in-the-drafts-corrections.md)
and [PDR-0146](docs/product/decisions/0146-the-fifth-merge-landed-at-ea3648db-and-work-continues-on-project-recovery-4.md).
They are not substituted for consolidation CI.

## Known work ahead

- Reconcile shipped scenarios and BAC configurations, wire experiment controls, repair terminal
  lane/replay/metric accounting and isolate evaluation/serving randomness before relying on new
  convergence claims.
- Complete reward strategy/composition consumption, effects reset and command/time lifecycle
  contracts. Some historical silent cache failures are repaired; initial item-appearance cache
  fidelity remains outside the static-access acceptance.
- Complete carried-item observation, item identity/locality/capacity and independent/shared-world
  semantics. Qualified static access does not solve those relationships.
- Make the viewer's loaded model, run identity, controls, reconnect and replay states truthful;
  add meaningful frontend/browser gates.
- Deliver BAC cognition and execution graphs, a second genuinely different configuration-authored
  world, and a portable trained-policy export path. No Murk integration is qualified here.

These are engineering and research boundaries, not a claim that a successful small demonstration
has completed the product. [Current state](docs/product/current-state.md) and
[roadmap](docs/product/roadmap.md) record the current priorities.

## Documentation

- [Vision](docs/product/vision.md): intended product, audiences and anti-goals.
- [Current state](docs/product/current-state.md), [roadmap](docs/product/roadmap.md) and
  [metrics](docs/product/metrics.md): dated status, priorities and measurements.
- [Product decisions](docs/product/decisions/), [PRDs](docs/product/prds/) and
  [trials](docs/product/trials/): contracts, acceptance boundaries and authoring witnesses.
- [Architecture](docs/architecture/HLD.md) and [config declarations](docs/config-schemas/declarations.md):
  implementation/design guidance. Check current consuming source when older prose conflicts.
- [Documentation map](docs/README.md): directory trust levels. Archived material is history.

## License

MIT. See [LICENSE](LICENSE).
