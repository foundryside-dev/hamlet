# CPU Adam RNG profile contract

The ordinary dense CPU public Adam step described here is qualified as consuming no Python, legacy NumPy or Torch CPU global RNG state in the measured environment. Qualification covers first-step empty Adam state and subsequent real updates with a warm library. It does not qualify model construction, gradient generation or full learning.

## Admitted execution

The optimizer is exact built-in torch.optim.Adam with unmodified public methods, ordinary eager execution, ordinary dense real CPU float32 Parameters and nonempty matching dense gradients. Parameters remain exactly paired with their genuine owning model. There is no closure, user optimizer step hook, custom Tensor dispatch, AMP, scripting/compilation/graph capture, or custom profiling/instrumentation extension in this admitted execution. These are qualification boundaries, not bans on supported capabilities.

Actual groups use positive finite float learning rate, betas(.9,.999), eps1e-8, weight_decay0, foreach/fused None, and amsgrad/maximize/capturable/differentiable/decoupled_weight_decay False. Native RND/adaptive witness learning rate is .001; actual resolved ICM and Q factory witness learning rate is .0001. New options, devices, runtime modifications or extensions require their own classification.

The genuine native RND, adaptive inner RND and ICM constructors supply their actual optimizers and Parameters. ICM configuration is resolved through real typed policy inputs and selected compiled configuration. The Q optimizer construction is actual OptimizerFactory.build using the effective selected brain's Adam/constant-schedule configuration and a real small Linear module as Parameter owner. This qualifies that optimizer factory profile, not POP's token-set network, Q forward/training or replay.

## Runtime identity

R35 candidate tree22ee68664004f4cb0b0177e8f92db1686211b18e, base d152425faf9cfdae1eed00e19719441ce11e0f5d; test tests/test_townlet/regressions/bac/test_cpu_adam_rng_profile.py307 lines, SHA2567c37fb24f54eda7f3e22712e1e7622f9579f8667365f7a1bc80f1048c86e5866.

| Installed component | Identity |
|---|---|
|Torch|2.11.0+cu130|
|torch/optim/optimizer.py|1193 lines; SHA256ea3497233845529a212f81d4d325828eadc20f387ab94b1c21b96057f0001536|
|torch/optim/adam.py|991 lines; SHA2567e5c8482c91b88e355a8bdf1d4b1930e8d961fb99f00c2179946b164a03652b6|

Installed source identities were obtained in the executing process by byte hashing. They identify the classified runtime; they do not prove arbitrary later monkeypatches or extensions harmless. The installed-source capsule establishes default nonempty CPU dispatch to single-tensor Adam and its public wrapper boundaries.

## Executable evidence

Collection found six nodes. Four fresh per-family processes each passed the actual native/factory first and second public zero-argument steps. Each step preserved complete Python random state, the complete legacy NumPy state tuple including array and cached-Gaussian fields, and Torch CPU RNG bytes. Next actual draws matched independently restored pre-step references. Every optimized Parameter changed, Adam state initialized then advanced step1→2, finite nonzero moments progressed, and real native service counters remained unchanged. Manual gradients were deterministic and prepared before measurement; no learning counters or moments were fabricated.

Each fresh process observed Dynamo absent before setup/construction, then present after actual construction and before first step. This is first-step-empty-state / warm-library evidence. No optimizer warmup was performed outside measurement. No cold-library or constructor RNG-purity claim follows.

The actual stochastic instance prehook control ran once and consumed all three streams; the same comparator returned(False,False,False). Its actual removable handle was removed in finally, ambient state restored, all global/instance step registries remained empty, and a subsequent genuine bare step3 returned(True,True,True). Existing hooks were never cleared to manufacture admission. This control demonstrates why stochastic callbacks do not inherit core-step exemption.

The scoped first sparse-gradient refusal raised the actual Adam RuntimeError and preserved all three RNG states/continuations, Parameters and empty optimizer state. It is not an arbitrary-failure rollback promise. Sparse COO construction at test line291 emitted one UserWarning about implicit invariant checks being disabled. The warning was retained; explicit invariant selection is optional P3 and was not implemented or suppressed.

Root's four-family runs plus the two controls passed. Fresh independent Astra review approved the actual five bodies with no P1/P2; its independent SAME-six execution passed6 with1warning in16.37s pytest/20.395822048187256s wall. These reproduce six unique nodes, not twelve. Root's final serialized verifier qualified source805/config573/artifact13/controller1/index/import/thread custody and registry14/MAIN1 for the closed evidence.

Root's warning-count parser was administratively corrected from the same closed controls log; the original receipt and invalid intermediate job-name receipt are preserved. The verified controls receipt is2PASS/1warning. No application rerun or test change was used to repair the accounting.

Evidence lives under /workspace/bac-review-2026-11-01/qualification/wave35-r35-*: family logs/custody, controls, collection and independent receipts. Independent log SHA2565b1a1ccc651d1b9165db2e6eecedc888ea6c80f6775b5634ccc5fd68c412063e; final independent custody SHA256b746af15beeb7e4e1df4fc68b1c63a32c73a4f1c5439793e41072615c07a785d. The author report records complete specification/log/custody seals.

Global Ruff, Black, expression documentation and no-defaults ratchet600 passed. Mypy retained six preexisting oracle/driver.py errors among197 checked source files; static all_passed remains false. This profile result is not a whole-repository static-green claim.

## Custody implications and preserved behavior

An independent owner's step satisfying this qualified RNG-free profile need not enter the global RNG admission gate merely because another owner's private stream is installed. It still mutates its own Parameters and optimizer state. Copying, reset preparation and publication of the same owner require actual owner exclusion/freshness regardless of unchanged RNG bytes. Native prepared handles alone check destination identity and single use; they do not detect intervening manual or native-accounted model mutation.

Constructors, stochastic forward/backward, closures, hooks and other nonadmitted execution regions require actual R0 admission where they consume ambient RNG. Supported direct/manual APIs, genuine optimizer replacement and RND/adaptive signed manual displacement remain available. No blanket interception, wrapper, closure/hook ban, capability removal or process-cohort checkpoint requirement follows from this result. Manually advanced ICM state is not claimed checkpoint-valid under its strict S=U-O equation.

Test cases run serially with no competing in-process RNG user; original ambient states are restored in finally, including failures. Independent qualification processes may execute elsewhere. CPU test code does not invoke CUDA RNG APIs; installed Adam's internal availability check remains part of its measured public path. CUDA is unavailable and unqualified.

This contract does not close full learning/native history, same-owner mutation exclusion, R0/B1 admission and reset freshness, outer publication, runner integration, exact stochastic/cohort continuation or whole-BAC acceptance. Main BAC remains28 qualified/38 remaining/66 total.
