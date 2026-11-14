# P3 actual-process identity — linked frozen author packet v2

This is a bounded repair of frozen v1, preserving that report, all old bytes and
its independent failure. It resolves v1's source-grant input-order integration
block. P1's fixed order is source, tests, configs, scripts, ratchet, artifacts,
preserving entry order inside each category; JSON object order is irrelevant.

Fresh reviewer first reproduced the defect against frozen v1:
E/hardware-identity-p3/independent-review/order-red-execution.json (PID 188885,
exit 1). Root required that independent RED before mutation. Author snapshots
ordering-before-v2 also preserve exact prior source and tests. The new regression
uses alphabetical candidate JSON keys, supplies P1's fixed grant order and checks
the emitted source witness's exact inventory. red-ordering-v2 fails on v1;
green-ordering-v2 passes all 45 selected tests, 3 discovery-only cases deselected,
exit 0. The final fixture tree is retained at ordering-fixtures-v2.

Production mutation is only _source's explicit fixed category traversal. The
shared test fixture now produces P1-valid grants rather than JSON-order-dependent
grants. No P0/P1 bytes or private schema were changed. Four counted bodies total
1,725 lines: historical 60, P0 520, identity 611, tests 534. Exact hashes, snapshots,
actual invocation PID/argv/UTC/exit and predecessor links are in freeze-v2.json.

All v1 proof boundaries and rulings remain: inert source metadata/Git doubles,
real local process/pytest mechanics, no APP/Torch/CUDA/server work; no independent
acceptance receipt; no owner-specific child/fork-three-trial/RNG/hardware claims;
P4 owns complete custody, lifecycle and absent-end qualification. Independent
review is still in progress. This packet is not self-approved or root-adopted.
