# P1 independent review v1

Status: **freeze v1 rejected; freeze v2 fixes independently verified for synthetic
P1 tooling, eligible for root adoption with output-interface-v2 pinned**. This is
synthetic tooling review only. Actual CPU/server/CUDA/application qualification is
**UNRUN**. No application/Torch import, real discovery, driver execution, server
access, checkout creation, Git write, installation, or production edit was used.

## Subject and contract

Frozen manifest `evidence-management/hardware-admission-p1/freeze-v1.json` SHA256
`d2e0a9b6897560e561a2fcc8178ae66275a4379214578d66684695152a75d0bf`.
Reviewed capture SHA256 `e4a94e819bb97e39c5f71cdb80eda8d309fcfaef70d15cc67daceb1d80acf751`,
author tests `04fe92dd1acc9fa6f91510c67af572c3ace9d5582adb510f1e090f5c8e90bfab`,
protocol pin `adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c`.

Contract: CUDA-RUNNER-TOOLING-UPGRADE-PLAN P1; P0 root-adoption-v2,
interface-contract-v4 and root-interface-amendment-decision-v1; accepted P1
private-payload, allocation-cpu and discovery-probe v2 contracts. The historical
capture body was not read or executed. The protocol was consumed through the
accepted interface and imported by the focused synthetic tests.

Packet includes the three pinned module/test files, declared opaque old capture,
and one independent probe: five files, 2,214 declared lines at freeze v1,
below the authorized 5,000-line ceiling. Inert snapshots are retained as evidence,
never executed in place of the original qualification paths.

Repaired manifest `freeze-v2.json` SHA256
`d8b4a363cc8f7d585e1d8fade9226a454ce54672995e08fc8dbb4bee30b30342`:
capture `edfb69054e8e89d65499fe18bfa53c2623dea0ca3eccaa9999e1b6a67d38c66a`
(922 lines), author tests `95a09f542de871dae1cb35638128876a2d167a46174b01c77af5db6db8dbb02b`
(756 lines), unchanged protocol and opaque historical capture. With the revised
79-line independent probe, the final packet totals 2,380 declared lines/five files.

## Confirmed defects

1. **Allocation identity is checked too late.** `discovery_preflight` compares
   affinity and resource overhead but not allocation host/boot against its own
   observation. A wrong-host or wrong-boot grant passes preflight and can reach
   driver/Torch work, with refusal only later in capture. Independent mutations
   of each field produced DID NOT RAISE. Bind capture identity before launch and
   discovery identity before costly CUDA probing; retain the final cross-check.

2. **Persistent lease-file replacement can publish an admitted spec.** `leases`
   checks each lock pathname's inode at acquisition, but only checks the enclosing
   directory after discovery. Replacing the pool lock while the old descriptor
   remains locked is undetected. An independent full capture mutation after
   discovery returned `admitted` and emitted `spec.json`. Every held lock must be
   revalidated before publication; checking only context-manager exit is too late
   because spec publication currently occurs inside the context. Root no-writer
   custody still remains necessary for transient restored edits and future use.

3. **Discovery cancellation can outlive its allocation lease.** A stub child
   whose `communicate` raises `KeyboardInterrupt` causes `launch_discovery` to
   return control without termination or reap. The outer lease finally can then
   release while discovery remains alive. The independent stub recorded only
   `communicate`, with no kill/wait. Cleanup must retain custody through bounded
   termination and reap, account for driver descendants, and preserve diagnostics.

These were first author hypotheses, then independently reproduced; none is
reported solely from the author's assertion. The author repaired all three; the
reviewer did not change production or author test sources.

## Fixed-source review and consumer requirement

The exact repaired diff was reviewed. Capture now checks actual host/boot before
launch. Discovery checks host/boot and active freeze/grant/allocation/partition
before CUDA work, then repeats authority checks before driver calls, Torch import
and device observations. Held lease inode/root identities are rechecked before
admission/spec publication and on release. Discovery owns a process group;
catchable cancellation/timeout causes TERM/KILL and direct-child reap while the
capture retains leases. Discovery and driver queries inherit lease descriptors;
normal completion with remaining group members refuses and triggers cleanup.

Independent full-capture lock replacement now refuses with no spec; the direct
lease replacement and cancellation probes also pass. Host/boot mutations pass
only their expected refusal, preceded by a valid positive preflight control.
The active-interval repair is additionally exercised by the independently rerun
author suite. No remaining confirmed defect was found within this packet.

**Consumer adoption requirement:** `capture-output-interface-v2.json`, SHA256
`dcdaf7ca144f7a91a349f3ec658a3b1dd2faae29b0f06f25c89efb536f557d08`, makes a
written spec provisional until the closed terminal `result.json` admits that
exact spec and admission reference with empty reasons. Late failures preserve
partial spec bytes but set terminal disposition refused/spec null. P2/root must
enforce this terminal check before a spec becomes runnable; standalone spec
validation is insufficient. The reserved capture-only `BAC_CAPTURE_LEASE_FDS`
environment entry describes actual inherited descriptors and does not alter job
environments. Root must adopt and pin this interface before consumer integration.

Cleanup does not guarantee supervision of deliberately escaped or FD-closing
native descendants, or uncatchable controller death. Incomplete attempts cannot
qualify, and root retains allocation/source/namespace custody. This is an explicit
operational limit, not hardware or end-to-end process-tree qualification.

## Evidence

All paths below are under `evidence-management/hardware-admission-p1/independent-review/`.
Each attempt has exact source `.txt` snapshots and JSON argv, cwd, PID, UTC and exit
records. Only existing `/workspace/hamlet/.venv/bin/python` ran successful harnesses.

| Attempt | Result | SHA256 record / log |
|---|---|---|
| author-suite-v1 | 87 passed, exit 0 | `bf4df6d58fc16e91580faf9c9b2504dedf4baf3b97a09b277129e6fe6633f81f` / `df87fe3cdf627608e5bbf4bc75a50b5e556df782dd160e9fae5e41fcb6fd10f7` |
| independent-red-v3 | 4 assertion failures, exit 1 | exact records/snapshots retained |
| independent-red-v4 | 5 assertion failures, exit 1 | `3f1864d256aa542a93b3e676eea9460bd084e24feb49597f4a329df9d446327c` / `e58eb1c57f6f8dd80f20297113772beb250220c6c8716a90c6a8da4280a26cbd` |
| author-suite-v2 | 99 passed, exit 0, exact repaired source | `e002018a4da19b3cbb83a3c064987b82fb9ed9229fe2fb31b62c178773fa4ad5` / `49b8999441b3a2b2a2d968272a2416d82da62b8f0f984bfc834ea68561f2ee96` |
| independent-repaired-v1 | 2 fixture KeyErrors, 3 passed, exit 1 | `0dd420ed59f370e080db8f06d0f8f988a5213a4cba5d6673cfc839be7bb11058` / `e7989a7c7c08a2962299771613b6b54ea02f911b2b49a3c698424b89fcc40c4f` |
| independent-green-v1 | 5 passed, exit 0, exact repaired source | `c127a4905d4e96ffec5197139adc9ca6d39d24dc0ed28d152a6f0aa43863a810` / `9f5fca75b3047a6b50338570acc3b84d6f91fc01f7616bf565c9c7f9222d4381` |

Independent probe SHA256 `527b41f49e971e944ab8ea3c6d84b601d24da0305820851c395b208c819d3a2b`.
`independent-red-v1` is a missing-pytest prerequisite failure and v2 a pytest
configuration failure; neither counts as an intended assertion RED. They remain
retained. Successful harnesses disabled plugin autoload and bytecode writes;
independent v3/v4 additionally used `-o addopts= --noconftest -p no:cacheprovider`.

The unchanged probe's first repaired-source run exposed absent `start` fields in
its previously partial allocation fixture, not a new production defect. The
fixture was completed with active start/end/authority fields and strengthened
with a positive control and host/boot-specific rejection matching. Revised probe
SHA256 `0c4771d75130d959a032b5873ac222d7cfb76963e3ecfb34beecc8a436724cf1`.
No expectation was weakened. Repaired runs also record unchanged post-run source
hashes. The original review is retained as `review-before-fixed-disposition-v1.md.txt`.

Author retention limitation, explicitly disclosed: all executed implementation
and test versions were retained before subsequent mutation, but some early
unexecuted intermediate test drafts were not each separately snapshotted. No
claim of complete per-edit author draft retention is made. Independent RED,
intermediate fixture failure and GREEN runs remain distinct; counts are not
summed into a broader qualification claim.

## Other observations and limits

Static review and the focused author suite support exact child/command provenance,
CPU no-Torch separation, actual Torch UUID joins without treating numeric CUDA
visibility as driver indices, selected-device contention filtering, nested
quota/cpuset/headroom arithmetic, retained scratch accounting, role CPU upper-bound
binding, source/dependency rereads, and refusal without spec on observed drift.
Unsupported MIG and unavailable mandatory probes refuse rather than invent facts.

These are checks of implementations and inert observations, not actual hardware
availability, actual no-writer enforcement, actual root authorization, compatible
server cgroup topology, or end-to-end CUDA/BAC behavior. Final tooling integration,
independent complete synthetic attempts, server admission and real-work witnesses
remain owed by the parent plan. No existing runtime obligation is waived.
