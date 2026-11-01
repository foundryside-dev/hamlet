# T03a independent SPEC/QUALITY review r0

Verdict: CHANGES REQUIRED (one confirmed P2). Review applies only to the original fixed candidate below, not subsequent shared-source repairs. Runtime completed 2026-11-01; no runtime rerun while recording this report.

## Candidate and scope

Base HEAD `1f9d831a8fe76ab00e06774ef6888985f6c2aec2`; index tree `ca22c9f84e79828c8f6bc6b4a31a53a6e46ace75`. Existing `/workspace/hamlet`, root MAIN. Exactly five whole source files, 2473 lines, plus the bounded inline probe below. No sixth implementation/test/helper source read or created, no source/test edits, stage/commit, worktree, copy, or delegation. Read AGENTS.md, T03a brief/work report, HC digest clarification, candidate manifest and native DATA. Approved history A preservation supersedes blanket pre-release deletion instructions.

Original source SHA256:

- `src/townlet/training/historical_checkpoint.py` (509): `6ab341e35dd959645eeb1717b136feb5f2a8efa6a903ac19ca64824e9182202c`
- `src/townlet/training/checkpoint_utils.py` (777): `591040896a3e83df23912b2167e6d885abd0b949debfd754ddd23193da9937df`
- `src/townlet/config/brain_config.py` (568): `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`
- `src/townlet/training/replay_contract.py` (222): `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c`
- `tests/test_townlet/regressions/bac/test_historical_dispatch.py` (397): `5dca328391648d4aeea3283937640385bd5638f3c5e005511a356766cbcbdb2e`

Native artifact SHA256, verified in the probe against portable-manifest.json:

- uniform.pt: `44a77c9e6edf183eaa5cb5761bad4999f0947175d51e8b308b7c2d3fcaf99d6d`
- per.pt: `8b4102b02e9a6d94e31095b67a5b1bb8e57641f60f3c3658fa2cb2f313f33c30`
- sequence-trained.pt: `f5ca18d9e4f8c8f9398d585fc2a7861d23883ca9a8ae7175c964e2e97e16ced6`

## P2: mixed optional reward components disappear from sequential queries

Location: original historical_checkpoint.py lines 264–266, especially `if all(episode[key] is not None for episode in episodes)`.

Contract: approved P2 archive query access preserves recorded rewards/components exactly; missing historic values must remain honestly unavailable. Existing sequential5 public validator accepts independent None/tensor optional components per episode (root supplied this source fact; reviewer independently executed the public validator).

Reproduction uses the complete genuine sequence-trained artifact, not abbreviated invented state: deep-copy its replay state; change only episode 1 rewards_intrinsic to None; call SequentialReplayBuffer(capacity, cpu).validate_serialized with the actual observation width; construct HistoricalReplayArchive with its correct state digest. All validation accepts. Query offset 0 with limit equal to episode 0 length, where every requested row has intrinsic rewards. The result omits rewards_intrinsic. A two-row window crossing episodes also discards the available value. The implementation checks every episode before slicing, so an absent component in unrelated history removes recorded data from an otherwise complete query.

Complete state export still roundtrips exactly; this is query-access loss, not destruction of stored archival bytes. Repair should preserve known values and explicitly represent missing coverage without inventing recorded rewards. Permanent regression should cover known-only, missing-only, and crossing windows.

## Independent runtime evidence

One authorized CPU process; torch threads 1, OMP/MKL/OpenBLAS 1, CUDA empty. Pre/post in-process guards verified HEAD, index tree, no unstaged diff, all five original hashes and HC import root. A final shell check repeated HEAD/tree/no-unstaged and HC/test hashes. Native data hashes remained unchanged.

Passed controls:

- Actual existing old uniform/sequential validation callbacks via the owned regression's prepared helper (including actual population validation); no positive no-op validator.
- Mixed-component state accepted by actual sequential public validator; exact archive export.
- source_formats, restored_clocks, learned-state and encoded-state mutation cannot mutate owned archives/envelopes.
- Current-shaped primitive dispatch for auto/full/inference retains active rows and embedded archives, survives codec roundtrip, and refuses unrecorded legality. This is explicitly primitive evidence, not native current-format runtime installation.
- Canonical bool/int/float, list/tuple, bytes/bytearray, dict/OrderedDict, signed-zero, NumPy dtype and tensor dtype/bit distinctions; equal logical tensor values across layouts.
- Injected first (file) and second (directory) fsync failures propagate, remove destination/temp files and preserve owned source state.

Actual stdout, exit 0 (PTY session 6156; initial chunk e916df, completion chunk 28d926):

```text
actual old validation callbacks: uniform and sequential PASS
MIXED_COMPONENT_REPRO {'validator': 'accepted', 'episode0_has_intrinsic': True, 'restricted_query_has_intrinsic': False, 'cross_query_has_intrinsic': False}
mixed state export exact PASS; query omission confirmed
ownership metadata/state/encoding PASS
current-shaped primitive dispatch/active retention/unknown refusal PASS (not native current integration)
typed scalar/container/dtype/logical tensor bit distinctions PASS
file and directory fsync failure cleanup/owned state preservation PASS
fixed source/index/native fixture post-guard PASS
```

The runtime command was `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' .venv/bin/python - <<'PY'` from `/workspace/hamlet`. Its exact 102-line inline body and full command are preserved as evidence data in `T03a-independent-review-r0-evidence.json`, transcribed from the original functions.exec invocation producing chunk e916df/session 6156. Combined source accounting: 2473 + 102 = 2575 lines. No standalone probe source was created and this body was not rerun while persisting evidence.

## Separate root-run status and limits

Root reported the original owned suite at these exact bytes: 11 passed / 4 PER failures. The four failures stem from scratch PER construction with annealed beta=1.0 rather than beta_initial=0.4, before intended assertions; not claimed as HC production failures or independently rerun here. Root authorized test-only PER prerequisite repair and permanent mixed-component regression; production repair awaited intended RED.

Root also reported 13 mypy errors and no-defaults/lint blockers; these remain separate pending qualification issues. Logs: `/workspace/bac-review-2026-11-01/qualification/wave03-green-r0/T03a.log`, `mypy.log`, `no-defaults.log`. This review does not claim those checks pass.

Future T10–T12/T25 runtime adapter installation, fresh-buffer/warmup behavior and actual current-format full resume are not omitted T03a deliverables. Repaired-source reassessment must inspect the actual changes and run fresh bounded verification against newly frozen hashes; this report is not acceptance of later edits.
