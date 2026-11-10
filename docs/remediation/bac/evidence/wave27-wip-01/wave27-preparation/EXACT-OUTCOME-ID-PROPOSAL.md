# Exact accepted world IDs / LaneOutcome: static preflight proposal

Status: confirmed by static inspection only. Bank prerequisites and RED qualification remain frozen. Root retains the sole source/test-writer and integration baton. No source/test changes, imports, runtime, index operations, branches, worktrees, copies, installation, deletion, commits, or pushes were performed for this preflight.

## Finding and minimum repair

`exact_world_ids` rejects nonstrings and empty strings, preserves each exact string, and requires uniqueness. `WorldRosterDeclaration.__post_init__` uses that validator. Thus `" "`, `"\t"`, and `"\r"` are each valid declared world IDs. `LaneOutcome.__post_init__` instead tests `not self.world_id.strip()`, rejecting all three. Current-state decoding constructs `LaneOutcome`; state encoding revalidates through decoding; freezing obtains that state; frozen decoding also uses the current decoder. The producer domain therefore excludes valid declared identities at each of those completion interfaces.

After root-owned genuine RED evidence and an explicit production-change baton, replace only the world-ID predicate's `not self.world_id.strip()` with `not self.world_id`. Preserve its existing `isinstance(..., str)` check and error path. This additively aligns the accepted domain with exact nonempty strings. Preserve all field names, current schemas, serialization and fingerprint recipes, tensor ownership, other validation, and exact string contents. Keep empty and nonstring rejection. No trimming, roster narrowing, compatibility decoder, historical fallback, or unrelated refactor is proposed.

This is the required C09 stable-identity / C13 native cross-interface correction before full PW05/BANK qualification. It is not an optional extension, a new programme, or grounds for reopening all T19 history or changing the 66-packet count. Existing zero-backwards-compatibility instructions remain applicable.

## Finite later TDD case plan (not authored or executed)

Only root may authorize the next phase after current qualification is CLOSED. New test file: `tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py`, maximum 450 lines. Use the actual imported public `WorldRosterDeclaration`, `EpisodeCompletion`, `LaneOutcome`, `lane_outcome_state`, `lane_outcome_from_state`, and `freeze_lane_outcome` APIs. No surrogate codec or ENV/NN fixture is required for this DTO domain proof.

Fixture precondition: explicitly supply every required field. Completion has agent index 0, reason `cap`, survival time 1, finite dense CPU observation and meter tensors. Envelope has batch episode 0, planned horizon 2 (at least survival time), finite real reward and entropy fields, supplied world ID, and world episode sequence 1. Root must collect/import and demonstrate a passing ordinary-ID control and roster acceptance before attributing failure to the old `.strip()` predicate.

1. Passing prerequisite control: ordinary ID `world-A` constructs, produces current state, round-trips through the current decoder, freezes, and decodes from the frozen envelope. Verify full scalar fields and tensor values/dtypes/shapes using actual APIs. Separately prove that a declaration accepts the exact ordered, unique tuple `(" ", "\t", "\r")` unchanged.
2. Three positive regression families, each parameterized over exactly `" "`, `"\t"`, `"\r"`: direct outcome construction preserves the ID; current-state encode/decode preserves the ID and full envelope; freeze/decode preserves the ID and full envelope with a fingerprint matching the frozen payload's SHA-256. These must fail under the old producer predicate after prerequisite controls pass. Root records command, node IDs, failure location, old-source hash, and custody before authorizing the production edit.
3. Refusal controls: `""`, `None`, `0`, `False`, and `b"world-A"` remain rejected with `ValueError` for construction and current decoding from an otherwise valid ordinary-ID state. Do not introduce a fixture failure by changing unrelated fields.
4. Exact-identity controls: include `world-A`, ` world-A`, `world-A `, `World-A`, composed `é`, decomposed `e\u0301`, `world\rA`, `world\tA`, and `world A`. Verify exact preservation through declaration, current-state round-trip, and frozen round-trip. Together with the three whitespace-only IDs, hold every other envelope field/tensor constant and verify all distinct IDs produce distinct fingerprints. This detects stripping, case folding, Unicode normalization, whitespace rewriting, and accidental ID omission from the existing fingerprint.

After old-code RED custody, root may authorize the one-predicate edit, rerun precisely the same tests for GREEN, then run the authorized explicit-config Ruff/Black checks on the owned test and episode paths. Parent integration is still owed: these finite DTO tests do not alone establish actual full runtime or BANK acceptance. Fresh Astra source/spec/quality review and adversarial execution remain later work under root control.

## Scope, source custody, and limits

Exactly two existing source/test files were read whole; no fourth source/helper/fixture was opened. `AGENTS.md` and the assigned brief were also read as instructions. Source inventories are the observed current bytes, not the brief's estimate.

| Owned slot | Role | Current whole-file lines | Cap | SHA-256 |
| --- | --- | ---: | ---: | --- |
| `src/townlet/config/world_roster.py` | READ | 312 | 350 | `1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33` |
| `src/townlet/training/episode.py` | Later MODIFY; currently read only | 176 | 250 | `53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf` |
| `tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py` | Later NEW; not opened or authored | Not measured; no test authored | 450 | Not applicable |

Observed existing whole-source total: 488 lines. Reserved three-slot ceiling: 1,050 lines, below 5,000. The brief estimated episode at 197 lines; observed source is 176. `git check-ignore` confirmed this proposal path is ignored before writing. No test result, runtime behavior, completed integration, or GREEN claim is made. This proposal is the only file written by this preflight; remain stationary pending root's explicit baton.
