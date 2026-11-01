# Compact-token owner independent static review — r10

Verdict: **SCOPED STATIC PASS for the compact-token owner-fixture maintenance. No actionable P1/P2 defect found in this maintenance within the authorized inventory.** This is not runtime qualification, a whole-BAC review, or a claim that archive payload/query/export and subsequent qualified training have been independently verified here. Writer is stationary after this ignored prose record.

## Authority and frozen receipt

Read `/workspace/hamlet/AGENTS.md`. The dispatch's explicit user-preservation instruction governs genuine supported old4 history; the generic pre-release delete-compatibility guidance is not authority to remove that support. Existing project/Emmy session scope and actual tool approvals govern; this review saves no new durable user-only rule.

Reviewed `/workspace/hamlet` against candidate manifest `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave04-preparation/generation-green-r10-candidate.json`:

- HEAD: `214408b107730b4511b8a690541569aeca4b7b67`.
- Index tree: `973ba6470ae481c0d14050c19f1022614a1b5bcd`, exactly the manifest candidate tree.
- `git diff --exit-code --name-only` returned zero with no paths: no unstaged tracked difference.
- `git diff --cached --exit-code --name-only 973ba6470ae481c0d14050c19f1022614a1b5bcd` returned zero with no paths: the index matches the candidate.
- The 22 staged campaign paths are existing root-owned candidate changes, not reviewer changes. Only the authorized test diff was opened; other campaign source/diffs were not inspected.
- `git check-ignore` confirms this review destination is ignored.

Whole source inventory read in full, independently assessed:

| Source | Lines | SHA256 |
|---|---:|---|
| `tests/test_townlet/integration/test_compact_token_acceptance.py` | 614 | `e21040b74b60b95d6e4591cb1c43df5cf8c60d114d481ae3f8f1a4d8a627cc06` |
| `src/townlet/training/replay_buffer.py` | 677 | `d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8` |
| `src/townlet/training/prioritized_replay_buffer.py` | 758 | `0248df10333845fd2498d10c2cfb9b59dabcce8c5e8f91f9e645bf9782f4c61c` |
| `src/townlet/training/sequential_replay_buffer.py` | 543 | `6c0b0d644677a6171f03e2ad62b8ab7b99669e401ac630bb2ea2106828e628a7` |

Total: **4 whole source files / 2592 unique source lines / 124543 bytes**. A 16-line reread recovered a tool-output truncation, and the authorized test diff is 82 displayed lines including headers/context. Conservatively charging every diff line as source gives **2690 inclusive lines**, below the 5-whole-file/5000-line cap. Hashes and line counts were obtained from the actual workspace files. Test and uniform hashes match the candidate manifest; all four match the maintenance receipt. The three runtime hashes also match the earlier causal diagnosis, so this r10 owner maintenance adds no runtime edit relative to that receipt; this is not a claim that campaign runtime source equals HEAD.

Also read the two authorized ignored prose records, `compact-token-owner-causal-diagnosis.md` and `compact-token-owner-maintenance-r10.md`. Their earlier runtime/lint results are attributed owner/coordinator evidence, not tests performed by this reviewer. No HC source, fixtures, helpers, or additional source file was opened.

## Independent semantic assessment

1. **The repaired diagnostic matches the actual uniform validator.** The matrix retains a deep copy of current5 and explicitly retags it4 at test lines487–496. Uniform `_validate_serialized` accepts supported integer4/5 first, then chooses the corresponding exact key set at replay_buffer lines470–482. A current-key payload with tag4 therefore reaches the key-set mismatch, not an unsupported-version diagnostic. The test does not turn this mixed schema into an accepted old artifact or weaken the exception to a generic refusal.

2. **PER and sequential retain their distinct contracts.** Test lines497–501 retain the exact-current-version regex and add deep before/after snapshots. PER current4 checks the version before kind/key validation at prioritized_replay_buffer lines531–546; sequential current5 does the same at sequential_replay_buffer lines413–429. Their current-minus-one negatives still target the correct diagnostics. Uniform's historical exception has not been generalized to these backends.

3. **The old4 positive is genuinely separate.** Test lines505–519 explicitly enumerate the exact 13 old fields, with literal kind/version/capacity/size/position and cloned transition tensors. It is not generated from private production key constants or a blanket unknown-field filter. `_transition_batch` supplies eight float32 observation/reward rows, int64 actions, bool dones and explicit DAC components; size8/position8/capacity16 agree with the validator's shape and cursor rules at replay_buffer lines485–491 and533–559. Compact width is independently supplied as `spec.total_dims` to validation.

4. **Inspection and full-resume refusal are separate assertions.** Test lines520–527 validate genuine old4 without installation, then require `HistoricalLegalityUnavailable` with the missing-historical-successor-masks diagnostic. The live destination already holds the original eight current rows. `load_for_mode` validates and checks the old4/full-resume combination at replay_buffer lines668–670 before calling materialization/installation at line673. The test does not claim masks can be inferred for old history. Deep input and live serialization snapshots are compared after both calls.

5. **Automatic old import exercises archive/fresh-active semantics.** Test lines529–540 use a separate fresh destination and the ordinary auto entry point. ReplayBuffer lines603–613 materialize old state into an archive and zero active storage; lines675–677 route ordinary loading through auto. The test requires zero retained transitions, length and position, one historical archive, and refusal to sample a positive active batch. A current-version archive-bearing serialization must round-trip exactly into another fresh buffer. The original old input remains exact after the load/sample attempt.

6. **Unsupported history remains distinct.** Test lines542–548 use explicit version3 on the genuine old shape and require the unsupported-format diagnostic, with exact before/after input and populated-live comparisons. ReplayBuffer lines470–472 reject this version before any schema/materialization route.

7. **Existing acceptance controls remain present.** The candidate-versus-HEAD test diff contains only the imported public exception binding and the expanded final version/history block. Existing sample compact-width, shape/dtype, mask/weight/index and current exact-round-trip assertions at test lines468–485 are intact. The substrate, architecture, BPTT, outer checkpoint, and malformed effect-selector controls remain intact. Deep snapshots are appropriate because sequential serialization can expose CPU views at sequential_replay_buffer lines355–370; a shallow live-state snapshot would weaken refusal-purity checks.

## Limits and required owner evidence

No maintenance defect requires a source repair from this review. Two explicit coverage boundaries remain, with concrete follow-through for root:

- **Archive payload preservation is not proved by this matrix.** One archive plus an exact archive-bearing current round-trip proves stable serialized transport of the produced archive; it does not compare the archived source payload to the original 13-key artifact, inspect the digest, query rows, or exercise export. A consistently incorrect archive could satisfy those narrow assertions. Retain and qualify the separately owned genuine-old4 payload/digest/query/export tests. This reviewer did not open those tests or HC and cannot attest to their completeness.
- **Subsequent qualified fresh replay is not exercised here.** Zero active rows and positive-size sample refusal protect the immediate boundary. This block does not push fresh recorded transitions, check readiness, or prove only those fresh rows become training eligible. Retain and qualify the separately owned policy-A fresh-qualified-replay controls. The purity checks compare input and serialization-observable live state, not arbitrary hidden fields or RNG state.

Root should run all three `test_replay_matrix` parametrizations, then the owning compact-token acceptance suite and mandated broader gates against this exact candidate. Keep supported real old4 artifacts/query/export, fresh qualified active replay, and explicit maskless full-resume refusal as separate acceptance claims. No runtime pass, no full retry result, and no whole-wave/BAC/release qualification is asserted by this static report.

## Reviewer actions

Only this ignored prose was written. No project imports, runtime execution, pytest, executable helper/probe, tracked/source/test edit, staging, commit, branch, worktree, source copy, deletion, or delegation was performed. Static shell reads, hashes/counts, Git metadata/diff inspection and an index-tree receipt were the only inspections. No additional work is pending from this reviewer; stationary for root-owned qualification.
