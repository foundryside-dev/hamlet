# Archive constants and runtime-local import

Root source verification for fix4, 2026-11-13; no application execution. The unchanged historical helper SHA256 remains `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`.

Its module constants are exactly `APPROVAL_REFERENCE = "BAC-HISTORY-A-2026-11-01"` at34 and `REWARD_SEMANTICS = "historical_recorded_pre_fix"` at35. Constructor comparisons at298 consume those actual exported constants. Import their values rather than inventing or duplicating a different policy.

In the immutable R100 tree `0b17ef1e48a6efc6e52bc814812439d4035e5447`, both flat and PER modules already import `historical_checkpoint as history` at module scope before defining their replay classes. Their raw validation traversals pass callbacks using `history._archive_from_state` into `ReplayPrefix.archive`. Thus, on these supported production routes, the helper module has completed import before archive planning executes.

The helper imports `HistoricalLegalityUnavailable` and `validate_successor_masks` from replay_contract, but does not import either replay-family implementation. A runtime-local import of these two constants inside `ReplayPrefix.archive` does not introduce a new module-level cycle: it reads the already loaded module on those routes. This is scoped source/import-order reasoning, supported by existing successful collection of the unchanged module graph; no new fix4 runtime result is claimed. Do not move this import to replay_contract module initialization or assert arbitrary future callsite safety.

No helper implementation read/edit grant or new helper callable/API is implied. Existing production PID/owner ordering and all application verification obligations remain unchanged.
