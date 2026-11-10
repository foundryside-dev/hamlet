# CLOCK-STAMP production handoff

Stationary for root freeze, GREEN and fresh source/independent review. Only WS production changed; named64-case test and both readonly files retain exact prior hashes. No pytest/project imports/executable probes/Git/index/branch/worktree/copy/deletion/subagents. Root-attributed R0 collected64 and produced64 explicit missing-ServiceClock call-phase assertions,0 errors; this author did not execute or reinterpret those results.

## Candidate inventory

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/world_curiosity_state.py | 846 | 8eb88bbe6e0aa3bf7d40d03905d054a82b56ac2825e2970b5750a5456e8a9d6f |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| tests/test_townlet/regressions/bac/test_pw_rng_domains.py | 798 | 5e671b5693eb3741424b1fadb098eca6ea3d5f51599dddc1513c1f2292847848 |
| tests/test_townlet/regressions/bac/test_pw_clock_stamp.py | 317 | 3f015cfc3d354d4c7e3b5abdbaf07137d8abc37af7edc2cb2c79f0cf7c479364 |

Actual4/2729; binding ceilings1500/800/1100/1000=4400; hard5/5000 intact. New production is112 lines added between unchanged KDF and descriptor. No imports, helper source, parameter defaults, adapter or old-format decoder added.

## Public ABI and self-review

Implements adopted proposal5251388f5ad7c0328b6be4825be595e4b3f8fafd2271f1babd6618ded8bac0f0:

- Frozen ServiceClock(unit,position) exact supported string unit, exact nonnegative int position, value equality/hash.
- Frozen CuriosityEventId(curiosity_epoch,world_id,world_episode_seq,eligible_seq) exact int minima0/1/0 and exact nonempty world string, value equality/hash. local0 is inactive no-admission marker; no bootstrap episode0 EventId.
- Frozen init=False/eq=False CuriosityStepStamp(*,event_ids,world_ids,world_episode_seqs,eligible_seqs,eligible), identity equality, explicit __hash__=None. Exact nonempty ordered tuples, exact EventId elements, unique exact strings, common epoch, dense strided CPU/CUDA rank1 int64/int64/bool same-device inputs. Complete correlation includes every inactive/last row. No coercion/device moves.
- Validates geometry first; clones detached tensor candidates; checks owned domains/ID content; publishes fields only after full validation. Tensor properties return fresh detached clones. Noncontiguous inputs accepted. Python integer ID/clock domains remain unbounded; stamp int64 correlation cannot wrap arbitrary IDs.
- Failure paths raise ValueError for malformed supported input contracts, with allocation/device failures naturally propagating. CPU paths only inspect tensor device metadata, never CUDA runtime APIs. Genuine CUDA behavior remains hardware-gated.

Self-review traced all constructor paths: non-tensors short-circuit before tensor attributes; exact tuple checks precede len/element access; dtype/device/layout checks precede operations; active local0 rejected; inactive retained positive cursor legal; no global RNG/provider callback/state mutation. Input quiescence and cooperative private-attribute discipline remain explicit. Existing descriptor/KDF/RNG/OwnedWorldBackend bodies were not edited. New types own no live epoch/service/episode cursor, acceptance authority, dedup cache or lifecycle coordinator.

Existing WS→RP import remains. Later RP context migration must use a reviewed cycle-safe runtime import arrangement and validate actual stamps/context identity. Context migration, PW04 provider/native unit/position/cadence rules, actual bank next-phase/retry authority, runner format9/native integration and final BAC acceptance remain OPEN. Required explicit current-format conversion/evaluation-clone sourceepoch+1/cleared active cache/local eligible and service origin0/actual restored episode/template-history handoff stays in adopted proposal; no API added here.

## Scoped author checks

Authorized Black with explicit pyproject.toml config completed successfully and formatted WS. Authorized Ruff with explicit pyproject.toml config passed again after formatting. Commands: UV_CACHE_DIR=/tmp/clock-stamp-uv-cache uv run --no-sync black --config pyproject.toml src/townlet/exploration/world_curiosity_state.py; same prefix with ruff check --config pyproject.toml and the same sole file.

No runtime success, GREEN, static typing/defaults result or independent approval is claimed. Root owns frozen process/source/config custody, new64-case execution, existing RNG regressions, required guards and fresh other-model review.

## Source fix round1/5: exact hash typing and test formatting

Root reports R1 CLI PASS in139.66098s wall and all R1 runtime closed; Astra specification PASS, quality CHANGES_REQUIRED for WS's intentional __hash__=None object-protocol assignment: global mypy8 errors/3 files versus baseline7/2. Root also reports global Black would reformat only the new test,705 files unchanged. Those are root/reviewer results, not commands executed by this author.

Applied only narrow authorized repair: retained runtime __hash__=None with one explanatory comment and exact `# type: ignore[assignment]` on that assignment. This suppresses only the deliberate object hash-protocol type incompatibility; stamp remains identity-equal and unhashable. No Any widening, global typing suppression, guard/default/style relaxation or behavior change. Ran explicit-config Black on both owned paths; its sole formatting change in the new test preserves all64 cases/assertions. No pytest/project import/Git/index or other source inspection.

Current WS847 lines SHA256 ec3cf8ded83f952ca4c1993b084b2ee0c7f1e611bf172ab31830ecfdc27f352d. Current new test316 lines SHA256 bffc26fff70116ac18d3cc43fa6c73c747c0e5ae7779abf077646aa0116a1a1e. Readonly RP768/RNG798 unchanged; actual4/2729 lines remains within all binding ceilings4/4400 and hard5/5000. Earlier source/test hashes above describe R1, superseded here only for these two owned paths. Public contract update awaits root results.

Authorized commands and actual outputs (both exit0):

- `UV_CACHE_DIR=/tmp/clock-stamp-uv-cache uv run --no-sync black --config pyproject.toml src/townlet/exploration/world_curiosity_state.py tests/test_townlet/regressions/bac/test_pw_clock_stamp.py`: reformatted tests/test_townlet/regressions/bac/test_pw_clock_stamp.py;1 file reformatted,1 file left unchanged.
- `UV_CACHE_DIR=/tmp/clock-stamp-uv-cache uv run --no-sync ruff check --config pyproject.toml src/townlet/exploration/world_curiosity_state.py tests/test_townlet/regressions/bac/test_pw_clock_stamp.py`: All checks passed!

Stationary for root freeze, covering/joint/guards and same Astra actual-fix rereview. No author claim that mypy baseline is restored until root's actual execution. No fresh runtime PASS/independent approval claimed.
