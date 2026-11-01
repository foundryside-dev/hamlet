# PW01 independent SPEC/QUALITY review — static phase

Status: static review ready for fixed-source runtime qualification; no final PASS.
Review date: 2026-11-01. Existing repository only; no source edits, index changes,
commits, copies, helper inspection, project imports or executable runtime probes.
Explicit preservation/default/historical-access task requirements override the
blanket pre-release deletion guidance in AGENTS.md.

Complete owned source inventory (all five inspected; 1890 lines charged):

| Absolute source path | Lines | SHA256 |
| --- | ---: | --- |
| /workspace/hamlet/src/townlet/config/bac_options.py | 285 | d4de5950c63398f8d7ebf977733e0204dad2038be05e7685f097ac369f253931 |
| /workspace/hamlet/src/townlet/config/effective_run.py | 362 | 0cc2c58fa70f5416b03721119103acdfdcb83a2bed97db6a4a66db610446be99 |
| /workspace/hamlet/src/townlet/config/exploration_policy.py | 762 | c5e7a767b4eea2069e9854f145434d2acde7b3eb1be8bcf4be06d9c3df9c7970 |
| /workspace/hamlet/src/townlet/exploration/world_curiosity_state.py | 220 | 4310308ca8d02ed2460997da728df3ea5513b8b51439a421505d4b3d0c51af5d |
| /workspace/hamlet/tests/test_townlet/regressions/bac/test_pw_scope_contract.py | 261 | d467ede1f0d2a841f62d51c70812f10b2dc6cb2ada28fa288ca32f14bcd8e150 |

These match the implementation-ready report and root inventory. Limits:
OP600 / EF400 / RP1000 / WS350 / test350; total5/5000. Inline executable
probe charge so far: 0. No sixth source/helper file inspected.

The native DATA manifest declares qualified producer
1c99510967c132fce04548564f4cb317e2ecddaf, tree
d3c1f4993efb73717826f6d4e1bf9e3cf0cd28d0, compiled schema1.41.
Actual artifact bytes were SHA256-checked:

- /workspace/hamlet/tests/test_townlet/fixtures/bac_curiosity_pre_scope/scope-omitted.msgpack:
  89e60038cdc532ce812634fbe06620ec5bf45b3e8639e44e444eddb2d745333a
- /workspace/hamlet/tests/test_townlet/fixtures/bac_curiosity_pre_scope/options-authored.msgpack:
  46e155bb01b376e206847dd70da4c1de6c316a4c23eace1e06a2cae5b6b2e315

No material static defect identified. Omitted scope retains shared numerics and
shared execution projection; authored options omit only absent new scope for old
training identity bytes. Policy legacy recognition requires the known complete
outer field set and excludes new scope markers in authoring/roles/units; current
partial payloads are not automatically inferred shared. Effective-run historical
validation compares the exact old projection against re-resolved authoring.
Private scope declares the seed/clock/origin/guarantee, uses cardinality1 for
omitted queue capacities, and enters policy identity. All five selectors flow
through that boundary. The descriptor preserves exact Unicode/case/dot/slash ID
strings, rejects duplicate/empty strict IDs before map creation, copies and
freezes nested seeds, verifies persisted derivation, and separates ordered runtime
binding from static policy identity. KDF inputs exclude lane/order/N/tick.

Pending after root pins the common staged candidate and authorizes execution:

1. Run the owned two-node suite, including real native load/recache and compiler
   roundtrips; confirm historical execution/authored/training/policy identities.
2. Run an independent inline probe, at most350 lines, using only public APIs:
   descriptor geometry/provider/schema/origin/binding/stream corruption,
   immutability and exact ID distinctions; all-provider private identity and
   local capacity stability, including drive-selected predictor batch; malformed
   current decode versus truthful legacy decode.
3. Recheck source identity before/after execution and attach actual results.

This review does not certify private optimizer/state-bank independence, which is
assigned to later packets. No whole-candidate or repository acceptance is implied.

## Authorized frozen runtime phase

Scoped behavioral verdict: PASS on candidate tree
ca22c9f84e79828c8f6bc6b4a31a53a6e46ace75 at base
1f9d831a8fe76ab00e06774ef6888985f6c2aec2. This supersedes static-only status
above, but is not full-candidate acceptance. Root reports six outstanding
OP/EF/RP no-default lint violations; actual repaired source requires revalidation.

Executed one inline Python probe through /workspace/hamlet/.venv/bin/python,
with OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1,
CUDA_VISIBLE_DEVICES empty and torch.set_num_threads(1). No helper file created.
Conservative inline source charge:150 lines (under350); total charge2040/5000,
five core files only. Runtime process exit0, output:

```json
{"result":"PASS","rejected_corruptions":171,"candidate":"ca22c9f84e79828c8f6bc6b4a31a53a6e46ace75","local_import":"/workspace/hamlet/src/townlet/__init__.py","threads":1}
```

The process asserted HEAD, index tree, no unstaged tracked source changes and all
five owned hashes both before imports and after all controls. All supplied
source hashes remained unchanged. It checked all five selectors, private policy
identity under N changes, descriptor streams under reordered exact Unicode IDs
and spectator admission, stream-map immutability and detached serialization.
171 rejection controls covered partial/current scope tags, inconsistent selected
scope/seed/origin/guarantee/clock units, invalid descriptor schema/geometry/types,
provider/hash/origin/binding/canonical IDs, duplicate/empty IDs, malformed or
changed seed maps, frozen fields and undersized drive-selected queues.

RND and adaptive RND drive-selected batch7 resolved local pending7 under N17 and
N999, accepted explicit19, and rejected explicit6. ICM selected batch11 derived
pending11 and retained explicit23. Both genuine old effective payloads decoded
with their original execution/training/authored identities; old-shaped payloads
containing a private authored declaration refused rather than downgrading.

Reused root's exact-source two-node execution as authorized, independently
reading the result/log and verifying the log SHA256:
/workspace/bac-review-2026-11-01/qualification/wave03-green-r0/PW01.log
ed07cda7361d47dd7d8a9b864c8d8dc489405baaadb14f55705ea1c82227d8a3.
The log reports 2 passed in23.82s. Its adjacent PW01-result.json pins the same
candidate, exit0 and30.722s process duration. That suite supplies genuine native
load/recache/compiler roundtrip assertions; these were not redundantly rerun.

No material behavioral/spec defect found in the bounded PW01 contract. Scope
still excludes private runtime bank/optimizer independence and later integration.
No production/test/index edits were made by this reviewer.
