# Current ClockLedger public ABI

2026-11-11. Root read the complete source-only 48-line src/townlet/training/clock_ledger.py after checking metadata, and verified the same SHA256 before and after: e7b40260b027bc63fd2cb751a4fb55840564c36a38d78fca30f876d9e41473e0. No import, runtime or source write occurred. This capsule supplies public ABI facts to a caller whose five-body inventory does not include that implementation; it does not authorize opening a sixth body.

ClockLedger is a frozen, slotted dataclass with exactly these seven integer fields, in declaration order:

1. vector_ticks
2. eligible_transitions
3. optimizer_updates
4. completed_batch_episodes
5. predictor_admitted_rows
6. predictor_consumed_minibatches
7. predictor_dropped_rows

Every field currently defaults to zero. Construction is ordinary dataclass construction, not keyword-only. Use all seven explicit keyword fields for portable restoration rather than omitting missing fields or relying on defaults. The public __post_init__ validates type(value) is int and value >=0; bool and negative/noninteger values raise ValueError.

The only other public ledger method is advance(**increments:int)->ClockLedger. It rejects unknown unit names and non-exact-int/negative increments, then returns a replaced immutable reading. It does not mutate the original.

There is NO to_dict, from_dict, state_dict, serialize or load method in this complete body. A fixture may explicitly encode an ordinary seven-key mapping using these named public attributes. Before reconstruction, require the exact keyset and declared scalar types, then use ClockLedger(**validated_mapping). That gives scalar/schema validity only; the caller still must authenticate the actual recorded values against its genuine independent component/parent commitment before publication. Do not infer historical work from episode cursors.

PreparedVectorStep and PreparedPopulationRestore are separate identity-only capability classes in this same body. No serialized mapping recreates those capabilities.
