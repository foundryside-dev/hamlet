# Exact outcome ID producer repair: sealed handoff

Root explicitly authorized the sole new-test writer baton, then separately authorized the narrow production change after reporting genuine old-code RED and closed runtime custody. This worker authored only the owned 171-line new test and changed only `not self.world_id.strip()` to `not self.world_id` in `LaneOutcome.__post_init__`.

## Root-attributed RED evidence

Root reported R0 tree `310c32d30e528332a12a2f382f3bad80cfaee017`: 27-node collection PASS (3.3493 seconds), two actual valid DTO/roster prerequisite controls PASS (3.45335 seconds), and the unchanged complete test file yielding 10 causal whitespace old-`.strip()` failures and 17 passes (4.46164 seconds), with no errors. Root also reported negative custody checks passing for source/config/artifact/index/import/process/thread/registry/MAIN state and all runtime CLOSED before production authorization. These are root-attributed receipts; this worker did not run imports, collection, pytest, or any runtime checks.

## Test identity and finite matrix

Owned test: `tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py`.

- `test_valid_ordinary_completion_control`: explicit complete finite dense CPU DTO, current state and frozen decoding control (1 node).
- `test_roster_accepts_exact_whitespace_ids_control`: actual declaration and current roster serialization accept the unchanged space/tab/CR tuple (1 node).
- `test_declared_whitespace_id_constructs_outcome`, `test_declared_whitespace_id_current_state_roundtrip`, and `test_declared_whitespace_id_frozen_roundtrip`: each parameterized as `space`, `tab`, `carriage-return` (9 nodes).
- `test_existing_exact_id_preservation`: ordinary, leading/trailing spaces, case distinction, composed/decomposed Unicode, and embedded CR/tab/space (9 nodes).
- `test_empty_or_nonstring_id_still_refused`: empty string, None, integer, boolean, bytes; actual construction and current decoder refusal (5 nodes).
- `test_existing_distinct_exact_ids_have_distinct_fingerprints` and `test_whitespace_and_existing_exact_ids_have_distinct_fingerprints`: otherwise identical real envelopes retain exact distinct identities in frozen fingerprints (2 nodes).

Total: 27 nodes; 17 existing-behavior/prerequisite controls and 10 whitespace-dependent regressions. Fixture survival is 1, planned horizon is 2, all required envelope/completion fields are supplied explicitly, and observation/meter readings are finite dense CPU tensors. Actual public APIs are used throughout; no fake codecs or additional source/helper files were inspected.

## Self-review and authorized verification

The one-predicate repair retains the string type guard and empty-string rejection and admits only the previously excluded nonempty whitespace-only string values. No normalization is performed. Fields, current schema, serializers, fingerprint recipes, completion validation, tensor ownership, roster code, and all tests remain unchanged by the production step. No backward-compatibility path was introduced.

Absolute `/workspace/hamlet/.venv/bin/black --check` and `/workspace/hamlet/.venv/bin/ruff check`, each with explicit `/workspace/hamlet/pyproject.toml`, passed for both owned episode and test paths. Black reported both files unchanged. No GREEN or full integration claim is made: root still owns the 27-node post-fix execution and fresh independent Astra review/adversarial execution, followed by actual BANK gap correction and implementation. This finite DTO-domain proof does not establish full runtime acceptance by itself.

## Final sealed inventory

| Owned slot | Lines | Cap | SHA-256 |
| --- | ---: | ---: | --- |
| `src/townlet/config/world_roster.py` (unchanged READ) | 312 | 350 | `1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33` |
| `src/townlet/training/episode.py` (one predicate) | 176 | 250 | `1616ba8c526051a4f3b8593a5c86daf5d405d311aacf9f0c375bce1756ceae4f` |
| `tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py` (sealed unchanged) | 171 | 450 | `82124334b10aec6e8d978b078224da2dc49240629635c48d74156f5617fb3088` |

Actual total 659 lines; reserved ceiling 1,050, below 5,000. Episode pre-fix SHA-256 was `53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`. No source/test files beyond these three slots were read. No index/commit/push/branch/worktree/copy/install/delete/subagent/runtime actions were performed. Sole writer baton is returned sealed to root; this worker remains stationary.
