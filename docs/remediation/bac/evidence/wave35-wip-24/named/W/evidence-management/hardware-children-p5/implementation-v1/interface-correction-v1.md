# P5 finite implementation interface correction v1

Links the immutable root-adopted P4/P5 owner contract SHA256
960f6e1b1dec411007c9d33ab388ea9b99d560c0c701f008fe5fdf113645af97.
Root explicitly approved both corrections during this implementation task.
Independent implementation review must cover them; no separate approval loop or
actual APP/hardware acceptance is implied.

## Explicit standalone selection

Current standalone API is
`verify_children(spec_path: Path, job_id: str, destination: Path, *, obligation_id: str) -> dict`.
The keyword is REQUIRED. A job may contain several strict obligations; a
single-obligation receipt must name the exact selected sealed obligation.
Absent/unsupported IDs and omitted keyword refuse. No implicit first obligation,
single-obligation-only restriction, compatibility overload or default is retained.
The pure API remains `validate_child_obligation(subject)` with the adopted exact
subject/result fieldsets and explicit subject.obligation_id.

## One canonical launch, distinct strict obligations

A launch carries one owner_contract. P0 case-contract carries one obligation_kind.
Consequently a launch cannot equal three distinct core/RNG/fork contracts at once.
For each actual owner case, find the unique sealed strict-child-core (or
strict-child-producer) obligation whose exact contract contains the outer child
role and selected case. Its contract is the canonical owner contract. The actual
spawn and nested guard launch bind that contract.

Each selected obligation still binds its own exact contract, validator, evidence
class, required cases, minimum_devices and witness schema. Its role subset may
differ from the canonical contract; every role definition must equal the job's
exact admitted definition, with no duplicate or foreign roles. Selected and
canonical cases/classes/minimum_devices/validator agree for these CPU controls.
Canonical evidence must name the same exact payload, producer process and case,
with exact own contract/kind/spec/job/attempt. Missing or ambiguous canonical
matches, crosswired graphs, altered role definitions and lowered requirements
refuse. The inherited case always checks three genuine guard trials and the
complete admission4/local7/invocation5 action sets, regardless of which strict
component is selected. This is correlation, not a generic status-string waiver.

`synthetic-contract-example-v1.json` illustrates one inherited_pid job with
canonical core roles controller + outer spawn + guard(count3), RNG roles
controller + outer spawn, and fork roles outer spawn + guard(count3). All select
the same inherited pytest node, cpu-standin, minimum_devices0. Guard count3 and
4/7/5 actions are semantic requirements, not P0 minimum_devices. The example is
explicitly synthetic; its references/resources do not authorize an APP run.

## Implemented boundary

The pure function performs fixed semantic dispatch and schema-directed traversal
of supplied bytes. It does no filesystem reads, dynamic imports, subprocess,
APP/Torch/CUDA/Git calls or receipt writes. Standalone performs live P0 validation,
no-follow reads and exclusive strict-component publication with observed own
PID/PPID/start/host/boot/UTC. It does not acquire external root/no-writer authority
or replace P4's independent common/source/process/full transport qualification.

Known owner filenames, source origins, actual report/claim/start/end graphs,
sampler policy/emission/return/parent custody, closed producer errors and RNG
baselines, independent phase receipts and exact consumed documents are checked.
Unrun/refused transport is unrun; retained failed/interrupted transport is
unsatisfied; malformed/conflicting referenced observations refuse ValueError.
Actual source assertion execution remains dependent on source-qualified owner
instrumentation and root custody; synthetic fixture success cannot supply it.

No P2/P3/P4/APP code changed. Historical verifier and P0 bytes remain unchanged.
Source1256 + tests1354 + historical752 + P0526 =3888 charged lines/four bodies,
within the granted4778 and individual1500/2000 ceilings.
