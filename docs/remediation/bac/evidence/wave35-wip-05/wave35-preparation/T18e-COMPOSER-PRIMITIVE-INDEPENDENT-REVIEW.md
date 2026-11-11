# T18e composer primitive independent review

## Initial authored-regression/spec review

Disposition: **AUTHORING APPROVED**, subject to root-attributed actual collection and causal RED. No material P1/P2 authored-test or finite-spec gap found. This is static authoring approval, not implementation approval or a runtime pass. Current production does not yet implement the required scale input; that is the intended RED and is not a test defect.

Review followed the exact primitive brief first, author Stage0/Stage1 report, real CONFIG-FIXTURE-API capsule, composer readiness report, accepted phase/clock reconciliation and independent review, and owner AGENTS.md. Required API and diagnostic semantics agree with the accepted design. No compatibility defaults, aliases, alternate composer, or capability reduction are proposed.

Metadata preceded source inspection. Exactly three whole source charges entered this context; relevant production sections were displayed, with their full files charged:

| Source | Whole lines | Ceiling | SHA256 |
| --- | ---: | ---: | --- |
| src/townlet/vfs/vtc.py | 3508 | 3550 | a27e205ec3531292e56c5b743d5f70b5208a060282278b47a1dc6ee3f7470951 |
| src/townlet/environment/dac_engine.py | 956 | 1000 | c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6 |
| tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py | 195 | 350 | 0ad34fdfb781a5679762a2eacfa4ff2d86a026967e5039fe514e81a2fce0e745 |
| Total | 4659 | 4900 | Three source slots |

No RWC/ENV/config/registry/other helper or fourth test implementation was opened or introspected. Config/registry constructor validity is attributed to the public capsule. Only this designated ignored report was written. No runtime/import/probe/compile, formatting, tests, git/index action, source copy, branch/worktree/checkout, or subagent occurred.

The seven test functions enumerate 29 cases. They instantiate actual DriveAsCodeConfig, VariableRegistry, DACEngine and VTCRewardProgram, compile the real authored modifier/extrinsic/efficiency bonus, and invoke real composition. The fixture matches the public constructors and does not substitute a backend, registry or config. The literal witness establishes raw2 * scale.5 * base.25 * modifier2 = intrinsic.5, plus extrinsic1 and shaping.1 = total1.6. Independent raw, scale, base and modifier variations discriminate ignored or duplicated scale, factor conflation and scaling unrelated terms. Scale0 preserves extrinsic/shaping at total1.1.

Heterogeneous per-row scale rejects scalar/mean transport. The distinct nonzero-scale terminal case prevents scale0 from hiding absent intrinsic done masking. Diagnostics retain provider raw, scale, raw*base and modifier-only weights even on done rows. These cases make no ENV retirement or inactive-entry claim.

Omission tests require scale at both real entrypoints and name the missing argument. Fifteen malformed cases reject non-tensors, scalar/rank/length broadcasting, non-float32 dtypes, NaN/infinities/negative values, and CPU-versus-meta device mismatch with scale-attributed exceptions. The meta case is a meaningful CPU-host-independent wrong-device control; it does not certify actual CUDA execution.

Ownership cases first check every input is unchanged, then mutate caller raw/scale and verify all saved outputs, then mutate each returned provenance tensor and verify caller storage and all other outputs remain independent. Autograd checks distinct live raw/scale derivatives and zero terminal derivatives, input values, and graph-bearing provenance. These controls adequately cover the finite requirement without importing test-helper implementations.

Expected initial RED: VTC currently rejects the unexpected explicit keyword before arithmetic; direct DAC currently accepts the keyword through kwargs and ignores it, so malformed-scale and required-omission controls fail by not raising. Root must distinguish these intended failures from fixture/collection failures. Source-derived 2.1 versus desired1.6 is not represented here as an executed numerical RED. Actual root collection/RED results remain pending.

No optional P3 change is required for this bounded authoring approval. Stage2 needs same-context review of the actual changed VTC/DAC sources and final unchanged-or-revised test identity, plus supplied runtime evidence. Production validation order, exactly-once scale multiplication, clone/autograd semantics, named forwarding and no-default API remain to be assessed on the actual patch.

This primitive remains unreleased coherent work. Original actual ENV/runtime all-family and both-scope integration, normalization/admission once, successor/predecessor identity, retirement/inactive masking, canonical replay, parent clock/service, current native continuation and full global gates remain mandatory and unqualified by this review.

## Root-attributed actual R11 RED qualification

Root supplied actual execution evidence after initial static review: collection **29 collected, PASS**, wall4.9118s; causal run **29 failed, 0 errors, 0 skips, 0 warnings**, wall9.9647s. Failure partition is 12 VTC unexpected-runtime_intrinsic_scale TypeErrors, 8 DID NOT RAISE ValueError, 8 DID NOT RAISE TypeError, and 1 DID NOT RAISE RuntimeError at the missing-required/invalid-scale direct DAC contracts. Root reports no import, fixture or config failures. These are the predicted causal missing-feature failures; collection and genuine construction succeeded.

Evidence is root-attributed, not independently executed by this reviewer: `/workspace/bac-review-2026-11-01/qualification/wave34-r11-{collection,causal}` logs and negative custody; exact798-source/573-config/13-artifact/3-pytest-process/index/14-registry MAIN1 custody PASS; tree403e9d839e59584d27e8aae44ccda1700b3f27fe, base30a802a9. No command text was supplied to this reviewer, so none is invented. Production remained frozen during this initial review.

Final initial disposition: **AUTHORING APPROVED — zero material findings**, with actual causal RED qualified as above. This clears the authored-regression review; it does not approve a production implementation that has not yet been authored or establish numerical GREEN. Retain the same bounded context for the requested actual Stage2 implementation review.

## Actual Stage2 source and independent GREEN review

Disposition: **APPROVED — zero owning material findings** for the finite composer primitive. The actual changed source satisfies the brief, and the independently executed frozen 29-case regression passes with custody verified. This is not whole-T18e or coherent-consumer release approval.

Metadata was refreshed before source inspection. Same three source slots, no fourth implementation body:

| Source | Whole lines | Ceiling | SHA256 |
| --- | ---: | ---: | --- |
| src/townlet/vfs/vtc.py | 3510 | 3550 | a2d14e8bf9d7363e36f5778182395a4e5110052ca5591efacb1c98d63dad4390 |
| src/townlet/environment/dac_engine.py | 977 | 1000 | b129d7ac5cdbf7e6ed27dd6cd5f9529dc9e7d2e0154b43a4db028d7aef78e317 |
| tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py | 195 | 350 | 0ad34fdfb781a5679762a2eacfa4ff2d86a026967e5039fe514e81a2fce0e745 |
| Total | 4682 | 4900 | Same bounded context |

VTC now requires scale explicitly and forwards it by name, without prescaling or changing output validation. DAC requires the keyword-only scale and validates tensor type, exact full-population shape, float32 dtype, selected device using existing device semantics, and finite/nonnegative values before reward computation. Meta mismatch is rejected before value inspection. The actual arithmetic multiplies cloned provider raw by cloned runtime scale exactly once and independently by drive base and real compiled modifier product, retaining existing terminal masks. Neither clone detaches. New provenance has owned storage; historical raw*base and modifier-only weights retain their exact meanings. No compatibility path, new config field, copied composer, or unrelated validation expansion is introduced. Existing extrinsic/shaping paths remain outside runtime scaling.

Independent commands, executed from `/workspace/hamlet` under root's explicit authority:

```
python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave34-r12-independent-spec.json
python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave34-r12-independent-spec.json
```

The runner executed `.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py -q --no-cov -p no:cacheprovider -p bac_source_identity -n 2 --dist worksteal --basetemp=/workspace/bac-review-2026-11-01/qualification/scratch/wave34-r12-composer-independent`. Inspected actual log: **29 passed in3.87s**, two workers, no failures/errors/skips; wrapper wall7.560001373291016s, exit0. The verifier independently reported29 passed,0 skipped/xfail/xpass and0 summary warnings. The raw log also contains the standard three startup PytestBenchmarkWarning messages disabling benchmark execution under xdist; these do not appear in the pytest summary count and are not hidden as an absent diagnostic.

Verified source/index/import/thread/fixture custody **PASS**:798 source guards,3 process identities,573 config digests,13 protected artifacts,14 worktree registry records,1 available worktree. Candidate tree444c2840c67598d882824564e98bdd6dcd9ab03b; base30a802a996fe8bf7cd63e53d211fa8b2cd028f77. Manifest SHA256cbb4c0b4aa1bf4aedbe56841e49aa296ed17f7fa26f11750b757378fe347117b; harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791; actual independent log SHA256c29827d69fcbad52287568462f6ad15e2f170eba380e22b2c4f227e7321d69c0 at `/workspace/bac-review-2026-11-01/qualification/wave34-r12-independent/independent.log`.

No optional P3 request is needed for this approval. The trusted runner/verifier were invoked without reading their helper bodies; no new implementation source, ad-hoc import/probe/script, git/index action, or tracked write occurred in this review. The ignored report remains the only reviewer-authored file.

Known integration boundary, supplied by root: existing RWC/current consumers are not yet migrated to the now-required scale API. That is a mandatory unreleased coherent-integration gap, not silently supported by a default and not closed by these29 passing cases. Actual parent/ENV/runtime all-family and both-scope behavior, stats/admission once, phase equality/identity, retirement/inactive handling, canonical replay, parent clock/service/current native continuation, and full gates remain required. Source and independent GREEN approval here qualify only the owning primitive.

## Public API capsule source-truth receipt

Disposition: **AUTHOR API APPROVED**, zero material correction required. Reviewed `T18e-COMPOSER-SCALE-API.md` at measured SHA2563859debca8e7dbe1a2b8543ce4ac4107b845787b3a774e453462d98ea7f505f0 against the same retained three-source/4682-line actual implementation context and independent executable evidence above. This prose review adds no source body or runtime execution and leaves the existing actual-source/runtime approval intact.

The capsule accurately publishes the required signatures and named forwarding; exact scale type/shape/dtype/device/value validation and its order; single DAC scale multiplication independent of base/modifiers; unchanged historical raw*base and modifier-only diagnostics; new cloned unmasked provider/scale provenance; input/output storage independence with ordinary autograd mutation caveats; and existing done semantics without claiming retirement or inactive-entry closure. Its root GREEN29 and independent GREEN29 are explicitly overlapping executions of the same29 cases, not58 unique cases. It correctly distinguishes author static checks from root/independent runtime evidence and limits approval to the unreleased primitive seam.

Additional global status is root-attributed, not newly executed here: four static guards PASS (Black/Ruff scoped to the three files, global no-defaults601 and expression guard); mypy FAIL10 errors in3 files, comprising9 existing oracle/POP errors and1 new RWC45 missing required runtime_intrinsic_scale. The latter is the explicit mandatory coherent-consumer migration boundary already documented by the capsule. Prior full baseline30a remained FAILED with1010 failures,231 errors,7285 passed,21 skipped across160 files/15 signatures, with source custody PASS. The current-candidate35-process CLI check was still running when this request arrived; no outcome is claimed here.

The capsule's lack of repository-green or whole-T18e claims is consistent with those open results. No new routine approval loop or source change is required by this receipt. Actual ENV/RWC/provider integration, parent/native ownership and continuation, canonical replay, remaining consumer repair, and original full gates remain mandatory before coherent release.
