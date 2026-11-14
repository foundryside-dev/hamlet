# P5 root decision and finite owner requests v2

Root decision received 2026-11-14: implement one upgraded closed current producer
protocol. Preserve every accepted semantic observation/correlation; replace
obsolete transport identity fields with explicit P0/P3 source/process links.
No old/new fallback, no adapter into the old verifier. Historical tools/evidence
stay immutable. Actual owner child/fork context, argv/environment phase transport
and parent RNG source schema must be supplied first. Exact two distinct phase
attempt/spec references plus separately recomputable strict receipts remain
mandatory. All six missing real-CUDA owner groups stay required/UNRUN.

This resolves v1 question1: retaining old identity transport as an accepted inner
schema is NOT selected. The v1 exhaustive semantic inventory remains the minimum
preservation checklist; the upgraded exact payload schema is owner-supplied.
No verifier/test body is authored until that finite schema is adopted. P5 current
body count remains 752+520=1272; two named new files remain reserved <=3528 total.

## Proposed fixed P5/P4 interface

`validate_child_obligation(subject: dict) -> dict` is the only proposed pure-data
integration function; its import is a fixed literal source dependency after
separate review, never selected by record contents or a file path.

Proposed exact subject keys: `schema,spec,job_id,obligation_id,documents`.
schema literal `bac-hardware-strict-validation-subject-v1`; spec is P0 reference;
job_id/obligation_id P0 IDs. documents is a list of exact `{reference,content}`:
reference is P0 path/bytes/sha256, content is actual `bytes` read by trusted caller.
References unique by path and content hash/length rechecked. Strict JSON parsing
rejects duplicate keys/nonfinite numbers. Every required referenced JSON object
must be present; unknown/unconsumed documents reject. The function performs no
filesystem reads/writes, subprocess, dynamic import, APP/Torch/CUDA calls, Git or
receipt-authority acquisition. It checks exact strict-owned schema and all typed
fields participating in its correlations. It does not duplicate P0's common
schema authority: P4/standalone transport reader performs adopted P0 validation
and live reference checks before this fixed function. No caller-supplied boolean
marks observations as verified, and direct use of this pure function alone
cannot claim P0/common custody.

Proposed exact return keys: `schema,obligation_id,verdict,reasons,cases,evidence,
payloads,producer_processes,related_attempts`. schema literal
`bac-hardware-strict-validation-result-v1`; verdict satisfied|unsatisfied|unrun;
reasons list[text], other list memberships exact to selected obligation and parsed
causal evidence. Satisfied requires empty reasons and full strict observations;
unsupported/missing owner schemas remain unrun, malformed/conflicting supplied
records refuse ValueError. This is data, not a qualification receipt.

P4 supplies authenticated parsed transport provenance as actual referenced bytes,
recomputes common process/source/report/outcome checks, invokes fixed P5 semantics,
and emits its existing closed `bac-hardware-case-validator-receipt-v1` with actual
P4 validation identity/UTC. P5 validates its exact contract/schema/evidence/process
correlations independently and does not accept generic P4 status strings as strict
proof. Root inventory explicitly pins source, dependencies, contract/schema,
finite obligation kinds and classes. Current P4 scope has no P5 import; later
integration requires root's explicit finite reslice and independent qualification.

Standalone `verify_children(spec_path: Path, job_id: str, destination: Path)` is
a separate transport reader/exclusive strict receipt writer using the SAME pure
data function. It records actual validation process/UTC, pins all bytes and
labels common custody/hardware outside its own strict component. It never claims
whole P0 acceptance from only strict checks. Exact standalone receipt fields and
phase subject wrapper will be agreed with P4 before implementation; no alternate
receipt or authority is implemented now.

Phase proposal: P0 related_attempts contains exactly two distinct spec references
in reference/failure order. Each parsed spec binds a distinct attempt_id and exact
single phase job, separate output directory, and independently qualified strict
receipt. A new closed owner phase wrapper must explicitly bind both job IDs and
strict receipt refs; never infer adjacent receipt paths. Subject verification
recomputes each strict receipt semantically before typed comparison, excluding
the phase-pair obligation itself from each individual prerequisite to avoid a
cycle. Preserve shared source/input/event vector, exact complementary completion
outcome, current per-subject start/end identity, and all old constraints. Exact
wrapper fields are pending the finite owner reply; this proposal grants none.

## Minimal metadata supplier slices for root dispatch

Paths below are relative to R=/workspace/hamlet unless Q prefix is explicit.
Line counts and SHA256 were measured as bytes only; no listed producer body was
read by P5. These counts are current observation, not permission for execution,
source edits or qualification. Root must recheck exact bytes at supplier start.
P3/P0 are opaque adopted interface metadata unless explicitly included in the
supplier body budget. No test body imports or execution are needed for replies.

| Supplier | Exact counted bodies | Current total / proposed read cap | Required finite reply |
|---|---|---:|---|
| Bootstrap/P3 linkage | tests/test_townlet/regressions/bac/test_world_rng_bootstrap.py (998); Q/bac_hardware_identity_v1.py (611); Q/bac_hardware_protocol_v1.py (520) | 2129 / 2400, 3 bodies | Source-factual qualification activation/env/output helper behavior; exact P3 direct-owner context, parent_start and nonperturbing fork feasibility; propose one new source/process transport, no APP edits. |
| Direct replay | tests/test_townlet/regressions/bac/test_replay_rng_custody.py (1156); test_world_rng_bootstrap.py (998, same directory) | 2154 / 2400, 2 bodies | Exact replay child target/emission order/queue/parent RNG actual assertions or serialization, source references and upgrade points; consume bootstrap/P3 capsule opaquely. |
| Recurrent replay | tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py (640); test_replay_rng_custody.py (1156); test_world_rng_bootstrap.py (998), same directory | 2794 / 3000, 3 bodies | Exact recurrent target and actually used replay/bootstrap helper linkage, parent RNG state proof and upgraded emission order. If a listed helper is not needed do not read it; any different helper needs root reslice. |
| Core/fork/phase | tests/test_townlet/regressions/bac/test_rng_cuda_admission.py (2883); test_world_rng_bootstrap.py (998), same directory | 3881 / 4200, 2 bodies | All16 exact roles, three fork4/7/5 actions, source-owned parent RNG facts, actual no-Torch child path, source/import authority and upgraded phase pair payload with explicit two subjects/strict receipts. No production core read; existing core contract/source-review metadata remains attributed. |
| Flat/PER producer | tests/test_townlet/regressions/bac/test_replay_cuda_producer.py (2558); test_world_rng_bootstrap.py (998), same directory | 3556 / 3800, 2 bodies | All10 exact mappings and actual current baseline/error/quarantine/output records, upgraded payload and actual child/parent emission/end/queue lifecycle; no production producer read. |

These are initial read-only supplier budgets, not projected implementation budgets.
Separate owner edit/test packets must be allocated after C1 source freeze release;
no APP/testproducer bytes may change during root's current qualification. A new
helper not listed above is an explicit root reslice, never an automatic dependency
read. No broad application review is requested; only exact interface capsules.

Current byte identities:
- test_world_rng_bootstrap.py: 452e427b945475e050b35273b6bb44effe3ade6ef96629c4382c2d68591ee727.
- test_replay_rng_custody.py: e64eaa3fd18489ca40d6193800a012ad53d9bc0086911a645a4e12df5ded7d50.
- test_recurrent_replay_rng_custody.py: 1044513adaab42b3d6caef624cd4b3e6d70298ed3096f5dfe3dd4de0f32ad5b0.
- test_rng_cuda_admission.py: b1f05946a4f2c0e145c44226323dc7b599f36a1364c854d26f090fa45b1a4409.
- test_replay_cuda_producer.py: e629acf35a89bb5719945b4c8c9a5578de2dc1c69791038ba2072bb71dabe801.

The supplier replies must explain PYTEST_CURRENT_TEST and any other inherited
phase keys using actual source/launch facts; exact child /proc argv may differ
from parent pytest argv and must be observed, not copied. No synthetic process
identity or guessed Torch/runtime facts may fill a missing observation. Root's
no-writer source/namespace authority remains external to all text/hash records.
