# Initial-mask temporal gate — bounded VTC owner facts

Read-only followup, 2026-11-11, root-supplied HEAD d4426803. Only this ignored prose was written. No implementation/test change, runtime/import/probe/compile/lint/git/index/branch/worktree/checkout/source-copy/new-agent action. No ENV/action-mask-builder or external expression implementation body was read. The supplied initial mask owner capsule SHA256 verifies as 5559dec45a7864e49aae9aa9a39ed24457cfcf95fe63759d069d5504fd187ea4.

## Current retained whole-source inventory

Metadata was repeated before this followup's source inspection; all identities remain unchanged from the approved primitive.

| Complete source | Lines | SHA256 |
|---|---:|---|
| src/townlet/vfs/vtc.py | 3510 | a2d14e8bf9d7363e36f5778182395a4e5110052ca5591efacb1c98d63dad4390 |
| src/townlet/environment/dac_engine.py | 977 | b129d7ac5cdbf7e6ed27dd6cd5f9529dc9e7d2e0154b43a4db028d7aef78e317 |
| tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py | 195 | 0ad34fdfb781a5679762a2eacfa4ff2d86a026967e5039fe514e81a2fce0e745 |
| Total | 4682 | exactly three bodies; <=5/5000 and existing ceilings4900 |

Only the already-owned VTC body was consulted for the named gate graph. Existing composer tests/receipts do not test or qualify this temporal gate.

## Public method and exact local call graph

Actual class is frozen dataclass VTCAffordanceGateProgram with rules: tuple[CompiledVTCAffordanceGate, ...]. Its actual public bound signature is:

```python
is_affordance_open(
    self,
    affordance_name: str,
    *,
    time_of_day: int | float | torch.Tensor,
    device: torch.device,
) -> bool
```

At vtc.py:1501 it calls self.compute(time_of_day=time_of_day, device=device), evaluating **all** compiled gate rules, not just the requested name. It then looks up affordance_name in that local result dict, raises a named KeyError if absent, checks numel()==1, and returns bool(value.item()). Public output is a Python bool, not a tensor on any device and not a per-agent vector. The separate ENV wrapper's population broadcasting is capsule-attributed, outside this inspected graph. An invalid unrelated compiled rule can fail the call before requested-name lookup.

compute at line1512:

1. Calls local _time_tensor. Tensor input must have numel()==1; otherwise ValueError. It uses .to(device=device, dtype=torch.float32).reshape(()). For Python int/float it constructs torch.tensor(float(time_of_day), device=device, dtype=torch.float32). Result is a scalar float32 temporal tensor. The tensor-input route can retain aliased storage when .to does not copy; VTC does not write it or promise an owned input snapshot.
2. Constructs a fresh ExecutionContext with bars={}, vfs={}, temporal={'time_of_day': time_tensor}, device=device, then a fresh Evaluator(context). These are external classes imported from townlet.world.expression.context and townlet.world.expression.evaluator.
3. For every compiled rule, local _evaluate_tensor calls evaluator.evaluate(rule.expression_ast). A non-Tensor result raises TypeError. The result is converted to device=device/dtype=torch.bool, must contain exactly one element or raises ValueError, and is reshaped to scalar shape().
4. Stores the scalar under target_affordance_id in a fresh local values dict and returns that dict. Duplicate targets overwrite the prior local dict entry. No program cache is retained.

Thus successful internal compute outputs are scalar bool tensors on the requested device; successful is_affordance_open output is a scalar Python bool. Non-scalar one-element temporal tensor input is accepted and reshaped, not broadcast across worlds. No explicit finite/hour-range check occurs here. CUDA .item() can synchronize/fail; device allocation/conversion/evaluation are fallible work.

## Actual supported compiler-produced expression boundary

compile_vtc_affordance_gates delegates to compile_vtc_affordance_gates_with_phase_graph. Construction creates a parser, local compiled-rule list and frozen rule records, sorts into a tuple with the phase graph, then constructs the program. These construction/parsing/sorting operations are distinct from calling an already compiled program; runtime gate calls do not call the parser, phase graph or compiler.

For the supported opening-hours compiler, _coerce_affordance_gate reads actual name/opening_hours. Disabled opening hours become [(0.0,24.0)]. Enabled hours require a nonempty schedule; starts/ends are converted to float. _opening_hours_expression generates only:

```
time_in_window(temporal.time_of_day, <literal start>, <literal end>)
```

joined by logical OR for multiple windows. There is no authored arbitrary expression parameter in this compiler path. Actual runtime dependencies for these compiler-produced rules are therefore temporal path lookup, literal values, the registered time_in_window function and logical OR through the expression evaluator. VTC imports FUNCTION_SPECS from townlet.world.expression.functions, but this gate's runtime delegates evaluation rather than directly calling that table. Manually fabricated/replaced ASTs or injected evaluators are not qualified supported compiler output.

## Verdict and finite external question

**Locally established:** at fixed compiled program/hour/device, this VTC graph has no direct random draw, VFS engine evaluation/tick/reset, history access, simulator action, self/rule assignment or lazy/persistent cache write. Its stores are fresh local context/result construction and local dict insertion. It does invoke the expression Evaluator; saying it does no evaluation at all would be false. The VFS mapping supplied to that expression context is empty, rather than the live VFS registry. No live registry/history/RNG object is passed explicitly by this VTC method.

**Whole delegated graph remains conditional:** the external ExecutionContext/Evaluator constructors, temporal path/literal/OR evaluation and registered time_in_window implementation were not opened in this bounded context. Their constructor/evaluation behavior cannot be certified merely from an empty vfs dict or a frozen outer program. Therefore this report establishes the VTC caller's nonmutating/RNG-free structure and constrained compiler-produced expression dependency, but does not independently certify complete deterministic/nonmutating/RNG-free execution through those unopened helpers.

Exact finite external owner question: for the actual builtin ExecutionContext/Evaluator and compiler-produced time_in_window(temporal.time_of_day,literal,literal) expressions joined by OR, do constructor/evaluate and the selected time_in_window implementation only read supplied temporal/literal values and produce outputs, without modifying input temporal tensor/AST, live state/global cache/history/VFS, or drawing RNG? Supply the actual builtin handler/dispatch source-backed fact; no arbitrary-expression/general purity audit is requested. Its precise window endpoint/wrap semantics also belong to that handler, not an inference from the function name. Once that narrow external fact is supplied, the local graph here supplies the remaining VTC evidence for deterministic read-only results at unchanged compiled program/hour/device under supported builtin execution.

The new C producer's supplied plan performs every fallible real mask/gate calculation before publication, then owns/clones the derived mask and clears retired rows without a second callback invocation. This report is compatible with that order: scalar device conversion/evaluation/.item(), missing-name checks and local allocations all belong before publication. It does not qualify the other mask dependencies, introduce a second gate invocation, authorize source changes, or close C/ENV/provider/replay/native/fullgate/global acceptance.
