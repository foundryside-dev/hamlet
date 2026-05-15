## Orchestration & Periphery (curriculum + recording + demo)

**Location:** `src/townlet/curriculum/`, `src/townlet/recording/`, `src/townlet/demo/`

**Responsibility:** Manage difficulty progression (curriculum), capture training episodes (recording), and host live inference + replay visualization (demo).

### Internal Structure

- **curriculum/** — Strategy pattern for environment difficulty progression
- **recording/** — Asynchronous episode capture, serialization, replay, and video export pipeline
- **demo/** — WebSocket inference server (port 8766), multi-day runner, SQLite state store, unified orchestrator

---

## Curriculum

**Protocol:** `CurriculumManager` abstract base class in `base.py`
- `get_batch_decisions()` — Computes per-agent `CurriculumDecision` once per episode (not per step)
- `checkpoint_state()` / `load_state()` — Serialization for resumption
- `initialize_population(num_agents)` — Per-population setup hook

**Implementations:**

1. **AdversarialCurriculum** (`adversarial.py`)
   - 5-stage progression: Stage 1 (easy, shaped) → Stage 5 (all meters, sparse)
   - Auto-transitions based on per-agent metrics:
     - **Advance:** survival rate >70% AND learning progress >0 AND entropy <0.5 AND min_steps_at_stage met
     - **Retreat:** survival rate <30% OR learning progress <0
   - Tracks `PerformanceTracker` (GPU tensors) with episode rewards, steps, baseline for learning delta
   - Maps stage (1–5) → difficulty_level (0.0–1.0) for external systems
   - Emits `transition_events` for telemetry (stage transitions with reason)
   - v2.1 config: `difficulty_metric`, `adaptation_rate`, `min_difficulty`, `max_difficulty` override mapping

2. **StaticCurriculum** (`static.py`)
   - No-op implementation; all agents receive identical decision for all episodes
   - Used for baseline experiments and interface validation
   - Minimal `_StaticTracker` for logging compatibility

**Integration with Population:**
- `VectorizedPopulation` calls curriculum once per episode after step collection
- Curriculum stage exposed in agent telemetry and database
- Recording criteria can read `curriculum.get_stage_info()` to predict transitions

---

## Recording

**Queue-based Architecture:** Non-blocking async capture via bounded queue + daemon writer thread

**Core Components:**

1. **Recorder** (`recorder.py`)
   - `EpisodeRecorder` — Main interface; spawns `RecordingWriter` thread
   - `record_step(positions, meters, action, reward, done, ...)` — Thread-safe queue push (clones tensors to CPU)
   - Captures: step #, agent position, 8 normalized meters, action, extrinsic + intrinsic rewards, Q-values, epsilon, temporal fields
   - Bounded queue (default 1000) prevents backpressure on training loop

2. **Data Structures** (`data_structures.py`)
   - `RecordedStep` — Frozen dataclass (~100–150 bytes/step); msgpack + lz4 serializable
   - `EpisodeMetadata` — Summary: episode_id, survival, total/extrinsic/intrinsic rewards, curriculum stage, affordance visits + layout
   - `EpisodeEndMarker` — Sentinel for episode boundaries in queue; allows writer to batch-commit

3. **Criteria** (`criteria.py`)
   - Evaluates whether to save episode (OR logic: any criterion triggers save)
   - **periodic:** Every N episodes
   - **stage_transitions:** Before/after curriculum stage changes (uses `curriculum.get_stage_info()` for prediction)
   - **performance:** Top/bottom percentile within rolling window (default 100 episodes)
   - **stage_boundaries:** First/last N episodes at each stage
   - Maintains internal state: `last_stage`, `episode_history`, `stage_episode_counts`

4. **Replay** (`replay.py`)
   - `ReplayManager` — Loads episodes from disk; supports seeking, step-by-step access
   - Returns `RecordedStep` and `EpisodeMetadata` for playback
   - Used by demo/live_inference and video export

5. **Video Export** (`video_export.py`, `video_renderer.py`)
   - `export_episode_video()` — E2E: load episode → render frames → ffmpeg → MP4
   - `EpisodeVideoRenderer` — Matplotlib-based frame rendering; substrate-aware:
     - **Grid2D/Grid3D/GridND:** Spatial grid with agent, affordances, heatmap overlays
     - **AspatialSubstrate:** No position; abstract affordance network or meter-centric view
   - Customizable: fps, speed, dpi, style ("dark"/"light"), auto-detect grid_size
   - Temporary directory pipeline; ffmpeg encodes frames to H.264

**Dependencies:**
- Core: msgpack, lz4 (always available in dependencies)
- Optional `[recording]` extra: ffmpeg-python, pillow, matplotlib (for video export)

**Integration:**
- Recorder initialized in `DemoRunner.run()` if `training_config.recording` is set
- Database hooks: `DemoDatabase.insert_episode_recording()` stores metadata + file paths
- Recording does **not** enter training hot loop (writes to queue; writer thread handles I/O)

---

## Demo

**Unified Architecture:** Training, inference, and frontend coordinated via `UnifiedServer`

### DemoRunner (`runner.py`)
- **Context Manager:** Implements `__enter__`/`__exit__` for resource cleanup (SIGINT/SIGTERM handlers)
- **Lifecycle:**
  1. Compile v2.1 hierarchical configs (`experiment.yaml`, `levels/<level_name>/training.yaml`)
  2. Instantiate environment, population, curriculum, exploration (RND), recorder (if enabled)
  3. Run training loop: environment step → population inference → curriculum decision → recording
  4. Checkpoint every 100 episodes; TensorBoard logging
  5. On shutdown: close recorder writer thread, database, TensorBoard gracefully
- **Database:** `DemoDatabase` (SQLite, WAL mode) for multi-day resumption
- **TensorBoard:** Auto-positioned sibling to checkpoint_dir (runs/LX_name/timestamp/tensorboard)
- **State:** `current_episode`, `should_shutdown` flag, periodic summary output

### Live Inference Server (`live_inference.py`)
- **FastAPI + WebSocket (port 8766):** Streams agent state snapshots to frontend
- **Checkpoint Detection:** Polls filesystem for new checkpoints; hot-loads into population
- **Modes:**
  - **inference:** Run latest checkpoint step-by-step at human-watchable speed (0.2s default = 5 steps/sec)
  - **replay:** Load episode from database + replay file; playback recorded trajectory
- **Telemetry Payload:** Per-agent Q-values, survival, episode count, affordance interactions, meters
- **Substrate-Aware:** Detects substrate type (Grid2D, Grid3D, GridND, Aspatial) for UI routing:
  - Grid substrates → Grid.vue component (spatial layout)
  - AspatialSubstrate → AspatialView.vue component (affordance network or abstract view)

### Database (`database.py`)
- **SQLite with WAL mode:** Multiple readers, single training writer
- **Schema:**
  - `episodes` — Summary metrics (episode_id, timestamp, survival, rewards, curriculum_stage, epsilon)
  - `affordance_visits` — Transition frequencies between affordances
  - `position_heatmap` — Visitation frequency per (x, y) grid cell (if spatial)
  - `episode_recordings` — Recorded episode metadata + file paths + recording reason
  - `system_state` — Arbitrary k/v store for run metadata

### Unified Server (`unified_server.py`)
- **Orchestrator:** Starts training thread, inference thread, frontend subprocess
- **Thread Isolation:** Training in background; inference async on separate thread; frontend via subprocess (npm run dev)
- **Config Snapshot:** Copies active config pack into run directory for provenance
- **Graceful Shutdown:** Coordinates SIGINT/SIGTERM → training stop → inference cleanup → frontend kill
- **Relationship to live_inference.py:**
  - `live_inference.py` is a standalone server (can be run independently with `LiveInferenceServer()`)
  - `unified_server.py` **orchestrates** it as a thread alongside training + frontend
  - No duplication; `unified_server.py` delegates inference to `LiveInferenceServer`

---

## Data Flow (Training → Recording → Replay)

```
VectorizedPopulation.step()
  ↓
EpisodeRecorder.record_step(positions, meters, action, reward, done, ...)
  ↓ [non-blocking queue push + tensor clone]
RecordingWriter thread
  ↓
RecordingCriteria.should_record(episode_metadata) → (bool, reason)
  ↓ [if yes]
msgpack.dumps() + lz4.compress() → DemoDatabase.insert_episode_recording()
  ↓ [at inference time]
ReplayManager.load_episode(episode_id) → [RecordedStep, EpisodeMetadata]
  ↓ [for visualization]
EpisodeVideoRenderer.render_frame() → PNG frames + ffmpeg encode → MP4
```

---

## Dependencies

**Inbound:**
- `scripts/run_demo.py` — Calls `UnifiedServer.start()`
- Training loop (population) — Calls `curriculum.get_batch_decisions()` and `recorder.record_step()`

**Outbound:**
- `environment/` — Curriculum feeds into reward shaping + meter depletion
- `population/` — Uses `curriculum_stage` for telemetry
- `training/` — Checkpoint/resume integration (v2.1 config compilation)
- `universe/` — CompiledUniverse for config resolution
- `substrate/` — Substrate type detection (Grid2D vs Aspatial) for rendering

---

## Patterns Observed

- **Curriculum:** Strategy pattern; pluggable difficulty managers (CurriculumManager ABC)
- **Recording:** Observer (non-blocking queue) + Writer pattern (async I/O isolation)
- **Demo:** Server/Hub (unified orchestrator) + Context Manager (DemoRunner cleanup)
- **Replay:** Cursor pattern (ReplayManager.seek) for frame-by-frame playback

---

## Concerns & Observations

1. **Curriculum Stage Transitions**
   - ✅ No hardcoded transitions; fully data-driven (survival/learning/entropy metrics)
   - Retreat logic prioritized before advance → prevents oscillation
   - min_steps_at_stage prevents premature transitions (~1000 steps default)

2. **Recording Runtime Cost**
   - ✅ **Zero** hot-loop overhead (async queue + daemon thread)
   - Recorder queue bounded (default 1000) to prevent unbounded growth
   - **Potential issue:** If writer thread stalls (I/O jitter), queue fills; training blocks on queue.put()
     - *Mitigation:* Consider logging queue depth; monitor I/O latency in production

3. **Video Rendering Substrate Mode**
   - ✅ EpisodeVideoRenderer detects substrate type from environment
   - Grid-based positions recorded as tuples (x, y) or (x, y, z); aspatial as ()
   - Frontend conditionally routes: spatial → Grid.vue, aspatial → AspatialView.vue
   - **Potential issue:** AspatialView.vue rendering logic unclear from codebase
     - *Recommendation:* Document aspatial frame rendering strategy (affordance network? meter visualization?)

4. **Unified vs Live Inference Boundary**
   - ✅ No duplication: UnifiedServer uses LiveInferenceServer as library
   - LiveInferenceServer can run standalone (useful for multi-machine setups)
   - **Clarity:** Docstring for UnifiedServer could emphasize "orchestrator, not executor"

5. **Database Concurrency**
   - ✅ SQLite WAL mode allows concurrent reads during write
   - Single training writer + multiple inference readers (safe)
   - **Note:** DemoDatabase.close() is idempotent; replay queries safe during active training

---

## Confidence

**HIGH**

- Curriculum: well-documented logic, clear stage configs, integration tested
- Recording: straightforward queue + async pattern; criteria logic verifiable
- Demo: clear separation of concerns (runner, inference, orchestrator); context manager cleanup pattern confirmed
- Database: standard SQLite + WAL; no exotic concurrency logic
- **Minor gaps:** AspatialView.vue rendering internals (frontend code, outside this audit)

