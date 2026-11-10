# CLOCK-STAMP ABI independent technical review R1

Reviewed artifact: CLOCK-STAMP-ABI-PROPOSAL.md, SHA256 dd37a9aa538780fa96c7fb6e67df4de84c5f749e644baa9faefe4ec4981050c2. Read CLOCK-STAMP-brief.md first. This is a static proposal review, not implementation or runtime qualification.

## Verdicts

**Specification verdict: AMEND BEFORE FREEZE.** The primitive boundary, exact identity, initial/inactive representation, clone ownership and future live-authority division satisfy the narrow brief in substance. Restore the accepted conversion/evaluation cursor initialization handoff in prose; its implementation stays with the later owners.

**Quality verdict: AMEND BEFORE FREEZE.** The declared stamp decorator and promised absence of a hash disagree. Resolve the exact Python ABI and add a finite assertion before tests-first dispatch. No architecture expansion or fifth source is needed for either amendment.

## Defects and required amendments

### R1-1 — Medium: stamp hashing is not specified consistently

Location: Public signatures and immediately following equality/hash paragraph.

The proposal declares `@dataclass(frozen=True, init=False, eq=False)` with no `__hash__` definition, while saying “no stamp hash ... is introduced.” With eq=False, dataclasses leave the inherited equality and hash unchanged; an ordinary object therefore has identity equality AND identity hashing. The proposed signature does not yield an unhashable stamp. A consumer can use an instance as a dictionary/set key even though two equal-content stamps remain unrelated keys. That is not content-addressed event identity or retry custody.

Required amendment: explicitly choose the already stated no-hash contract by adding `__hash__ = None` to the stamp declaration and describing it as identity equality with hashing disabled. Add `hash(stamp)` raises TypeError to the finite primitive matrix. Keep EventId/ServiceClock value equality/hash. Do not add tensor equality, content hashing or bank deduplication to solve this. If root intentionally wants identity hashing instead, that must be stated explicitly; silently deriving it from the decorator would leave the exact public contract contradictory.

### R1-2 — Medium specification handoff gap: accepted clone/conversion initialization rules are not published

Location: Strict domains and first/inactive representation, paragraph ending “New conversion/evaluation-clone APIs are outside this bridge.”

The accepted per-world addendum section 2, line44, explicitly assigns PW01/PW02 receipts publication of the cursor initialization rules: explicit conversion/evaluation cloning uses source epoch+1, clears active last-event caches, starts local eligible/service counts at0, retains the actual restored world episode identity, and labels inherited learned/history counters as template data rather than active inherited dedup IDs. The PW02 interface capsule repeats that handoff. The proposal specifies fresh/reset/resume well, but its exclusion of new APIs does not publish those required future initialization semantics.

Required amendment: add a short normative later-owner handoff with those exact rules. Distinguish episode-local eligible cursor0 and new cumulative service origin0 for explicit cloning from ordinary reset, which retains cumulative service position. No clone/conversion API, live bank, migration decoder, old-format compatibility or runtime test is requested in this bridge. Explicit current-format operations and source-artifact preservation remain later mandatory obligations under the accepted scope; no-compat does not itself erase those obligations.

## Sound contract decisions; refuted blockers

- EventId episode>=1 and inactive eligible_seq0 are coherent with ENV accepted sequence1 and absence of an accepted context before reset. INITIAL world/RNG snapshots with accepted cursors0 do not require fabricated event stamps. Standalone EventId0 in its eligible component is a marker, not a live admission.
- Actual eligibility is authoritative for admission. An inactive row retaining the last positive eligible sequence may reuse an ID without creating a service event. Whole-batch ID/order/content validation and later context correlation are both retained.
- ServiceClock is immutable typed data. Monotonicity, lawful units for a selected provider, next-phase ordering, accepted-token authentication, bounded equal-content retries and expiry require live owner history. Their absence from these three constructors is not a missing primitive implementation or permission to omit them later.
- Input detach/clone into local candidates before value validation, publication only after full validation, and clone-on-access provide the promised cooperative ownership. Private-attribute introspection is explicitly outside that supported accessor contract. Raw/scales belong to the future reward result.
- Shared vector-tick cadence and genuine private learning remain required; nothing in this bridge warrants frozen predictors, removing shared mode, weakening real optimizer/tail evidence, or claiming full BAC isolation. Existing RNG/OwnedWorldBackend regressions remain mandatory preservation gates.
- Actual context migration, PW04 provider/native-parent coherence and ordinary runner format9 remain open. A pure stamp suite cannot close them. No new defect in uninspected provider/runner source is asserted.

## Evidence and custody

Prose examined: narrow brief/proposal; accepted PER-WORLD-CURIOSITY-ADDENDUM.md relevant public-state/lifecycle/consumer sections; PW02-interface-capsule.md; PW02-phase2-work-report.md; PW04-READINESS-report.md; historical CURRENT-WORLD-IDENTITY-CONTRACT.md; implemented wave18 CURRENT-WORLD-VFS-CONTRACT.md. Large combined receipt output was truncated, so no claim of exhaustive whole-document reading is made; decisive public ABI/lifecycle excerpts and PW04 readiness were separately visible. The older addendum's PROPOSED heading is interpreted under root's explicit accepted-overlay assignment, not reopened here.

Independently verified current inventory metadata with wc/sha256sum, with no project imports or runtime execution:

| Named source/test | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/world_curiosity_state.py | 734 | 8b242ef58af2840c069db3d599606ba4760eea675e6be5bf00d8eb89c23b5b82 |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| tests/test_townlet/regressions/bac/test_pw_rng_domains.py | 798 | 5e671b5693eb3741424b1fadb098eca6ea3d5f51599dddc1513c1f2292847848 |

All match proposal custody. Charged existing inventory remains3/2300, reserved four-file ceilings4400. No source/test contents were opened for this proposal review; source behavior remains attributed to the capsule/receipts, not independently re-audited. Reserved test was not opened/created. No fifth helper/source, provider/ENV/bank/runner inspection, implementation, runtime, imports, Git/index/branch/worktree operation, source copy, deletion or subagent was used. Only this ignored review document was written. Actual source review and independent execution require root's later frozen-candidate authorization.

Optional extensions: none requested. Portable schema, content hashes, new lifecycle coordination and expanded device support remain outside this primitive bridge. These two finite amendments preserve the accepted obligations rather than reducing scope.

## Additional root-attributed consumer handoff

Root reports that current WS imports RP. When the separately bounded RP/context owner adds a stamp consumer, a reciprocal module-initialization import from RP to WS would create an import-cycle risk. Publish this dependency direction in the consumer handoff. That later owner can use a bounded local runtime import plus TYPE_CHECKING annotations, or another explicitly reviewed cycle-safe arrangement, while retaining actual runtime stamp validation. This is a future integration constraint, not an independently inspected current cycle defect and not authority to edit/read a fifth source now. Both R1 amendments and this handoff are routine additive clarifications requiring no user scope decision.
