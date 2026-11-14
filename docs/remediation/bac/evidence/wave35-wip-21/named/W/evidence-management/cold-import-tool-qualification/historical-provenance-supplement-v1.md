# Historical source provenance supplement v1

2026-11-14. Additive supplement only; the implementation report, freeze, attempt records/logs, tool-seal proposal and all frozen executable tools are unchanged.

At the original attempt01–08 runs, records and logs retained source SHA256 values but intermediate source bodies were not separately snapshotted. This was a historical byte-retention omission, not an additional execution result. The exact original write/edit/append buffers remained in this implementer’s conversation context.

A single bounded in-memory reversal of those recorded edits recovered all12 distinct source-path/hash subjects named by attempt01–08. Every candidate was required to match its already recorded SHA256 before any output write. All12 matched; no unavailable or unmatched subject remains. The unchanged strict verifier and attempt08 synthetic tests were recovered directly from identical current frozen bytes. Other versions were recovered from exact recorded edits and append boundaries. No guessed source, test rerun, application import or execution copy was used.

The inert snapshots are in `historical-source-snapshots-v1/`, exclusively created as content-addressed `.py.txt` files. `historical-source-recovery-v1.json` binds each source path, recorded hash, attempt aliases, snapshot path/size/line count and precise recovery method. Its SHA256 is `4c0502a54f6e7dc3c17aaa881b83daf7b1afa1bc266d6d83dab90434a0fafeef`.

These are post-attempt recoveries authenticated by contemporaneously recorded hashes, not a claim that snapshots existed at execution time. Historical RED/setup/failure/intermediate-GREEN logs remain diagnostics of their own exact historical bodies; they do not qualify the final source. Final-source qualification remains attempt09 (188 new plus81 unchanged strict synthetic nodes,269 passed), followed by root’s separately recorded independent review/qualification. No historical status was upgraded and no rerun was performed for this recovery.

Verification rehashed every recovered snapshot against every referencing historical attempt, all original attempt records/logs against the frozen manifest, the four frozen tool files, the existing implementation report, freeze and tool-seal proposal. All matched. Runtime/application acceptance remains root-owned.
