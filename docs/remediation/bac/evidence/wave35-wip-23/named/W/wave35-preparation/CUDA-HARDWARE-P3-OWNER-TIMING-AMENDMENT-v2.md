# P3 fork timing endpoint amendment v2

Immutable predecessor v1 SHA88867b7fe9f5eed6426c3285b2f0633f691acbad3443be9e425568047c3cb154.
This linked revision implements the two focused Astra review corrections.

Status: concrete private metadata correction for root/Astra review; no P0 change.
Links owner proposal v2 SHA223951b0bbefb319892ecbd9c1b37b1cf686aea929546acffd652f9f68de57b3
and review v2 SHA29482fad19e6b1eee5abee82298a78caa71c51a26e7e42ddedd57e7310ff002f.
Historical proposal and reviewed bytes remain immutable. This correction does not
claim the current P2/P4/P5 consumers or APP producers implement it.

## The observed boundary

A sampler record referenced by raw cannot include the later raw/process emission
in its own end timestamp. A new post-process record also cannot timestamp its own
future write or the function return. No self-referential hash or predicted end is
permitted. Preserve the original 3s per recorder call, 6s combined recorder time,
8s absolute cleanup cutoff and 10s owner deadline. Actual external caller and
parent observations supply the missing complete-call upper bound.

## Acyclic records

1. Existing sampler observation fields keep their exact shape. Its start_ns is
   actual recorder entry, end_ns is actual completion of source sampling before
   sampler/raw/process emission. cumulative_ns is the sum of these observed
   source-sampling intervals for completed start/end phases. It is explicitly
   NOT whole-call time. Commands retain actual argv/PID/reaped status/log refs,
   lock observations and source correspondence. P3 internally retains observed recorder-prefix duration up to its last internal
   clock sample for conservative runtime checks. That prefix cannot include its
   own future return and is never called whole-call time. Exact complete-call and
   cumulative acceptance comes from the source-qualified actual owner brackets.
2. Add required, exclusively written
   sampler-emission-{process_id}-{phase}.json after source/raw/process emission,
   exact keys:
   {schema: 'bac-hardware-owner-sampler-emission-v1', policy:ref, launch:ref,
    identity:P0 identity, phase:'start'|'end', sampler:ref, raw:ref, process:ref,
    emission_end_ns:uint, module_names_after_sha256:sha256}.
   The actual emitter samples emission_end_ns and the final module-name hash
   AFTER the complete process write/reference hashing. It then writes this record
   with the prepared primitive writer. This clock explicitly excludes the
   emission record's own write, final checks and actual return. A final module
   check and runtime budget check still run after its write. No P0 end by itself
   implies this record, return or owner success happened.
3. The actual source owner brackets EACH call to record_fork_process with
   preloaded monotonic_ns(), in the SAME actual guard. It samples entry_ns before
   invoking P3 and return_ns immediately AFTER the P3 function returns, before
   any owner emission. Its existing strict terminal child payload gains the
   required recorder_returns list, exactly two rows in start/end order:
   {phase:'start'|'end', process:ref, emission:ref, entry_ns:uint, return_ns:uint}.
   The process ref is the returned P0 ref. The emission ref is obtained from the
   known fixed output filename through the preloaded primitive no-follow hash
   operation; it is not decoded in the guard and not predicted before the call.
   No separate source body/helper is proposed. The emission record path follows
   the actual process identity, never a worker label. The owner uses the existing
   prepared path/encoder machinery; no import, Torch/NumPy, Queue, RNG or scope
   unwind is introduced. Nonfork/spawn owners do not acquire this field/profile.
4. After all strict guard actions/assertions, BOTH P3 calls, both return samples,
   emission-reference hashing and the existing strict terminal payload write,
   the actual guard sends its existing pipe acknowledgement. The parent samples
   its monotonic clock immediately AFTER receiving that actual acknowledgement
   and after its actual wait/reap. The exact parent custody extension is:
   {launch:ref, child_identity:P0 identity, terminal_payload:ref,
    acknowledgement_received_ns:uint, reaped_ns:uint, wait_status:int}.
   These are observations inside the existing source-owner pipe/wait protocol;
   parent-PID/payload/pipe/trial/action correlation remains mandatory under P5.
   Parent records are written later and make no claim their own write occurred
   before the guard cutoff. They record an earlier observed guard endpoint.

The parent preserves its original min(existing 10s limit,
launch.owner_deadline_ns) deadline for actual acknowledgement and successful reap.
A genuine P3 return at7.9s with acknowledgement at8.1s remains eligible; parent
ack/reap is NOT required by8s and cannot independently prove an earlier8s return.
The source-qualified owner's actual brackets enforce the 3s per-call, 6s combined
and8s absolute recorder limits. This caller observation was already necessary for
individual and cumulative durations. Parent receipt/reap independently corroborate
that the exact successful child/payload/identity completed later by the original
10s deadline. No unqualified self-declared clock row or deadline-derived guessed
return can replace actual source-qualified caller instrumentation.

A killed guard, failed call, missing second row, missing emission receipt, missing
ack or missing reap cannot qualify. Actual wait status and parent timestamps are
parent-owned; P3 never emits them. No deadline is extended or narrowed.

## Independent checks and no last-write recursion

P2/P4 require the two emission records and independently reconcile every exact
ref, actual identity/phase/context/source/launch/claim, module-name equality and
inventory coverage. P4/P5 require the owner's real call-return rows and parent's
actual ack/reap endpoint, tied to the exact strict payload and existing pipe
custody proof. A child self-declared receipt is insufficient for whole-call time.

Required chronology for each phase:
owner.entry_ns <= sampler.start_ns <= sampler.end_ns <= emission.emission_end_ns
<= owner.return_ns <= parent.acknowledgement_received_ns <= parent.reaped_ns.
Actual parent wait implementations may reap before reading the ack; suppliers
must retain their actual ordering rather than fabricate this order. In that case
both independently observed endpoints must be >= owner.return_ns and <= the
original owner deadline;
no ordering between ack and reap is required by this amendment.

Each owner.return_ns - owner.entry_ns <=3s; their sum <=6s. Both phase starts and
returns lie within launch.monotonic_ns..launch.sampler_cutoff_ns. The end entry
follows the start return and the owner's required strict actions. The same host/
boot and actual immediate ancestry establish the shared monotonic clock domain.
Existing P2 launch/reap bounds remain additional independent constraints.

The source-qualified measured child return includes the new emission record's write and the final
P3 module/deadline checks. The parent's observed ack and reap occur after those
returns AND the terminal payload write. Thus no endpoint needs to include its own
future evidence write: the later observer records a fact about an already-complete
earlier operation. If parent evidence emission itself fails, missing custody
records prevent qualification. There is no infinite receipt chain and no waiver.

Abrupt guard death with a live Git sampler still relies on the separately tested
P2 OWNED PROCESS GROUP cleanup backstop; no successful return is invented and no
parent-death auto-kill claim is made. Spawn owners retain their 90s joins and empty
sampler profile. Required strict 4/7/5 guard trial/actions remain unchanged.

## Existing CPU/resource authority

Use the existing closed bac-hardware-cpu-bound-v1, not a new bound schema.
Its justification list includes the exact sampler policy reference. The role's
cpu_reservation_evidence pins that exact bound, and the bound occurs in the
root-authorized source grant's cpu_reservation_evidence inventory. Exact role/
config/argv/environment/cases/head/tree/fixed-order inputs match the sealed
job/candidate. Policy CPU limits cannot exceed the accepted role peak. The exact
accepted complete workload includes additional emission/owner/parent receipt
bytes and inodes, pipe/wait costs, child and concurrent Git process costs. Root
supplies those explicit nonzero reservations. Existing allocation/grant/admission
custody still applies; a policy reference alone grants no resources. Actual Git
executable bytes are pinned in the sealed environment.dependencies inventory.

## Bounded implementation and acceptance

P3 edits remain only its existing identity/tests within the reviewed five-body
3878-line ceiling. Add emission receipt after actual process emission, correct
sampler source-stage cumulative scope, and test ordinary complete/late/aborted
fork returns with actual no-import pipe/wait observations in the existing test
body. Mutate missing/cross-wired receipt/return/ack/reap, late return and ack beyond the ORIGINAL owner deadline,
plus interruption between process write and receipt/return. Include valid7.9s
return/8.1s ack acceptance and reject falsely labelled complete internal-prefix
timing. Real source-qualified owner instrumentation remains separately required. P0 process alone must
never pass. Keep exact immutable attempt snapshots and RED/GREEN metadata.

APP owner instrumentation and independent P2/P4/P5 acceptance changes need their
own root grants and exact source-qualified tests. P3 synthetic caller observations
qualify this transport only; they cannot certify unmodified producers or hardware.
