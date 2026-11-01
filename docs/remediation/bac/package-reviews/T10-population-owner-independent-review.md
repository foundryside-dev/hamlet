# Population owner fixture maintenance — independent static review r10

Verdict: no P1/P2 blocker found in the three-line standard-fixture repair. The candidate removes the false legacy relabel while retaining all four intended corruptions, their existing exception expectations, and the recursive no-mutation comparisons. This is a bounded static verdict, not an r10 test result or whole-BAC qualification.

## Custody and source receipt

Reviewed the existing `/workspace/hamlet` only. HEAD is `214408b107730b4511b8a690541569aeca4b7b67`; the index tree is `973ba6470ae481c0d14050c19f1022614a1b5bcd`, matching `generation-green-r10-candidate.json`. All 30 manifest SHA256 entries verified successfully through digest-only checks. `git diff --name-only` was empty. The three reviewed files' working contents correspond to their index entries. Fourteen worktrees remain present; none was created, changed or removed by this review.

Read `AGENTS.md` and the two requested prose artifacts, `population-owner-causal-diagnosis.md` and `population-owner-maintenance-r10.md`. Explicit session scope preservation governs over the generic pre-release compatibility-deletion guidance. No durable user-only rule was adopted; existing instructions, Emmy's session scope authority and actual tool approvals remain authoritative.

Read exactly these three whole source/test files, 4413 distinct lines total. The first large display was truncated by the output wrapper; bounded overlapping displays covered the missing ranges before this verdict. No fourth source, conftest, fixture, helper, historical implementation or PER implementation was read. Digest checks on other manifest paths did not expose their contents into this review context.

| Whole file | Lines | SHA256 |
|---|---:|---|
| `tests/test_townlet/unit/population/test_vectorized_population.py` | 1882 | `843558019df85fb2e4fd508df90653ebef3f2de26bb29d7fabc26e798dca8948` |
| `src/townlet/population/vectorized.py` | 1854 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| `src/townlet/training/replay_buffer.py` | 677 | `d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8` |

Index blob IDs are respectively `0ec18f7b9d207b9f07ed819c3c91f0f5ddb94273`, `9e2cd5a30176fbbda86b16a2635f8707b0b2548e`, and `f72fd80b34a19f735f967b8c3b35a269f24d5dc7`. The index file SHA256 before report writing was `cb1973e19e423908ff23d831a4ea2fccdccabbbd0aa51c6538a9488ef6d6769d`. `vectorized.py` also has no difference from HEAD. Both reviewed production files have no difference between r9 tree `b34cf49af0bd041fffb197d2096a4a52d6179dc7` and the r10 candidate.

## Before/after assertion semantics

The actual r9-to-r10 diff in this source inventory changes exactly test lines 1000, 1002 and 1003. No corruption branch, expected diagnostic or state comparison changes.

| Shared producer precondition | Before | After and consequence |
|---|---|---|
| Outer population version | Assign 6 | Assert 6; a producer ABI mismatch is exposed instead of overwritten. |
| Uniform nested replay version | Assign 4 to current producer output | Assert 5; the emitted version and its exact key set remain consistent. |
| Initial nested replay kind | Assign `standard` | Assert `standard`; wrong producer routing is exposed before a deliberate kind corruption. |

These assertions are supported directly by the inspected producers: population format constant 6 and `get_checkpoint_state()` at `vectorized.py:46,1160-1198`; uniform format constant 5/kind `standard`, the exact key definitions, and `serialize()` at `replay_buffer.py:31-45,423-450`. The test's `_standard_population` pushes two transitions at lines 817-824. The uniform serializer owns cloned row tensors, so the later replacement of serialized observation fields with narrowed views does not narrow live replay storage. The wrong-kind and version branches change only serialized dictionary values.

The prior assignment to format 4 manufactured a hybrid payload. Uniform validation accepts supported integer versions before selecting a version-specific exact key set (`replay_buffer.py:470-482`). Format 4 excludes eight current keys: `action_dim`, `legality_mode`, `historical_archives`, `next_action_masks`, `legality_recorded`, and the three component-presence keys. That gate precedes kind and width validation. Leaving producer format 5 intact removes the earlier unrelated error without weakening the gate.

## Independent control-flow assessment

| Existing corruption case | Retained mutation / expectation | Static path in r10 |
|---|---|---|
| `replay-kind` | Kind becomes `prioritized`; match `replay_kind` | Current exact keys remain valid. The uniform kind gate at `replay_buffer.py:483-484` rejects the corruption before storage work. |
| `replay-version` | Version becomes 3; match `format_version` | Unsupported-version gate at lines 470-472 still precedes key validation. Asserting producer version 5 does not remove this deliberate version-3 refusal. |
| `replay-width` | Both observation tensors lose one column; match `obs_dim` | The producer's kind, keys, size/position, unconstrained metadata and empty archive list remain valid. Expected current observation width is supplied by population validation; lines 533-538 reject the narrowed observations before row restoration. |
| `current-env-width` | Monkeypatch environment width by +1; match `token_spec.total_dims` | Population width gate at `vectorized.py:1612-1618` rejects before nested replay validation. It now starts with an otherwise honest current replay fixture. |

Population `load_checkpoint_state()` calls complete validation at line 1754 before replay materialization at 1767 or any network, optimizer, scheduler, counter, replay or exploration state application at 1770-1779. Its nested replay call is at 1744. Each of the four inspected rejection paths occurs before that application region. The test retains the same `pytest.raises(ValueError, match=expected_message)` and before/after recursive equality at lines 1018-1023. No broad catch, accepted-set expansion, regex broadening, skip or key stripping was introduced.

The prior outer population version 5 refusal at test lines 847-869 still changes the outer version to 5 and matches `population checkpoint version.*5.*expected=6`; it reaches the first exact-current population version gate at `vectorized.py:1594-1600`. Exact-integer negative controls for `6.0` and `True` also remain intact. These are version-gate controls, not proof of an authentic historical artifact's shape.

PER's case at test lines 1025-1057 is byte-for-byte unchanged by this repair: outer 6, nested 4, wrong kind `standard`, the `replay_kind` expectation and recursive no-mutation comparison remain. Population construction routes prioritized configuration to `PrioritizedReplayBuffer` at `vectorized.py:268-280`; uniform format 5 therefore must not be imposed on it. The maintenance prose reports root's separate confirmation of the PER format-4 ABI. That provider was outside this independent source inventory, so this report neither independently certifies its ABI nor invents a demonstrated PER failure.

## Findings and limits

- P1 blockers: none found in the reviewed fixture maintenance and its inspected rejection paths.
- P2 blockers: none found. The contradictory uniform format-4 relabel that masked kind/width validation is removed, with the intended assertions preserved.
- Optional P3 observation: the existing no-mutation snapshot covers network/target, optimizer, scheduler, counters, serialized replay and exploration state, but its incoming valid fields generally equal the same population's current fields. Equality alone cannot detect a redundant early application of identical values. The inspected validation-before-application ordering supplies the independent static evidence here; this is an existing oracle limit, not a demonstrated r10 regression or a request for another repair.

No genuine uniform format-4 archival positive control exists in this owner file, and none was removed. The inspected uniform code keeps old-format rows in a separate legacy path, materializes them through archive creation with empty active replay (`replay_buffer.py:603-613`), and refuses explicit full resume without historical legality (`668-670`). The historical module's own qualification, archive invariants and PER validation internals were not reviewed. This receipt cannot substitute for that existing evidence or for executed qualification.

Only static shell/Git inspection and this ignored prose report were performed: no application imports, execution, pytest, probes, helper scripts, source/test edits, staging, commits, new branches/worktrees, source copies, deletion or delegation. Both working and cached `git diff --check` for the owner test exited 0. Root retains runtime, candidate and index custody and must attribute any executed r10 results separately.

Stationary: the only authored artifact is this ignored report. Final source digests, HEAD, index digest and empty local diff were rechecked after writing; they match the receipt above.
