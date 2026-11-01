# Portable receipt source-fact review — r10

Disposition: one precise T10 wording correction is recommended below; the remaining scoped implementation and limitation claims are consistent with the five inspected sources. This is a static documentation review during the full r10 run, not a full-suite result, release clearance, native admission receipt or global BAC acceptance. Source commit identities and the final full result remain PENDING.

## Bounded source receipt

Inspected only the following five whole implementation files for this new task: 2031 lines. No population/test source or other implementation was opened for this documentation review. Existing `/workspace/hamlet` only; no application imports, execution, tests, probes or helpers were run. Recorded result/log data was read as data.

| Implementation | Lines | SHA256 |
|---|---:|---|
| `src/townlet/config/resolved_launch.py` | 102 | `b55b4b816b02b167ee963a9a443045bff9b26d2ec5e3a0307026253767fe939d` |
| `src/townlet/training/replay_buffer.py` | 677 | `d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8` |
| `src/townlet/training/historical_checkpoint.py` | 666 | `093b842d75aa54dd3e929ef0cdc83ef1b929040773d622126aa073c3677041eb` |
| `src/townlet/exploration/count_based.py` | 206 | `163cb33f06799a75c887ff7beb58e4897875c94a4780ab722d019f714b33e9c1` |
| `src/townlet/exploration/icm.py` | 380 | `8004aec68d19c962df0cf6785b00af32c8553a3746fee95be39009555f9d44b8` |

All five match the embedded candidate inventory. HEAD remains `214408b107730b4511b8a690541569aeca4b7b67`. The frozen index remains the candidate previously identified as tree `973ba6470ae481c0d14050c19f1022614a1b5bcd`; its byte digest is unchanged at `cb1973e19e423908ff23d831a4ea2fccdccabbbd0aa51c6538a9488ef6d6769d`. The unstaged path list is empty. Fourteen existing worktrees remain present. No source, tracked file, index, branch, worktree or source copy was changed, and no delegation occurred. This ignored report is the only write.

Read the complete four requested implementation drafts, complete `qualification-receipt-draft.json` and complete `NATIVE-CURRENT-HANDOFF.md`. Reviewed document SHA256 receipts at inspection were:

- T05: `8163718f93e713dfcf52b4a4ef4fda98b371fd60e58bfe1f9dd7dfb44ae8619b`.
- T10: `4345defe10f1d06367ba6e8d36631e11f59bcbff56533a7e0f9cad8be010913e`.
- T18b: `ace091bf955ce87f59a328d21fbe471ab08a1bb775895f873d22adee4a73e983`.
- T18c: `3024d7e27d2623c2d7750c7ee0dd73cebb8c09eab34851f75bfef9124e34b185`.
- Qualification draft: `9d091a81a8c420af2d5353722dfcd4d2dd1792e8dde9ebf269fe7abbbd3895e5`.
- Native handoff: `77f6479d2df123f9508cb6a5ba1925a24a68d2058d0317b27384231a4507ccf8`.

## Specific wording correction

T10 currently says ordinary old-format loading “starts fresh qualified active replay.” Replace that phrase with:

> starts fresh empty active replay; subsequent rows must satisfy recorded-legality and readiness requirements

The old4 path creates an honest standalone replay-domain archive and a candidate with `size=0`, `position=0`, `action_dim=None`, no active tensor storage, and `legality_mode="unconstrained"` (`replay_buffer.py:600-613`). The request-based readiness code considers a buffer qualified only when it has an action vocabulary and recorded legality (`343-353`). Fresh replay is therefore empty and has no qualified sampling population at this point. The correction prevents conflating preserved archive rows or restored source clocks with current learner readiness. It requires documentation wording only; it does not propose changing historical acceptance, legality admission or storage behavior.

## Scoped source-fact checks

T05: PASS for the producer/delegation scope. `ResolvedLaunch` is frozen and copies declaration origins behind a `MappingProxyType`; it transports the selected root/name, compiled artifact and that artifact's existing effective configuration. `resolve_launch` calls actual declaration discovery, validates direct-level/explicit/single-level selection, and calls the compiler once with `primary_level=selected`. It does not independently reapply overrides. The broad renamed/nested/multi-document and duplicate diagnostics rely on the delegated declaration/compiler authorities and retained focused evidence; those authorities were not independently reopened in this five-file review. No CLI/server/runner transport, public-section-loader repair or D20/global closure follows from this producer. The explicit T06/T07 limitations remain necessary and are present.

T10: PASS for the storage/history claims after the wording precision above. Format5 explicitly includes legality masks, action geometry, recorded flags, archive transport and three optional reward-component presence fields. The original unconstrained `push`/`sample` adapter remains callable; capture-aware admission is the separate `push_recorded` path. State serialization rotates wrapped rows into chronological order, owns tensors, and preserves absence separately from real zeros. Version-specific exact keys, row geometry/dtypes, component presence and legality declarations are checked before installation; archive merge validation precedes installation. Genuine old4 is admitted using its exact old schema, archived under `scope="standalone_replay"`, and never promoted into active experience. Explicit recorded full resume of maskless history is refused at `668-670`. Query/export and state/domain digest ownership are implemented in the historical module (`274-382`), without fabricated native-container provenance.

Historical/current-native distinction: PASS. Historical format classification recognizes old9/pop6 and current10/pop7 families, but current preparation does not call the legacy callback or the complete current storage/population/learned-state validators (`historical_checkpoint.py:506-603`). Current archive accounting reads the top-level embedded registry at line 548; it does not construct the required validated nested/outer canonical union. The native handoff and qualification draft correctly keep actual current admission, explicit outer registry/subset reconciliation and single validated archive accounting REQUIRED OPEN for T24/T25. The handoff's native10/pop7 producer/consumer requirements are future obligations, not claims that those producers are implemented by these files. The inspected primitive cannot certify populated-target native atomicity, clocks/RNG continuation or inference isolation end to end. Neither old9/pop6 dispatch nor standalone replay provenance is removed by the written obligations.

T18b: PASS for provider primitives. Exact integer-ratio floor quantization avoids floating division overflow/rounding across bin boundaries. Row keys are prepared before mutation; explicit `update_stats=True` updates counts and ordered LRU in stable input order, while omitted/false flags neither count nor refresh LRU. The reward computation uses arbitrary-precision counts through logarithms, keeping outputs finite even when the output underflows to a real zero. Checkpoint state owns counts/LRU/policy transport, and restore validates the complete candidate before assignment. Service returns zero neural admissions/updates and does not add a second count admission. Factory/bank routing, private RNG/local clocks and canonical production reward wiring remain later owners; the drafts correctly do not claim X01/X02 closure or world binding.

T18c: PASS for provider primitives. The implementation constructs encoder/inverse/forward networks and Adam. Active transition novelty is half the mean squared forward-feature error with detached successor targets; reward computation has no admission/service effect even when the validated `update_stats` flag is true. Observation-only rewards and generic batch updates refuse missing transition context. Admission owns CPU predecessor/successor snapshots, bounds FIFO, accounts for overflow, uses the shared monotonic vector tick, and applies the configured ordinary per-tick budget; mandatory service-before-admit is separately accounted. Checkpoint/restore transport includes all models, warm Adam state, pending rows, counters and service budget, validating/preparing off-side before replacing live provider state. “Atomic state” here is supported as checkpoint restoration, not a blanket claim that every service failure rolls back all earlier admissions. The constructor uses ordinary module initialization and the service budget is shared-vector-tick based; private initialization/RNG/local service clocks and actual bank/reward integration are correctly left open. CPU evidence cannot establish CUDA or cross-device bitwise continuation, and the draft explicitly says so.

## Evidence data and pending boundaries

Read only the recorded tails of the result logs named by the embedded JSON. They support the draft counts: T05 8 passed; T10 63 passed; COUNT 34 passed; ICM 28 passed; launch owners 165 passed; uniform owners 100 passed/4 skipped; exploration owners 161 passed; historical callback 16 passed; r10 population owners 69 passed; r10 compact-token owners 14 passed. Reading those records did not run tests or reopen their source. The complete-owned-context equality assertions are retained evidence supplied by the qualification record; this limited source review does not independently recertify all uninspected dependency/test files or worker import identities.

All four implementation drafts say `Qualified source commit: PENDING`. Qualification `release.source_head` is null, release status is pending final full result/identities/tree equality, and `full_suite_status` says `RUNNING r10; no release/pass claim`. The failed r9 run remains explicitly failed rather than being counted as green. No prefix commit is individually full-qualified. These pending fields must remain pending until root records actual result and exact source/commit evidence.

The drafts retain approved historical A and strict per-world B, preserved public/shared alternatives, local-only publication scope, later finite learning/E2E work, coverage/slow/applicable-hardware gates, final independent lenses/synthesis and exact-tip remote CI. No private-bank implementation, GPU pass, whole-BAC completion or final acceptance is established by this review. Recording/T33 implementation claims and the actual six guard executions are outside these five sources; the qualification record preserves their separate evidence rather than this report silently extending its source verdict to them.

Stationary: final checks after writing confirm unchanged five source hashes, HEAD/index digest and empty unstaged path list. No final full result or qualified commit was invented or written.

## Corrected T10 draft verification

Root applied the wording correction. The inspected draft now says “starts fresh empty active replay; new rows must satisfy recorded-legality/readiness requirements.” Corrected T10 draft SHA256 is `53423da70f09b11a371aa45ac94b8f427760dcb287271f89511dcad3687a5fbc`. Reversing only that exact phrase in a read-only stream reproduces the original reviewed draft SHA256 `4345defe10f1d06367ba6e8d36631e11f59bcbff56533a7e0f9cad8be010913e`, confirming that this replacement is the only change from that reviewed T10 draft.

Disposition: scoped source-fact PASS for the corrected T10 draft and the previously reviewed remaining claims, with every limitation above retained. No additional implementation source was read; the inventory remains the same five whole files / 2031 lines. Digest-only checks confirm all five source hashes and index digest remain unchanged; HEAD remains `214408b107730b4511b8a690541569aeca4b7b67`, with no unstaged paths. The draft still says `Qualified source commit: PENDING`; qualification release status remains pending, with null `source_head` and no full-pass claim. Root separately reports an artifact-pipeline fixture observer failure in the current full run. This prose verification does not investigate that failure, qualify the full run or certify any affected implementation outside these five sources. No runtime, tests, source/index edits or other writes were performed beyond this ignored report append.
