# R124 failed-diagnostic restore ordering addendum

2026-11-14, `/root/bac_astra_wip22_terminal_review`. Source facts from the already charged POP3163 body SHA256 `ea05fddb584cc7836e663e2aa2cada3c4dca1fcbc08584e030efa1816ac4bf38`; no new implementation body or mutation. The sealed R124 review and diagnostic recommendation remain unchanged.

Actual `prepare_checkpoint_state` order:

1. 3045–3053: genuine receiving owner idle/failed/pending checks, accepted-is-None and ENV fresh-unbound checks.
2. 3055: deepcopy caller checkpoint into owned data.
3. 3056: `_validate_checkpoint_state(owned)`. It checks mapping/version and exact twelve-key shape, universe/geometry, scheduler consistency and required nonnull states, exact counters, network/optimizer/scheduler structures, and replay serialized content. For recurrent/PER captured5/6 it can create an offside replay before validation. `replay_target.validate_serialized` is2999.
4. 3057: `_checkpoint_clocks(owned)`. It validates exact seven-unit clock mapping and counter correlation. Non-None progress must be completed/completed; otherwise3019 raises `ValueError("Failed or in-progress work cannot enter a healthy native restore")`.
5. 3058–3061: mode/progress agreement, then required parent preparation proof for noninitial modes.
6. 3062–3066: deepcopy and load candidate Q/target/optimizer/scheduler.
7. 3067–3070: replay materialize, possibly deepcopy live replay receiver, then load prepared replay. Current materialize/load calls still lack lineage; these remain a separate restore prerequisite. Failed diagnostics must never reach them.
8. 3071+: read exploration cadence, set preparing correlation, then call runtime `prepare_restore` or private initialization. Nested exploration validation belongs to that later supplier route.

Crucial distinction: `_validate_checkpoint_state` checks `exploration_state` only for nonnull before `_checkpoint_clocks`; it does **not** validate a nested exploration schema or call runtime validation at that point. An additive explicit diagnostic tag inside a full exploration-state reading therefore need not block the required precise failed-progress refusal. Conversely, a new top-level diagnostic envelope/version will fail at current header validation first, and a differently shaped replay diagnostic may fail at replay validation first. Neither incidental failure satisfies the existing original assertion.

Recommended concrete adjustment to the preceding design memo: prefer retaining the existing twelve-field outer transport for the preserved failed `get_checkpoint_state` route. Let producer-owned exploration diagnostic state carry explicit nonresumable identity while retaining complete captured content. Preserve failed progress and actual clocks so the current parser rejects before parent proof and materialization. A separate new inspection API/envelope may be additive, but is not a silent replacement for this route.

If any child diagnostic representation (especially replay) requires a schema that the healthy child validator cannot read, split a pure header/exact-counter validation stage and run the existing failed-progress/ledger gate before network/native/replay validation. Validate enough outer shape/counter types first to avoid accidental KeyError/type errors; retain every existing healthy validation afterward. No failed input is granted install authority by an earlier rejection. Confirm this ordering against malformed/healthy inputs and the real failure artifact. Do not repair or execute replay materialization as a workaround for classifying a failed diagnostic: correct classification must happen earlier.

Required test remains a real failed export and a genuinely fresh compatible receiver obtaining the precise failed/in-progress refusal before parent-proof, child preparation or publication. Observe child prepare/materialize/install call counts and unchanged destination identities/state to substantiate that ordering. This is a proposed bounded contract reconciliation, not authorization to weaken the original diagnostic assertion or any producer's health contract.
