# WIP20 independent documentation ground-truth review

2026-11-14. Reviewer: `/root/bac_astra_wip20_doc_review`. Independent of the documentation producer and root application.

**SPEC PASS / QUALITY PASS for the exact five-document proposal, for root application together with the WIP20 evidence checkpoint.** No material false source, qualification, count or acceptance claim was found in the proposed changes. This is document review, not terminal application qualification, evidence assembly approval, remote publication or merge approval.

## Exact subject and integrity

Proposal manifest `wip20-docs/proposal-manifest-final.json`: `d385458a97d594f37fcda2d0cc1ac9790853908b529f05f051be42a9a8688383`.
Patch `wip20-docs/wip20-docs-final.patch`: `604e9a44daada2f3d34ba119a329736215ee07a3b33bf1ac02edacd347637f8e` (34453 bytes).
Source-facts report `wip20-docs/SOURCE-FACTS-AND-RISKS-FINAL.md`: `e6017170c75861f6bdbd132dfc3761838a1af3e9c80324c1ba82051950b4c92b`.

Independently rehashed all original and proposed document bytes and checked all ten sizes against the manifest. Recomputed the complete unified diff from those original/proposed pairs: byte-for-byte identical to the sealed patch. Root must rehash before applying; this approval does not transfer to altered bytes.

| Document | Original SHA256 | Proposed SHA256 | Original / proposed bytes |
| --- | --- | --- | --- |
| `README.md` | `efed71def427225be84e0d6f9e67d6f87df4401df392907de2195d195d3e36a3` | `3bfd2e19a18d5b6599d7a05e5b39c8fceb4b24129dac94181f08f5788d4d3b35` | 32210 / 32503 |
| `docs/remediation/bac/STATUS.md` | `52d5261a3b7eb5f8f36286ab2c7e5aa5b13abcaf8764147dcfeb21fe32c4affe` | `384255460e70dfdf97712b73e5d7ca6a4ea112f3eca19f9cd09f9e1fd6c490fa` | 98514 / 102002 |
| `docs/remediation/bac/EVIDENCE-INDEX.md` | `9646ff5b9672b505943d2a3c335b01d8662253f8b92358aee16ad0b050ef6fad` | `e21c1c63b7dddc1bf01dd759d59aefff5ba5ae68780695518cfe24ea2373438c` | 8979 / 12599 |
| `docs/remediation/bac/CURRENT-RNG-CUSTODY-CORE-CONTRACT.md` | `553a840a6b54c28763cec8a1e2e84f8161f9aa67832b2d3e1b07bf90c0eb7aab` | `8d2e1096bfdac94afc97691834e2418a4463de0d70c644ba14aa20ffa73fc99e` | 44999 / 47345 |
| `docs/remediation/bac/CURRENT-REPLAY-CUSTODY-CONTRACT.md` | `00082f3cc8dfca251de21ae3e6a41e814f1698f4054aebce0a81ebf4cc57222b` | `8cd7b369e2e1ac35273680ab16e346c8f540b664586904c8b4b9985f630c2137` | 11552 / 18978 |

## Inspection boundary and actual source

Read AGENTS.md and docs/remediation/bac/EVIDENCE-PROCESS.md. Read exactly five whole implementation/test bodies, 4799 unique lines; repeated slices only recovered truncated tool output. No producer2558, core-test2360, historical-helper675 or other implementation/test body or snippet was opened. No application/import/test/lint execution, source edit, branch/worktree/checkout/execution copy, external message or subagent was used. Standard-library text/hash/JSON/diff checks did not import the application. The sole authored artifact is this review.

| Direct body | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rng_custody.py | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |
| src/townlet/training/replay_contract.py | 881 | `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4` |
| src/townlet/training/replay_buffer.py | 816 | `683e0b9b0f500cc523391b8574acbfc31bf8dc8a36d92ad0547323621261838d` |
| src/townlet/training/prioritized_replay_buffer.py | 1310 | `7a76183ded0712103c81ebd31b3e05425b3738e9338689cacfbefbc8fd493a29` |
| tests/test_townlet/regressions/bac/test_replay_cuda_activation.py | 597 | `cf2e0c46d3910eb3b2aa01ebb746664333d7c83e52278e5cafd5f9f08a3fa8fe` |

All five seals and line counts match the proposal. Source directly supports the finite 18 opaque identities (flat8/PER10), frozen descriptors and mapping, healthy=True/post_poison=False, fixed lazy imports under actual RLock ownership, successful-only descriptor/policy cache, exact owner class/participant binding and no lifetime owner retention by cached policy. Input tags are classification, not arbitrary-hook purity validation, as the documents explicitly say.

Flat/PER dispatch maps match the listed contracts. Flat mode-load has its own local validation prelude; PER reuses validate_serialized, without a nineteenth contract. Constructors use empty registration and preserve selectors. Shared wrappers release the initial planning owner guard before domain resolution, replan under owner exclusion, and retain that exclusion through completion and authentic outcome inspection/quarantine. Sampling and preparation require explicit lineage; installation checks original prepared issuer material, owner revision and current token. Preflight is admission/enrollment, not parent outcome ownership. Detached PER archive validation bypasses lifetime registration; canonical kind checks remain visible, with digest-helper semantics attributed to the independent evidence rather than an extra helper read.

Direct activation-body inspection confirms actual CPU numeric copies, masks/component presence, wrapped stable-ID mapping, duplicate-max priority updates, stale-refusal invariance, and separately observed nonempty PER archive install/property ownership. Real registration and source-issued gates remain intact. CPU tensor subclasses simulate CUDA metadata and completion; this is correctly distinguished from physical CUDA and arbitrary-subclass qualification.

## Bound execution and independent evidence

Rehashed candidate `wave35/r113-candidate.json`: `0f05c4f3faab3e6f5ea15b7ba8fc8c466f0e3dda9bbc87abbde47af7bd2f3daa`. Root record `wave35/r113-root-checks.json`: `743d10da55b9c5ffecb58b22c67000f6cf34cebc978b423e7d8f27be6ec7334f`; it binds execution tree `b5298dec04379db31bf9107a26ead7764f53d73c` and base `0597715b8d59ab3bdda41ef5521b9772aaa9c436`. Read its structured metadata and attempt references; independently counted its 1203 distinct passed node IDs. Its two distinct failed nodes are disjoint. Core89 + activation67 + producer840 + BANK155 + replay54 = 1205, with replay52 PASS/2 FAIL. The 31 children (16/10/4/1) and actual phase pair are included, never added again. Existing execution/custody qualification is attributed to root's sealed record; this reviewer performed no rerun.

The record explicitly retains actual R113 global mypy15 FAIL (oracle6/POP9), R113 changed producer-test style PASS and R111 unchanged-production owned style/types/defaults PASS. The proposal preserves these attributions without promoting earlier static evidence to a fresh global pass.

Independent route ledger `T18e-R0-CUDA-B-R113-ROUTE-EVIDENCE.json`: `1a68e332eefc1721cd029c96f7893da1df47e4a98cb578b82a701c22085ee6e9`; review: `75eb423fe901244adaf35c0d84e6a729fb59945f967ee8e76429f286b3bfedef`. Rehashed both and inspected all 18 route mappings. Nine activation and nine producer identities have public witnesses distinct from empty-gate canonical binding. Producer assertions are attributed to that independent body review, not claimed as directly reread here. The flat archive-property witness proves public execution/digest, without an isolated exact completion trace or numeric/mutation ownership assertion; the proposal explicitly preserves this limit. Only its install gets the trace claim.

Peer-wait diagnosis `T18e-R0-CUDA-B-PEER-WAIT-FAILURE-DIAGNOSIS.md`: `05329b1ef7df41821cea034b367dd76240be7c3b01b8020c15087c6bd8b47b2b`, independently rehashed. Its obsolete public-operation observer explanation matches directly inspected admission/device-invocation dispatch. The document correctly describes diagnosis and proposed fixture repair, not an implemented repair or passing exclusion assertions. Both affected failures remain authoritative.

Latest remote/CI is explicitly attributed to observed WIP19 0597715b8d59ab3bdda41ef5521b9772aaa9c436: Config PASS, Lint FAIL15, fast Tests FAIL; transport closure leaves the test cause unclassified. This review made no remote query and establishes no newer remote outcome.

## Concrete gaps and application boundary

No blocking content defect found. Two nonblocking editorial limitations remain: compressed number/word spacing (for example `records1,203` and `mypy15`) reduces readability; the pre-existing core source link uses ../../../src from docs/remediation/bac, which resolves under docs rather than repository root. Neither changes the bounded evidence claim; changing approved bytes requires a new seal/review binding.

The EVIDENCE-INDEX proposal calls WIP20 current and links its authoritative record/selection plan. These are prospective publication-navigation bytes, not evidence that root has already materialized or remotely published WIP20. Apply them with the actual root-owned checkpoint records and verified links; do not publish this index alone. This is the existing evidence-process publication prerequisite, not an additional application acceptance gate.

Required cold core-first/producer-first import-order execution remains missing. Peer observer repair and qualified rerun remain owed. B6 post-poison capability is required and unqualified despite false staged bits. Actual one-/two-GPU behavior, access/topology for the offered 16-worker server, parent outcome ownership/lock handoff, recurrent/runner integration, global typing/full/default suites, coverage >=70%, slow/learning, fresh final review and exact-final-remote CI remain open. None is hidden by bounded PASS. Original-package accounting remains 28 qualified /38 remaining /66 total; no full B or whole-programme acceptance or merge claim is made.

Historical preservation was checked against the exact diff: STATUS retains its old body after the new heading section; the replay capsule retains the complete original body verbatim under an explicit historical boundary; the core updates current clauses while retaining historical records and their scopes; WIP19 remains in the index as history. README changes only the stale current BAC paragraphs. These edits do not rewrite historical acceptance, add compatibility authority or remove required capability.
