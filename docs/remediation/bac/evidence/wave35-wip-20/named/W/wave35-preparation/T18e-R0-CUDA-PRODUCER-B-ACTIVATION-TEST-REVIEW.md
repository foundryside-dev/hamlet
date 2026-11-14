# Producer B activation tests — independent bounded review

2026-11-13. Reviewer `/root/bac_astra_activation_review`.

**SPEC PASS for the bounded activation-test contribution; QUALITY PASS with the finite coverage limitations below. No concrete P1/P2 defect found in these frozen tests.** This is static review, not a passing runtime result, complete B qualification, or authorization to infer hardware/global acceptance. Production B is absent at review time.

## Seals and boundary

The reviewed activation test is `tests/test_townlet/regressions/bac/test_replay_cuda_activation.py`, 420 lines, SHA256 `cf5667cc3d61d8277a7ac7ce11483e21bcd393ed51cd80c4a8f0ad6c65b59448`.

The five authorized implementation/test bodies were measured before source inspection:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rng_custody.py | 948 | ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e |
| src/townlet/training/replay_contract.py | 881 | 8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4 |
| src/townlet/training/replay_buffer.py | 816 | 683e0b9b0f500cc523391b8574acbfc31bf8dc8a36d92ad0547323621261838d |
| src/townlet/training/prioritized_replay_buffer.py | 1310 | 7a76183ded0712103c81ebd31b3e05425b3738e9338689cacfbefbc8fd493a29 |
| tests/test_townlet/regressions/bac/test_replay_cuda_activation.py | 420 | cf5667cc3d61d8277a7ac7ce11483e21bcd393ed51cd80c4a8f0ad6c65b59448 |

Whole-body budget charged: 4375 lines/five files. I read the complete activation test and relevant source sections within the other four charged bodies. No other implementation/test body, imported fixture body, helper implementation, relocated snippet or execution copy was read. AGENTS.md and the preparation, preparation review and core supplier capsule were consumed as prose authority. Only this report was authored. No source/test edits, branches, worktrees, checkouts, application/import/test/lint runtime or delegation occurred. Root owns collection, RED execution and integration.

## Causal pre-B expectation

Static parameter expansion gives 60 proposed nodes: 1 exact-manifest + 18 canonical-owner + 18 wrong-family + 8 unlisted-identity + 2 nested-gate + 2 sequential-instance + 2 lifetime + 2 failed-lookup + 1 fixture + 2 serialize + 2 priority + 2 CPU controls. Of these, 57 encounter `_contract` and its explicit missing-source-constant assertion before their B-dependent body. The remaining three are the standalone CPU-backed source check and two CPU-local controls. This count is not collected execution evidence.

The current core has an empty immutable manifest and no B constants. Shared replay dispatch retrieves the named constant only after its real inventory determines CUDA local work. Thus the missing-constant failures are a genuine staged dependency, not a deliberately false numeric assertion or a fake policy installation. These first failures alone do not prove that each later assertion is correct; root must run final B bytes to expose any masked errors. The frozen suite itself introduces no B implementation.

## Authority, cache and fixture quality

The exact18 table agrees with the accepted flat8/PER10 mappings, including flat's distinct `load_for_mode` validation constant and no nineteenth PER constant. The manifest control verifies exact key equality, distinct opaque identities, immutable mapping/descriptors, closed owner/input tags, separate permission bits and nonempty rationales. Rationale semantic adequacy remains source-review work rather than a consequence of nonempty text.

Canonical controls construct actual registered ReplayBuffer/PrioritizedReplayBuffer objects. Their real gates inspect actual cached descriptor/policy identities and canonical classes/input types. Wrong-family cases cover all18. Subclasses, a registered unrelated class spoofing the canonical module/name, invalid participants and invalid contracts refuse before the CUDA sentinel permits any query. The fixture neither replaces the production manifest nor mocks policy resolution. Its retained owner list ensures negative tests cannot pass merely because registration lost its weak owner.

The sequential-instance test checks reuse of the exact cached tuple across distinct participants; the retired-owner check unregisters in finally and checks collection while the cached policy remains reachable. Together they support finite class/policy retention without permanent owner retention. They do not independently prove every live-gate pinning/thread invariant; that is supplied by the separate core packet.

The cold-lookup test removes only one cold cache entry under real idle admission, then temporarily removes the canonical module attribute. Its broad exception acceptance is bounded by a no-CUDA sentinel, no successful cache publication, restored canonical lookup, a successful real completion and unchanged domain status. It does not substitute a resolver result. Scoped monkeypatch cleanup restores module/cache bindings; no domain poison or health state is reset. Missing-class refusal is covered; fresh-process import order and partial-import variants remain separate controls.

Nested public local gates are explicitly refused and the cache snapshot remains unchanged. This correctly avoids confusing active-cache stability with permission to open a second local scope. Resolution of a different route while the first gate stays authentic is intentionally owned by the separate core test packet, per the supplier capsule.

The owners fixture uses real CPU constructors, records every registration and unregisters after each test. The test source does not import hidden fixtures. CPU-only controls prevent both CUDA attribute access and local gate entry while running real push_recorded/serialize/clear paths.

## Actual leaf/data evidence

The source stand-in changes only the tensor's reported device and CPU conversion observation. Slicing/detach and numeric values remain real; conversion returns a native CPU tensor. Its independent control verifies values, dtypes, CPU device, copy ownership and the exact conversion trace. This is explicitly CPU protocol evidence, not arbitrary-subclass purity or GPU execution evidence.

The observer wraps and yields the actual local gate; it does not fabricate policy, gate, output or sampling result. CUDA seams report initialized finite inventory and record synchronization; unused selector lookup/initialization fail. The serialize cases compare every field against ordinary real serialization, then mutate output observations to check detached ownership. The actual source path clones chronological flat rows or physical PER rows and the expected single source-copy/completion trace is consistent with those bodies.

Both PER public priority methods execute actual float64 CPU conversion, absolute-value-plus-epsilon staging and float32 publication. Expected numeric priorities, untouched inactive slots, maximum, owner revision advancement and retained CPU destination are asserted. Thus success requires meaningful data effects, not only absence of an exception or a gate-call count.

## Finite defects/gaps ledger

1. **Remaining real-route coverage obligation (qualification gap, not a defect in these four positive cases).** This file provides actual CUDA-seamed public execution for flat serialize, PER serialize, PER update_priorities and PER update_unit_priorities. Fourteen rows have binding-only evidence here: flat push, push_recorded, readiness, validate_serialized, load_for_mode, historical_archives, install_historical_archive; PER push, push_recorded, declare_unconstrained_action_dim, readiness, validate_serialized, historical_archives, install_historical_archive. Root must attach exact existing public-route node evidence or add bounded controls; unread tests are not presumed sufficient. The CPU push_recorded setup is not CUDA activation evidence. Canonical archive traversal is not exercised by the empty archive lists here.
2. **Success-outcome assertion timing (minor test-quality limitation).** Lines137–138 inspect False inside `gate.complete`, before that phase exits. That proves live access to the current flag, not successful completed-phase outcome for each of18 rows. Other controls inspect False after completion, and actual producer paths call the authentic outcome in owner-held finally; no outcome implementation regression is inferred. Moving this assertion immediately after the completion context, while retaining the gate, would directly strengthen the all18 test. This is not a request to edit frozen bytes silently.
3. **Stable-ID numeric discriminator (finite coverage limitation).** The first two inserted IDs are 0 and1 and equal their physical slots. The stable-priority case proves actual stable public dispatch and numeric mutation but cannot distinguish correct ID-to-slot lookup from erroneous direct indexing, nor test duplicate-max reduction. Existing algorithm tests must supply nonidentity/wrapped IDs, stale refusal and duplicate reduction evidence if those behaviors are claimed qualified. B need not change these algorithms, and this case is meaningful as activation evidence.
4. **Explicit separate-owner obligations remain open.** The core packet must supply opaque construction/copy/serialization and signatures, fresh import order, actual cache/fork/PID/reentry/thread guards, live descriptor/policy tamper refusal, second-route resolution stability, partial/unavailable class refusal as applicable, and isolated poison behavior. Root must run existing completion-failure/quarantine, CPU/admitted/prepared/owner competition controls and publish exact non-overlapping accounting. No such results are inferred from this file or the prose capsule.

No independent execution was performed. This report accepts the frozen test contribution as an appropriate bounded prerequisite to B; it does not close the above qualification gaps, validate an as-yet-unwritten resolver, or grant B6/R0/global/hardware acceptance.
