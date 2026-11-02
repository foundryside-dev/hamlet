# T15 ENV action metadata API — finite supplier supplement

Read-only static supplement at HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, 2026-11-01. Reuses the previously read exact **five complete files / 2609 lines**; only ENV references were refreshed. No sixth DTO/helper/compiler/action-config source was opened.

| Complete source | Lines | Unchanged SHA256 |
|---|---:|---|
| `src/townlet/environment/vectorized_env.py` (ENV) | 1714 | `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d` |
| `tests/test_townlet/_fixtures/environment.py` | 460 | `21bd79b1736efd53fdacb76ca6a6f4abaf3917340204aef74994ba20b6af745c` |
| `tests/test_townlet/_fixtures/config.py` | 145 | `f25801c31ddb8354cc8b63a25fa145b518a65c05b275d19f558cf6f4e3f04fb8` |
| `tests/test_townlet/helpers/config_builder.py` | 181 | `3cc6dc19e579d03835692146ee88f4befada29c403174cfa406049c4a4d2235a` |
| `tests/test_townlet/_fixtures/brain_configs.py` | 109 | `aac8397902f8f038bee0c3da913c1a6b3930478d70c8a82156898231605cc9f4` |

**Source-proven named-action record route:** `env.level.runtime_action_space.actions`. ENV102–104 retains the selected level as public `env.level`; ENV283 passes that level's `runtime_action_space` to the local builder. ENV520–536 iterates its `.actions` and directly reads each record's **`.id`, `.name`, `.type`, `.delta`** (plus costs/effects/teleport_to/enabled/description/icon/source/source_affordance/writes) to build the runtime action configs. These field spellings are verified by actual accesses, not inferred from an excluded DTO name.

For a pack declaring WAIT/REST, select the record whose **`.name` exactly equals `'WAIT'` / `'REST'` and take its `.id`**. For a movement control, select a record with **`.type == 'movement'` and `.delta is not None`**, then take that record's `.id` and inspect its actual `.delta` for the required direction. ENV720–726 uses precisely this movement predicate and indexes `deltas[action.id]` with the stored delta. Do not assume movement names, WAIT/REST presence, a fixed ID, list position, or a particular direction from these source lines; those depend on the selected artifact. This route requires no unverified named-lookup method on an excluded helper.

**Index semantics actually established:** `.id` is used directly as the row index of ENV's movement-delta tensor, whose first dimension is `env.action_dim` (ENV712–724). `env.action_dim` comes from `self.action_space.action_dim` at284. These lines establish ENV's use of movement IDs as action-indexed rows; they do not independently prove the external DTO validates contiguous IDs, that `.actions` list position always equals `.id`, or every downstream executor's interpretation. Use the returned record ID, not `enumerate(...)` position.

Two other public surfaces must not be guessed into equivalent name lookup:

- `env.get_action_label_names() -> dict[int, str]` is the actual method at ENV730–742. It delegates to `self.action_labels.get_all_labels()`. ENV154–164 constructs `ActionLabels` from a copy of selected `level.action_metadata.labels`, with optional label_description/domain. The documented result is action-index → **display label**; the excluded label helper/metadata DTO was not read. No proof says display labels must equal authored names WAIT/REST, and no `get_action_id(name)` method is defined in ENV.
- `env.action_ids` is assigned directly from `level.runtime_action_space.action_ids` at ENV285 and passed to the mask builder at305. Its mapping keys/value shape and named-lookup spelling are not used or exposed further in ENV; no `env.action_ids['WAIT']`, `.WAIT`, `.by_name`, or `.index(...)` API is asserted.

If the test author specifically needs a dedicated `ActionSpaceMetadata` name→ID helper, `action_ids` accessor, proof of full ID/column ordering, or display-label equivalence, that exact missing interface belongs to the excluded `RuntimeActionSpace`/action-ID/`ActionSpaceMetadata`/`ActionLabels` supplier; root must provide its separately source-verified prose. The raw selected-level record route above already resolves declared names and movement descriptors without guessing those helpers.

Only this ignored receipt was written. Fresh postwrite readback/HEAD/count/hash/ignore checks establish custody, not runtime acceptance. No imports/runtime, code/tests/index/metadata edits, branches/worktrees/copies/subagents or gate activity were performed. Runtime remains paused; return stationary.
