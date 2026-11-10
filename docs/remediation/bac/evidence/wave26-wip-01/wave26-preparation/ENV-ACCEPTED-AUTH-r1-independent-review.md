# R1 independent actual-source/spec/quality review

Candidate: 2f5a63a58a728af624be0262a22d9fdd6ac48833.
Base: 2640353422d2946d9a74c58ec11ce9bf03c49579.

Verdict: CHANGES REQUESTED for qualification fixture; the minimal production
bridge matches its specified identity-only contract. No production defect found
in the added four lines. Runtime remains pending root collection authorization;
no independent execution result is claimed in this revision.

## Material finding

P1 qualification blocker: tests/test_townlet/regressions/bac/test_env_accepted_auth.py
quarantine test (lines 227–239) cannot reach its validator call. After
abandon_episode it invokes _pure_validation, which calls _snapshot, which calls
the reused _state helper (old fixture lines 75–87). That helper unconditionally
calls env.vfs_random_state(). The real ENV method (lines 1506–1512) explicitly
raises ValueError in quarantined phase. Therefore the positive authentication,
repeated-call purity, step refusal and INITIAL refusal assertions in this case
are not exercised on the candidate. Missing-method RED masks this fixture
problem because _validator fails before the snapshot is taken.

Repair the owned new fixture's quarantine observation strategy using permitted
observable state, preserving explicit native-export refusal. Do not weaken the
production quarantine gate or suppress unexpected snapshot errors. Retain real
positions/meters/dones/step counts/tick, identity/cursors/phase and all three CPU
RNG witnesses before/after the real validator and refusal calls. Then reseal and
rerun the prescribed qualification. No source edit was made by this reviewer.

## Source conclusions

validate_accepted_episode has the required keyword-only accepted argument, no
default, and delegates only to the unchanged _accepted guard. That guard uses
object identity and an explicit None rejection, with no token attribute reads,
equality dispatch, reconstruction, normalization, mutations or random draws.
The public method returns None on genuine current identity and raises ValueError
for every other identity. The existing phase and owner-receipt checks remain on
activation, physics, close, release, save and abandonment operations. Closed,
released and quarantined current-token validation is intentionally identity
validation only. INITIAL has no accepted token. A fresh accepted reset replaces
the object, invalidating the previous identity. Exact case and Unicode IDs are
not interpreted or normalized by this bridge.

The actual constructor/compiler/lifecycle fixtures create genuine ENV tokens.
The independently meaningful lifecycle prerequisite does not consult the new
ABI. Copy (including copied private fields), constructed, duck, None, foreign
same-public-identity, stale and exact-ID cases use appropriate positive and
negative witnesses. Tests use real reset and real participation through existing
public lifecycle operations. The repeated-validation checks do not reset.

Purity snapshots are selected actual state witnesses, not exhaustive snapshots
of every private simulator object. The reviewed production call graph supplies
the complementary no-write/no-RNG argument. CPU tests do not establish CUDA RNG
or hardware behavior. The local _Run fixture supplies nine named roles through
three local _Sink objects (several roles legitimately share the boundary owner).
These are explicit unit interface receipts, not nine distinct production owners
or actual BANK/replay/network/runner/native-parent integration.

## Scope and evidence

Exactly four charged whole implementation/test files were reviewed; no fifth
source/helper/introspection implementation was opened. Prose contracts and
review documents were read. Whole-file inventory and SHA256 were independently
checked using read-only shell commands:

- ENV: 2403/2500, a7f998355bec48e3a12c5b8a57648797592bc16c84af0d3f099eb7799db9540b.
- world_roster: 312/350, 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33.
- old fixture: 856/900, 31a7d0d607a643f0e1f5b36f951fd10188f62d37b3981eadf5f928e39151b006.
- new fixture: 239/700, b6a7a1074e06f88183d9e80018c1437b91b485507d142fdaabc6fcdaf6b2da7f.

Total 3810, ceilings 4450. Candidate diff stat is exactly four ENV additions and
239 new test lines. This ignored review file is the only reviewer write.

Root-attributed prior CPU evidence: genuine fixture 1 PASS; missing ABI 15 FAIL /
1 PASS, with 347-source/573-config/13-artifact/index/process/thread custody PASS.
These are not independent reviewer executions and do not show final GREEN.
Actual BANK integration, current callback/issuer parent wiring, native parent,
runner, nine-role production behavior, global mypy, full54/22-lens requirements,
CI/hardware and final release gates remain open. No overall release increment.

## Authorized independent R1 execution (final addendum)

After root supplied collection authorization, ran only the prescribed locked
packet command with wave26-r1-independent-spec.json. The wrapper finished with
exit 0, but its pytest child returned 1: **15 PASS / 1 FAIL**, 16 collected,
pytest 3.53s, wrapper job wall 7.218922615s. The exact failed node is
`test_env_accepted_auth.py::test_identity_authentication_keeps_quarantine_and_physics_refusal`.
Its captured traceback confirms the static finding exactly: new test line233 ->
_pure_validation line51 -> _snapshot line36 -> old _state line83 ->
ENV.vfs_random_state line1509, before public authentication is called.

The controller identity receipt names the exact candidate/base, the installed
module at /workspace/hamlet/src/townlet/__init__.py, Torch 2.11.0+cu130 and one
Torch thread. This is a CPU fixture run, not CUDA qualification. Run artifacts:
/workspace/bac-review-2026-11-01/qualification/wave26-r1-independent/independent.log
and independent-result.json; log SHA256
23f4385568860cb2b1a3c2c68428d87027ddf1b6d6f2eb4be61d55fc44ffb7c9.
The captured failure-controller-60e1e7155fa677ab.json agrees with that result.
Manifest SHA256 8b736b2add7ad71e5ef376a08bc027246f42b6d2e5a1584a1825c6fd5d76bf85.

No positive verifier was run because the child failed. Full negative custody
verification beyond these captured failure/identity/result artifacts remains
root-owned; it is not inferred from wrapper exit 0. Session 10754 is CLOSED.
No rerun, helper source inspection, source/test/index edit or further runtime
was performed. Final bounded verdict remains CHANGES REQUESTED for the test
fixture; production spec/quality review finds no defect in the four-line bridge.

## R2 final independent re-review — supersedes R1 blocker verdict

Candidate 5028604b97fa241f00e4bae758125b4aeb2e8755; base unchanged.
SPEC: APPROVE. QUALITY: APPROVE within the four-file producer bridge scope.
Prior quarantine fixture finding: ADDRESSED. No remaining material finding.

Reviewed the actual R1-to-R2 test diff and updated author report. The only source
change since R1 is the new test's quarantine observation strategy: a dedicated
snapshot retains public identity/cursors/phase, physical tensor clones, tick,
semantic identity and Torch/Python/NumPy RNG witnesses. It does not invoke the
forbidden VFS native exporter. The test calls the actual public validator twice,
checks None returns and state equality, and explicitly verifies VFS export,
physics and INITIAL refusal before, between and after authentication. Ordinary
cases retain their original full snapshot. No test identity is removed or
skipped. This addresses the causal failure without weakening production or
hiding snapshot exceptions. Production bridge and the other two source files
retain their reviewed hashes and conclusions.

Independently checked final inventory: ENV2403, roster312, old fixture856, new
fixture270 = 3841/4450 ceiling. New test SHA256 is
eadc370b7773eac8ebbef0eeddd60e803416dd71f7eca7875fc4244ea315d98b;
other three SHA256 values remain those recorded above. No fifth source opened.

After root authorized the successful single-quarantine prerequisite, executed
only the prescribed locked wrapper with wave26-r2-independent-spec.json, then
the prescribed positive verifier using the same full spec. Child exit0:
**16 PASS, 0 skipped, 0 xfailed, 0 xpassed, 0 warnings**, wall6.840346336s.
Positive verifier exit0 confirms source/index/import/thread/fixture custody
PASS: 347 source guards, 573 config digests, 13 protected artifacts, one process
identity, 14 registry records, one available worktree. Exact candidate/base
match. Session66192 CLOSED; verifier completed without an ongoing session.
Log SHA256 11ce7cd2a0205e070e1cff8d1d5dbfd8f13e27f6721e1a39f1078581b9b37dca.
Manifest SHA256 7f112b4df86c2e0b668cce0455279306f99db64af831c7de85195d38416d2517.
Artifacts: /workspace/bac-review-2026-11-01/qualification/wave26-r2-independent/.

Root separately attributes R1 broader identity/constructor/VFS evidence to
182 PASS/4 CUDA skips,22.601s, plus custody PASS, on byte-identical production.
That is reused R1 evidence, not an R2 broader rerun. Root corrected its initial
collection count to authoritative202 (owned16 plus covering186). Root reports
four global guards PASS and nine known mypy errors; no global mypy GREEN claim.

The approval establishes this narrow public current-token authentication seam
and its CPU tests. Quarantine VFS internal-state equality remains intentionally
unobservable through the refused public export; source inspection proves the
bridge performs no writes or random draws. Actual BANK implementation and its
callback/issuer wiring, production nine-role parent behavior, runner/native
parent, full54/22-lens requirements, CI/hardware and integrated release remain
open. Only this ignored review report was written by the reviewer.

## Final public contract prose verification

Document-truth verdict: APPROVE for CURRENT-ENV-ACCEPTED-AUTH-CONTRACT.md,
SHA256 f9085a17150946d7266ca09d41de1b72d3012fb314381685ac33106e2b8d335e.
Read and hashed that exact ignored handoff; compared it with the already-reviewed
four source/test files and qualified R2 receipts. No material contradiction or
unsupported qualification claim found.

The required keyword-only API, bound callback form, exact current nonnull object
identity, refusal of copies/foreign/stale/constructed identities, no token or
receipt issuance, and separation from phase/context/outcome/owner authority all
match the production implementation. Its statements about INITIAL, Unicode,
repeat purity and the quarantine observation limit match the actual tests.
The full four-file3841/4450 inventory and hashes match the reviewed candidate.
R2 root16/18.2854s is explicitly received root evidence; independent16/6.84035s
and positive custody agree with this reviewer's execution. R1 broader182 PASS /
4 CUDA skips/22.601s is correctly attributed as earlier evidence on unchanged
production, not an R2 rerun. Actual BANK, runner/native/production role wiring,
GPU and integrated release obligations remain explicitly open.

This last verification used prose reads and a document hash only, with no new
runtime, code/test/index changes or additional source/helper inspection. Only
this ignored review report was appended.
