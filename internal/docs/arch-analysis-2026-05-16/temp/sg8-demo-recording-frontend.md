# SG8 — Demo, Recording, Frontend

Scope: `src/townlet/demo/`, `src/townlet/recording/`, `frontend/`.
Method: source-derived; cited file:line for Python, component name for Vue.

---

## Part A: Demo

**Location:** `src/townlet/demo/` (3,172 LOC, 4 `.py` files + `__init__.py`)

### Responsibility

Demo orchestrates a *live, multi-day training + inference* experience that the
Vue frontend connects to. Three things happen in one process:

1. A vectorized RL training loop runs in a background thread, periodically
   writing PyTorch checkpoints to disk.
2. A FastAPI/uvicorn WebSocket server runs in a second thread, watches the
   checkpoint directory, hot-loads the newest weights, and runs *inference*
   episodes at human-watchable speed, broadcasting state frames to all
   connected browser clients.
3. A SQLite database (`metrics.db`) records per-episode metrics and recording
   index entries.

The frontend (Vue dev server, port 5173) is documented as a separate process
the operator runs by hand; `unified_server.py:441` does have a
`_start_frontend()` subprocess helper, but `start()` does not call it — only
the training and inference threads are started.

### Files

| File | LOC | Purpose |
|------|-----|---------|
| `__init__.py` | 1 | Package marker. |
| `database.py` | 410 | SQLite schema + DAO. |
| `unified_server.py` | 546 | Process-level orchestrator. Two threads (training, inference). |
| `runner.py` | 960 | `DemoRunner` — the actual training loop, checkpointing, recorder wiring. |
| `live_inference.py` | 1,255 | `LiveInferenceServer` — FastAPI WebSocket server, inference loop, replay endpoint. |

### `UnifiedServer` (`unified_server.py:32`)

Threading model:

- `_run_training()` (`unified_server.py:334`) runs in `TrainingThread`
  (`daemon=False`, explicit join required). Instantiates a `DemoRunner` and
  calls `runner.run()`. On exception, sets `shutdown_requested = True`.
- `_run_inference()` (`unified_server.py:377`) runs in `InferenceThread`
  (`daemon=True`). Creates a `LiveInferenceServer`, wraps it in
  `uvicorn.Config(host="0.0.0.0", port=self.inference_port, ...)`, and runs
  `server.serve()` inside an asyncio event loop owned by that thread.
  The uvicorn `Server` is stashed on `self._inference_uvicorn_server` so
  `stop()` can set `should_exit = True` for graceful shutdown
  (`unified_server.py:307`).
- The main thread `start()` (`unified_server.py:115`) ticks once per second,
  monitoring thread liveness and `shutdown_requested`. It also writes a
  config snapshot under `<run_root>/config_snapshot/`
  (`unified_server.py:97`) and adds a file handler logging to
  `<run_root>/training.log` (`unified_server.py:255`).
- `_determine_run_directory()` (`unified_server.py:220`) demands an explicit
  `run_metadata.output_subdir` from the training config; there are no
  implicit defaults. Run directory: `runs/<subdir>/<YYYY-MM-DD_HHMMSS>/`.
- `_start_frontend()` / `_stop_frontend()` exist (`unified_server.py:441`,
  `:522`) but are not invoked by `start()`. The docstring at the head of
  the file claims frontend runs as a subprocess; the implementation has
  drifted from the docstring.

How training reaches the broadcast: it doesn't, directly. `DemoRunner`
writes `checkpoint_ep{N:05d}.pt` files under `<run_root>/checkpoints/`.
`LiveInferenceServer` polls that same directory for the highest-numbered
file (`live_inference.py:419`); when it sees a new one it calls
`safe_torch_load` and `q_network.load_state_dict(...)`
(`live_inference.py:443-449`). So the bridge between the training step and
the broadcast is the filesystem, not in-memory state.

### `LiveInferenceServer` (`live_inference.py:73`)

FastAPI app with one WebSocket route registered twice for compatibility:
`/ws` and `/ws/training` (`live_inference.py:173-174`). CORS is wide open
(`allow_origins=["*"]`).

Lifecycle:

- `startup` hook (`live_inference.py:245`) calls
  `_initialize_components()` (`:290`), which uses `UniverseCompiler` to
  build a `CompiledUniverse` from `config_dir`, then constructs the same
  `VectorizedHamletEnv`, `VectorizedPopulation`, curriculum, and
  exploration that `DemoRunner` uses — but for inference only. After that
  it calls `_check_and_load_checkpoint()` to pick up the latest weights.
- `websocket_endpoint` (`live_inference.py:514`) accepts a client, adds it
  to `self.clients: set[WebSocket]`, sends a `connected` frame, then loops
  receiving JSON commands.

Client → server commands (`_handle_command`, `live_inference.py:551`):

- `play`, `pause`, `step`, `reset` — control inference (or replay) loop.
- `refresh_checkpoint` — manually re-scan checkpoint dir.
- `toggle_auto_checkpoint` — flip `auto_checkpoint_mode`; when on,
  `_check_and_load_checkpoint()` is called before each new episode.
- `set_speed` — `step_delay = 0.2 / speed`.
- `load_replay`, `list_recordings`, `replay_control` — replay mode.

Server → client frame types (broadcast via `_broadcast_to_clients`,
`live_inference.py:955`):

- `connected` — initial handshake with `substrate` metadata, `action_labels`,
  `total_episodes`, current epsilon (`live_inference.py:520`).
- `model_loaded` — emitted when a newer checkpoint is hot-loaded
  (`live_inference.py:501`).
- `episode_start` — per-episode setup with `curriculum_stage`,
  `curriculum_multiplier`, `telemetry`, `substrate` (`live_inference.py:697`).
- `state_update` — per-step frame with `grid`, `agent_meters`, `q_values`,
  `action_masks`, `affordance_stats`, optional `temporal` block
  (`live_inference.py:858`).
- `episode_end` — per-episode summary with `total_reward`,
  `final_meters`, `affordance_stats`, `agent_age`,
  `lifetime_progress` (`live_inference.py:770`).
- `replay_loaded`, `replay_finished` — replay mode boundary frames.
- `recordings_list` — list of available recordings.
- `auto_checkpoint_mode` — mode change ack.

The inference loop (`_run_inference_loop`, `live_inference.py:630`) runs
episodes back-to-back, sleeping `step_delay` between steps (default 0.2s
= 5 steps/sec). Q-values are also written line-by-line to
`qvalues_inference.log` in the working directory (`live_inference.py:276`,
`:849`) for offline debugging.

Replay mode shares the same WebSocket — a `load_replay` command swaps the
server into `mode="replay"`, after which `play`/`pause`/`step`/`seek`
operate on a `ReplayManager` (from `townlet.recording.replay`) rather than
the live env. The replay frame shape is a near-clone of `state_update`
with a `replay_metadata` block and `"mode": "replay"`
(`live_inference.py:1144`).

### `DemoRunner` (`runner.py:38`)

Standalone training driver. Highlights:

- Constructor (`runner.py:45`) requires `level_name` explicitly — legacy
  single-file `training.yaml` was removed (`runner.py:75`).
- `_validate_checkpoint_compatibility()` (`runner.py:164`) refuses to
  resume checkpoints that lack `substrate_metadata` — a deliberate hard
  break (no backwards compat).
- Context manager (`runner.py:239`, `:243`) wraps `_cleanup()` which closes
  recorder, DB, TensorBoard logger (matches the `DemoRunner` context-
  manager guidance in CLAUDE.md).
- `save_checkpoint()` (`runner.py:265`) packs `version: 3` checkpoints
  containing population state, optimizer, replay buffer, curriculum state,
  affordance layout, brain hash, training config, and the universe
  metadata. Saved as `checkpoint_ep{N:05d}.pt`.
- Recording is wired in lazily — `runner.py:516` imports
  `EpisodeRecorder` only if recording is enabled in the training config,
  and `runner.py:758` emits an `EpisodeMetadata` per episode.

Intervals: `HEARTBEAT_INTERVAL = 10`, `SUMMARY_INTERVAL = 50`,
`CHECKPOINT_INTERVAL = 100` (`runner.py:41`).

### `DemoDatabase` (`database.py:8`)

SQLite (`check_same_thread=False`, WAL mode — `database.py:27`) with the
following tables:

- `episodes` — per-episode summary row (survival, total/extrinsic/intrinsic
  reward, intrinsic weight, curriculum stage, epsilon, observation schema
  hash) — `database.py:50`.
- `affordance_visits` — `(episode_id, from_affordance, to_affordance,
  visit_count)` — used by the frontend's "garden path" / affordance graph.
- `position_heatmap` — `(episode_id, x, y, visit_count, novelty_value)`.
- `system_state` — generic K/V (e.g., last training step).
- `episode_recordings` — index into the on-disk msgpack/LZ4 recording
  files (file path, sizes, recording reason, plus a denormalised copy of
  episode summary fields) — `database.py:88`.

Lifecycle: idempotent `close()`, `__enter__/__exit__/__del__` all
provided (`database.py:388–408`).

### Entry point: `scripts/run_demo.py`

Top of file:

- Requires `--config <experiment-dir>`, `--level <level-name>`,
  `--inference-port <port>`; `--episodes`, `--checkpoint-dir`,
  `--force-new-vfs`, `--debug` are optional (`run_demo.py:62–100`).
- Imports `UnifiedServer` and calls `.start()`. No CLI arg drives the
  frontend; the script's epilog tells the operator to run
  `cd frontend && npm run dev` manually.

### Dependencies

**Inbound:**

- `scripts/run_demo.py` → `townlet.demo.unified_server.UnifiedServer`.
- `townlet.recording.video_export` → `townlet.demo.database.DemoDatabase`
  (recording's video CLI reuses the demo DB).
- `townlet.recording.replay` → `townlet.demo.database` (TYPE_CHECKING only).

**Outbound (from demo modules):**

- `townlet.config.{training_v2_config, brain_config}`
- `townlet.curriculum.{factory, adversarial}`
- `townlet.environment.vectorized_env.VectorizedHamletEnv`
- `townlet.population.vectorized.VectorizedPopulation`
- `townlet.exploration.adaptive_intrinsic.AdaptiveIntrinsicExploration`
- `townlet.training.{checkpoint_utils, state, tensorboard_logger}`
- `townlet.universe.{compiler, compiled}`
- `townlet.substrate.{grid2d, grid3d, gridnd, continuous, aspatial}`
  (only for runtime `isinstance` dispatch in metadata builders)
- `townlet.recording.{recorder, replay, data_structures}`

Third-party: `torch`, `fastapi`, `uvicorn`, `sqlite3` (stdlib), `signal`,
`threading`, `asyncio`.

---

## Part B: Recording

**Location:** `src/townlet/recording/` (1,603 LOC, 7 `.py` files + `__init__.py`)

### Responsibility

Episode-level trajectory persistence. Captures step-by-step state from the
training loop, evaluates configurable selection criteria, and serialises
chosen episodes to msgpack+LZ4 files indexed in the demo SQLite DB. Also
ships a CLI for rendering selected episodes to MP4 via matplotlib + ffmpeg.

The recorder is non-blocking: training thread pushes
`RecordedStep`/`EpisodeEndMarker` items onto a bounded `queue.Queue`; a
daemon writer thread drains the queue, evaluates criteria at episode
boundary, and writes to disk.

### Files

| File | LOC | Purpose |
|------|-----|---------|
| `__init__.py` | 1 | Package marker. |
| `data_structures.py` | 108 | `RecordedStep`, `EpisodeMetadata`, `EpisodeEndMarker` dataclasses + msgpack deserializers. |
| `recorder.py` | 307 | `EpisodeRecorder` (producer) + `RecordingWriter` (consumer thread). |
| `criteria.py` | 224 | `RecordingCriteria` — periodic / stage_transitions / performance / stage_boundaries selectors. |
| `replay.py` | 222 | `ReplayManager` — loads, decompresses, streams a single episode. |
| `video_renderer.py` | 342 | `EpisodeVideoRenderer` — matplotlib frame rendering. |
| `video_export.py` | 252 | Single + batch MP4 export, drives ffmpeg via `subprocess`. |
| `__main__.py` | 147 | `python -m townlet.recording …` CLI: `export` and `batch` subcommands. |

### On-disk format

Per recorded episode, one file:

```
<output_dir>/episode_{episode_id:06d}.msgpack.lz4
```

Encoding pipeline (`recorder.py:265–292`):

```
episode_data = {
    "version": 1,
    "metadata": asdict(EpisodeMetadata),
    "steps": [asdict(RecordedStep), ...],
    "affordances": metadata.affordance_layout,
}
serialized = msgpack.packb(episode_data, use_bin_type=True)
compressed = lz4.frame.compress(serialized, compression_level=0)
file_path.write_bytes(compressed)
```

LZ4 frame format, fastest compression level (0). Compression toggleable via
`config["compression"]` ("lz4" or anything else for none).

`RecordedStep` (`data_structures.py:48`, frozen dataclass with `slots=True`,
~100–150 bytes/step per the comment):

```
step: int
position: tuple[int, ...]      # (x,y) / (x,y,z) / ()
meters: tuple[float, ...]      # 8 normalized [0,1] (size varies by config)
action: int
reward: float                  # extrinsic
intrinsic_reward: float
done: bool
q_values: tuple[float, ...] | None
epsilon: float | None
action_masks: tuple[bool, ...] | None
time_of_day: int | None        # temporal mechanics
interaction_progress: float | None
```

`EpisodeMetadata` (`data_structures.py:75`):

```
episode_id, survival_steps, total_reward, extrinsic_reward,
intrinsic_reward, curriculum_stage, epsilon, intrinsic_weight, timestamp,
affordance_layout: dict[str, tuple[int, ...]],
affordance_visits: dict[str, int],
custom_action_uses: dict[str, int],
```

`deserialize_step` / `deserialize_metadata` (`data_structures.py:11`, `:31`)
reconstruct the dataclasses from msgpack output, converting lists back to
tuples (msgpack does not preserve tuple vs list).

### Queue + writer thread

`EpisodeRecorder.__init__` (`recorder.py:29`) creates a bounded
`queue.Queue(maxsize=max_queue_size)` (default 1000) and a daemon thread
running `RecordingWriter.writer_loop`. Producer side: `record_step` clones
GPU tensors to Python tuples and calls `queue.put_nowait`. On overflow it
logs a warning and *drops the frame* (graceful degradation —
`recorder.py:141`).

`finish_episode` (`recorder.py:145`) pushes an `EpisodeEndMarker`. On the
consumer side (`writer_loop`, `recorder.py:199`):

```
while running:
    item = queue.get(timeout=0.1)
    if isinstance(item, RecordedStep):
        self.episode_buffer.append(item)
    elif isinstance(item, EpisodeEndMarker):
        self._process_episode_end(item.metadata)
        self.episode_buffer.clear()
```

`_should_record_episode` (`recorder.py:242`) currently only checks the
`periodic` criterion (Phase 1 implementation, comment in source). The full
`RecordingCriteria` evaluator in `criteria.py` supports four families:

- **periodic** — every N episodes (`criteria.py:39`).
- **stage_transitions** — record M episodes before and N after a curriculum
  stage change (`criteria.py:40`).
- **performance** — record top/bottom percentile within a sliding window
  of episode-summary stats (`criteria.py:49`, deque of `EpisodeMetadata`).
- **stage_boundaries** — first/last N episodes at each stage
  (`criteria.py:42`).

OR-logic across criteria; first match wins.

### `ReplayManager` (`replay.py:20`)

Used by both the live inference server (replay endpoint) and the video
exporter. `load_episode(episode_id)`:

1. Queries `DemoDatabase.get_recording(episode_id)` for the relative file
   path.
2. Reads + LZ4-decompresses + msgpack-unpacks.
3. Caches `self.steps: list[dict]`, `self.metadata: dict`,
   `self.affordances: dict`.

Step access is index-based: `current_step_index`, `next_step()`, `seek()`,
`reset()`, `is_at_end()` — straight forward cursor over the deserialized
step list.

### Video export

CLI: `python -m townlet.recording.__main__ {export|batch} …`
(`__main__.py:24`). Both subcommands need `--database` and `--recordings`.
`video_export.export_episode_video` (`video_export.py:20`) uses a
`ReplayManager` plus `EpisodeVideoRenderer` (matplotlib with `Agg`
backend — `video_renderer.py:13`) to render PNG frames into a tempdir,
then invokes `ffmpeg` via `subprocess` to mux them into an MP4.

`AFFORDANCE_COLORS` and `METER_COLORS` in `video_renderer.py:22-43` are
defined separately from the frontend tokens — *the colour palettes are
not shared*; this is a small duplication.

### Dependencies

**Inbound:**

- `townlet.demo.runner` → `EpisodeRecorder`, `EpisodeMetadata`.
- `townlet.demo.live_inference` → `ReplayManager`.

**Outbound:**

- `townlet.demo.database.DemoDatabase` (replay query, recording insert).
- `lz4.frame`, `msgpack`, `torch` (for tensor.tolist() in producer), and
  for video: `matplotlib`, `numpy`, plus `subprocess` to ffmpeg.

No imports of `townlet.environment` or `townlet.population` — recording
treats step data as POD.

---

## Part C: Frontend

**Location:** `frontend/` (10,432 LOC Vue, 27 components, one Pinia store)

### Stack

Confirmed from source (no `package.json` in the tree, see Concerns):

- Vue 3 SFCs with `<script setup>`. `main.js` imports `createApp` and
  `App.vue` (`main.js:1-3`).
- **Pinia** is in use — `main.js:2,8,10` creates and registers it; the
  store is `defineStore('simulation', ...)` (`simulation.js:4`).
- **Vite** as bundler — `vite.config.js` registers `@vitejs/plugin-vue`,
  dev server bound to `0.0.0.0:5173` with no proxy
  (`vite.config.js:5-11`).
- No router — the app is a single `App.vue` shell.
- `index.html` is the only entry HTML (`demo.html` also present but
  unused by the Vite config); both reference `/src/main.js`.

### Component inventory (27 components, one-line each)

Spatial rendering / overlays:

- `Grid.vue` — SVG 2D grid with cells, affordances, agent dots, agent
  trails, heat-map overlay (`Grid.vue:1-117`).
- `AspatialView.vue` — Meters-only dashboard for aspatial substrates
  (no grid).
- `NoveltyHeatmap.vue` — SVG novelty heatmap (RND novelty per cell).
- `InteractionProgressRing.vue` — Animated SVG ring around the agent for
  multi-tick interactions.
- `ZoomControl.vue` — Range slider that drives `simulation.gridZoom`.

Meters / agent state:

- `MeterPanel.vue` — Primary 8-meter bar panel.
- `ProjectedRewardBar.vue` — Real-time step-reward indicator (0–1).
- `TimeOfDayBar.vue` — Day/night cycle indicator (top-left).
- `AgentBehaviorPanel.vue` — Action / Q-values / affordance-use breakdown
  ("Agent Behaviour" panel).
- `IntrinsicRewardChart.vue` — Last-100-steps extrinsic vs intrinsic
  reward chart.

Controls / connection:

- `Controls.vue` — Full controls panel: connection status + commands.
- `MinimalControls.vue` — Compact top-right control cluster (refresh
  checkpoint, toggle auto-checkpoint, etc.).
- `CheckpointProgress.vue` — Progress bar showing `checkpoint_episode /
  checkpoint_total_episodes`.

Curriculum / exploration / progress:

- `CurriculumTracker.vue` — Curriculum stage (1–5) with description.
- `EpsilonProgress.vue` — Exploration→exploitation epsilon indicator.

Telemetry / charts:

- `SurvivalTrendChart.vue` — Avg survival per 100 episodes.
- `StatsPanel.vue` — Episode info (current episode, step, reward).
- `AffordanceGraph.vue` — Affordance transition graph (learned routines).
- `AffordanceLegend.vue` — Affordances guide / legend.

Event logs / certificates:

- `CriticalEventLog.vue` — Critical events feed (low-meter / dying state).
- `DeathCertificates.vue` — Death-certificate cards per episode.
- `FailurePanel.vue` — Failure log with refresh control.

Generic UI primitives:

- `EmptyState.vue` — Empty-state placeholder.
- `LoadingState.vue` — ARIA live-region loading placeholder.
- `ErrorState.vue` — ARIA alert error placeholder.
- `InfoTooltip.vue` — Hover/focus info-icon tooltip wrapper.
- `ReferencePanel.vue` — Collapsible reference panel (toggle button).

### Store: `frontend/src/stores/simulation.js`

Single Pinia store; 668 lines. State broken into groups:

- **WebSocket** — `ws`, `isConnected`, `isConnecting`, `connectionError`,
  `reconnectAttempts` (max 10, `reconnectDelay = 3000ms`),
  `manualDisconnect`, `serverAvailability`
  (`simulation.js:6-23`).
- **Simulation** — `currentEpisode`, `currentStep`, `cumulativeReward`,
  `lastAction`.
- **Training** — `isTraining`, `totalEpisodes`, `trainingMetrics` (avgReward5,
  avgLength5, avgLoss5, epsilon, bufferSize).
- **Checkpoint progress** — `checkpointEpisode`, `checkpointTotalEpisodes`,
  `autoCheckpointMode`.
- **Grid** — `gridWidth`, `gridHeight`, `agents`, `affordances`, `gridZoom`.
- **Substrate** — `substrateType`, `substratePositionDim`, `substrateMetadata`.
- **Agent / chart data** — `agentMeters`, `heatMap`, `episodeHistory`
  (capped at 10), `deathCertificates` (capped at 20), `availableModels`,
  `rndMetrics`, `transitionData`, `actionLabels`, `qValues`, `actionMasks`,
  `affordanceStats`.
- **Temporal** — `temporalEnabled`, `timeOfDay`, `interactionProgress`,
  `agentAge`, `lifetimeProgress`.
- **Misc** — `stepReward`.

Computed: `averageSurvivalTime` (mean over `episodeHistory`).

Actions:

- `checkServerAvailability()` — probes `/ws` and `/ws/training` on port
  8766 by opening short-lived WebSockets (`simulation.js:112-146`).
- `connect(mode)` — opens the WebSocket, registers `onopen/onclose/
  onerror/onmessage`, auto-reconnects up to 10 times with 3s delay
  unless `manualDisconnect`. On open, calls `sendCommand('play')` after
  100ms — *auto-starts the simulation* (`simulation.js:184`).
- `disconnect()` — manual close.
- `handleMessage(msg)` — central switch on `message.type`.
- `updateState(msg)`, `handleEpisodeComplete(msg)`, `handleEpisodeEnd(msg)`,
  `createDeathCertificate(msg, affordanceStats)` — message handlers.
- `sendCommand(command, params)` — JSON encode + `ws.send`.
- `setSpeed`, `setZoom`, `loadModel`, `refreshCheckpoint`,
  `toggleAutoCheckpoint`, `startTraining` — UI-facing command wrappers.

### WebSocket protocol

URL derivation (`simulation.js:158-164`):

```
protocol = (location.protocol === 'https:') ? 'wss:' : 'ws:'
host     = location.hostname
port     = 8766
endpoint = '/ws'
wsUrl    = `${protocol}//${host}:${port}/ws`
```

The store always connects to port **8766** and endpoint **/ws** regardless
of `connectionMode`. `checkServerAvailability` also probes `/ws/training`
but `connect` does not actually use it.

**Server → client** (frame shapes match `live_inference.py`):

| `message.type` | Carried fields (from handler) | Source |
|---|---|---|
| `connected` | `available_models`, `action_labels`, `checkpoint_episode`, `total_episodes`, `epsilon`, `auto_checkpoint_mode`, `substrate`, `action_labels` | `simulation.js:254`, server `live_inference.py:520` |
| `training_status` | `is_training`, `current_episode`, `total_episodes` | `simulation.js:275` |
| `training_started` | `num_episodes` | `simulation.js:281` |
| `episode_start` | `episode`, `epsilon`, `checkpoint_episode`, `total_episodes` | `simulation.js:287` |
| `state_update` | `step`, `cumulative_reward`, `grid`, `agent_meters`, `q_values`, `action_masks`, `affordance_stats`, `heat_map`, `rnd_metrics`, `affordance_graph`, `temporal`, `step_reward`, `epsilon`, `checkpoint_episode`, `total_episodes`, `substrate` | `simulation.js:306`, `updateState` `:359` |
| `episode_complete` | `episode`, `length`, `reward`, `avg_reward_5`, `avg_length_5`, `avg_loss_5`, `epsilon`, `buffer_size`, `loss` | `simulation.js:310`, `handleEpisodeComplete` `:453` |
| `episode_end` | `episode`, `steps`, `total_reward`, `reason`, `final_meters`, `affordance_stats` | `simulation.js:314`, `handleEpisodeEnd` `:479` |
| `training_complete` | — | `simulation.js:318` |
| `model_loaded` | `model`, `episode`, `total_episodes`, `epsilon` | `simulation.js:323` |
| `auto_checkpoint_mode` | `enabled` | `simulation.js:337` |
| `paused`, `resumed` | — | `simulation.js:342-348` |
| `error` | `message` | `simulation.js:350` |

Replay-mode frames (`replay_loaded`, `recordings_list`, `replay_finished`,
`state_update` with `mode="replay"`) are sent by the server but not
handled in the store — the store has no replay UI surface; replay is
addressable via direct `sendCommand` calls and the matching server logic
exists, but no component path consumes the replay frames.

**Client → server** commands (all wrapped in `{ command, ...params }`):

| Command | Params | Sent by |
|---|---|---|
| `play` | — | auto on connect, `Controls.vue` |
| `pause` | — | `Controls.vue` |
| `step` | — | controls |
| `reset` | — | controls |
| `set_speed` | `speed: number` | `setSpeed()` |
| `load_model` | `model: string` | `loadModel()` |
| `refresh_checkpoint` | — | `refreshCheckpoint()` / `MinimalControls.vue` |
| `toggle_auto_checkpoint` | — | `toggleAutoCheckpoint()` / `MinimalControls.vue` |
| `start_training` | `num_episodes, batch_size, buffer_capacity, show_every, step_delay` | `startTraining()` |

Replay commands (`load_replay`, `list_recordings`, `replay_control`) are
not currently emitted from the store; the server handlers exist
(`live_inference.py:969–1073`) but no JS path drives them.

### Design tokens (`frontend/src/styles/tokens.js`)

Single source of truth, exported as `tokens`:

- **Palette** — dark theme: `backgroundPrimary #1e1e2e`,
  `backgroundSecondary #2a2a3e`, `backgroundTertiary #3a3a4e`;
  text `#e0e0e0 / #a0a0b0 / #808090 / #6a6a7a / #ffffff`.
- **Interactive / status** — primary `#10b981` (emerald), warning
  `#f59e0b`, error `#ef4444` (+`#dc2626` hover, `#b91c1c` dark),
  info `#3b82f6`.
- **Meter colours** — energy `#10b981`, hygiene `#06b6d4`, satiation
  `#f59e0b`, money `#8b5cf6`, mood (high/mid/low =
  `#3b82f6/#f59e0b/#ef4444`), social `#ec4899`.
- **Affordance stroke colours** — light indigo, cyan, amber, light red,
  purple, pink, emerald — used by `Grid.vue`.
- **Spacing** — `xs/sm/md/lg/xl/2xl` (0.25 → 3 rem).
- **Typography** — sizes `xs/sm/base/lg/xl/2xl` (0.75 → 1.5 rem);
  weights normal/medium/semibold/bold.
- **Layout** — `leftPanelWidth: 320px`, `rightPanelWidth: 380px`,
  `maxGridSize: 600px`, `headerHeight: 70px`.
- **Border radius / transitions / breakpoints / a11y / z-index** —
  standard scale.
- `tokensToCSS()` helper generates CSS custom properties; the comment
  notes `variables.css` is hand-maintained in parallel
  (`tokens.js:163-165`).

### Constants (`frontend/src/utils/constants.js`)

- `CELL_SIZE = 100` — px per grid cell; 8×8 grid = 800px total.
- `ACTION_ICONS` — numeric `0..4` and string-keyed mappings: `↑ Up`,
  `↓ Down`, `← Left`, `→ Right`, `⚡ Interact` (only 5 entries despite
  the 8-action global vocabulary — see Concerns).
- `AFFORDANCE_ICONS` — current v2.1 all-caps ids (`EAT`, `SLEEP`,
  `SHOWER`, `EXERCISE`, `WORK`, `SOCIALIZE`, `MEDITATE`, `DRINK_WATER`,
  `BRUSH_TEETH`, `LAUNDRY`, `COOK`, `CLEAN_HOUSE`, `ENTERTAINMENT`,
  `DOCTOR`) *plus* a parallel set of legacy camel-case keys (`Bed`,
  `Shower`, `Fridge`, `Job`, ...). Both kept in one map — dual-support
  for transitional config packs.
- `METER_THRESHOLDS`: CRITICAL 20 / LOW 30 / MODERATE 60 / HEALTHY 80.
- `MOOD_THRESHOLDS`: LOW 30 / MODERATE 60 / HIGH 80 (mood is
  higher-is-better).

### Concerns

1. **No `package.json` in the tree.** `frontend/` has `vite.config.js`,
   `index.html`, `demo.html`, `.nvmrc`, and `src/`, but no
   `package.json`, no `package-lock.json`, no `node_modules/`. `npm run
   dev` (referenced from `unified_server.py:469` and `run_demo.py`'s
   help epilog) cannot work in this checkout without one. Either it is
   `.gitignore`'d, lives outside the snapshot, or has been deleted —
   regardless, the documented workflow is broken at the file level.

2. **Pyproject lists both FastAPI and Flask.** `pyproject.toml` declares
   `fastapi>=0.100.0`, `uvicorn[standard]>=0.23.0`, `websockets>=11.0`,
   plus `flask>=3.0.0` and `flask-cors>=4.0.0`. A grep across `src/`
   for `flask` and `Flask(` returns nothing. The demo subsystem uses
   only FastAPI + uvicorn; the Flask dependencies are dead weight that
   should be removed. (`msgpack` and `lz4` appear twice — once with
   each version pin — separate redundancy.)

3. **CORS wide open.** `CORSMiddleware(allow_origins=["*"],
   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])`
   (`live_inference.py:165`). Fine for a localhost dev demo, not fine
   if the host is ever exposed beyond localhost. The uvicorn server is
   bound to `0.0.0.0` (`unified_server.py:417`,
   `live_inference.py:1231`), which is exposure-friendly by default.

4. **Frontend subprocess code is dead.** `_start_frontend()` /
   `_stop_frontend()` exist in `unified_server.py:441-547` but `start()`
   never invokes them. The class docstring at line 32 still claims a
   "Frontend Subprocess" component. Either delete the methods or wire
   them in.

5. **`ACTION_ICONS` only has 5 entries** (`constants.js:11-24`). The
   global action vocabulary is 8 actions for Grid2D, 10 for Grid3D, 16
   for GridND, 4 for aspatial. Anything beyond index 4 will render
   without an icon. The server sends `action_labels` at connection time
   (`live_inference.py:521`) and the store captures them
   (`simulation.js:257`), but `constants.js` still hardcodes a partial
   map — there is duplication and the hardcoded copy is stale.

6. **Replay UI is server-only.** Replay command handlers exist on the
   server (`live_inference.py:969-1073`) and `ReplayManager` is a
   first-class module, but no Vue component sends `load_replay` or
   `list_recordings`, and no handler in the store consumes
   `replay_loaded`, `recordings_list`, or `replay_finished`. The
   feature is half-built on the frontend side.

7. **Per-step `qvalues_inference.log` is written to the process CWD**
   (`live_inference.py:157`). No path control. Long demo runs will
   accumulate at the CWD of whoever launched the server.

8. **Q-value debug log spam.** `simulation.js:410-411` does
   `console.log('[DEBUG Q-VALUES] ...')` on every state_update. At 5
   steps/sec for a long session this is noticeable — leftover debug.

9. **Duplicate palette.** `video_renderer.py:22-43` defines
   `AFFORDANCE_COLORS` and `METER_COLORS` independently of
   `tokens.js`. If one drifts, exported videos won't match the
   frontend.

10. **Recording criteria not fully wired.** `recorder.py:242-263`
    explicitly comments "For now, just check periodic criterion. Full
    criteria evaluator will be implemented in Phase 2." `criteria.py`
    contains a much richer `RecordingCriteria` class that is *not*
    referenced from the writer thread. Stage-transition, performance,
    and stage-boundary criteria are configured-but-not-honoured.

11. **`DemoDatabase.insert_recording` reason is hardcoded.**
    `recorder.py:300` writes `reason="periodic"` for every recording,
    regardless of which criterion actually matched. Tied to (10).

12. **`flush_episode` only iterates by integer index.**
    `runner.py:262` does `for agent_idx in range(self.population.num_agents)`
    — fine for now, but `agent_ids` is a string list. Mixing index- and
    id-based addressing is a smell.

---

## Cross-system dependencies

**Demo imports from (concrete modules cited):**

- `townlet.universe.{compiler, compiled}` — `runner.py:32-33`,
  `live_inference.py:30-31`
- `townlet.environment.vectorized_env` — `runner.py:18`,
  `live_inference.py:21`
- `townlet.population.vectorized` — `runner.py:20`, `live_inference.py:23`
- `townlet.curriculum.{factory, adversarial}` — `runner.py:16`,
  `live_inference.py:18-19`
- `townlet.exploration.adaptive_intrinsic` — `runner.py:19`,
  `live_inference.py:22`
- `townlet.training.{state, replay_buffer (indirect), checkpoint_utils,
  tensorboard_logger}` — `runner.py:21-31`
- `townlet.config.{training_v2_config, brain_config}` — `runner.py:15`,
  `unified_server.py:23`, `live_inference.py:17`
- `townlet.recording.{recorder, replay, data_structures}` —
  `runner.py:516`, `runner.py:758`, `live_inference.py:24`
- `townlet.substrate.{grid2d, grid3d, gridnd, continuous, aspatial}` —
  `live_inference.py:25-28`, `:919-920`

**Recording imports from demo:** `townlet.demo.database.DemoDatabase`
(`video_export.py:13`; `replay.py:15` TYPE_CHECKING). One-way edge
recording → demo for the DB; no edge demo → recording at module level
except the lazy imports in `runner.py`.

**Frontend protocol surface:** Pure WebSocket. URL
`ws://<host>:8766/ws`. No REST endpoints exposed by the FastAPI app —
`live_inference.py` registers only the two WebSocket routes
(`/ws`, `/ws/training`); no `@app.get`/`@app.post` decorators are present.
Message envelope is JSON with a `type` discriminator; frame shapes per
the table in Part C "WebSocket protocol".

---

## Open questions

1. Where does `frontend/package.json` live? Is it `.gitignore`'d, or has
   it been removed? `pnpm-lock.yaml` / `yarn.lock` are also absent.
   Without it the Vite build cannot resolve `vue`, `pinia`, or
   `@vitejs/plugin-vue`.
2. Is Flask intentionally a dependency for something not yet committed
   (a planned management API?), or is it pure cruft from an earlier
   architecture? If cruft, `flask`, `flask-cors`, and one of the two
   `msgpack`/`lz4` declarations in `pyproject.toml` should be removed.
3. Is the replay UI planned, or is it intentional that replay can only
   be driven via direct `sendCommand` calls? If planned, who owns the
   `RecordingsBrowser` component that would call `list_recordings`?
4. `RecordingCriteria` in `criteria.py` is unreferenced from the writer
   thread. Is it dead, or is the writer expected to be retrofitted to
   use it? Same question for `custom_action_uses` in `EpisodeMetadata` —
   never populated by the recorder caller.
5. `_start_frontend()` in `unified_server.py` — keep and wire it, or
   delete? Per CLAUDE.md ("no maintaining unused code paths") deleting
   seems right.
6. Should the qvalue log path move under the run directory rather than
   CWD? The pattern matches `tensorboard/` and `training.log` already
   being placed there.
