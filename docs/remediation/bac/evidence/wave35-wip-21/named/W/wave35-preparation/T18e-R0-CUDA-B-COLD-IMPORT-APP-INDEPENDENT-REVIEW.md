# Independent cold-import APP implementation review

2026-11-14. **SPEC: PASS. QUALITY: PASS for the frozen bounded APP implementation.**
No material P1/P2 defect found. This approves the reviewed source for root-owned
qualification after exact TOOL adoption; it supplies no collected or executed
application result.

Reviewer `/root/bac_astra_cold_import_plan` is independent of the APP writer.
The accepted V2 proposal is SHA256
`a3afe3ff38c1de66176c751a16ec8b43edc0e65c4c23dc190e3de903f3837a31`;
its plan review is `123c6745dfd85b96480bb25b51486cc5b849502a624eee1cf5ab3655075398ee`.
Root's accepted supplemental BAC_COLD_SPEC interface is included in this review.

## Exact subject and independent static evidence

| Subject | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rng_custody.py, admitted unchanged source | 1195 | 6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8 |
| tests/test_townlet/regressions/bac/test_rng_cuda_admission.py, final APP subject | 2883 | b1f05946a4f2c0e145c44226323dc7b599f36a1364c854d26f090fa45b1a4409 |
| Q/verify_bac_replay_spawn_identity.py, previously admitted unchanged source | 752 | 6006c7247d79a99226a74756a2266a2966fce800f9f84af802f2990db4606173 |

Read reservation remains 4830/three bodies. Q is
`/workspace/bac-review-2026-11-01/qualification`. No producer or new TOOL body
was read. Supplier constructor/owner-context facts remain attributed to root;
this review checks their use and live assertions, not those producer bodies.

Independently rehashed APP report
`T18e-R0-CUDA-B-COLD-IMPORT-APP-IMPLEMENTATION.md`:
`6ca0817cc417d04505cd2ab8b4f479f747c36bd75437ec5f32c23afda7179610`.
Independently rehashed/read TOOL independent review:
`146ea3e77b28d205991b8b7fa7fb13657d9e9c3ddf03dedadc649f7dd03572fc`.
Tool implementation/parser claims below are explicitly supplied by that separate
review, not independently repeated here. Also read root's runtime-facts-v1 JSON;
its dependency-only discovery is not application or hardware qualification.

Fresh stdlib-only in-memory AST/hash checks, without executing/importing the
application/test/literal, established:

- Removing only the appended cold block and new `import subprocess` reconstructs
  exactly original2360 bytes, SHA256
  `6ec962f9c0b3d467375528b26de39bac154b46e4d5c6435ffcc289960f063085`.
  Original test/helper bytes are retained, rather than merely similar node names.
- Final file2883; growth523, within <=650 and test<=3010. APP total4078/two.
- Probe is ASCII, 360 lines, 20489 UTF-8 bytes, SHA256
  `449a01b27740c7744f9e44e4f86beaf7acf56f0fa646609e43e0588d30093705`.
  One stored `_COLD_IMPORT_PROBE` name at enclosing line2364; source inspection
  confirms the single raw string assignment and direct launcher use.
- Actual fault sites are literal assertion192 and sentinel raise158. Full source
  inspection confirms preload caller200 and CUDA-touch caller202.
- Appended functions are the one launcher and two parametrized tests, yielding
  the finite three positive entries and two fault roles. Existing89 plus5=94 is
  source-expected only; actual collection remains root work.

No application, test, probe, collection or TOOL execution occurred. No Git,
branch/worktree/checkout, source execution copy, source edit or delegation
occurred. This report is the only write.

## Full-path implementation assessment

**Source/launch custody.** The parent passes `_COLD_IMPORT_PROBE` directly as
argv[3] to Popen, using the full root/.venv/bin/python invocation spelling,
-I/-c, fixed mode/entry, canonical root/output and fresh32-hex nonce. No formatting
or wrapper changes the literal. Child compares all actual orig/proc argv, checks
isolated mode and sys.executable, and hashes the observed script/command/binary.
Parent independently hashes launch argv/script, captures Popen PID, and requires
child PID/PPID/nonce/argv/worker reference agreement. Parent reads its actual
start_ticks before launch and again while the child is live; worker PID/role and
start_ticks bind to that parent. Worker record/log/plugin authentication remains
the strict TOOL's responsibility, as the approved contract requires.

Child independently reads candidate manifest/source hashes and BAC_COLD_SPEC,
checks manifest/root linkage, authenticates tool-seal reference bytes and compares
actual runtime paths/versions/binary against the seal. Existing receipt spec_ref
binds the actual spec at qualification; no invented child schema field is needed.
Qualified setup requires all existing qualification keys and BAC_COLD_SPEC;
partial qualification fails rather than downgrading. The local unqualified branch
cannot satisfy the strict worker/log/plugin chain.

**Coldness and observations.** Before the selected application import, setup is
stdlib plus real Torch/NumPy. Empty Townlet inventories are observed before and
after dependency import and at the selected boundary. Explicit root/src insertion
is the source path; there is no warmed test/helper import, module deletion, fake
module or cache reset. NoCUDA is installed before any application import and
remains through completion/cleanup. Actual CPU getters and thread/task observations
supply the one-thread profile; configuration alone is not emitted as observation.

The profile callback uses filename/code-name matching without obtaining custody
objects beforehand. The import observer forwards permitted requests and rejects
custody-origin canonical producer imports for the declared absolute/relative/
fromlist cases. Both hooks are installed before the selected/preload imports and
restored in finally. Core-first checks producer absence; producer-first modes
allow their genuine dependency graph. Observed module paths/hashes are matched
to manifest-derived names, with no observed-origin expansion of the allowed set.
These remain bounded source/import observations, not universal Python import purity.

**Canonical lazy-cache work.** The initial actual policy dictionary is checked
empty. The fixed18 expected table checks actual opaque constant types, complete
manifest keyset, descriptor type, tags/routes/bits and rationale; distinct
contracts/descriptors are retained. Real CPU owners are constructed and held
strongly, with exact canonical classes and actual participant-to-owner bindings.
No substitute owner/class/manifest or cache replacement is used.

The resolver counter forwards to the saved genuine resolver. Real class exports
are removed only for the two missing-export calls, restored in finally, and both
failures precede any success. Body/cache/state/CUDA checks and total resolver
count distinguish failure from cache hits. Core's reviewed resolver raises before
cache insertion or gate creation. Then the first genuine serialize gates resolve
one policy each; the two repeats retain identical tuples/policies with no new
resolution. Prior cache tuple identities are checked throughout. Live gates bind
actual participant, owner, contract, descriptor and canonical owner/input types;
policy route/rationale/permission bits agree with the source descriptor.

Real owner contexts acquire the actual replay lock, which is asserted owned
before empty-device completion. Live completion checks precede gate close.
State snapshots surround the complete gate/owner-context lifetime, avoiding an
invented live-gate zero count. RNG snapshots are actual Python/NumPy/Torch CPU
states sampled after constructors and after gate work. Unregister occurs in
finally; success is emitted only after cleanup, zero members/gates/operations,
healthy/not-ready state, two cached policies, sixteen unresolved contracts,
unchanged RNG, unchanged sentinel identity and zero CUDA accesses. No domain
health or membership counters are reset to force a pass.

**Causal fault controls.** Preloaded mode imports real custody under the observers,
then emits the non-success witness immediately before the designated cold-boundary
assertion. CUDA-touch mode has no application import; its deliberate attribute
access increments the sentinel count once, emits its witness and raises at the
fixed site. Witness PID/PPID/orig/proc/script/source facts come from the actual
child, not the parent launch declaration. Neither path reaches positive identity
emission. The parent retains stderr, checks expected exit1/final diagnostic/count
and success-file absence. Strict independent traceback/caller/site validation is
supplied by the separately reviewed TOOL, so an unrelated terminal failure cannot
qualify merely by returning nonzero.

**Lifecycle and retention.** Files and logs are exclusive. Popen starts a new
session, with bounded90-second wait and terminate/kill/reap handling. Failed
setup/import/validation/cleanup emits a separate failure record preserving actual
files and process facts; it does not turn into a success observation. Partial
artifacts remain available for root inventory/retention. No child or pytest
execution is silently claimed by static inspection.

## Disposition and remaining gates

No source correction or scope expansion is required before the planned root
qualification. TOOL review reports strict schema/provenance/fault checking and
independent synthetic rejection controls; root still adopts those exact seals
and runtime facts rather than treating this APP review as tool execution evidence.

Root must collect the exact94 set, qualify both fault jobs before any positive
job, then run the three positives and required final-byte existing89 and applicable
activation/producer/profile selections. Preserve failed/partial/unexecuted attempts
and unique-union accounting. A runtime failure remains a failure requiring its
own diagnosis and linked new seal if source changes.

This PASS establishes source readiness only. Actual CUDA hardware, producer leaf
purity, post-poison permission, B6/R0, package completion, coverage and final CI
remain outside this bounded APP review and retain their existing obligations.
