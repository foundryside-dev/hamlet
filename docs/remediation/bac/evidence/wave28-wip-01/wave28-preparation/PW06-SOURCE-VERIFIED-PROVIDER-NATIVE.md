# PW06 actual provider native facts — root source verification, not worker source expansion
Verified at committed41e5742307ad170bc9871e0b5354b00599084da6/tree5bf6ea6520d7897c0faf36f9e0f6524a5fd35e92. Static source inspection only; no new runtime qualification. Worker must not read these extra implementations. Existing PW05 source-verified capsules cover the other actual APIs.

## Epsilon/none: actual current load is unvalidated
EPS118, checkpoint_state returns exactly epsilon,epsilon_decay,epsilon_min, scalar values taken directly from live attributes. load_state109-118 sequentially indexes and assigns these three attributes, with NO schema/type/bounds/policy validation and NO transaction. A missing later key can partially change the receiver. There is no existing validate_state/prepare_state/install_state, no embedded policy identity, no recorded initial epsilon separate from current epsilon, no RNG/optimizer/counts/gradient state. Do not assume calling this loader constitutes strict validation. Off-side newly constructed actual provider loading is possible, but the complete parent candidate still needs finite exact policy-bound validation before any active swap. Current ResolvedExplorationPolicy768 validates finite nonbool epsilon_start/end/decay,0<=end<=start<=1 and0<decay<1. For a bank's policy-bound epsilon native payload, exact decay must equal policy.epsilon_decay, minimum equals policy.epsilon_end, and epsilon must lie in [policy.epsilon_end,policy.epsilon_start]. A public producer validator could be added in a separately bounded handoff if needed; don't implement it blindly in an unlisted file or pretend it exists.

## Count: complete atomic loader, but no fixed observation-width field
Count206, exact11fields: schema_version,policy_identity,policy,quantization_width,max_entries,epsilon,epsilon_decay,epsilon_min,counts,lru,eviction_count. checkpoint schema literal count-state-v1. load_state163-206 accepts Mapping with exact field set and schema, reconstructs actual ResolvedExplorationPolicy, requires strategycount_based and consistent saved/active policy identities. Quantization width finite nonbool int/float convertedfloat and capacity nonboolint>=1 must equal active constructor values AND policy.provider_parameters quantization_width/max_entries. Constructor already requires width>0. Native epsilon/decay/min finite nonbool numbers; decay equals restored policy.epsilon_decay, min equals epsilon_end, min<=epsilon<=epsilon_start. Evictions nonboolint>=0. counts must dict, lru must list, count cardinality<=capacity. Each count>=1 nonboolint. Every key must nonempty tuple of signed nonbool ints (arbitrary precision). LRU list must contain exactly every count key once (matching cardinality, no duplicates, identical sets). It creates OrderedDict in LRU order before assigning policy/epsilon/_counts/eviction_count. No active mutation before all validation and candidate dictionary allocation succeed. No standalone validate_state/prepare_state exists.
Actual loader DOES NOT check tuple length against a bank's observation_dim and provider stores no obs_dim. The reward method accepts any positive D on each call, computes exact rational floor bins, and uses these full tuples. In a bank whose descriptor fixes D, cross-width/injected count keys therefore need an explicit bank geometry check or a new producer seam; never claim existing Count.load_state checks D. This is a concrete bank-native qualification boundary, not permission to narrow standalone Count's supported variable-D API or duplicate its quantization algorithm. Native snapshots are independent count dict and LRU list; load builds another independent OrderedDict. Other Python overhead is not represented by tensor allocation estimates.

## RND/adaptive/ICM gradients versus native state
Current RND rnd-state-v2, ICM icm-state-v2, adaptive adaptive-intrinsic-state-v2 native payloads do NOT serialize Parameter.grad. They do serialize actual model state_dict tensors, Adam state and previously documented queues/counters/RMS/history/RNG wrapper data. RND _prepare_available_state653 copies actual fixed/predictor/optimizer together then loads state_dict; ICM _model_state329 deepcopies module and loads strict state_dict; adaptive prepares its nested actual RND through load_state. Installed local Torch2.11 Parameter.__deepcopy__74-82 returns a fresh Parameter from cloned .data and requires_grad, and does NOT copy .grad. Thus reconstruction/deepcopy/native restore must not be described as preserving existing nonempty gradients. Actual RND optimizer update510 calls zero_grad before backward; ICM202 calls zero_grad(set_to_none=True), so residual gradients are cleared before the next actual update. Next-update equivalence alone therefore does not prove full live-state equality. Ordinary PW05 completion deliberately preserves live gradient objects and storage and has qualified proof; it does not load native models.
Ruling for this current full-bank transport: explicitly preserve independently owned per-parameter optional gradient values for trainable families as part of the full bank checkpoint boundary, or surface a concrete different contract for review before implementation. No invented gradients for Count/none or frozen targets. A full-bank wrapper may add exact gradient transport/validation using actual public model parameters without changing the existing provider native schemas; don't claim those native schemas already carry gradients. Preserve model/optimizer pairing, finite dense exact shape/dtype/device checks and no aliases. Validation/allocation failures must preserve all current live gradients along with the other active state. This is a finite completion/restore ownership reconciliation, not a general cleanup programme.

## Origin/rebasing facts and scope
No clone-learned/reset-origin/rebase-service public API exists in these five actual providers. Existing native prepare/install is same-current-configuration restore. Private RND/adaptive service unit world_eligible_admission requires service_position==admitted_rows, step_counter0, valid conservation and bounded budgets; ICM likewise position==admitted_rows and valid counters/budgets, with Adam successful-step consistency. Do not rebase only one field or infer backend-owned current counters may be reset independently. Original PW07 owns explicit fresh_private and clone_learned_archive_pending semantics, including inherited labels, fresh future local counters and archived mixed pending; those are required later producer/consumer work. PW06 should preserve exact same-scope state and propose a concrete composable seam rather than inventing a presently nonexistent conversion method. No original PW07 guarantee is waived.

## Identities
{
  "src/townlet/exploration/epsilon_greedy.py": {
    "lines": 118,
    "sha256": "f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059"
  },
  "src/townlet/exploration/count_based.py": {
    "lines": 206,
    "sha256": "163cb33f06799a75c887ff7beb58e4897875c94a4780ab722d019f714b33e9c1"
  },
  "src/townlet/exploration/rnd.py": {
    "lines": 834,
    "sha256": "0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d"
  },
  "src/townlet/exploration/icm.py": {
    "lines": 481,
    "sha256": "eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f"
  },
  "src/townlet/exploration/adaptive_intrinsic.py": {
    "lines": 315,
    "sha256": "cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4"
  },
  "src/townlet/config/exploration_policy.py": {
    "lines": 768,
    "sha256": "af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c"
  },
  ".venv/lib/python3.13/site-packages/torch/nn/parameter.py": {
    "lines": 308,
    "sha256": "1327b7a24eafccd098c1b22aabb8a83383bd730802edd018744e9247e5941381"
  }
}

## R2 copier refusal source facts (root static verification after actual68 failures)
All68 actualR2failures stop at CP.owned109 because it only accepts exactdict/list/tuple and exactPythonprimitive types. Current RND.available_state calls actual fixed_network.state_dict() and predictor_network.state_dict() then deepcopies; current Torch state_dict default result is collections.OrderedDict, retaining its module metadata. RND available_state does not normalize those mappings to exactdict. Adaptive embeds this same RND state. This is CURRENT producer data, not historical compatibility. A bounded codec must handle actual producer mapping semantics/ordering/ownership and real scalar types without bypassing native validation.
Another concrete scalar boundary from actual RND75-105: RunningMeanStd.update computes numpy.mean/numpy.var; update_from_moments assigns the resulting numpy floating arithmetic values directly to mean/var. Public native snapshot retains those values. Actual RND native validation explicitly accepts numpy.floating alongside Python int/float; do not assume exactPythonfloat-only tree. Preserve real native value/type/precision semantics through the copier/load and existing independent live witnesses. Do not change learning/provider algorithms to sidestep serialization. No new source read authorized to implementer. These are static producer facts, not a claim that the original trace identified the deepest rejected value (the first unsupported mapping hides later leaves).
