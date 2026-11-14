# Independent P3 review v1

Disposition: ACCEPT the bounded P3 actual-process observation implementation at
linked freeze v2 for root consideration. One material interoperability defect was
confirmed on v1, repaired by the author, and independently verified on exact v2
bytes. No remaining confirmed P3 implementation defect was found in this review.
This is not whole-toolchain, owner-child, application, CPU checkpoint or CUDA
qualification; root adoption remains a separate decision.

## Scope and immutable identities

Reviewed AGENTS.md, accepted P3 plan/context v3 and retained v2 observations,
root interface decision, adopted P0 contract and the author freeze/report. The old
60-line identity body remained opaque. Current counted bodies: identity 611,
tests 534, P0 520, independent probe 82 = 1,747 lines / four files. No APP bodies,
Torch/CUDA imports, hardware/server work, Git writes, installations, execution
copies, checkout changes or author-source edits were performed by this reviewer.
Inert .txt snapshots precede each review run. Existing author bodies were imported
in their authorized existing checkout; the probe only uses inert fixture sources.

| Artifact | SHA256 |
| --- | --- |
| Original freeze-v1.json | 829de9e2b48d3f82fdf5c52ec3b4000308918609fc90e83ac47208c38e2396e2 |
| Original identity source | a47a69c1e6639dae842d76e4b8f87b8ef21ec99cf07e926cda595a01a2f9c048 |
| Original tests | 3ab11afad87ea26fb68f64aa01c2b520f135dcd8b3708e4444a4686ed4ac1af4 |
| Linked freeze-v2.json | 536efffcd437970d8e6831100cb5697e3a9f3c606b60154cf7829f6dbba1b8af |
| Interface-contract-v2.json | 51369fe91bd72a44eaf1f8526f22ff7692fb5a62247a870c05d699f341b0d798 |
| Reviewed identity source v2 | 938d44339e6c0fdc5b7763eb2b33031bf3794a66e97064cf3601e7b3dbf9b445 |
| Reviewed tests v2 | 5cb82462041e95dec1bd617cc05b4dd76988400611ee0ae3297038d95e8c11c7 |
| Unchanged P0 source | adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c |
| Independent probe v2 | 64ff0f4b73e7ffff65e4fca3e3dc7e88186044a5cdee5de1df5a4f3c0bbcf1f3 |

## Confirmed defect and repair

P3-IR-1: valid P1 grants were refused when candidate JSON used sorted object keys.
P1 supplies inputs in source, tests, configs, scripts, ratchet, artifacts order,
preserving each category's entry order. Frozen P3 flattened dict.values(), while
its fixture supplied alphabetical grant order and concealed the mismatch.
The independent test supplies P1 order against alphabetical candidate JSON and
failed specifically with root/inventory authority mismatch. This is a material
integration defect, not an allowed transport variation.

Author repair changes only that flattening to the fixed category sequence, fixes
the grant fixture, and adds an order-specific regression. The independent frozen
RED now passes unchanged in intent. Inspection of the snapshot diff confirms no
other production behavior changed. No P1 or P0 mutation was needed.

## Retained execution evidence

All paths below are relative to E/hardware-identity-p3/independent-review.
Actual argv, child PID, UTC bounds, exit code and source hashes are retained.

- order-red-execution.json: PID 188885, 2026-11-14 07:14:43.998514 through
  07:14:44.476944 UTC, exit 1; one intended regression failure.
  SHA e5f4e3c14aaaac6e346e7a8a06fd708f165c67c5ad4c0df014f88f997ff1c903.
  order-red.log SHA 45370c40cc64af50624fefcc7dc67717cb2e352c594147b8405a481b3b51516d.
- fixed-v2-execution.json: PID 189108, 2026-11-14 07:16:07.869283 through
  07:16:17.244235 UTC, exit 0; 49 passed, 3 deselected.
  SHA 7c1045192b1a8ceef59108065ebf17886f7957b73b5a7b84574cc5cc97521c1f.
  fixed-v2.log SHA 75c1751439d269ea87530ff87ce100d4629b85a32cd54338a7733b951b42c092.
- snapshots-v1.json SHA e3eb89d861b8c3be4bef039c428ff53aa15b4dff45984b131dcea28230aa3320;
  snapshots-v2.json SHA a73f13575457f9c66b7615737fb4367ce9800e56d38af7af1b141209f9f6c95e.
- evidence-inventory-v1.json hashes retained fixtures, logs, executions and snapshots.

The 49 are one combined run: 45 author tests plus four independent checks. They
must not be added to the author's overlapping 45. Independent checks cover P1
order, mutated unloaded config input, deleted sealed environment key, and actual
reparenting. Grandchild PID 189110 emitted its own start under PPID 189109, then
observed PPID 1 and refused end with actual parent process identity mismatch;
reparent-result.json and start/source/raw evidence remain in fixed-v2-fixtures.
No prerequisite failure was discarded. The sole independent RED is retained.

The three deselections are test_xdist_environment_probe and the two parametrized
test_xdist_replacement_probe discovery controls. Those require an explicit discovery
destination and intentionally crash one worker; they are not the substantive
acceptance checks. The selected suite still executes actual serial pytest, two
xdist workers, crash/replacement, spawned children and synthetic fork guard.
Three selected inert case helpers and one hook-surface assertion are included in
the author count; the count alone is not acceptance evidence.

## Findings and qualification limits

The implementation samples actual PID/PPID/start token/host/boot, interpreter,
/proc argv, cwd and complete environment; it observes and hashes actual loaded
source imports, rejects changed frozen references, and samples source/grant
intervals. Parent/start matching and exclusive writes preserve missing or partial
records. The independent reparent check confirms a changed actual parent cannot
produce a paired final witness. Full environment equality refuses extra, deleted
or overridden launch keys; worker additions derive from actual workerinput and
controller lifecycle, with explicitly declared common/worker framework additions.

Non-work observers use module dictionaries for the loaded CUDA marker without
Torch getters/imports or RNG draws. Fork guard returns unavailable configuration
facts without Torch calls. Work-role getter checks preserve intra-op 1 and the
admitted inter-op/debug contract. Loaded markers and declared device mappings do
not prove native CUDA execution or every possible native context.

Static policy has only prior references and known paths; runtime descriptor binds
spec, command, trusted grant and runner source to actual live parent identity.
Root-delegated P2 custody and the no-writer interval supply authority. Hashes alone
do not authenticate an author. Direct owner contexts remain authorized only by
separately accepted owner integration; they cannot substitute for CLI provenance.
Actual argv is recorded, while whole-launch agreement remains a P2/P4 check.

Actual worker configuration/down records retain prior references in causal order;
replacement consumes a recorded failed predecessor and enforces its role limit.
Crash evidence retains the absent end. Collection/report aggregation writes an
exclusive closed P0 job-evidence envelope without inventing runner exit, log,
terminal disposition, obligation satisfaction or acceptance receipts.

Remaining finite obligations: P2→P3→P4 synthetic interoperability on jointly frozen
bytes; independent P4 whole-job cardinality, causal ancestry, missing-end and
required-case/obligation acceptance; P5 actual strict owner-child/producer,
three-fork-trial and phase/RNG contracts; subsequently authorized actual source and
hardware qualification. Generic fork witness checks do not discharge any of those
strict owner trials. Source hashes cannot exclude edits restored between samples;
the root-maintained no-writer interval remains necessary. These boundaries are
explicit contract allocation, not waived P3 acceptance or a claim that hardware
qualification is complete.
