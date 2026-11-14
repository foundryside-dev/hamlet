# P2 → P4 completion correspondence: current adopted implementation

Factual supplier only, 2026-11-14 UTC. No new owner requirements, source changes,
tests, APP reads, or P3 body reads. Scope is the existing counted P2/P0 bodies.

Authority: `evidence-management/hardware-runner-p2/root-adoption-v1.json`,
which adopts `freeze-v2.json` SHA256
`fa917444e22b3cc3fde25392640a0d10b47c2246caebd8cfeee2ac6b40e3d5d6`.
Runner SHA256 `fc235ddfe853cab303c7299e782188e2e6c3fd895b16d1638d8525f2c152cedc`;
P0 SHA256 `adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c`.
Existing interface: `evidence-management/hardware-runner-p2/interface-contract-v2.json`
SHA256 `9c7b4e37f07014f99237b9f6ae5f70bc70fb79eb67639779c534af17a0aeb43e`.

## Exact producer/result correspondence

`Custody.result` (runner lines 1198 onward) copies these five fields unchanged
from a validated `completion.json` envelope into `result.json`:

- `collected_ids`
- `outcomes`
- `process_records`
- `obligation_records`
- `source_witnesses`

For an accepted completion these are exact JSON-value equalities, including
array order and complete reference objects (`path`, `bytes`, `sha256`). They
are not subset comparisons. P2 adds no runner source witnesses or other refs
to these five arrays. If evidence validation fails, all five arrays remain
empty; an ordinary actual exit zero then remains `completed-unverified`.
Evidence may be copied on a nonzero/interrupted execution, but it cannot turn
that execution into successful. Actual parent wait observations supply status,
start/end/elapsed/signal; P2 independently binds command and final log refs.

`result.inventory` is independently rebuilt by `_inventory(job.output)` at
result construction. It is not copied from `completion.inventory`, and is not
defined as producer inventory plus a fixed list. It lists all files recursively
present under job output at that instant, with current exact refs, sorted by
path. Normal successful execution therefore includes completion, producer files,
command, stdout, runtime context, launch, and wait. It excludes the not-yet-written
result itself. The final attempt seal inventories the entire output attempt
after all results and the final runner source witness, plus the original P1
terminal capture-result reference; it excludes the not-yet-written seal itself.
Runner source witnesses are attempt-level files, not additions to job
`source_witnesses`. Later files or byte mutations cannot be assumed covered by
an earlier inventory.

## What producer evidence is currently mandatory

P0 `job-evidence` requires all named fields, and nonempty inventory; its sources,
process and obligation arrays are structurally allowed empty. P2 then requires
the exact planned collection/outcome case sets, passing phases, role cardinality,
paired process START/END, and all planned obligation/case pairs. Process and
obligation records must be inside job output. Each obligation producer ref must
be an exact member of the completion process-record array.

For every process, the identical intra/inter/debug provenance reference must
be an exact member of **completion.inventory**, at the fixed raw observation
filename. The complete raw/context/policy/runtime/lifecycle checks remain
mandatory. Each process's own source-witness ref is read and validated against
that process identity, command lifetime, candidate/freeze, HEAD/tree and exact
candidate input inventory. Separately, completion.source_witnesses must be
nonempty, and every listed source witness must validate and match candidate and
freeze. These checks occur in `process_context` and `evidence` (runner lines
1041 onward and 1121 onward). P0 references validate current bytes/hash; a matching
path alone is insufficient.

## Explicit current gaps, not newly imposed requirements

Current P2 does **not** enforce that every process.source_witness is listed in
completion.source_witnesses, or that the source array equals the deduplicated
set of process source refs. A nonempty, candidate/freeze-matching source list
can omit another process source ref that P2 separately validates.

Current P2 does **not** require general completion.inventory membership for
source witnesses, process/obligation records, outcome evidence, lifecycle refs,
or every transitively referenced artifact. The specific raw-observation
membership rule above is enforced. Nor does P2 explicitly require general
completion.inventory to be a subset of result.inventory: valid external refs
can appear in the former and cannot appear in the job-local latter. P0 alone
adds none of these correspondence rules. A stronger producer closure rule
needs explicit agreed policy; it must not be described as already enforced.

Existing negative conditions sufficient for correspondence repair: changing or
omitting any of the five copied arrays while retaining a different successful
result contradicts actual producer→runner transport; absent/empty source list
or omitted raw provenance contradicts existing P2 acceptance; stale refs fail
hash validation. A producer inventory and result inventory need not be equal.
The presence of additional complete files in final inventory does not repair
an incomplete producer declaration or prove it was originally accepted.
