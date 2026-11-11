# Current native restore configuration contract

2026-11-11. Fixed R52 producer contract for RND, adaptive RND and ICM. This documents native component behavior and its qualified CPU evidence; consumer adoption and parent publication remain separate work.

## Current checkpoint wire

- RND uses `rnd-state-v4` with top-level `adam_restore_recipe`.
- Adaptive uses `adaptive-intrinsic-state-v4`; its sole recipe is inside `rnd_state`, whose schema is `rnd-state-v4`.
- ICM uses `icm-state-v4` with top-level `adam_restore_recipe`.
- Missing recipes and obsolete schemas refuse. There is no compatibility decoder, migration or inferred-association fallback. RND `predictor_service.version` remains exactly3.

Public inert TypedDicts `AdamRestoreRecipe` and `AdamRestoreGroup` are defined in `townlet.exploration.rnd`; ICM shares their validation/construction helpers. Recipe keys are exactly `version`, `algorithm`, `groups`: exact int1, exact string `torch.optim.Adam`, and a nonempty list of group records. Each group has exactly `parameter_names` and `options`: an ordered list of exact strings and an owned dictionary of actual Adam group fields excluding `params`.

RND names are `predictor_network.<named_parameters name>`. Adaptive preserves that nested namespace. ICM names are `encoder.<name>`, `inverse_model.<name>` and `forward_model.<name>`. Association comes from actual model/optimizer Parameter identity at capture, never tensor shape/value, integer arithmetic, checkpoint enumeration or gradient order. Model names/Parameters and ordered integer IDs require complete unique coverage; aliases, foreign/missing/duplicate Parameters and nonconcrete Adam refuse. RND excludes its frozen, gradient-free fixed target.

Recipe group order, per-group names/length and options agree with the corresponding actual optimizer payload. The payload remains authoritative for moments and ordered integer IDs. Recipe and payload own their exported tensors/containers independently. No optimizer defaults, Parameter handle, callable, module, optimizer, controller or RNG owner is portable recipe data.

Option correspondence checks exact keys and concrete scalar/container types and values. Accepted numeric forms and finite dense floating scalar Tensor settings remain supported under family validation. Tensor comparison checks type/shape/dtype and exact values under concrete CPU/CUDA mapping, without ambiguous Tensor truth. RND destination validation retains its disposable Adam execution probe. Actual extra group fields accepted by RND remain bool, with `foreach`/`fused` additionally permitting None; numeric scheduler `initial_lr` is unsupported. Reconstruction retains these actual bool fields in group dictionaries rather than treating them as constructor keywords.

RND/adaptive preserve individual empty groups, including their position/options, with nonempty groups overall and full total Parameter coverage. ICM requires exactly one fully covering group. ICM validates raw recipe/paired optimizer types before CPU ownership normalization, so Parameter-valued options and malformed record/container types cannot become acceptable through normalization. Legitimate model `OrderedDict` inputs remain accepted.

## Explicit reconstruction and installation

Each native exposes `with_restore_configuration(self, state: dict[str, Any])` returning its same concrete family. The receiver must already be a genuine offside selected-factory candidate with actual selected policy, geometry, dtype, device and clock. Receiver provenance and source exclusion are caller obligations.

The method owns input, copies receiver model/wrapper data, resolves ordered saved names to the copied actual Parameters, and constructs genuine Adam with checked group configuration. It invokes substantive native validation of the saved record before returning. It constructs no model, activates no RNG and installs no transported learned state or gradients on the returned candidate. Returned Adam history is empty; all returned model Parameter gradients are None and RND targets remain frozen. Source/receiver values, identities, queues, metadata, history and existing mixed gradients remain unchanged on success/refusal.

The returned candidate is configured for restoration, not an installed continuation. Required consumer sequence:

1. Construct through actual `make_backend` with selected policy/geometry/device and actual candidate RNG/scope binding.
2. Call `with_restore_configuration(saved_native)` on that offside receiver.
3. Call `validate_state(saved_native)`, then `load_state(saved_native)` on the returned candidate.
4. Require exact native checkpoint roundtrip; perform the final ownership copy/install.
5. Attach separately captured/validated gradients by name to the final actual Parameters. No copy/load follows gradient attachment.

Existing `checkpoint_state`, `validate_state`, `prepare_state`, `load_state` and `install_state` remain substantive. Ordinary validation/loading requires the candidate's actual named association to match the saved recipe; ICM also requires exact current group option types/values. RND retains its existing permitted group-value flexibility. A differently paired fresh factory uses explicit configuration first. ICM reconstructs copied optimizer membership in recipe order, including supported same-shaped reordering, while model tensors load by name.

Capture is observational under caller-held source exclusion: no optimizer step, model construction, service, RNG activation, counter repair or gradient mutation. Native preparation handles authenticate destination identity/consumption only. They do not certify managed-owner freshness, health, currentness or publication authority.

## Learning clocks, copying and reset

Let U be retained native successful service optimizer updates, O the optimizer epoch origin and S the common dense Adam step. RND/adaptive retain complete-or-empty dense history and signed `optimizer_step_offset = S - (U - O)`. Genuine dense manual steps can create positive displacement; genuine replacement after recorded service can create negative displacement. Retained origins, FIFO order, service budget/position, normalization and adaptive history remain part of exact native state.

ICM retains its narrower `S = U - O` history contract: history is empty iff epoch updates are zero, with last_loss0 for a zero-update epoch. A displaced extra manual step, invalid empty history, multigroup history or learned amsgrad history refuses. Supported single-group mutable LR/configuration and same-Parameter replacement with genuinely valid history remain usable. Mutable optimizer LR does not overwrite selected immutable policy/config `learning_rate`; ordinary scalar Tensor LR is qualified.

Ordinary independently owned native copies, supported direct/manual routes and genuine optimizer replacement remain capabilities subject to those existing family checks and caller exclusion. Copying does not promise gradient preservation; gradients have their separate final attachment rule. Neither replacement nor reconstruction fabricates moments, counters or service events.

Native learning reset carries the fresh recipe together with fresh optimizer state, retaining service lifetime and the authored origin/reset semantics. Existing actual canonical pairing, configuration compatibility, fresh-learning checks and group mismatch refusals remain. Restore reconstruction does not bypass reset refusals or act as a reset.

## Device and integration boundary

RND retains exported Tensor-option placement. ICM retains its CPU-canonical archive, including its recipe, and separately preserves source-device provenance while receiving model/history tensors on the selected destination. Permitted concrete CPU/CUDA comparison copies do not grant a new device capability. CPU paths introduce no CUDA availability query; actual CUDA hardware remains unrun/unqualified. Caller-declared device completion, allocation reporting, quiescence and actual RNG custody remain required.

The embedded inert recipe enables payload-only native/archive reconstruction using selected construction, without a live source owner. This producer capability does not prove current CP/archive/origin transformation or actual BANK adoption. SOURCE-policy reconstruction before TARGET transformation, protected-source recovery eligibility, quarantine handling, managed-owner currency, common-domain ordering, final gradient adoption and full-parent publication still require their consumer/core qualifications. Native private RNG/clock tests do not establish accepted episode or ENV/full-parent behavior. No whole-programme closure follows from this component contract.

## Fixed producer and qualification evidence

The exact five-body packet is3427 lines:

| Path | Lines | SHA256 |
|---|---:|---|
| `src/townlet/exploration/rnd.py` |1128|`53cccad55acad4018518bd498206129feddc5f54113560103cab60c94659ac46`|
| `src/townlet/exploration/adaptive_intrinsic.py` |352|`150a31a838ab7cba566cba388d1aeef0ad9f2c2244c26e7ca99499263731faf8`|
| `src/townlet/exploration/icm.py` |582|`413a31b55349864cf9f25dd7ed5f22e3fac87cd28c6707efd6697e7196286e40`|
| `src/townlet/exploration/provider_factory.py` |153|`dc69a831e045bed5c71b5bd448b1e9ff0163e6bce9d816b41d10af0f580708c8`|
| `tests/test_townlet/regressions/bac/test_native_restore_configuration.py` |1212|`08fe4698c0342500d0b53a738b2b340c5f9c164a0d4c54b891affe29fd580924`|

Published evidence target: [WIP12 receipt](evidence/wave35-wip-12.json) and [independent review](evidence/wave35-wip-12/wave35-preparation/T18e-NATIVE-RESTORE-CONFIGURATION-INDEPENDENT-REVIEW.md),143 lines, SHA256`96fa2bef1fabc4cc8d33fbfcecca8ebd4e0d34a02969f10f00f036cffe288800`, give final bounded SPEC/QUALITY approval, independent fixed-source execution and public-contract review. Root guarantees those paths in publication assembly; this documentation edit does not claim the assembly is already published. Root reports378 PASS in84.9132638s; independent Astra repeats the same378 PASS in85.3792868s, not756 distinct cases. Root reports810-source/573-config/13-artifact custody PASS and CLI34 packs/35 profiles PASS in244.28324s. Independent log: `/workspace/bac-review-2026-11-01/qualification/wave35-r52-independent-native/independent-native.log`, SHA256`743e1ec0748565fae78c8d7869a14ab6557c7e06f67ddd72f51cafe7255f6b78`.

The focused suite qualifies CPU named next-service continuation, supported configurations/history, raw-type refusal, ownership/identity/value/RNG purity, returned gradient state and final attachment. Root global Ruff/Black/expression/default600 checks passed; global mypy retains20 unresolved BANK14/oracle6 errors with no new native errors. Required native/owner fixture migration, consumer integration and remaining programme gates are not closed here. This documentation author performed no runtime or Git/index operation.
