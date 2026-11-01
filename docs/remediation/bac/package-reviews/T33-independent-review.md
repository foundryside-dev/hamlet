# T33 fixed independent review r9

Verdict: PASS — scoped T33 design, implementation and independent runtime review at exact r9. No unresolved P1/P2 or in-scope blocking gap established. No full-BAC/GPU/release qualification is claimed.

Candidate: HEAD `214408b107730b4511b8a690541569aeca4b7b67`, coordinator staged tree `b34cf49af0bd041fffb197d2096a4a52d6179dc7`; 28-file manifest `generation-green-r9-candidate.json`. Read-only git inspection found no unstaged tracked difference and the expected 14 existing worktrees. No source/index/branch/worktree mutation, source copy, imports, tests, application probes, prior probe-source reads or delegation occurred during this phase.

Complete inspected source inventory (four whole files, 3422 lines):

| Source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/recording/recorder.py | 699 | 8fca0b033bdc74f9e8146006c029b8bce6228b067f89b72109e1a886f4a32825 |
| src/townlet/demo/database.py | 1178 | 7335e9798d15e14721e5278cb4e7402eea7f7da2344187c56f8bc8e42b93902e |
| src/townlet/recording/receipts.py | 114 | f4f90c3ae1584965cbfc7ad84170fb3b0413ba5599a9eeb3d0d447f48b6fd647 |
| tests/test_townlet/regressions/bac/test_recording_drain.py | 1431 | 90b876583bcc6bf047cfd7f424dac889a86103b5109bef29c38bcce838e18912 |

Normative proposal read completely and SHA verified: `b28387782a8e3f9b09d5644fd59461fa9ca4f3389d64d44cd090a934260bb18c`. Independent design review r1, activation JSON, accepted P8/T33 task brief, root AGENTS and baseline witness report were also read. User preservation overrides blanket pre-release deletion guidance. Historical T24/T25 native checkpoint handoffs remain outside this storage review.

## Static reassessment

Legacy repeat and file-only routes create nonce-separated immutable artifacts and independently copied/replaced aliases. Indexed legacy rows use explicit original relative locator and full fifteen-field reconciliation; positive generations are allocated inside an owned DB lease. Scoped identity remains exact with generation zero and collision refusal. Receipt grouping follows sequence tickets rather than repeated episode keys. Legacy queue.Full handling is narrowly caught with cumulative read-only counters and per-boundary dropped/accepted reconciliation; strict qualified/bound routes do not increment legacy counters. The fence, sentinel, task completion, incomplete-group reporting and cached shutdown result/error retain the closed-set contract.

Closed companion schema2 pins complete sqlite_schema inventory and DDL, its tagged association and integer/metadata rows. Canonical v1 classifier is retained. Unassociated/v1/foreign index evidence is refused before owner opens; ordinary canonical/scoped reads do not create a companion. Both closes and complete checkpoint admission retain owned-family custody.

The r9 ancestor repair is substantive: writer admission walks physical output ancestry through filesystem root, including existing entries left by failed prior owners; index creation does the same with a sticky flag cleared only after all fsync/close operations succeed. Associated fresh DB owner admission sets the flag and executes that synchronization immediately, so read-only reopen followed by close/checkpoint need not perform a publication. This requires direct runtime recovery and lifecycle witnesses rather than inferred PASS.

Nested publication cleanup handling now descends ExceptionGroups to obtain primary publication observations while preserving the entire grouped cause. A companion commit-after-success exception therefore retains unconfirmed index state and actual index ID even if root release also fails. Required permanent negative control exercises these observations, earlier artifact/row preservation and canonical latest state.

Root guard uses persistent inode flock plus root-keyed reentrant thread ownership; publication acquires root before DB and holds DB generation lease through commits/readback. Same-thread nesting avoids second-descriptor flock. Independent current-source real-process qualification remains pending.

## Refuted static hypotheses and limits

- Reopened associated owners being permanently checkpoint-blocked merely because no new recording is published: r9 constructor performs and clears the pending sync itself.
- Recovery relying only on newly created directory lists or a new owner's reset flags: both physical-ancestry paths explicitly resynchronize existing ancestors.
- Nested root cleanup necessarily discarding primary index ID/uncertainty: recursive structured observation extraction retains those fields and the whole cause group.
- Alias replacement mutating prior receipt through a shared inode: immutable file staging and separately staged alias copy use distinct temporary files.
- max_queue_size<=0 is not promoted to a supported unbounded mode; the supplied historical bounded-queue calibration remains applicable.

No optional P3 recommendation is raised. Runtime plan is one independently authored fifth source at most350 lines, targeting ordinary read-only associated reopen/close/checkpoint and relocated family access, persistent ancestor failures/recovery over fresh ownership, nested commit/release error custody, and actual interprocess/reentrant lock ownership. Every application process must verify all28 manifest source hashes, HEAD, staged identity, worktree identity, local imports and Torch1 before/after. Existing focused/owner/static gates remain coordinator-owned.

## Final independent runtime evidence

Coordinator explicitly granted one CPU after its focused/owner runs. The exact independently authored fifth probe ran once and passed, exit0. Total inspected/authored context is five whole sources /3637 lines (3422 production/regression plus215 probe), below5/5000. No sixth source was inspected or authored. Probe SHA256 `10e07f8d8e4b4693e133584c6a33907391e322e21334801a43139c85d20f469f`; source hashes above were reverified unchanged after execution. No production or index mutation occurred. Runtime slot returned immediately after completion.

Command from `/workspace/hamlet`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/hamlet/src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' .venv/bin/python .superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave04-preparation/T33-independent-r9-probe.py
```

Log: `T33-independent-r9-probe.log`. Real artifacts: `/tmp/t33-r9-independent-9g2539qf`. The application parent and independent application child each verified all28 source hashes, exact HEAD, index equality to candidate tree, no unstaged tracked difference, unchanged index entries and worktree topology, all imported townlet paths beneath this checkout's src, exact reviewed module paths, and Torch intra/inter-op threads1 before/after. The child used the same interpreter/environment. No prior probe was read or reused.

Observed independent cases:

1. Real indexed publication, successful close/checkpoint, ordinary fresh associated reopen and by-index read, close/checkpoint without any new publication. Both family files copied as data to a relocated directory; reopened canonical/by-index reads and complete close/checkpoint succeeded. The original immutable artifact bytes remained exact. This refutes the suspected lifecycle capability reduction directly.
2. Persistent fsync failure at a containing ancestor of newly created nested output directories blocked both first and fresh writer admission. Existing directory entries did not bypass failure. Clearing the fault caused the same failed ancestor to be successfully synced before actual persisted publication.
3. Persistent fsync failure above the nested metric-family directory failed actual first publication and fresh DB owner admission after close. Clearing the fault permitted fresh associated read-only owner admission, close/checkpoint without publication, then fresh actual publication and complete checkpoint. This tests recovery across ownership epochs rather than only retry on one in-memory owner.
4. Real companion commit completed and then raised while real root unlock also completed and raised. Failed receipt retained artifact, generation2/index_id2, phase=index, confirmed alias/canonical and unconfirmed index. The cause tree retained both actual failures. Two real committed history rows existed and the prior artifact remained exact. Repeated shutdown returned the same failure object and no queued ownership remained.
5. Parent nested the actual root guard on one thread while an independent process attempted nonblocking flock on the persistent file and observed contention. After parent release the child completed an actual file-only publication. Lock inode remained unchanged and child receipt artifact existed. This is current-source interprocess and same-thread reentrancy evidence, not attribution to r7.

Coordinator-attributed supporting evidence at the same candidate: focused main56, unit23, other recording144 (including ten ordinary Runner attempts), five cheap guards including mypy0/default614. These were not independently rerun here. Complete source/test review also checked their required permanent controls for legacy repeat/file-only/bound routes, strict versus legacy capacity, generations, closed companion admission and canonical-first partial commits. The review does not substitute for remaining root collection/CLI/full/static/release gates.

Final disposition: scoped PASS. Both supplied r7 mechanisms are independently refuted on r9 with actual fault/recovery witnesses; normal lifecycle remains usable. No concrete unresolved P1/P2, in-scope blocking gap, or optional P3 is raised. Historical baseline behavior evidence remains attributed to the coordinator's supplied report; it is not recast as current-source runtime proof. Native checkpoint handoffs T24/T25 and final whole-wave integration remain outside this bounded review.
