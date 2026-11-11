# Native Adam construction and managed call facts

N1 constructs actual torch.optim.Adam with only positional parameters and explicit lr. Its managed training/validation calls supply no closure or other step argument. No optimizer pre/post/global hook registration occurs in the four owned production sources. These source premises support selecting a real CPU default-Adam witness; they do not prove that every exposed optimizer, transported configuration, external hook/closure or installed Torch extension is RNG-free.

2026-11-11; read-only extraction at root-supplied current HEADd4426803. Same five-source context, counts/hashes verified before targeted reads, total2524. No Torch implementation, EPS/Count, helper or sixth implementation read. No import/runtime/test/probe/git/branch/worktree/source-copy/subagent or production/index action. Only this ignored prose written. Installed Torch implementation/path facts are another owner's evidence; not rederived here.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py |910|30d3e9fba6ae6f90ffdda425c986bd6abecaf70e3728bdf104ca21ca832adc78|
| src/townlet/exploration/adaptive_intrinsic.py |335|1f448e07908d6b709b1e66ab5e163fa6dbc93a306b86d9eb8702d7968a47b47a|
| src/townlet/exploration/icm.py |541|f6cdecb466ac99b4dfe63ec00417495c3117e8947c5793e54c0dd71aa76d4964|
| src/townlet/exploration/provider_factory.py |153|dc69a831e045bed5c71b5bd448b1e9ff0163e6bce9d816b41d10af0f580708c8|
| tests/test_townlet/regressions/bac/test_native_learning_reset.py |585|b02394963c5a33401a4018b5f4eff1b49d002dfd7cd2bb4df1c2535aa04930d5|

Factory hash now reflects separately owned N2's explicit NoneExploration import/selection; no factory/native edit was made for this capsule. Three model sources and frozen test retain their original N1 seals.

## Actual construction sites and kwargs

- rnd.py218: `self.optimizer = torch.optim.Adam(self.predictor_network.parameters(), lr=learning_rate)`. Positional first argument is actual predictor Parameters. Constructor learning_rate is retained from the genuine native constructor argument, selected by make_backend from policy.rnd_learning_rate. No other Adam argument is explicitly passed.
- Adaptive constructor delegates to actual RNDExploration using `learning_rate=rnd_learning_rate`; it constructs no additional optimizer. Its real inner optimizer is the preceding RND call. Factory supplies policy.rnd_learning_rate as rnd_learning_rate.
- icm.py117: `self.optimizer = torch.optim.Adam(self._parameters(), lr=self.learning_rate)`. `_parameters()` concatenates actual encoder, inverse_model, forward_model Parameters in that order. self.learning_rate is float of the validated constructor value; factory supplies actual selected provider_parameters['learning_rate'].
- icm.py378, actual state reconstruction: `optimizer = torch.optim.Adam(parameters, lr=self.learning_rate)`, with Parameters from the three copied prepared modules, then `optimizer.load_state_dict(_owned(payload))`. This constructor also explicitly passes only parameters and lr; loaded groups can determine subsequent flags under ICM's current strict destination-group validation.
- RND state preparation deepcopies `(self.fixed_network, self.predictor_network, self.optimizer)` together at656, preserving their copied graph/Parameter relation, then loads validated transported optimizer state. It does not call a new Adam constructor there. The disposable probe is deepcopy of that prepared optimizer at711.

At **all owned production Adam construction calls**, betas, eps, weight_decay, amsgrad, foreach, maximize, capturable, differentiable, fused and any installed-version additional option are **not explicitly supplied**. Their effective initial values come from the installed torch.optim.Adam implementation; this capsule does not substitute remembered defaults. Factory itself directly constructs no optimizer. No generic optimizer wrapper was added.

## Exact managed step calls and callback scope

RND `_update_predictor` at494 computes the actual target/predictor MSE, checks finite loss/gradients, calls `self.optimizer.zero_grad()`, `loss.backward()`, then at518 **`self.optimizer.step()`**, with zero positional and zero keyword arguments. It subsequently removes the FIFO batch and increments native consumed_rows and optimizer_updates once. Shared public update/update_predictor and both explicit clock services reach this same implementation. Adaptive delegates actual training/service to its inner RND.

RND `_prepare_available_state` builds disposable `probe=deepcopy(optimizer)`, supplies zero gradients to copied Parameters, then at716 **`probe.step()`**, again with no arguments, before finite destination checks. A restore/reset validation may therefore execute real off-side Adam. No native closure function is built or supplied to either call.

ICM `_train_batch(mandatory: bool)` at191 computes actual inverse/forward objectives, calls `self.optimizer.zero_grad(set_to_none=True)`, loss.backward(), finite-gradient checks, then at207 **`self.optimizer.step()`**, no arguments. Real queue/counter/mandatory-or-ordinary publication follows. Both shared context service and explicit eligible-admission service reach that method. ICM state validation reconstructs/loads actual Adam but does not itself call optimizer.step.

There is no native method override of Adam.step, no `closure=` passing, and no project registration call for optimizer step pre-hooks/post-hooks/global optimizer hooks anywhere in the three model sources or factory. The scoped source search also found no hook-registration code in the frozen fifth test. This is a negative claim **only about these owned bodies**. Other project/bootstrap/library/caller code can register hooks or install profiling/dynamo/other extensions; absence here does not certify their absence process-wide. Deepcopy/state_dict does not establish that arbitrary attached hooks are absent or harmless. Installed Torch's closure/hook/profiler/dynamo behavior and dispatch path require that producer's source facts and the actual witness conditions.

## Exposed manual operation and replacement remain possible

The actual existing manual form is `rnd.optimizer.step()` after caller-owned gradients; adaptive uses `adaptive.rnd.optimizer.step()`. The frozen regression at441 performs that real call without arguments. Managed source never passes a closure, but the exposed object is actual Torch Adam: whether/how `optimizer.step(closure=...)` executes is the installed Torch public API, not a native wrapper signature or a prohibition established here. No native/domain gate intercepts existing direct optimizer calls, closures or hook invocation today.

The existing negative-displacement control at native test518 assigns a **genuine** new `torch.optim.Adam(rnd.predictor_network.parameters(), lr=0.001)` to rnd.optimizer. It preserves actual model Parameters while replacing optimizer history, rather than fabricating steps/moments. Public zero_grad/state access and actual manual updates remain available. RND/adaptive derives signed delta=S-(U-O); manual action changes actual S independently of native service U. Native reset still chooses O=retained U/delta0 and fresh Adam, preserving supported future manual actions.

Exact `type(backend.optimizer) is torch.optim.Adam` checks occur in **prepare_learning_reset** (RND852 and ICM508) on both current and fresh objects, alongside exact actual model Parameter pairing. These reject an optimizer subclass/wrapper as a reset candidate; do not pretend a proposed wrapper already satisfies them. They are not a general managed-step interception, nor a claim that every direct assignment was validated at assignment time. RND transport validates exact group keys/IDs/types, numeric settings, bool execution flags (foreach/fused can also be None), complete coherent moments and actual disposable execution. It permits qualified nondefault configuration; a blanket default-path claim for every RND restored/manual optimizer would be false. Reset additionally requires current/fresh exact optimizer groups equal. ICM transport requires exact groups equal destination reference and exact field types, then reconstructs paired actual Adam and validates S=U-O; it supplies no signed manual-delta feature.

No closure/hook registry/domain admission is serialized or authorized by the native lifetime/origin arithmetic. Do not ban manual step/replacement to simplify R0 proof. Enforced explicit custody for standalone/direct/manual operation must be supplied by the actual native/optimizer/domain producer design while preserving current actual Adam type/Parameter/transport constraints or coherently updating them under an approved current-generation design.

## CPU witness premise and remaining qualification

A bounded R0 witness can deliberately use genuine freshly constructed CPU RND (or adaptive inner RND) with these exact actual Adam construction arguments, establish nonempty Adam state through a real managed batch, then execute actual native no-argument managed step under the new custody design. The other worker's installed Torch evidence must establish the effective flags and `_single_tensor_adam` path under those actual conditions. No arbitrary optimizer subclass, mocked step, fake moments or closure should stand in for that witness. If it intentionally exercises manual/default or nondefault extension paths, identify their real public inputs and enrollment separately.

This capsule supplies construction/call-site premises, not runtime dispatch evidence. Outstanding qualifications include process-global hooks/extensions, supported user closures/manual replacements, exact registered custody entrypoints, actual private candidate factory/installed owner binding and next service, CUDA variants, shared parent/standalone enrollment and outer publication. N1 rng=None component tests do not discharge those. No production change or capability removal was made.
