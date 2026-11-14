# Independent P3 owner amendment review v2

Verdict: APPROVED FOR BOUNDED INERT IMPLEMENTATION, subject to root's WIP22
checkpoint and explicit source-freeze release. This approves the design only;
implementation, executable evidence and actual owner/hardware qualification are
not claimed.

Exact reviewed final proposal:
CUDA-HARDWARE-P3-OWNER-AMENDMENT-PROPOSAL-v2.md
SHA256 223951b0bbefb319892ecbd9c1b37b1cf686aea929546acffd652f9f68de57b3.
Predecessor review:
CUDA-HARDWARE-P3-OWNER-AMENDMENT-INDEPENDENT-REVIEW-v1.md
SHA256 c5ea83e41d709481e46dc3efb5a4e4dbc55a50d75ce9c8496bfb0829668f43fe.

Focused actual-byte review closes all three original findings:

1. Actual call ownership: the identity-bound pytest_runtest_call wrapper records
   actual item.nodeid, clears its entry in finally and rejects stale/foreign or
   overlapping entries. Caller case and environment are independently checked.
   Nested owners retain their authenticated own launch case; inherited pytest
   registry entries do not authorize them. Later reports remain required.
2. Preparation/custody: all preload, parsing and parent source checks precede
   the final snapshot. Recorder metadata locks are released and descriptors
   closed before fork, without releasing P2 resource leases. The final emission
   tail is checked for module growth. An exclusive actual-child-written claim
   prevents distinct children from qualifying through one launch; end binds
   the same claim and identity, with independent final-inventory reconciliation.
3. Bounded fork sampler: explicit cumulative/phase/absolute limits, nonblocking
   lock acquisition, concurrently drained capped pipes, owned unreaped-PID
   TERM/KILL and bounded actual reaping replace unspecified blocking behavior.
   Cleanup failure preserves incomplete evidence. Abrupt guard death explicitly
   relies on P2 owned-group cleanup; no parent-death auto-kill or qualified
   consumer integration is falsely claimed.

The intermediate v2 scope defect is also closed. Final launch.sampler_policy is
empty and both deadline fields are null for spawn; fork requires its singleton
policy and exact deadlines. Raw sampler observations are mandatory only for
successful fork-guard phases. The supplied outer spawn 90-second joins and
legitimate work interval are preserved. Atomic launch claims remain required for
all owner children. The added negative test protects this distinction.

The numerical fork policy is an explicit proposed qualification profile, not a
claim that current hardware or the frozen input set meets it. Implementation must
retain actual timing/resource evidence and failed attempts. Runtime inability to
meet that profile cannot justify relaxing owner semantics or inheriting source
facts. P2 group-backstop execution remains a separately required integration gate.

P0 shapes remain unchanged; Python debug and Torch anomaly remain separate;
actual child Git/source observations, complete environment inheritance, acyclic
root/parent authority and owner RNG/cleanup/report requirements remain intact.
Missing source-owned inter-op=5 setup blocks actual owner qualification only;
inert P3 work may use explicit synthetic sentinels, never recorder thread setters.
P2 adopted v2 and P4 repaired v3 still require separate bounded consumer amendments.
No backwards-compatibility adapter is approved.

Retain the two-file edit scope and five-body 3878-line ceiling. After root's
checkpoint/freeze decision, proceed with retained exact-source RED, bounded
implementation, focused GREEN, whole P3 suite and independent implementation
review. This design review does not substitute for those gates.

Only proposal metadata was read for this follow-up; no additional implementation
body, import, test, Git operation or source mutation occurred. This new immutable
review is the only file written. Root's requested preservation of the earlier
277e0581c7728e2d72a0c381f4b2d0cfe79185183cefc28ac759327a7d7ebd63 draft
remains author/root evidence-retention work and is not asserted complete here.
