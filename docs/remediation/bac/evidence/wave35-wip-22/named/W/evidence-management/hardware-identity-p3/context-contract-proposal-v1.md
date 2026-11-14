# P3 actual-process context proposal v1

Public record_process(context, phase) returns immutable P0 process file reference.
Closed context: schema='bac-hardware-identity-context-v1', spec=P0 reference,
job_id=P0 id, role_id=P0 id, command=P0 reference,
trusted_grant=P0 reference, required_imports=[{name:P0 id, reference:P0 reference,
phases:nonempty unique subset of [start,end]}], worker_roles=[{worker_id:P0 id,
role_id:P0 id, replacement_start:[P0 reference] length0/1}],
parent_start=[P0 reference] length0/1, replacement_start=[P0 reference] length0/1.
Root/caller supplies trusted_grant out of band, matching source-freeze.grant;
context itself is authority-bearing input, not an untrusted self-authenticating
file. A pytest CLI option --bac-identity-context PATH plus
--bac-identity-context-sha256 SHA pins root-authored context. Never derive this
trust anchor from candidate/spec/grant itself.

required_imports pins exact module names/files and mandatory observation phases;
start may omit modules required only at end. Already-loaded declared modules are
always checked. All must
be in candidate input inventory or sealed environment dependency references.
No APP/Torch import is performed by the recorder. Non-owner calls cannot invent
child observations: PID/PPID/start/host/boot are sampled inside actual emitter;
parent_start must match observed live PPID identity; replacements must point to
an earlier actual process start for same role, with distinct full identity.

Exact role is context.role_id. Controller pytest uses it. With xdist configured,
controller distributes context to workers through workerinput; worker_roles maps
actual workerinput.workerid to explicit role_id and predecessor start reference.
Controller writes immutable lifecycle association with actual gateway worker id,
controller start reference and sent worker context. Worker checks actual workerid
and observed parent. Missing replacement mapping fails closed; no inferred gwN
predecessor. P4 remains responsible for cardinalities/replacements acceptance.
Actual child owners invoke record_process with explicit role context.

Source witness checks immutable grant active interval/no-writer/untracked,
exact candidate fields/inventory and freeze bindings, HEAD and read-only
cached diff-index against candidate tree under existing no-follow index lock.
No write-tree/staging/source writes. All candidate and loaded import files hash.

No loaded Torch => unavailable thread/debug facts with reasons, not-loaded,
uninitialized. Nonwork role with loaded Torch => no Torch API calls; reads only
module __dict__ CUDA _initialized bool (unavailable => refuse), loaded-without-calls.
This is Torch loaded initialization-marker evidence only, not a proof about all
native CUDA contexts; a private raw observation file states that limit.
Fork guard => no Torch/CUDA access beyond loaded module dictionaries/origins,
forbidden-inherited-module-witness and unavailable thread/debug facts. Work role
requires already-loaded Torch and observes get_num_threads/get_num_interop_threads/
is_anomaly_enabled/cuda.is_initialized only; no RNG/device initialization.
Device assignments remain admitted provenance, never a real-device work claim.

Distinct exclusive files process-IDENTITYHASH-{start,end}.json and source witness
files are under job.output. Duplicate phase refuses. End requires start from same
actual process identity plus monotonic interval. Closed completion.json is P0
job-evidence, controller-produced only after pytest sessionfinish, aggregating
worker/child files without fabricating observations. Incomplete/extra identities
remain detectably incomplete for P4 (P3 assembly never certifies custody); partial files remain. Runner owns final log/exit/signal/
end/elapsed/disposition and must treat missing envelope as unverified.

Private pytest reports are exact schema/kind/process/case/phase/outcome/longrepr;
P0 outcome.evidence references them. Required IDs/outcome disposition remains P4.
No obligation_records are fabricated: owner-supplied envelopes remain external.

process.environment records exact job.environment projection after comparison;
actual complete environment is separately retained in raw observation. Dynamic
xdist keys are therefore visible without widening sealed job.environment.
