# T15 checkpoint fixture repair R3

Root closed all R2 runtime barriers and authorized edits only to `tests/test_townlet/integration/test_checkpointing.py`. Root corrected the checkpoint-consumer baseline to **2 failed /47 passed**, 83.63 pytest seconds /88.9967 wall seconds. Those counts are root-relayed; this worker did not run or independently inspect the runner log.

## Inventory and identity

Same exact five complete sources as `T15-checkpoint-fixture-audit.md`; initial inventory4525 lines. No sixth implementation/helper/conftest/buffer/runner source was read. Post-edit checkpointing.py has1662 lines, making current corresponding five-file total4522. HEAD observed75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7. Parent baseline frozen tree929bc8952a2e797871d15376e2ef61a8aec73ca5 is attributed, not a new tree claim.

| File | Post-edit lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py |2146|9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a|
| tests/test_townlet/integration/test_checkpointing.py |1662|70d13c5df324111b1e9f53aba91360edfe31a0abb1cf2e5a3c7cf46b6e08968d|
| tests/test_townlet/_fixtures/environment.py |460|21bd79b1736efd53fdacb76ca6a6f4abaf3917340204aef74994ba20b6af745c|
| tests/test_townlet/_fixtures/config.py |145|f25801c31ddb8354cc8b63a25fa145b518a65c05b275d19f558cf6f4e3f04fb8|
| tests/test_townlet/_fixtures/brain_configs.py |109|aac8397902f8f038bee0c3da913c1a6b3930478d70c8a82156898231605cc9f4|

## Repair

Training-resumption node now derives checkpoint collection from actual selected training retained warmup and passed batch sample support: max(min_size1000,batch32). It asserts the passed-brain/public-buffer capacity10000 supports that collection, positive optimizer counter at the saved point, and retained occupancy. It deepcopies the checkpoint before source continuation. Source and resumed branches both must advance optimizer counters and change parameters with retained atol1e-6. Restored total tick/counter, exact checkpoint weights and replay occupancy are checked before fresh episode reset. Architecture assertion is preserved. No production configuration or warmup changed.

New recurrent checkpoint assertions now require exact captured6 payload, action geometry, captured legality, all six resolved options, active2 transitions, two episodes, episode/transition identities, original spans, captured boolean legality and exact stored successor masks. Source and restored complete learner state must match, including replay. Restored captured replay remains active2 with no historical archive and zero legacy transport. Existing completion-once/survival-history idempotence, rollout exclusions, fresh ENV and completion counters, empty current episode containers/zero hidden state, unchanged source artifact bytes and producer state equality remain.

Removed assertions described a just-produced checkpoint as maskless5 and demanded archive-only restored state. They were incompatible with the qualified captured producer. Genuine historical5 archival semantics are unchanged in their separately protected root-owned fixtures/tests; no other source was edited.

## Owned static verification

`git diff --check` passed. Owned Black check passed (one file unchanged); owned Ruff check passed. Initial uv cache initialization outside writable roots failed before checks; rerunning with UV_CACHE_DIR=/tmp/t15-fixture-uv-cache and --no-sync completed both checks successfully. No project imports/runtime, pytest, collection or execution was performed. No index/commit/worktree/branch/source-copy/deletion/delegation operation occurred. Only owned test source and ignored audit receipts were written. Independent checker owner may have disjoint writes; this receipt claims only this worker's custody.

Root must run the exact two previously failed nodes before broader/full qualification. This receipt makes no runtime-success claim. Worker returns stationary and will not edit while root runtimes run.
