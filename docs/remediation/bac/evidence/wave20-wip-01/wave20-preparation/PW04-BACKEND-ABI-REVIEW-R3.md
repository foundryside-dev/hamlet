# PW04 backend ABI scoped correction review R3

Reviewed proposal SHA256 `44c00e460cc83940c3b1a5c8a746f48ae78014c8f1539a814ea45ff5521472bd` against root's PW04-NO-DEFAULTS-RULING.md and the preserved previously reviewed R2 proposal. Scope is the required-input correction, its fixture transport and new amendment breakage only. Read prose only; no provider/test/WS/RP/helper/POP source inspection, runtime/imports/tests, Git/index, branch/worktree/copy/deletion or subagents. This ignored review is the sole write. Exact four-file/3750 projected ownership remains binding.

## Verdicts

**Specification: PASS for this required-input correction.** Both newly introduced constructor arguments are explicitly required and keyword-only for RND, ICM and adaptive. Neither has a default, and no compatibility adapter, signature probing, whitelist or default ratchet exemption is authorized.

**Design quality: PASS for the narrow correction and fixture migration contract.** No new blocking defect was found. This is design review, not source/test acceptance or production/runtime clearance. Root retains those decisions. Integrated POP/ordinary runner/native qualification remains REQUIRED OPEN.

## Disposition

The earlier R2 review missed the no-new-defaults conflict in the proposed constructor arguments. Its approval of those defaults is superseded by this correction and root's binding ruling. Requiring explicit inputs fixes that conflict without requiring capability removal or a global redesign.

The revised boundary preserves prior constructor parameters and explicitly selects shared behavior with rng=None and service_clock_unit='vector_tick'. Shared ambient allocation order, direct actual learning, grouped service and native continuation remain requirements. The private factory passes its actual candidate RNG and world_eligible_admission explicitly. RNG ownership and cadence remain independent selections; supplied RNG cannot infer the unit. Adaptive must explicitly forward both inputs into its actual nested RND. No native schema, clock progression, preflight, prepared-install or overflow semantics changed.

The counted regression's permitted migration is narrowly defined: _build transports its named selected unit and RNG/override values; invalid explicit overrides remain invalid and are not normalized away. Its two direct RND/AI constructor branches transport explicit None/vector_tick. Preserve all 214 cases/assertions and all nine direct-defect controls. No old/new signature fallback, exception swallowing, skip, changed expectation or inference of omitted arguments is permitted. The old-source fixture preflight necessarily predates transport of keywords that those old constructors do not yet accept; it is valid phase-specific fixture evidence, not evidence that omitted inputs remain supported by the new ABI.

Root reports 18 positive fixture preflight passes, then 195 call-phase failures/19 passes across 214 cases, comprising 186 explicit missing-API witnesses plus nine existing direct defects, and 193 source-custody passes. These are attributed root results only; this review ran nothing and inspected no executable test source. The allowed future helper change must be recorded and checked as required-input transport at the next frozen candidate, with those cases and causal assertions intact. No initial constructor TypeError caused solely by adding required keywords may be relabeled as a promised-behavior RED or GREEN.

The prose comparison shows only the constructor/default and construction-context correction, archive/status wording, and its appended receipt. It introduces no new source file, helper, option family, learning substitution, clock fallback or native-format compatibility path. The receipt explicitly acknowledges external caller/test breakage and requires bounded migrations before integrated release and the early coherent full gate. Earlier wording about running existing suites unchanged applies only where still current; it cannot override this explicit migration obligation or justify pretending old signatures continue working.

Factory/POP/runner owners must receive the exact exported required-input ABI. Preserve all previous release gates, including actual current runner.run, native artifact/digest and receiving load, next actual optimizer/tail/clock continuation, and complete parent unchanged refusal of deep malformed provider state combined with changed candidate parent state. No backend-only pass, old-source fixture result or stub/skip closes those obligations.
