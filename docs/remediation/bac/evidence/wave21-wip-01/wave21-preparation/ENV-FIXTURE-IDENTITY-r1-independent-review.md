# Actual basic_env R1 independent review

SOURCE: APPROVE. SPEC: APPROVE. QUALITY: APPROVE. No defects found within this bounded static review. Independent runtime: NOT RUN; explicit root slot remains required. No integration closure is claimed.

Reviewed the actual fixture and consumer at frozen base 7e702ab8 / root-supplied R1 tree 4c0cec9a4cd8893910a0abb64c396eb7011f5787. These identifiers are supplied receipts; no Git/index command was run. The brief was read first, followed by ENV-FIXTURE-IDENTITY-report.md and ENV-FIXTURE-IDENTITY-r1-review-package.md. The latter supplies the exact two-file R0-to-R1 delta. Actual on-disk source and SHA256 checks corroborate the named sealed files. No fifth implementation/test/helper/provider/WS file was opened.

## Counted source custody

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/environment/vectorized_env.py | 2399 | 5508110716c38d89497c6d3c0443d6eba15f7bd546b9f2231dd86a41f5b6c166 |
| src/townlet/config/world_roster.py | 312 | 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33 |
| tests/test_townlet/_fixtures/environment.py | 466 | 85467cd5cfe169306c2893944041c1e58d5fe21941498cca6cb2bd7ab9022180 |
| tests/test_townlet/unit/exploration/test_exploration_strategies.py | 1358 | 9dca12dcd0c58aef663b3287052fed40e3c233517e6010ad4513fe0cc7f43dc7 |

Total 4 whole files / 4535 lines, within 4800 and individual 2400/350/550/1500 caps. wc and sha256sum exited 0. ENV and roster match their sealed read-only receipt byte hashes. This reviewer changed no source or tests. The only write is this ignored review artifact; ignore status is received from root, not independently queried through Git.

## Source and specification findings

The actual basic_env fixture at environment.py:44 compiles the same test_config_pack_path, selects L0_test, retains one agent and explicit device, and calls the real VectorizedHamletEnv.from_universe. It adds a literal authored WorldRosterDeclaration(world_ids=("basic-env-world",)), passes that declaration's exact world_ids tuple as lane_world_ids, and supplies universe.get_level("L0_test").training.seed. This is declared test-owned identity rather than row-derived or config-label identity discovery. The environment level and training seed lookup select the identical explicit level. The owner report attributes to root the finite source-verified receipt that TrainingV2Config.seed is a direct int field (training_v2_config.py:347); this review consumes that receipt without opening a fifth source file. No hardcoded/fallback seed or signature adaptation appears.

Actual ENV from_universe (1038–1072) requires all three world inputs and forwards them unchanged through its actual factory route. Constructor identity validation (1939–1971) checks declaration, exact integer seed/count, full roster membership and lane cardinality, then creates fresh-unbound state with zero accepted cursors. WorldRosterDeclaration validates and owns the immutable ID tuple. No validation is replaced by fixture logic.

All 18 actual basic_env test functions in strategies.py:986–1358 use the fixture only for observation_dim. They comprise seven RND completeness cases, seven AdaptiveIntrinsic completeness cases, two round trips and two malformed-state refusal cases. Their actual network tensors, predictor/Adam training, optimizer/network restoration, novelty comparisons, epsilon/history/weight checks and strict malformed-state assertions remain in place. ENV assigns observation_dim from the selected level's compiled token_spec.total_dims at line 380 during construction; constructor completion does not call reset or activate an episode. Consequently the repair needs construction and metadata, with no episode permission. Actual reset still requires an issued reservation (2090) and step still requires active world phase (1287). The fixture neither forges bootstrap/owner receipts nor bypasses those guards.

The only strategies delta in the supplied package adds epsilon_min=0.0 beside epsilon_start=0.0 in TestAdaptiveIntrinsicActionSelection.test_select_actions_delegates_to_rnd. The actual test retains rng=None, explicit vector_tick clock, real AdaptiveIntrinsicExploration.select_actions and both positive argmax assertions. The current backend prose receipt requires valid epsilon bounds/floor. Transporting an explicit zero floor expresses the existing greedy intent without weakening the assertion or changing provider behavior. Provider implementation is outside this four-file review and was not opened.

The actual fixture file retains the other nine from_universe sites and their configuration, substrate, overrides and factory features. Those sites still lack current identity inputs; they remain outside this narrowly authorized causal repair. The supplied two-file delta does not rewrite or disable them. No new helper, probe, test, monkeypatch, synthetic observation or lifecycle adapter is introduced.

Allowed prose reviewed: CURRENT-WORLD-IDENTITY-CONTRACT, CURRENT-WORLD-CONSTRUCTOR-TRANSPORT, CURRENT-WORLD-VFS-CONTRACT and CURRENT-BACKEND-LOCAL-SERVICE-CONTRACT. Historical direct-constructor routing and scalar VFS statements are superseded by the current transport/VFS receipts and actual ENV source. This fixture repair does not rely on those historical statements.

## Evidence limits and required next gate

This review ran only static text/line/hash operations. It ran no project import, runtime, pytest, lint process, installation, Git/index/branch/worktree operation, repository copy, deletion or subagent. Root reports the actual 19 existing prerequisite cases PASS in 10.8583s (18 checkpoint cases plus greedy consumer), with 196-source/573-config/13-artifact/1-process custody PASS. Those results are attributed to root, not independent execution by this reviewer. Independent execution of those same 19 cases remains pending explicit root slot clearance.

The unchanged required actual runner node test_native_runner_checkpoint_retains_tail_and_rejects_corruption remains OPEN. Its code is preserved and it may be excluded only from a separately labeled component proof while actual runtime/bank/native prerequisites are repaired. Neither this source approval nor root's prerequisite PASS closes that node, the nine other fixture constructors, broader suite obligations, or integrated BAC acceptance.

## Independent runtime qualification after explicit slot clearance

Root explicitly cleared the independent 19-case slot after its component and guard sessions closed. Executed the exact authorized commands sequentially:

```text
TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave21-r1-global-independent-spec.json
python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave21-r1-global-independent-spec.json
```

Both exited 0. Independent result: 19 PASS, 0 skipped, 0 xfailed/xpassed, 0 warnings; 8.171828269958496 seconds. This is the actual 18 basic_env checkpoint consumers plus the existing greedy positive case. The locked run identifies exact base 7e702ab885c2bc1bba37652273cfb89742624f08 and candidate tree 4c0cec9a4cd8893910a0abb64c396eb7011f5787. Run log: /workspace/bac-review-2026-11-01/qualification/wave21-r1-global-independent/global-independent.log; SHA256 80d4bb25e94773670735e233ec38a8aa1f6122dc59c0915fd9c2c5427b21549d.

Verifier custody: 196 source guards, 1 process identity, 573 configuration digests, 13 protected artifacts, 14 registry records and 1 available worktree; source_index_import_threads_fixture_custody PASS. Harness session 13631 completed with exit 0 and no active reviewer execution session remains. No helper source was opened and no counted source/test was changed; counted static inventory remains 4/4535 within 4800. Earlier NOT RUN/pending statements describe the static-review stage and are superseded by this completed runtime receipt.

Final bounded verdicts: SOURCE APPROVE, SPEC APPROVE, QUALITY APPROVE, INDEPENDENT 19-CASE RUNTIME PASS, CUSTODY PASS. Root separately reports 412 component cases PASS in 26.2254 seconds with exactly one unchanged required actual runner explicitly deselected. That is an attributed component proof, not 413 PASS or PW04 release. test_native_runner_checkpoint_retains_tail_and_rejects_corruption and actual runtime/bank/native prerequisite repair remain required OPEN; no integration closure follows.
