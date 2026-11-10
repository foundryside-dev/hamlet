# PW03 final ABI proposal review

Reviewer configuration: root-confirmed gpt-6-astra, reasoning_effort=medium. Prose-only exact-byte review; no new source/test files opened, no runtime execution or code/test edits.

Reviewed artifact: PW03-ABI-PROPOSAL.md SHA256 d55ec8f46c1c772e4bf55002fdd3caeebc8eac10ce646380da4bfdcd5a6b3bcd, verified directly before review.

Spec verdict: APPROVED for the bounded factory producer handoff. Quality verdict: APPROVED at proposal level. No remaining material finding in these exact proposal bytes. This is not implementation acceptance, runtime qualification or integrated release approval.

Prior blocking composability finding resolved: step4 uses the actual required-argument validate_binding API on the actual callback candidate, explicitly permitting that owner's active context. No snapshot/from_snapshot preflight is attempted inside construct's model_init activation. Step5 preserves actual-candidate provider draws, while clones appear only in quiescent test comparison. Existing owner isolation, descriptor/domain/device validation and lifecycle guards remain authoritative. The proposal neither exposes private RNG fields nor duplicates canonical hashing or broadens binding into continuation validation.

Prior geometry finding resolved: exact integer obs_dim>=0 for none/count; positive width for trainable RND/adaptive/ICM; exact positive action dimension. Existing nonrandom zero-column capability and actual trainable constraints are represented in positive/negative tests.

Identity/configuration review: factory expected descriptor reconstruction uses supplied roster and explicit seed with resolved policy/geometry; complete equality validates the supplied descriptor against that expectation. The bridge separately compares actual owner stable identity, exact ID and device inventory, so spectator changes/reordering remain supported. Negative parameter tests target actual active provider_parameters (and required matching scalar fields), not diagnostic epsilon. none has empty provider parameters; no invented mismatch requirement is imposed. Wrong seed/provider/geometry/ID/device controls remain required.

Ownership/capability review: explicit shared None ownership/vector_tick remains positive, and all five current backend families are constructed with their exact selected config and service options. Private nonrandom families still receive binding validation. Separate fresh selector preserves global epsilon ownership. Real instance/state/storage/optimizer independence and genuine callback handoff remain factory evidence; genuine learning/isolation under updates remains PW05. CUDA initialization stays at explicit runtime quiescence and conditional execution limitations stay visible. No family, owner isolation or restoration capability is removed.

Error wording clarification: proposal step4 says to let ValueError/RuntimeError propagate; this is not an exhaustive exception normalization promise. The corrected CURRENT-CONTRACT records that structurally forged typed descriptor records may raise AttributeError/TypeError during serialization before from_dict. Factory must let such failures propagate before allocation too; it must not catch-and-continue or infer successful binding from exception type. This clarification requires no ABI or production change.

## Source-verified bridge receipt

Actual source src/townlet/exploration/world_curiosity_state.py remains871 lines, SHA256 a639d6f927492cf0334a49f330f514b6472be75f624f24a2f1b5e8381af93b2c. Public signature: validate_binding(self, *, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]) -> None. All arguments required; no draw/clone/owned-state/global-stream mutation. Full contract, active-boundary and forged-record exception qualifications are in RNG-BINDING-CURRENT-CONTRACT.md.

Final R2 root receipt:51PASS/1CUDA-skip10.0588s; custody PASS197source/573config/13artifacts/3process; scoped static PASS. Sol re-review: style ADDR, no new breakage. These are root-reported results from closed sessions, not fresh execution in this review. Exact formatted test419 lines SHA25607503ca5c5e9e92ea94a4403d688f6b0528f96012a2aa0ad025c9e2df6aeea06. RP768 SHA256af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c. Three-file bridge inventory sum2058 remains within ceilings; no source expansion.

Root must separately authorize factory test correction, freeze candidate/spec, establish valid fixture prerequisite and genuine missing-factory RED, then authorize factory production. Existing9 mypy errors,26 old RNG consumer fixture migrations, required native/runner integration, PW05 learning and full qualification remain OPEN. No package release/count increment.
