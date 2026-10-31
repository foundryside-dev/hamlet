# Townlet

**Deep reinforcement-learning environments written as configuration.**

Townlet lets you describe an RL environment in YAML (its world variables, spatial topology,
meters, actions, affordances, effects, items and reward function), compile it into a single
hash-stamped `CompiledUniverse`, and train agents on it with a vectorized PyTorch runtime. It
runs on CUDA when available and falls back to CPU.

The aim is authoring. If you have an idea for a game mechanic, you should be able to turn it
into a running, trainable and reproducible experiment without writing an environment subclass,
observation-tensor plumbing or reward-function code. Anything that can only be expressed by
editing Python is treated as a gap in the framework.

> The repository is called `hamlet`; the Python package it ships is `townlet`. They are the same
> project.

## Project status

Townlet is **pre-release alpha** (version 0.1.0). There is no backwards-compatibility contract:
removed configuration keys and old artifact versions fail loudly rather than being migrated.

What works today:

- A compiler that discovers, validates and compiles a config pack into one artifact, with a CLI.
- Grid (2-D square and 3-D cubic), N-dimensional grid, continuous and aspatial worlds.
- Declarative meters, affordances, effects, items, typed variables with read/write/exposure
  policies, and reward functions.
- Token-based observations that keep the same type schema across very different worlds, plus
  feedforward, dueling, token-set and recurrent (LSTM) Q-networks.
- Training with checkpointing, a WebSocket inference server and a Vue live viewer.

What is not finished:

- Some accepted reward settings are inert, notably `composition.normalize` and
  `composition.clip`.
- Brain-as-code beyond network selection (cognitive topology, goals, execution graphs) is design
  only.
- The live viewer supports fewer spatial modes than the compiler and has known gaps around
  model readiness, controls and reconnects.
- The five shipped curriculum levels share most of their content. L0_0, L0_5 and L1 differ only
  in training settings; only L2 (partial observability) and L3 (day/night cycle) change the
  world.
- No multi-seed convergence study of the current default scenarios has been published.

See [Vision](docs/vision.md#known-gaps) for the larger gaps.

## Quick start

Townlet needs Python 3.13 or newer and [uv](https://github.com/astral-sh/uv). The viewer also
needs Node.js 20.19 or newer (Vite 7).

```bash
git clone https://github.com/foundryside-dev/hamlet
cd hamlet
uv sync --all-extras --locked
```

Validate the demonstration pack without writing a compiled cache:

```bash
uv run python -m townlet.universe validate configs/default_curriculum \
    --primary-level L1_full_observability
```

Compile it and inspect the result:

```bash
uv run python -m townlet.universe compile configs/default_curriculum \
    --primary-level L1_full_observability
uv run python -m townlet.universe inspect configs/default_curriculum \
    --primary-level L1_full_observability --format json
```

Train an agent. This also starts the WebSocket backend for the viewer on port 8766, the port the
viewer connects to:

```bash
uv run scripts/run_demo.py --config configs/default_curriculum \
    --level L1_full_observability --episodes 10000 --inference-port 8766
```

Training runs on CPU when no GPU is present, but 10,000 episodes then takes a long time; pass a
smaller `--episodes` for a first look. Run outputs (checkpoints with SHA-256 sidecars, a metrics
database, TensorBoard logs and a config snapshot) go under `runs/<output_subdir>/<timestamp>/`,
for example `runs/L1_full_observability/2026-10-31_213045/`. Rerun with `--checkpoint-dir` to
resume.

To watch, start the viewer in a second terminal and open <http://localhost:5173>:

```bash
cd frontend
npm ci
npm run dev
```

To serve a saved checkpoint without training, pass the checkpoint directory, port, delay between
steps in seconds, number of episodes, pack and level:

```bash
uv run python -m townlet.demo.live_inference \
    runs/L1_full_observability/<timestamp>/checkpoints 8766 0.2 10000 \
    configs/default_curriculum L1_full_observability
```

## Writing a universe

A config pack is a directory of YAML declarations. The compiler identifies each declaration by
its content, not its filename, and searches nested directories, so the layout below is a
convention rather than a rule. Declarations under `levels/<level>/` apply to that level; the rest
apply to the whole pack.

```text
configs/default_curriculum/
  experiment.yaml       # declared levels and experiment identity
  stratum.yaml          # spatial topology, shared by every level
  environment.yaml      # meter types, cascade/modulation graphs, affordance vocabulary
  actions.yaml          # movement and custom actions
  brain.yaml            # network, optimizer, loss, Q-learning and replay
  variables.yaml        # typed state, access policies and item profiles
  items.yaml            # optional item catalog
  effects.yaml          # optional effect catalog
  transition_rules.yaml # optional per-tick transition rules
  levels/<level>/
    curriculum.yaml     # vision and temporal settings
    bars.yaml           # meters, bounds and cascades
    affordances.yaml    # costs, interactions, opening hours and placement
    drive.yaml          # reward function
    training.yaml       # training hyperparameters and enabled actions
```

A pack must declare experiment, stratum, environment, actions, brain and variables; each level
must declare curriculum, bars, affordances, drive and training. Every behavioural parameter has to
be stated explicitly: there are no hidden defaults, and unknown keys are rejected. The
demonstration pack in `configs/default_curriculum` is a small survival world (eight meters,
fourteen affordances, an 8×8 grid). It is an example of what can be built, not a limit on it.

### Space

The demonstration pack's `stratum.yaml`:

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

Other substrate types are `gridnd` (4 to 8 dimensions), `continuous`, `continuousnd` and
`aspatial`. Boundaries can clamp, wrap, bounce or stick, and distances can be Manhattan,
Euclidean or Chebyshev. In August 2026 the survival rules were moved onto a six-dimensional
grid by editing configuration alone; `configs/test/gridnd_4d_pack` is a shipped four-dimensional
example. See [Strata](docs/architecture/STRATA.md).

### State

Variables are declared with a scope (`global`, `agent`, `item` or `affordance`), type, lifetime,
initial value and explicit access policy. A training batch is N independent single-agent worlds,
so `global` means one value per world. This variable is readable and writable only by the engine
and is never shown to the agent:

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

Reading and observing are separate: a variable is only in the observation when it declares
`exposed_to: [agent]`. These policies control what the agent can read and observe, but they do not
make hidden state secret. A reward that depends on a hidden value can still leak information about
it. See [variables](docs/config-schemas/variables.md).

### Expressions and transition rules

Variable expressions, action writes, transition rules, effects and item spawn rules share one
expression language with one way to name each thing: a bare `x` is a registry variable, `bar.m`
is a meter and `item.x` is the state of the bound item. Any other spelling is refused at compile
time with the accepted one named. Expressions can read history (`lag`, `delta`, `ema`,
`moving_average`, edge detectors), draw reproducible randomness (`uniform`, `normal_dist`, a pure
function of seed, episode, tick, site and world) and measure distances to affordances.
Pack-level `transition_rules` write variables or meters at a declared phase each tick. See
[expressions](docs/config-schemas/expressions.md) and
[transition rules](docs/config-schemas/transition_rules.md).

### Rewards

Rewards are declared in `drive.yaml` and combined as
`extrinsic + intrinsic × effective_intrinsic_weight + shaping`:

```yaml
drive:
  version: '1.0'
  modifiers:
    energy_crisis:
      bar: energy
      ranges:
      - {name: range_0, min: 0.0, max: 0.2, multiplier: 0.0}
      - {name: range_1, min: 0.2, max: 1.0, multiplier: 1.0}
  extrinsic:
    type: constant_base_with_shaped_bonus
    base_reward: 0.01
    bar_bonuses:
    - {bar: energy, center: 0.0, scale: 0.5}
    - {bar: health, center: 0.0, scale: 0.5}
    variable_bonuses: []
    apply_modifiers: []
  intrinsic:
    strategy: adaptive_rnd
    base_weight: 0.1
    apply_modifiers: [energy_crisis]
    adaptive_config: {enabled: true, threshold: 100.0, decay_rate: 0.995, min_weight: 0.01}
  shaping:
  - {type: approach_reward, weight: 0.01, target_affordance: EAT, max_distance: 5.0}
  - {type: completion_bonus, weight: 0.1, affordance: SLEEP}
  composition: {normalize: false, clip: null, log_components: true, log_modifiers: true}
```

See [Drive as Code](docs/config-schemas/drive_as_code.md) for the full vocabulary.

## Reproducibility

Every compiled universe and checkpoint carries content hashes. Before it loads weights, a
training resume or a checkpoint server compares the checkpoint format, the selected level, the
reward function, the effective brain, the variable layout, the observation contract and the
content hashes of every pack and level declaration, and refuses on any mismatch. Changing
`boundary: clamp` to `wrap`, for example, stops a run from resuming.

Observations are typed tokens, and the token type schema is the transfer contract. Every
compilable shipped level, across 2-D and 3-D grids, N-dimensional grids, continuous and aspatial
worlds, has the same `token_type_schema_hash`, while the observation width ranges from 19 to 474.

Townlet is being rebuilt behind a frozen reference implementation, the *oracle*, pinned at the
`oracle-2026-08-17` tag. A differential harness runs both side by side on the same inputs and
compares their observation, action, reward and done streams:

```bash
uv run python -m townlet.oracle.harness --cell default_curriculum:L0_0_minimal
```

The harness fails on any difference not registered in
[known divergences](docs/oracle/known-divergences.md). The oracle is a reference for preserved
behaviour, not a merge gate. See [the oracle rules](docs/oracle/ORACLE.md).

## Development

```bash
uv run ruff check .
uv run black --check src tests
uv run mypy src/townlet --show-error-codes
uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt \
    --ratchet .defaults-ratchet
uv run python scripts/validate_compiler_cli.py
uv run pytest -n auto
```

The ratchet pins the number of whitelisted defaults: removing one means lowering
`.defaults-ratchet` in the same change. Pytest deselects the wall-clock `perf` tests by default.

GitHub Actions runs lint, config validation and the test suite on every pull request, plus a
nightly full run. The frontend has its own `npm test` and `npm run build`, which CI does not run
yet. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow.

## Documentation

- [Vision](docs/vision.md): what Townlet is for, who it serves, what it refuses to be, and what
  has been demonstrated so far.
- [Architecture overview](docs/architecture/HLD.md), with companion documents on
  [the compiler](docs/architecture/COMPILER.md), [spatial substrates](docs/architecture/STRATA.md),
  [variables](docs/architecture/VFS.md) and [agent networks](docs/architecture/BAC.md).
- [Config reference](docs/config-schemas/), one page per declaration family.
- [Documentation map](docs/README.md), which says how far each part of `docs/` can be trusted.

## License

MIT. See [LICENSE](LICENSE).
