# Current exact world-ID completion contract

This document records the source-verified DTO seam at root's final R1 candidate `2558d794476a4e7a1878b3c334b62d1733d62bb9`. It does not qualify BANK, the runner, parent integration, or the global repository.

## Accepted identity domain

`WorldRosterDeclaration` uses `exact_world_ids`: an ordered nonempty list/tuple of unique nonempty strings. Every string is preserved exactly. A space (`" "`), tab (`"\t"`), or carriage return (`"\r"`) is a valid nonempty world ID. Leading/trailing spaces, embedded whitespace, letter case, and distinct Unicode sequences remain identity-significant; no trimming, case folding, or Unicode normalization occurs.

`LaneOutcome.__post_init__` now accepts the same individual exact nonempty string domain, using `isinstance(self.world_id, str)` and the string's nonemptiness. Empty strings and nonstrings remain refused. This producer validation correction replaces only `not self.world_id.strip()` with `not self.world_id`; no roster membership validation or envelope field is added.

The current native `lane_outcome_state` / `lane_outcome_from_state` mapping and `freeze_lane_outcome` / frozen `to_outcome` preserve exact world-ID strings. Field sets, schema rules, serialization, fingerprint recipes, scalar checks, and tensor ownership semantics are unchanged. Distinct exact IDs produce distinct frozen fingerprints in the finite regression matrix with other envelope contents held constant. No historical loader, migration, fallback, or compatibility path was introduced.

## Evidence and attribution

This worker statically inspected exactly the two existing owned source files and authored the one owned regression file. Root then reported old-source R0 tree `310c32d30e528332a12a2f382f3bad80cfaee017`: 27-node collection PASS, two actual valid DTO/roster prerequisite controls PASS, and full unchanged-test execution yielding 10 causal old-`.strip()` failures plus 17 passes, with no errors. The causal failures cover three whitespace-only IDs through construction, current-state round-trip, frozen round-trip, and the combined exact-identity fingerprint matrix. Only after that RED custody did root authorize the one-predicate repair.

For final R1 candidate `2558d794476a4e7a1878b3c334b62d1733d62bb9`, root reports all 27 nodes PASS in 3.10259 seconds and a fresh independent Astra execution of the same 27 nodes PASS in 3.387248 seconds. Root reports independent source/specification/quality review PASS with no material findings, and custody checks covering 349 source files, 573 configuration files, 13 artifacts, index/import/process state, and one thread. These runtime/review results are root-attributed receipts; this worker performed no runtime execution.

This worker ran absolute-venv Black/Ruff checks with explicit repository configuration for the owned source/test paths; both passed. Root additionally reports all four global guards PASS, including Black (46.8038 seconds) and the defaults guard (601). Root reports the nine old mypy oracle/POP findings unchanged. These checks do not convert the bounded DTO proof into broader integration qualification.

## Exact three-slot inventory

| Owned source/test slot | Actual lines | Cap | SHA-256 |
| --- | ---: | ---: | --- |
| `src/townlet/config/world_roster.py` (READ, unchanged) | 312 | 350 | `1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33` |
| `src/townlet/training/episode.py` (single predicate change) | 176 | 250 | `1616ba8c526051a4f3b8593a5c86daf5d405d311aacf9f0c375bce1756ceae4f` |
| `tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py` (new regression) | 171 | 450 | `82124334b10aec6e8d978b078224da2dc49240629635c48d74156f5617fb3088` |

Total actual lines: 659. Reserved ceiling: 1,050 (below 5,000). Episode's old RED-source SHA-256 was `53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`.

## Remaining parent work and classification

The 27 cases establish a finite DTO-domain seam: explicit valid dense finite CPU completion readings, planned horizon at least positive survival time, all required fields supplied, actual public APIs, exact-ID positives, and empty/nonstring negatives. They do not exercise actual ENV issuance/acceptance, runner completion integration, BANK behavior, or full PW05 acceptance.

Root reports a representative old T19 owner-fixture case failing before its DTO assertion at `tests/.../fixtures/episode_lanes.py:48`, because current required `world_roster`, `training_seed`, and `lane_world_ids` inputs are missing. This remains required coherent parent-fixture integration debt, OPEN. It is neither evidence against the now-verified exact-ID DTO seam nor a reason to mark parent integration complete. The broad unchanged suite was not repeated. Existing old-fixture debt and its classification are preserved; this document does not reopen all historical T19 work or change the 66-packet count.

Root's next checkpoint is the tiny producer repair plus genuine TDD and the BANK draft, followed by actual BANK test-gap correction and implementation. Those subsequent actions and their qualification remain root-owned. This prose-only record introduces no code, tests, index changes, or runtime activity.
