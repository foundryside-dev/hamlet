# Historical producer evidence review

Portable canonical data consists of `uniform.pt`, `per.pt`, and `sequence-trained.pt`, their matched authored packs and native inventories. `portable-manifest.json` records relative artifact/config/inventory paths, exact key inventories and versions, reward tensor digests, pack file hashes, producer provenance, and independent restore results. Existing `sequence.pt` remains an optional smaller untrained recurrent artifact. All three original native files and their manifest/inventories were preserved.

## Source and read boundary

Every Python execution asserted checkout HEAD `4aa5363b5de54d9a112977c32c2975f37627197f`, `townlet.__file__` and runner module paths against `/tmp/hamlet-bac-4aa5363b/src`. The process used one CPU affinity and Torch intraop thread, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, and empty `CUDA_VISIBLE_DEVICES`.

Implementation/test/probe read inventory (conservative full-file line charges):

- Pinned `src/townlet/demo/runner.py`: 998 lines; selected checkpoint/run sections and symbol searches.
- Pinned `src/townlet/training/replay_buffer.py`: 651 lines; selected serialization/validation section and symbol searches.
- Pinned `src/townlet/training/prioritized_replay_buffer.py`: 758 lines; selected serialization section and symbol searches.
- Pinned `src/townlet/training/sequential_replay_buffer.py`: 543 lines; selected serialization section and symbol searches.
- Owned `verify_capture_owned.py`: 213 lines, sole new capture/verification executable.

Five files, at most 3163 full-file lines, below the 5000-line bound. No population, checkpoint-utils or helper implementation source was read. Runtime imports of `probe.pack`, `probe.runner`, and checkpoint APIs were uninspected; API and eligibility facts were supplied by the root agent. Existing root capture source was not read. Native inventories, JSON/YAML data, file lists, git HEAD and process metadata were read as data. No project source/index/HEAD/branch edits, network, installations, deletion or delegation occurred.

## Actual learned-state evidence

| Canonical artifact | Demo/population/replay | Native replay kind/count key | Retained rows | Training counter / Adam steps |
|---|---|---|---:|---:|
| uniform.pt | 9/6/4 | standard / size | 4 | 3 / 3 |
| per.pt | 9/6/4 | prioritized / size_current | 4 | 3 / 3 |
| sequence-trained.pt | 9/6/5 | sequential / num_transitions | 34 | 2 / 2 |

New sequence SHA256: `f5ca18d9e4f8c8f9398d585fc2a7861d23883ca9a8ae7175c964e2e97e16ced6` (1463292 bytes). It contains 17 complete two-step episodes, all 34 rows eligible for full sequence length 2, capacity 64, explicitly small recurrent architecture, batch size 2/min size 2. The original producer checkpoint and its exact copied bytes are retained; native save ran old validators without optimizer or learning mocks.

Initial fresh 16-episode capture produced 32 retained rows but zero optimizer updates. The root supplied the causal old-runtime prerequisite: eligibility tests completed episodes inside `step_population`, before the current runner episode is flushed. Sixteen finished episodes first become available after episode 16's final step. This is a genuine boundary gap in the initial recipe, not proof of learning. Its native checkpoint and unique authored pack remain preserved at `/tmp/bac-B09/historical_trained_sequence_eb3a4ebd2c854ca9b3a5eb0af7883d71_run/checkpoints/checkpoint_ep00016.pt` and corresponding sibling pack.

A new unique resume run copied that checkpoint and digest, reused the identical authored pack, and used `max_episodes=18`. Old resume sets current episode to saved episode + 1, so one further episode ran (17), producing 34 rows and two actual Adam/training updates. `sequence-trained-record.json` records both native paths and initial/final digests. This corrected 34-row precondition was expressly accepted by the root. No repeat broad capture was used.

## Independent verification

Each canonical artifact was SHA256 checked against its producer record and loaded with the existing `safe_torch_load(..., allow_unsafe_pickle=True)` after verifying trusted local provenance. A separate new Python process and unique scratch directory copied the matching full pack and checkpoint, persisted the copied checkpoint's digest, and ran the actual pinned `DemoRunner` with `max_episodes` equal to the artifact episode. Initialization executed strict outer payload/runtime/identity and population/buffer validators before loading; the post-load loop performed zero new learning steps. Scratch final saves did not modify original files.

For all three canonical artifacts, recursive comparisons required identical types, mappings, tensors (shape/dtype/value), arrays, lists and scalar values across the entire restored population state: Q network, target network, optimizer, scheduler, exploration state, metadata, replay and counters. Direct replay serialization also matched exactly, preserving reward component ownership and optional values. Agent IDs and completed live-agent steps matched; the known runner resume index increment was checked separately. Every serialized reward tensor, including each component, was finite. All original three SHA256 values remained unchanged after every verification.

Results are in `uniform-verified.json`, `per-verified.json`, `sequence-trained-verified.json`; logs show successful exact restores and `resume_learning_steps=0`.

## Commands and artifacts

Command prefix for each Python invocation:

```sh
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=/tmp/hamlet-bac-4aa5363b/src:/tmp/bac-B09 /workspace/hamlet/.venv/bin/python /workspace/bac-review-2026-11-01/qualification/historical-producers/verify_capture_owned.py
```

Executed initial `capture` (preserved failure to prove training), corrected resume `capture`, then `verify --label uniform`, `verify --label per`, `verify --label sequence-trained`, and `finalize`. The owned script's final `capture` mode records the corrected native-resume recipe. Initial setup used `probe.pack(unique_name,max_steps=2,batch_size=2,min_size=2,family='recurrent')`; full wrapped training YAML had replay capacity64, sequence length2 and max episodes16, brain replay capacity64. Unique pack/run names were asserted absent before invoking the helper that can delete an existing name. Original native checkpoints and packs were copied verbatim; the JSON inventories describe actual native data, not schema guesses.

## Limits and remaining acceptance

These data qualify historical fixtures only. No new archival policy, schema migration, successor masks, complete RNG continuation guarantee, or new OptionA acceptance was implemented or claimed. Native PyTorch payloads include trusted local pickle objects. The portable manifest uses relative data/config paths; absolute historical paths are retained only as provenance. Independent verification proves the old runtime restores the exact learned state using relocated matching packs. New policy acceptance, malformed/future/cross-kind rejection, current-path integration and project tests remain owed by the implementation task.
