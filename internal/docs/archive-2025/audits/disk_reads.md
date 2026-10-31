# Disk Reads & Usage Trace (runtime code)

Scope: `src/townlet/**` runtime modules only (docs/tests excluded). Each entry lists the reader, what it opens, where it is called, how the data flows, and whether it is load‑bearing, bypasses the compiler, or is effectively dead.

## UniverseCompiler intake (load‑bearing)
- `src/townlet/config/base.py:14 load_yaml_section(config_dir, filename, section)`
  - Opens `config_dir/filename` with `open()`.
  - Called by `bars_v2_config.load_bars_v2_config`, `affordances_v2_config.load_affordances_v2_config`, `training_v2_config.load_training_v2_config`, `drive_as_code.load_drive_config`, `exploration.load_exploration_config`.
  - Feeds section dicts into Pydantic DTOs that become `RawConfigsV21` and then the `CompiledUniverse`.
- `src/townlet/config/{experiment,environment,actions,agent,stratum,curriculum}.py:from_yaml(path)`
  - Each opens its YAML path and `yaml.safe_load`s into its DTO.
  - `RawConfigsV21.from_experiment_dir` (UniverseCompiler stage 1) invokes all of these to build the shared config bundle consumed by later compiler stages.
- `src/townlet/config/items_config.py:140 ItemsCatalogConfig.from_yaml(path)`
  - Opens `items.yaml`, returns `ItemsCatalogConfig`.
  - Called from `RawConfigsV21.from_experiment_dir` (experiment‑level optional), also in compiler when loading per‑level `items.yaml` overrides.
- `src/townlet/vfs/schema.py:305 load_variables_reference_config(config_dir)`
  - Opens `variables_reference.yaml` if present.
  - UniverseCompiler stage 6 (`_build_universe_metadata`) loads it to derive VFS observation marks; output flows into `CompiledUniverse.vfs_observation_marks`.
- `src/townlet/universe/raw_configs_v21.py:375 RawConfigsV21.from_experiment_dir(experiment_dir)`
  - Opens every shared YAML and each level’s `curriculum.yaml`, `bars.yaml`, `affordances.yaml`, `training.yaml`, plus optional `items.yaml`.
  - Returns `RawConfigsV21` consumed by UniverseCompiler semantics, metadata, and artifact emission.
- `src/townlet/universe/compiler.py`
  - `_phase_0_validate_yaml_syntax` opens all YAML files under the pack to fail fast on syntax (no data retained).
  - `_compile_vfs_profiles` reads `vfs_profiles.yaml`; compiled profiles feed VFS expression schema & item profiles.
  - `_compile_effects_catalog` reads `effects.yaml`; compiled catalog feeds runtime effect engine.
  - `_build_action_space_metadata` reads optional `action_labels.yaml` to override labels in the action metadata emitted into the compiled artifact.
  - `_compute_config_hash` + `_normalize_yaml` reopen all YAMLs (plus `configs/global_actions.yaml`) to hash normalized content for cache invalidation.
  - `_build_universe_metadata` optionally reloads `variables_reference.yaml` (via `load_variables_reference_config`, above).

## Compiler cache & runtime artifacts (load‑bearing)
- `src/townlet/universe/compiled.py:334 CompiledUniverse.load_from_cache(path)`
  - Reads MessagePack bytes from cache; used by `UniverseCompiler` and `townlet.compiler.__main__` to fast‑path compilation.
- `src/townlet/training/checkpoint_utils.py`
  - `_compute_sha256`/`verify_checkpoint_digest` read checkpoint files and checksum sidecars; used by `DemoRunner` and `live_inference` to guard checkpoint integrity.
  - `safe_torch_load` wraps `torch.load` for checkpoints in demo runtime.
- `src/townlet/recording/replay.py:65 load_episode`
  - Reads compressed replay bytes from disk, decompresses, and feeds replay playback state. Used by the replay UI.

## Manual config reads outside the compiler (bypass path)
- `src/townlet/demo/runner.py:133`
  - Opens `self.training_config_path` with `yaml.safe_load` after compiling the universe; used only to pull optional sections (e.g., recording/run metadata). This bypasses the compiler and re‑reads raw YAML.
- `src/townlet/demo/unified_server.py:199 _load_config`
  - Opens `training_config_path` once per process to cache raw YAML; used for determining run directory naming. Also bypasses the compiler.

## Legacy or currently unused loaders (safe to delete/redirect)
- `src/townlet/config/cues.py:113 load_cues_config` — not referenced by runtime code; only tests/docs mention it.
- `src/townlet/agent/brain_config.py:487 load_brain_config` — unused in runtime; only test fixtures/docs.
- `src/townlet/curriculum/adversarial.py:195 AdversarialCurriculum.from_yaml` — unused; docs only.
- `src/townlet/environment/action_config.py:105 load_global_actions_config` and `src/townlet/environment/action_builder.py:_load_global_custom_actions` — legacy pre‑compiler path; `ActionSpaceBuilder` is not instantiated anywhere in current runtime (only tests/docs).
- `src/townlet/universe/source_map.py` — helper that opens YAML to track line numbers but is not imported or used elsewhere.
- `src/townlet/environment/action_builder.py:_compose_action_space` raises a hard `RuntimeError` (dead legacy path).

## Notes
- The only runtime config intake that bypasses the new compiler today is the demo tooling (`demo/runner.py` and `demo/unified_server.py`) re‑reading `training.yaml` for ancillary metadata. Everything else on the main training/inference path flows through `UniverseCompiler` and its DTO loaders.
- Tests exercise many of the above readers directly, but those uses were omitted here to focus on live code paths.
