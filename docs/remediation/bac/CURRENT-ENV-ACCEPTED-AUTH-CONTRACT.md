# Current actual ENV accepted-token authentication contract

The bounded public bridge is source-verified at root R2 candidate
`5028604b97fa241f00e4bae758125b4aeb2e8755`. Root reports 16 PASS in 18.2854s;
fresh independent Astra reports 16 PASS in 6.84035s, SPEC and QUALITY APPROVE,
and quarantine fixture review addressed. Root/independent custody checks PASS
covering 347 source, 573 config, 13 artifact and process/thread witnesses. All
runtime sessions are closed. These are received execution receipts, not new
executions by this document author. This is a bounded source handoff, not
integrated BANK or BAC release qualification.

## Exact public API and authority

```python
from townlet.config.world_roster import WorldAcceptedEpisode
from townlet.environment.vectorized_env import VectorizedHamletEnv

VectorizedHamletEnv.validate_accepted_episode(
    self, *, accepted: WorldAcceptedEpisode
) -> None
```

The argument is required and keyword-only. An actual instance supplies the bound
callback `env.validate_accepted_episode`; invoke it as `callback(accepted=token)`.
The implementation delegates directly to the existing private exact-identity
guard and returns None on success. It accepts only the nonnull object that is
currently this actual ENV's accepted token. Obtain a genuine token from the
actual reset receipt's `.accepted` through the existing reservation/reset and
owner activation lifecycle. The bridge issues no token, receipt or authority.

Copied tokens (including `dataclasses.replace` with unchanged fields), explicitly
constructed tokens, duck-typed objects, None, a foreign ENV token with identical
public IDs/sequences/batch/semantic identity, and an old token after fresh
acceptance all raise ValueError. Structural field equality is insufficient.
INITIAL has no accepted token to authenticate; None and a manufactured
zero-sequence token refuse. No normalization, fallback or alternate authority
exists. Case-distinct IDs and Unicode composed/decomposed IDs remain exact.

## Identity truth and independent phase/owner checks

The method authenticates current token identity only. It grants no activation,
reset, physics, step, completion, checkpoint, context, outcome or owner-receipt
permission. Existing operations retain their own phase, role, capability,
content and issuer checks. A caller must perform its own required validation;
successful producer authentication alone does not authenticate caller contexts,
steps, outcomes, owner receipts or runtime phase.

A still-current token can authenticate before activation, while active, after
closure/release, and while quarantined. This does not lift any phase restriction:
the tests retain preactivation step refusal, closed step/save/next-entry refusal,
and quarantined physics/save/native-export refusal. Quarantine does not make a
genuine current identity false; it continues to bar those operations. No state
or RNG changes arise from repeated identity validation itself.

## Evidence and observability limits

The 16 cases include an independent actual lifecycle prerequisite that does not
look up the new method, successful repeat calls, unissued/foreign/stale negatives,
exact case/Unicode IDs, INITIAL, required keyword argument and phase/quarantine
separation. The prerequisite compiles the actual smoke capsule and uses the real
ENV constructor, required WorldRosterDeclaration/seed/lane binding, reservation,
reset, activation, actual participation, closed boundary release and fresh next
acceptance. Missing-public-ABI RED was independently established before the
four-line production addition: root reports 15 expected missing-callable failures
and one passing prerequisite, with no collection errors or skipped cases.

Purity compares public identity/cursors/phase/semantic identity, cloned physical
position/meter/done/step tensors, global tick and Torch CPU/Python/NumPy RNG.
Normal cases also compare the full existing fixture state including public VFS
native context. Quarantine correctly forbids VFS native export, so its diagnostic
snapshot compares the listed available witnesses and explicitly checks export
refusal before, between and after validation. It makes no private VFS-state
equality claim and does not bypass quarantine to serialize.

The reused nine-role owner fixtures are explicitly local cooperative test owners
with actual issuer-sealed receipts. They do not qualify actual runtime NN,
provider learning, BANK, replay, runner, parent nine-role wiring, native whole
pipeline restore, GPU behavior or integrated BAC completion.

Root's prior R1 covering selection reports 182 PASS / 4 CUDA skipped in 22.601s;
ENV production bytes are identical at R2. No R2 covering rerun is claimed.
Four R1 global cheap guards passed, including Black in 47.313s and defaults601;
final root scoped ENV/test Ruff and Black checks passed. Nine existing global
mypy caller errors, compiler CLI/full checks, actual BANK work and broader
integration/release requirements remain open.

## Exact four-file inventory

| File | Lines / ceiling | SHA256 |
| --- | --- | --- |
| src/townlet/environment/vectorized_env.py | 2403 / 2500 | a7f998355bec48e3a12c5b8a57648797592bc16c84af0d3f099eb7799db9540b |
| src/townlet/config/world_roster.py (readonly) | 312 / 350 | 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33 |
| tests/test_townlet/regressions/bac/test_world_episode_identity.py (readonly reused fixture) | 856 / 900 | 31a7d0d607a643f0e1f5b36f951fd10188f62d37b3981eadf5f928e39151b006 |
| tests/test_townlet/regressions/bac/test_env_accepted_auth.py | 270 / 700 | eadc370b7773eac8ebbef0eeddd60e803416dd71f7eca7875fc4244ea315d98b |

Actual total 3841; ceiling total 4450. The only production addition is the public
method/docstring/direct guard delegation. Existing private guard and mutating
phase/reset/role/native/quarantine protocols remain unchanged. This document is
ignored prose only; its author made no new source/test/index/runtime changes.
