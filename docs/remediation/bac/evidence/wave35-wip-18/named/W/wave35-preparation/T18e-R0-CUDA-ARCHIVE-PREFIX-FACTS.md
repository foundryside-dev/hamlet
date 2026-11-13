# Historical archive record prefix — source facts for I5

Root inspected the relevant definitions in `src/townlet/training/historical_checkpoint.py` (675 lines), SHA-256 `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`. Read-only source inspection; no imports, execution, source changes or extra worker body required. This is a supplier fact capsule, not qualification or a grant to change archive behavior.

`_archive_from_state` at line471 performs exactly this prefix in order:

1. `_mapping(state, "embedded archive")`: `isinstance(value, Mapping)` or ValueError `embedded archive must be a mapping`. The diagnostic does not render the rejected value.
2. `_keys(state, (field.name for field in fields(HistoricalReplayArchive)), "embedded archive")`: materialize the expected set, compare `set(state)` with it. On mismatch raise ValueError containing `embedded archive schema key mismatch: missing=` and the set difference, then `unknown=` and its set difference. It does **not** traverse record values or clone them. Unknown key representation in the error can itself access a Tensor key; do not assume arbitrary non-string keys are effect-free. Ordinary missing/extra string keys do not inspect unused GPU values.
3. Only after the exact key set passes: `HistoricalReplayArchive(**state)`. There is no pre-constructor field-value validation.

The exact six field names are `source_formats`, `original_state`, `source_digest`, `archived_row_count`, `reward_semantics`, `approval_reference`. A record with six entries but a wrong/missing field name is rejected at step2 before constructor/cloning. An exact-key record with malformed field **values** enters the constructor.

At line295, `HistoricalReplayArchive.__post_init__` first calls `_own(self, ("source_formats", "original_state"))`. `_Owned.__getattribute__` clones those fields on public access; `_own` calls `_clone(getattr(...))` and stores the owned result. Thus the clone boundary comes before semantic, approval, row-count and digest validation. Next `state, formats = self.original_state, self.source_formats` clones on read again, then reward/approval checks, `_validate_archive_state`, archived-row-count comparison and digest comparison run. Do not hoist those later refusals ahead of the real clone boundary in metadata planning.

`_clone` at line51: Tensor → `detach().clone()`; OrderedDict → recursively clone keys and values; any Mapping → recursively clone keys and values into dict; list/tuple recursively clone elements; otherwise `copy.deepcopy`. An exact-key record's source_formats can therefore supply the first GPU clone; otherwise original_state can. This capsule does not authorize skipping actual constructor copies because a later field will fail.

The caller distinction matters: direct `_archive_from_state` checks one record; `_embedded_archives` at line477 first checks optional field presence, then `_mapping_sequence` validates list/tuple and that **every** item is a Mapping before constructing any archive. The flat/PER callers' own list/key/order checks remain their separately admitted source responsibility. No statement here makes every nonempty archive list a clone-producing branch.

The prefix matrix must preserve diagnostic-source inventory and identify the actual first copy/constructor boundary. It must not execute key/error rendering on GPU values while planning or silently reject an accepted Mapping transport.
