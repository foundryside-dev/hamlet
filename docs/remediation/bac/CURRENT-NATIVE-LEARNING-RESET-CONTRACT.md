# N1 current native learning reset contract

The three model-native families can now prepare fresh learning while retaining their exact recorded service lifetime, ordered pending work, service clock and spent ordinary budget. Preparation does not install live state. The enclosing owner supplies an already-constructed genuine fresh same-family candidate, then consumes the returned destination-bound native handle through existing `install_state`. This is a bounded native component contract, not same-BANK/parent transfer publication or programme release.

Current native wire and exact R52 source/evidence are defined by the [native restore configuration contract](CURRENT-NATIVE-RESTORE-CONFIGURATION-CONTRACT.md). Native schemas are strict v4 with embedded Adam recipes; the R17 inventory and executions below remain historical reset evidence and are not relabeled as v4-qualified owner/N1 execution.

## Historical R17 source inventory

The following inventory binds the historical R17 reset candidate. Its production hashes/line counts are superseded by the current R52 inventory linked above; its factory/test bindings and runtime evidence remain historical. No extra implementation body or runtime was used for this documentation alignment. No optional factory reset dispatcher was added or required.

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py |910|30d3e9fba6ae6f90ffdda425c986bd6abecaf70e3728bdf104ca21ca832adc78|
| src/townlet/exploration/adaptive_intrinsic.py |335|1f448e07908d6b709b1e66ab5e163fa6dbc93a306b86d9eb8702d7968a47b47a|
| src/townlet/exploration/icm.py |541|f6cdecb466ac99b4dfe63ec00417495c3117e8947c5793e54c0dd71aa76d4964|
| src/townlet/exploration/provider_factory.py |153|7ca30733720017eea4a8063be0261dfd365c9547f501649bd71d937eecd5efb0|
| tests/test_townlet/regressions/bac/test_native_learning_reset.py |585|b02394963c5a33401a4018b5f4eff1b49d002dfd7cd2bb4df1c2535aa04930d5|

Total2524, within prospective1300/500/900/500/900=4100 and absolute five/5000. Root identifies final R17 candidate b0e3814b982eca65fa8ea3cb0dd7391a97009793 on base1938; these three production files, factory and frozen test are unchanged from R16. Canonical N1 production patch SHA2564b0e8839e62ba0a374772215d03fa86fc412099f20e4b51797a1025c942bf1c4.

## Actual public calls and handle contract

| Actual class | Preparation | Existing installation |
| --- | --- | --- |
| RNDExploration | `prepare_learning_reset(*, fresh: RNDExploration) -> _PreparedRND` | `install_state(prepared: _PreparedRND) -> None` |
| AdaptiveIntrinsicExploration | `prepare_learning_reset(*, fresh: AdaptiveIntrinsicExploration) -> _PreparedAdaptive` | `install_state(prepared: _PreparedAdaptive) -> None` |
| ICMExploration | `prepare_learning_reset(*, fresh: ICMExploration) -> _PreparedICM` | `install_state(prepared: _PreparedICM) -> None` |

Call the method on the actual destination. Treat the underscore handle as opaque; no new generic wrapper/transaction type or dispatcher exists. Handles are the same family-owned types used by current state preparation. Installation checks exact handle type, destination identity and unconsumed status, marks it consumed and replaces that destination's owned attribute dictionary. Wrong destination/type and reused handle raise ValueError. Preparation leaves destination and supplied fresh object uninstalled and returns owned candidate attributes; the resulting modules/optimizer/pending payload do not alias caller fresh learning or live old pending tensors.

These native handles do not check an intervening destination revision or authenticate a parent boundary. BANK/parent must own freshness, nonreentry, actual factory provenance and final coordinated installation. A caller-visible equal snapshot, epsilon, boolean or native handle is not boundary authority. No owner may infer same-BANK reset provenance from successful component preparation alone.

## Current state schemas and arithmetic

RND exact current checkpoint schema is `rnd-state-v4`, with top-level `adam_restore_recipe` and unchanged `predictor_service.version=3`. `optimizer_epoch_origin` is inside predictor_service, alongside lifetime counters/queue/clock/budget and signed optimizer_step_offset. Adaptive exact outer schema is `adaptive-intrinsic-state-v4` with the complete RNDv4 record and its sole nested recipe. ICM exact current schema is `icm-state-v4`, with top-level recipe and optimizer_epoch_origin, separate from its five-entry counters. Missing recipes and obsolete schemas refuse without compatibility decoding or fallback.

Use U for recorded lifetime service optimizer_updates, O for optimizer_epoch_origin, S for actual coherent Adam parameter step, and delta for RND's existing signed optimizer_step_offset. Constructor O is exact0. Complete prepare/load validates exact integer0<=O<=U, preserving the current dense Adam/group/Parameter/moment requirements.

- RND/adaptive validate **S=(U-O)+delta**, with exact signed integer delta and nonnegative S. Export derives delta from actual Adam history. Existing supported manual optimizer actions remain distinct from recorded service work; delta may be positive or negative. Actual ordinary/overflow service increments U and S together, preserving O and delta. A manual action never manufactures admissions, consumed rows or parent predictor minibatches.
- ICM validates **S=U-O** and adds no displacement capability. Adam state is empty iff epoch update count is0; otherwise complete actual Adam moments and parameter steps must match that count. Last loss must be0 without an epoch update.
- Fresh reset sets O to actual retained U and installs empty Adam. RND delta becomes0; ICM last_loss becomes0. Next actual service optimizer operation increments lifetime U once and fresh Adam S once. No fake Adam moments/steps are prepopulated.

Existing exact `checkpoint_state`, `validate_state`, `prepare_state`, `load_state` preserve the new fields and actual learning. Exact restore does not create a reset. Native conservation remains A=C+D+P and C=batch_size*U; ICM retains actual M<=U and ordinary-budget<=U-M checks. RND/adaptive do not invent cumulative M. All queue/counter/clock/budget validation uses retained lifetime work, independently of O/Adam epoch.

## Reset payload behavior

RND replaces fixed and predictor learned tensors, Adam learning, its corresponding fresh adam_restore_recipe and RMS using validated fresh candidate data. All resulting gradients are None; fixed target stays frozen. Fresh RMS is mean0,var1,count1e-4. It retains current diagnostic epsilon/min/decay, exact ordered pending observations, admitted/consumed/dropped/optimizer_updates, service options, batch size, service_clock_unit, service_position, ordinary_updates_at_position and step_counter. Current diagnostic epsilon remains separate from any runtime global selector.

Adaptive delegates exact inner RND reset, retains authored wrapper configuration/derived threshold, clears survival_history and restores current_intrinsic_weight to retained initial_intrinsic_weight. Historical completion/cache evidence is outside native; no old completion is reapplied here.

ICM replaces encoder/inverse/forward learning and Adam with the corresponding fresh adam_restore_recipe using validated fresh data. Gradients become None and last_loss0. It retains selected policy, receiver geometry/device, current diagnostic epsilon/min/decay, exact ordered predecessor/action/successor pending rows, all five lifetime counters including mandatory_service_updates, service unit/position and already-spent ordinary budget. ICM has no RMS to reset or synthesize. Portable source-device provenance is retained while actual candidate destination device must match.

Reset performs no admission, drop, training, queue flush, service call, clock advancement or budget refill. Equal shared native ticks retain spent budget. Private native clocks remain admitted-row clocks, not parent vector ticks. Source-Q geometry alone does not change these already-owned receiver-native dimensions. Repeated reset replaces one O; native does not store reset epoch/history chains.

## Required candidate qualification and refusals

Each method rejects self and wrong concrete fresh-family type. It validates complete current and fresh snapshots before returning a candidate. Selected configuration must match: RND dimensions/batch/device/service unit/options/diagnostic schedule and actual optimizer groups; adaptive retained wrapper config/device plus nested RND checks; ICM exact resolved policy and selected config/actual destination device/unit/schedule. Existing reset canonical Parameter pairing and group-compatibility refusals remain; `with_restore_configuration` does not bypass them or act as reset. RND target must be frozen and gradient-free.

Fresh must have zero service history/O/budget and initial service position, no pending obligations, empty Adam and no learned gradients. RND also requires delta0/step_counter0 and exact initial RMS; adaptive requires empty survival history/initial weight; ICM requires last_loss0. Learned/contaminated or configuration-mismatched candidate and malformed current source are refused with ValueError through these explicit checks/current native validation. No generic has-method fallback exists. Existing low-level state-validation malformed transport checks remain in force.

Constructor-like native state is not an authenticated factory provenance proof. The enclosing owner must supply genuine `make_backend(...)` construction, selected immutable policy/geometry and lawful candidate RNG custody. No none/count behavior is added by these three methods; their separate producer contract applies.

## RNG scope and evidence limits

The new reset methods do not construct networks, call a factory, draw random values, select seeds or activate RNG streams. They validate/copy existing learning, including existing RND disposable zero-gradient Adam validation and ICM optimizer reconstruction on copied modules. Model initialization draws happen during external genuine fresh construction before native preparation. Actual current-stream private cloning, retaining constructor draws in candidate continuation, shared parent exclusion/publication and failed joint-reset custody remain B1/actual-parent obligations.

Historical R17 tests used explicit rng=None with both native clock units. They proved that reset component's native clock/accounting and ambient no-draw profile, not private named-stream ownership or shared-parent custody. Current R52 native v4 reconstruction evidence is linked above; current owner/N1 fixture migration remains separate qualification. CUDA construction/execution, whole-parent atomic publication/restore, same ENV/BANK issuer identity, epochs/historical receipts, inherited baselines, runtime global epsilon/cadence and serving behavior are not qualified by those historical N1 runs.

Historical final R17 coherent139 PASS (native61, parent47, ENV31) in46.656654s, plus independent Astra execution of the same61 native cases PASS in15.788089s, remain bound to the historical inventory. These are139 unique cases, not200. Root reported zero errors/skips/warnings and full801 source/573 configuration/13 artifact/controller/index/import/thread/registry14 MAIN1 custody PASS. Historical owning Astra production SPEC/QUALITY and public API-truth reviews were approved. No tests were run by this documentation author.

At R17, global Ruff, Black, expression and no-defaults checks passed; no-defaults was600 after the separately owned parentfix3 and six oracle mypy errors remained. That historical owner233 suite stopped29PASS/1FAIL when its old ENV.from_universe fixture lacked required world inputs, before the actual native DemoRunner checkpoint assertion. This is not current v4 native-owner or ordinary runner qualification: current D/B1/F producers and their genuine fixture/ownership integration remain required. Current native/global evidence and limitations are recorded in the primary contract above.

Native component approval and these executions do not close BAC, same-BANK/parent transfer/reset publication, shared/private RNG custody, ordinary runner qualification or the remaining B1/F1/P1/O1/serving release gates.
