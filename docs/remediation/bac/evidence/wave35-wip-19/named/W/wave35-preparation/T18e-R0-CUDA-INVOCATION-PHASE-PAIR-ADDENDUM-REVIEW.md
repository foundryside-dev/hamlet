# Invocation phase pair — bounded addendum review

2026-11-13. Reviewer `/root/bac_astra_invocation_source_review`.

**SPEC: APPROVED at protocol level. QUALITY: APPROVED at protocol level. No required addendum correction identified.** The proposed explicit pair function resolves the missing cross-job verification interface without changing the application API or broadening the six-role protocol. Actual tooling implementation and synthetic qualification remain owed.

Reviewed only the proposed `verify_invocation_phase_pair(reference_spec_path, failure_spec_path) -> dict` interface, its return/error/inventory contract and relevant supplier facts in `T18e-R0-CUDA-INVOCATION-VERIFIER-PREPARATION.md`, freshly verified SHA256 `5b3024f2cab1b5a808ac1d6ef23755e65e54289f3bec99cb9a5fbb5c05e71ee8`. Comparison basis is the approved six-role qualification protocol `d2b9d7fdfe5b9bb3db796830608aeb74a0de2ee0955f19878d495a5c997580d9` and its review `ace6b4ea9acaca1d93f128901f686dc1332754cdd16bc0239ffdbc16a4bf8863`. No verifier/test body, new implementation body, application execution, tool/source/test edit, branch/worktree or delegation was used. This is the sole authored artifact.

## Interface and custody

The supplied current-tool facts explain the need: existing `verify(spec_path, job_index=0)` validates one job and exclusively writes its individual receipt. Those are supplier-attributed facts, not an independent verifier-source review here. Two explicit distinct one-job spec arguments provide the missing selection mechanism without guessing a peer, changing the CLI, or silently assuming a shared multi-job spec.

The first argument must select the exact reference job/role/case and the second the exact failure job/role/case, each with integer workers1 and sealed argv. Distinct resolved subjects/job directories plus exact complementary roles prevent double selection. Root can call the function through its owned Python caller; no CLI is needed.

The mandatory individual strict receipts remain exclusive historical artifacts. The pair function reuses full side-effect-free subject validation and receipt construction, including current repository/source/verifier checks, then compares each existing parsed strict receipt against the freshly recomputed expected value. It does not trust status strings, call the exclusive-writing verifier again, rewrite a receipt or produce partial success. The phase hash added only to the two phase-role individual receipts binds the observed artifact into this revalidation.

Exact-field/type/hash/source/process checks, required existing receipts, and fail-closed ValueError behavior are appropriate. Retaining OSError/JSONDecodeError for file/JSON failures does not create a success path. Root alone exclusively materializes the returned pair dict and binds its hash later. The acknowledged final-rehash/immutable-capture obligation correctly avoids claiming that validation prevents subsequent external filesystem mutation.

## Pair comparison and returned evidence

Shared equality is limited to the normalized repository root, base/tree/manifest/source identity, devices, exception labels and observed synchronization vector. Manifest path differences are allowed only for equal exact bytes. Each subject's child and parent process values remain bound to that subject's qualified records. Avoiding cross-job PID uniqueness/equality is correct: independent sequential jobs can reuse numeric PIDs.

The seven exact top-level keys, fixed schema/status/scope strings, exact shared and per-subject keys, and eight typed path/bytes/hash references make the returned evidence concrete. References include the explicit spec, manifest, result, controller, child identity, parent observation, phase artifact and existing strict custody receipt. Their paths derive from the selected subjects, not caller-provided free-form receipt references. Reference outcome null and failure outcome identity-True preserve the approved distinction.

Comparing observed vectors rather than hard-coding an early-stop tail follows the adopted design. The pair result establishes parity and source/process custody; actual E/F identity, observation construction and parent RNG/lock semantics still depend on the independently reviewed child assertions and their qualified execution. The narrow returned scope says this accurately.

The finite `invocation-phase-*.json` inventory rule makes artifact placement enforceable without admitting roles by prefix or applying a broad job-directory allowlist. Each phase subject needs exactly its expected marker artifact, and nonphase subjects must have none. Other historical artifact namespaces retain their existing policy.

## Required implementation checks under the later grant

These enforce the proposed contract rather than amend it:

- Separate subject validation/receipt construction from exclusive receipt materialization. Pair revalidation must accept the mandatory existing receipt as input; it must not accidentally retain the ordinary writer's destination-must-not-exist precondition. Ordinary `verify` must still refuse overwriting its destination.
- Compare exact schemas and types, not only Python dict equality: `True == 1` and `1 == 1.0` must not let a tampered existing receipt or returned reference metadata satisfy the stated exact-type contract. Exercise coherent receipt rehashes and type substitutions independently of stale-hash rejection.
- Hash and count the actual bytes used for each reference and validate the existing strict receipt against the recomputed subject, including current verifier and phase hashes. Preserve each subject's own process bindings while checking shared provenance across the pair.
- Synthetic controls must prove exact return shape/reference values, no writes or partial receipts on failures, swapped/same-role/duplicate subjects, absent or malformed peers, stale verifier/source/manifest and tampered existing custody, misplaced marker artifacts, and coherently rehashed unequal event vectors. Old individual exclusive-write behavior needs regression coverage after factoring.

Root may adopt this exact finite interface and grant its implementation separately once actual application protocol bytes are frozen. This approval neither certifies the unseen verifier implementation nor grants app/tool writes, new roles, hardware qualification, producer/parent-owner acceptance or programme closure.
