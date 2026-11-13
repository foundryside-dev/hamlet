# R0 replay child verifier — authored and frozen, checks UNRUN

2026-11-13. Root released the tooling writer after Stage B application source
freeze. Only the two newly named tooling bodies below were written. The old
102-line verifier remains byte-identical. No application source body was read,
imported, copied or executed; no Git/index, branch/worktree/checkout/repository
creation, subagent or application edit occurred. Synthetic tests and static
checks are **UNRUN by author**. Independent other-model source review is required
before real use; root owns checks, actual execution, candidate binding and custody.

| Body | Lines | SHA256 |
| --- | ---: | --- |
| Q/verify_bac_publication_spawn_identity.py (read-only) | 102 | 8fd7638fca79d2479286821f55573445f1acb4fc28a5efd801cec8a40cb53209 |
| Q/verify_bac_replay_spawn_identity.py (new) | 154 | 0986a6f3edebc0a208da073eda849ccb8f9d867a330fe1c2848ac38158e6f868 |
| W/evidence-management/test_replay_spawn_verifier.py (new) | 234 | 3f01b82ca3f5c3c2cb5629d11aa398e611efcbe2bbc0f736d41ee64261f44633 |

Q=/workspace/bac-review-2026-11-01/qualification;
W=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades.
Whole source packet490lines/3bodies, within102+300+600 ceilings.

## Exact bounded contract

CLI: `python Q/verify_bac_replay_spawn_identity.py SPEC [JOB_INDEX]`, default
index0, negative indices refused. Fixed role `replay_poison`, message
`replay poison fail closed`, job name `replay-poison`. Root sealed exact args:
`-m pytest tests/test_townlet/regressions/bac/test_replay_rng_custody.py::test_isolated_replay_poison_refuses_all_direct_samplers --no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q`.
The actual spec/result schemas were taken from root-authorized R75 DATA JSON,
then restricted to this newly sealed R76 job contract. Result command must equal
the root venv interpreter plus those exact args. Spec workers must be1 (harness
concurrency, not an xdist worker claim). Completed parent exit must be exact
integer0; result name, manifest/base/tree, pinned harness SHA and log bytes/path
must agree. Harness SHA is pinned to
`180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

Strict schemas cover spec, selected job, result, controller, child and observation.
Manifest source/config/artifact inventories retain existing format, permitting
manifest metadata beyond the fields used by this verifier. Every expected import
must be present in source_files. Source/config/artifact bytes, current HEAD,
locked write-tree, clean unstaged diff and exact worktree registry remain guards.
The new helper intentionally performs these Git/index checks only when root runs
it; author performed none. Existing bootstrap imports3 remain exact; separate
replay_imports requires fully qualified townlet.training keys for replay_buffer,
prioritized_replay_buffer, sequential_replay_buffer and replay_contract.

Positive exact integer child PID/PPID and parent Process/queued/parent PIDs must
pair: child.pid == observed.process_pid == observed.queued_pid, child.ppid ==
observed.parent_pid != child.pid. Child exit0, qualified True, exact message,
manifest identity, worker identity, debug True, intra1/interop5, package/import
paths and controller/child Torch version agreement are required. These extend
new producer observations; historical records did not contain PPID and are not
rewritten or reinterpreted.

Output `replay-spawn-custody-replay_poison.json` uses exclusive creation. It binds
spec/manifest/result/controller/child/observation/self hashes, pinned harness,
actual PIDs and narrowly worded CPU child scope. Missing UTC timestamps remain
disclosed. No environment values absent from actual result are invented: root's
supplied OMP/MKL/OpenBLAS/CUDA/PYTHONPATH/BAC environment setup is harness context,
not a newly claimed recorded attestation. The verifier checks recorded identity
facts and fixed command/harness bindings; it does not establish JSON authorship
independently of root's trusted actual producer execution.

## Root-only proposed validation — UNRUN

From /workspace/hamlet, without app imports or real Git calls:

```
.venv/bin/python -B .superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/test_replay_spawn_verifier.py
.venv/bin/ruff check --no-cache /workspace/bac-review-2026-11-01/qualification/verify_bac_replay_spawn_identity.py .superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/test_replay_spawn_verifier.py
```

Tests create isolated synthetic DATA files, never import their placeholder source
paths, and mock subprocess metadata calls and flock. Controls cover valid receipt,
exclusive duplicate preservation, wrong role/message/PID/PPID, parent failure,
partial/unknown schemas, missing records, missing/wrong/extra import keys,
manifest/source/config/artifact/tree/HEAD/registry mismatches, coherently changed
commands and invalid job index. Ordinary temporary fixture cleanup is local test
housekeeping; no historical evidence is deleted. These tests prove only verifier
logic, not real child execution. If root's static configuration imposes formatting
changes, those change the tooling hash and need a new freeze before review/use.

This tool admits only the explicitly named one-controller CPU replay poison
consumer job. It does not qualify a broader suite's child, CUDA, restoration
failure, other roles, or the whole application. Parent source assertions and root
independent actual evidence verification remain essential. **CODE FROZEN;
TESTS/STATIC UNRUN; REAL CHILD QUALIFICATION UNRUN BY AUTHOR.**

## Fix round 1/5 — D1 elapsed duration, frozen

Root granted only the two new tooling bodies after independent Sol review
`98717b6f...` identified that result.seconds was present but not validated.
The verifier now requires exact int/float type, finite value, and seconds > 0;
null, booleans, strings, zero, negatives, NaN and infinities refuse before custody
publication. A focused synthetic test exercises each of those negative cases.
No other contract or application source was changed. Author ran no static check,
synthetic test, application import/execution, Git/index action or actual verifier.
Root's earlier12 tests and independent12 tests remain historical overlapping
pre-fix results; they do not validate these new bytes.

| Frozen body | Lines | SHA256 |
| --- | ---: | --- |
| Q/verify_bac_replay_spawn_identity.py | 157 | aef826f304f66798c1845bdf1436b8fb27336708776a514f50d2f353942402a8 |
| W/evidence-management/test_replay_spawn_verifier.py | 241 | bf2a20c8f2fa7120219717b62a8db4186e3914b66e78b0efe3955c2293658b4f |

Whole three-body packet500lines including the unchanged102-line old verifier,
whose SHA256 remains8fd7638fca79d2479286821f55573445f1acb4fc28a5efd801cec8a40cb53209.
Earlier new-helper/test hashes remain recorded above and in root's retained
REVIEW.diff; no historical evidence was overwritten. Root commands above remain
**UNRUN by author for fix round1**. Root must rerun synthetic checks and obtain
the same other-model scoped review before real poison use. **FIX1 CODE FROZEN.**
