# Current CP gradient adapter public facts

2026-11-11. Narrow public prose from the SAME four already-owned source bodies; no new body, Torch implementation, active core, fixture, import/runtime/probe/Git/index/code exposure or write. Only this capsule and the necessary readiness qualification were written. Current CP1138 SHA2564de4c481eca21fb3d7fa9aea8804c2b2875c63df6077046e7e286470b6faeb5a; BANK1284 SHA256294ef0f8d9f11e74869567e21f2ca44b623fe1cd54ca5c3eb59819c80681a05f. Identity1611 SHA25641b3ae394a7378762b92e87bead77ced9389881e2f2ef28d45252027b24f1268 and clock48 SHA256e7b40260b027bc63fd2cb751a4fb55840564c36a38d78fca30f876d9e41473e0 remain READONLY. All four match prior/final seals, total4081 lines.

## Exact existing signatures and outputs

These are actual module-level names in townlet.exploration.curiosity_checkpoint; their arguments are positional-or-keyword, with no defaults:

| CP location | Exact signature | Actual result |
|---|---|---|
|979|gradient_modules(provider: Any, family: str) -> dict[str, Any]|New insertion-ordered label-to-real-native-module dict; modules/Parameters are actual provider references, not copied inventory.|
|991|check_pairing(provider: Any, family: str, modules: dict[str, Any]) -> None|None after actual identity checks; returns immediately for empty modules.|
|1005|capture_gradients(provider: Any, family: str) -> dict[str, Any]|New nested ordinary dict: module label -> named parameter name -> None or independently owned detached tensor clone.|
|1022|attach_gradients(provider: Any, values: Any, family: str) -> None|None after attaching to actual provider Parameters; exact values keysets/profile/pairing validated first.|

There is NO current CP public function that returns a flat Parameter inventory, native optimizer or a typed Parameter/gradient bundle. gradient_modules exposes real modules; capture_gradients exposes data by name, not Parameter authority.

## All five selected families

| Family | Insertion-ordered label/module entries | Optimizer used by check_pairing | Additional rule |
|---|---|---|---|
|none|empty dict|none accessed|capture returns {}; attach requires exact empty dict.|
|count_based|empty dict|none accessed|capture returns {}; attach requires exact empty dict.|
|rnd|predictor_network -> provider.predictor_network|provider.optimizer|Every actual provider.fixed_network Parameter.grad must be None.|
|adaptive_rnd|rnd.predictor_network -> provider.rnd.predictor_network|provider.rnd.optimizer|Every actual provider.rnd.fixed_network Parameter.grad must be None.|
|icm|encoder -> provider.encoder; inverse_model -> provider.inverse_model; forward_model -> provider.forward_model|provider.optimizer|All three actual modules participate; no fixed-target rule in this branch.|

The fixed-target check occurs whenever gradient_modules is called, including both capture and attach. A zero fixed-target gradient is unlawful just like a nonzero gradient: exact None is required. gradient_modules itself is not a full policy/family validator; its final branch returns {} for other strings too. Selected-family validity comes from the existing resolved policy/native path, not a newly inferred restriction here.

## Actual parameter order and pairing

check_pairing traverses modules.values() in the dict's insertion order, then each real module.parameters() in that API's returned order. It requires all collected Parameter object IDs unique. It flattens every actual optimizer.param_groups entry's params and requires equal cardinality and equal SET of IDs. Thus group duplicates/missing/foreign Parameters refuse; group ordering is NOT required to match the module traversal order. Actual optimizer.state keys' IDs must be a subset of those module Parameter IDs; lazily absent state is allowed. It does not require every Parameter already have Adam state or derive gradient identity from counters. It does not select or replace an optimizer.

capture_gradients and attach_gradients separately traverse modules.items() in insertion order, materialize dict(module.named_parameters()), then traverse that dict's names/Parameters in returned order. Capture preserves that name insertion order. Attach requires exact ordinary-dict keysets for labels and each module's names, but CP.keys compares sets and does not require the supplied dict's insertion order to match. Assignments follow actual module/named-parameter order, not supplied values order. No independently inspected Torch guarantee about those APIs' ordering, duplicate-removal or deepcopy behavior is claimed.

## Gradient values, aliases and publication timing

Each non-None live/saved gradient must be a torch.Tensor with torch.strided layout, EXACT Parameter shape, EXACT Parameter dtype and EXACT Parameter device, and all finite values. The validation uses the actual CP tensor profile validator; no implicit dtype/device conversion or sparse conversion occurs. None, explicit zeros and finite nonzero values remain distinct and supported. No gradient sign/magnitude inference or required nonzero rule is added.

Capture detaches and clones each non-None gradient independently; a caller mutation of returned tensor data cannot edit the source gradient. The returned nested dict is newly owned. It does not preserve a shared-storage relationship among separate transported gradient entries. Modules/Parameters themselves are not returned by capture.

Attach first obtains actual modules and validates actual pairing/fixed-target None, then checks exact nested ordinary-dict keys. For each saved non-None value it validates the final actual Parameter profile and makes an independent detached clone. It prepares ALL Parameter/gradient pairs before assigning any Parameter.grad. Only after all validation/cloning succeeds does it assign None or the clone to each actual Parameter.grad. It returns None. Consequently an expected profile/key/pairing/clone refusal before that assignment loop does not partly attach earlier entries. The assignment loop itself has no rollback or arbitrary-exception guarantee. Input tensors/dicts are not installed as aliases; Parameter objects remain actual existing ones. No optimizer step, native counter update, factory or native load is performed by these four functions.

Actual BANK current private paths do owner.prepare_restore -> owner.install on an OFFSIDE replacement owner -> owner.call(attach_gradients). Shared current path does raw native validation -> load_state -> exact checkpoint roundtrip -> attach_gradients, still offside. Attachment therefore occurs AFTER the final native load and against the final loaded Parameters. Original BANK publication is later one preallocated dictionary replacement. Any new core callback has to preserve that timing and the None/zero/nonzero result through the FINAL core ownership copy, not just the callback's temporary candidate.

## Exact implication for a generic core adapter

A family-aware CP adapter CAN produce an exact ordered inventory of actual native candidate Parameters using its returned modules and their actual parameter APIs, after applying the current fixed-target/pairing validation. A generic core can consume a typed callback-supplied inventory without inspecting rnd/adaptive/icm internals. This is a possible additive adapter contract, NOT an existing CP inventory-return API and NOT a selected new core API. Label/name identity and final-candidate binding need explicit contract if copies are involved; native data shape or optimizer counters alone are not binding authority.

Root supplies the active core fact that current validate_backend is pre-load/pure, and that a post-final-load callback before opaque sealing is under consideration. Those are received facts; active core was not read here. Existing CP.validate_native can remain the pre-load semantic validator, but existing CP.attach_gradients cannot run before final load and be assumed to survive it. A callback inventory naming Parameters of candidate C does not by itself name Parameters of a later deepcopy D. Root further identifies a possible deepcopy omission of Parameter.grad; no independent Torch claim is made here. A core ownership copy after attachment must preserve/reattach explicit gradients on the final actual candidate and revalidate pairing/fixed-target state under the qualified adapter contract, or run the adapter at the final isolated-candidate cut. Calling CP.capture_gradients on C alone cannot prove D retains gradients. Opaque PreparedWorldBackend need not expose candidate/backend/rng fields for any of this.

The bounded sequential offside install + managed gradient attachment strategy remains sufficient for GRADIENT timing if all replacement owners exist legitimately, all final native loads have finished before attachment, all ordinary attachment work precedes issuing the final BANK currency token, and no later core copy loses gradients. That statement does not qualify constructor/bootstrap purity or final domain membership/currentness.

## Concrete bootstrap question, not resolved by an inventory

Actual SharedWorldBackend.construct, per the core owner's supplied public fact, consumes/retains real GLOBAL factory continuation and registers while domain is idle. Therefore preconstructing an extra shared replacement during BANK.prepare_restore can change ambient state even if BANK never publishes. A clone factory/native constructor cannot be assumed RNG-free. The earlier readiness two-stage replacement recipe is CONDITIONAL and must not be used to claim pure ordinary shared preparation.

Exact producer question: which qualified public route prepares an independently owned shared replacement/native candidate under current ambient preservation WITHOUT registering a new lifecycle owner inside a held lease and WITHOUT advancing global ambient continuation on ordinary preparation success/refusal? A legitimate pre-registered disposable participant, existing shared owner's held candidate seam, or another explicitly qualified producer seam could answer this; none is inferred or selected here. The same registration/custody question applies to CP archived native validation. If no such route exists, sequential replacement construction is not sufficient despite correct gradient timing. Keep this as a concrete adoption dependency while R0 verified bugfixes retain priority.
