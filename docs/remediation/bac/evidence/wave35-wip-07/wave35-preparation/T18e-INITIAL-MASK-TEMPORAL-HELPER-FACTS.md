# Initial-mask temporal helper — bounded builtin facts

Read-only source analysis, 2026-11-11; root-supplied repository HEAD d4426803 (not checked with git). Only this ignored preparation prose was written. No source/test edits, application execution/import/probe, tests, lint, compile, git/index/branch/worktree/checkout/source-copy, or new agents. Python was used only for file metadata and writing this report.

## Attributed caller boundary and inventory

The supplied `T18e-INITIAL-MASK-TEMPORAL-GATE-FACTS.md` was metadata-checked before reading: 63 lines, 7818 bytes, SHA256 `8e566febb7af7306d1ce81138aafbcfdc02935a442d727029da04f03255a5cfa`. Its VTC/compiler statements are caller-owner attribution, not independent source inspection here. No VTC, ENV, parser, tests, or general expression implementation beyond the named helpers was opened. Repository AGENTS.md was read.

Metadata for exactly the initial three source bodies was obtained before their contents; `ast_nodes.py` was added only after its own metadata, to close the actual `node.accept` dispatch. The whole-source budget charges entire files even where named slices alone were inspected.

| Source body | Lines | Bytes | SHA256 |
|---|---:|---:|---|
| src/townlet/world/expression/context.py | 71 | 3319 | ffd4993fe75dbb871edc07dfa2a894a5f43508ff1c80fa60ec767c6f60f4839b |
| src/townlet/world/expression/evaluator.py | 145 | 5553 | cc3862dc21c85cd912b96205eb8eeadaad6a39416c06c292b755b24ae14969bf |
| src/townlet/world/expression/functions.py | 1720 | 65083 | ba38ff02343c011b1b08d8cfd3a988de88fec83c3712a4a578bcf60169286540 |
| src/townlet/world/expression/ast_nodes.py | 333 | 8911 | 492f5eec3a84740d700d7d636b9c492962d3a89468e983b7a2ba94317a579408 |
| Total | 2269 | 82866 | four bodies; initial three total 1936; within hard <=5 bodies / 5000 lines |

`references.py` was unnecessary: the named temporal lookup returns before `parse_reference`. No fifth/sixth helper body or general expression audit is needed for this graph. `functions.py` inspection was limited to its named dispatch/record/registry construction and `time_in_window` implementation, not a claim about other handlers.

## Actual constructor and dispatch facts

Caller-attributed input is a fresh `ExecutionContext(bars={}, vfs={}, temporal={"time_of_day": time_tensor}, device=device)` and fresh `Evaluator(context)` per compute. Caller-attributed `time_tensor` is scalar float32 on requested device; tensor conversion may alias caller storage. The supported graph here consists only of builtin `FunctionCall("time_in_window", [PathAccess(["temporal", "time_of_day"]), numeric Constant(start), numeric Constant(end)])`, optionally combined by builtin `BinaryOp(..., OperatorType.OR, ...)`. The caller capsule supplies its compiler provenance; this report does not inspect or expand the parser.

* `ExecutionContext` is a dataclass (`context.py:17`) with no custom initializer, post-init hook, or factory. Initialization assigns supplied fields to this fresh context. The other fields default to `None` (including history, rng, draws, positions and item state); `device` has an ordinary builtin torch.device default. It neither copies nor modifies the supplied tensors/dictionaries and allocates no history/random stream.
* `ExecutionContext.get(self, path: str) -> torch.Tensor` (`context.py:53`) splits the path; for exactly two segments headed `temporal`, where the second key exists, it returns `self.temporal[segments[1]]` immediately. For `temporal.time_of_day` the supplied scalar tensor is returned by reference. There is no call to `parse_reference`, VFS, history, or RNG on this branch.
* `Evaluator.__init__(self, context: ExecutionContext)` (`evaluator.py:23`) only sets `self.context` on the fresh evaluator. `evaluate(self, node) -> torch.Tensor` (`:26`) returns `node.accept(self)` without caching or annotation.
* Builtin `Constant.accept`, `PathAccess.accept`, `BinaryOp.accept`, and `FunctionCall.accept` (`ast_nodes.py:132,169,189,228`) directly call the corresponding visitor method. Their dataclass records are frozen. Their contained lists are not deeply frozen, but this dispatch and the visited methods do not write them.
* `visit_constant(self, node: Constant) -> torch.Tensor` (`evaluator.py:30`) calls `torch.tensor(node.value, device=self.context.device)` for the numeric literals in this graph. `visit_path_access` (`:40`) joins segments and calls the context getter; it does not edit the list or returned tensor.
* `visit_function_call(self, node: FunctionCall) -> torch.Tensor` (`:100`) evaluates every argument into a fresh local list, reads `FUNCTION_SPECS.get(node.function_name)`, raises if absent, then returns `spec.eval_fn(args, self.context, node.arguments)`. It performs no per-call registry write or validation callback. Although the AST argument list and context are passed to the handler, this particular handler does not use or mutate them.
* `visit_binary_op(self, node: BinaryOp) -> torch.Tensor` (`:45`) evaluates both children before dispatch. For `OperatorType.OR` it returns `left | right` (`:80`), a new boolean operation result; it does not short-circuit. All windows can therefore perform fallible allocations/evaluation even after an earlier true window.

## Actual registered handler and window semantics

`FunctionSpec` is a frozen dataclass (`functions.py:85`), with `eval_fn: Callable[[list[Any], ExecutionContext, list[ASTNode]], torch.Tensor | Any]`. The module-level `FUNCTION_SPECS` dictionary is mutable; `_register` (`:818`) inserts specifications during module initialization. `_numeric_spec` (`:828`) returns a fixed-arity spec with `requires=()`, pointwise shape, and its supplied evaluator. The actual registration (`:1332`) gives `time_in_window(time, start, end)`, numeric arity 3, return type bool, and `eval_fn=_eval_time_in_window`. Evaluation reads this already-initialized builtin spec; it does not invoke its validation or return-type lambdas. The supplied caller capsule says VTC itself imports `FUNCTION_SPECS`, so normal gate execution already has that module initialized. This report does not call module import/registry construction free of global writes: initial registration is a separate construction phase.

Actual signature (`functions.py:676`):

```python
_eval_time_in_window(args: list[Any], context: ExecutionContext,
                     arg_nodes: list[ASTNode]) -> torch.Tensor
```

The function reads `args[0]`, creates a scalar `24.0` tensor on its device and dtype, and computes `hour = remainder(time_value, 24)`. It converts literal endpoints to that same device/dtype, then takes each modulo 24. With `start_raw`, `end_raw` denoting converted endpoints, its exact boolean formula is:

```text
always_open = remainder(end_raw - start_raw, 24) == 0
start = remainder(start_raw, 24); end = remainder(end_raw, 24)
if always_open: true
elif start < end: (hour >= start) & (hour < end)
else: (hour >= start) | (hour < end)
```

The implementation selects with nested `torch.where`; the formula describes its values, not Python short-circuit execution. Thus ordinary finite non-wrapping windows include the start and exclude the end; wrapping windows include the late-day segment and the early-day segment with the same endpoint convention. Equal endpoints modulo 24, including 0-to-0 and 0-to-24, are **always open**, rather than empty. Hours/endpoints outside the day are normalized by remainder; no range/finiteness rejection is present in this handler. Floating-point values are those actually converted to the input dtype, not exact real-number arithmetic. For nonfinite inputs the stated tensor formula applies; no stronger conventional interval claim is made.

Every tensor operation on this path is an ordinary non-in-place tensor constructor, `.to`, remainder, subtraction, comparison, `&`, `|`, `ones_like`, or `where`. There is no assignment into the temporal tensor, endpoint tensors, AST, context maps, registry, cache, history, or live VFS; no generator/draw stream, random sampler, or history method is called. `.to` may alias an already matching tensor, but subsequent operations do not mutate it. Intermediate allocations remain fallible.

## Bounded verdict and constraints

**The named builtin helper graph is read-only on supplied temporal/AST/live state and RNG-free, and returns deterministic boolean tensor values for unchanged supported compiled graph/hour/device under unchanged builtin registry and torch execution configuration.** Together with the attributed VTC facts, this closes the identified delegated helper question for normal already-compiled opening-hour gates: scalar float32 temporal input yields a scalar bool tensor here, then the caller performs its stated conversion/check and public Python-bool extraction. It does not require opening another repository helper.

Precision of that verdict matters. Numeric literal construction omits an explicit dtype (`evaluator.py:34`), so its float dtype follows torch's global default before the handler converts to the temporal dtype. Changing that default (for example lowering its precision) can change endpoint values despite unchanged program/hour/device. This is a read of ordinary framework configuration, not a cache mutation or random draw. Repeatability therefore assumes that configuration is unchanged; this source does not prove a function solely of those three inputs across arbitrary default-dtype changes. It also assumes no concurrent mutation of input storage, AST-contained lists, or the mutable global registry, and ordinary unmodified builtin Python/torch classes and operations. Arbitrarily replaced AST nodes, registry callbacks/evaluators, tensor subclasses/overrides, or injected stateful implementations are outside the compiler-produced builtin graph.

No runtime verification was performed or claimed. No essential unopened repository-helper gap remains for the stipulated graph; framework implementation internals were not audited. This finite helper fact does not certify arbitrary expressions, ENV/provider/replay/native/fullgate/global acceptance, or any other initial-mask dependency. Fallible gate computation/allocation and scalar extraction still belong before the producer publication boundary as stated by the caller capsule; no second callback invocation is introduced or recommended.
