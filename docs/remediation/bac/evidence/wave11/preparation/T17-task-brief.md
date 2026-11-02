# T17 read-only readiness; implementation not cleared

### T17: Descriptor/value interactions while retaining mean — G01

**Interfaces:** NF passes P4's explicit encoder mode/hidden width into token-set/recurrent constructors; NET keeps linear state/forward behavior and adds per-type prepool interaction MLPs. Static context is target-owned/nonpersistent for both modes.

- [ ] Add `test_mean_can_bind_descriptor_value`, `test_linear_mean_is_preserved`, `test_semantic_permutation_absence_and_memory`: constructive row feature witness gives .375 versus.125; authored B02 complementary-variable pack has a selected nonzero Q distinction, semantic row+context permutation is equal within1e-6, absent/empty pooled values and encoder gradients equal exact0.
- [ ] Run `test_token_binding.py` red for the new mode; retain exact linear-mean alias as a truthful historical control rather than asserting random weights must distinguish.
- [ ] Implement P4 and mode-aware state identity/factory routing, preserving mean/attention, token/recurrent and zero-start sequence semantics.
- [ ] Run green plus B02 compact/context/empty/permutation/network suites and frame-vs-history separation.
- [ ] Review and commit `feat(agent): add interaction encoders to mean token policies`.

## Exact source boundary

[
  {
    "alias": "NET",
    "access": "modify",
    "path": "src/townlet/agent/networks.py",
    "projected_lines": 750
  },
  {
    "alias": "NF",
    "access": "modify",
    "path": "src/townlet/agent/network_factory.py",
    "projected_lines": 250
  },
  {
    "alias": "BC",
    "access": "read_only",
    "path": "src/townlet/config/brain_config.py",
    "projected_lines": 750
  },
  {
    "alias": "OP",
    "access": "read_only",
    "path": "src/townlet/config/bac_options.py",
    "projected_lines": 600
  },
  {
    "alias": "test",
    "path": "tests/test_townlet/regressions/bac/test_token_binding.py",
    "access": "create_test",
    "projected_lines": 350
  }
]

5 complete sources/projected2700physical lines. No sixth implementation/helper/probe/test; use source-verified supplier prose for uninspected runtime APIs. Read whole named files and independently count/hash.

## Accepted interfaces

### P1. Authored, effective and transport identities

T02 adds `config/bac_options.py` with immutable validated `BaCOptions` and nested policies. T03 adds `config/effective_run.py`:

`resolve_effective_run(base: BrainConfig, training: TrainingV2Config, *, primary_level: str, origins: Mapping[str, str], drive_intrinsic: IntrinsicStrategyConfig) -> EffectiveRunConfig`.

`EffectiveRunConfig` contains `base_brain`, `effective_brain`, `training`, `options`, `exploration: ResolvedExplorationPolicy`, `primary_level`, `field_roles: Mapping[str, FieldRole]`, `authored_brain_hash`, `execution_hash`, `training_hash`, and `derivations: Mapping[str,str]`. `FieldRole` has `status: Literal['active','inactive_preset','derived','unqualified']`, `origin` and `reason`. Continue existing `brain_hash`/`pack_brain_hash` meanings and `compute_brain_hash` API; **add** `execution_hash`, do not silently redefine an existing hash. Effective brain still applies exactly gamma, target interval, Double DQN, learning rate and replay capacity after complete level replacement. Valid nonselected blocks remain validated authored content. Their edit changes authored identity and can retain identical execution identity/weights. Cache fingerprints remain separate transport/source/runtime freshness identities.

New options are portable typed authoring, carried through compiled serialization/checkpoints and telemetry. The old-document resolution table is fixed here: successive-without-replacement PER sampling, preserved legacy episode-length-with-replacement nonprioritized recurrent sampling, fixed-full windows, whole-episode retention, window-mean objective, max-absolute priority reduction, paced FIFO with one ordinary update per vector tick, max pending rows `max(2*N, predictor_batch_size)`, lossless service-before-admit overflow, completion commitment, stage-band difficulty, greedy-eval network mode, no initial save and final save enabled. Derived values are recorded, including the bounded-service upgrade; explicit options override only their named field. The preserved legacy-step, linear mean, stochastic serving and alternative modes remain explicitly selectable. Existing documents without the new options block retain a published, versioned semantic-resolution table; the resolver records each derived choice and origin. Constructors consume the resolved object, never invent local defaults. T02's explicit YAML fixtures exercise every new mode. Required existing fields remain required; omitted new additive options do not retroactively invalidate working packs.

`BaCOptions` exposes: `replay.sampling_mode` (`successive_without_replacement`, `independent_with_replacement`), `replay.uniform_sequence_adapter` (`legacy_episode_length_with_replacement`, `uniform_windows_with_replacement`); `replay.sequence_mode` (`fixed_full`, `adaptive_prefix`); `replay.retention_mode` (`whole_episode`, `transition_tail`); `replay.sequence_objective` (`window_mean`, `anchor_transition`); `replay.priority_reduction` (`max_abs`, `mean_abs`); `rnd.service_mode` (`occupancy_fifo`, `paced_fifo`), `rnd.max_updates_per_tick`, `rnd.max_pending_rows`, `rnd.overflow_policy` (`service_before_admit`, `drop_oldest`, `drop_newest`); `curriculum.commit_mode` (`completion`, `legacy_step`), `curriculum.difficulty_mode` (`stage_band`, `rate_limited`); `serving.policy_mode` (`greedy_eval`, `mc_dropout`); `checkpoint.save_initial`, `checkpoint.save_final`; the typed provider/source settings in P5a (all five drive choices), and the evaluation/viewer settings in P7. Old accepted stage/recording fields remain present with truthful roles; unqualified does not mean forbidden.

### P4. Representation without losing mean

Add `TokenEncoderOptions(mode: Literal['linear','interaction_mlp'], hidden_width: int|None)` in OP and `TokenSetConfig.token_encoder` / `RecurrentConfig.token_encoder` in BC, independent of mean/attention selection. Linear requires no hidden width; interaction MLP requires a positive explicit hidden width. Omitted new field resolves to recorded linear semantics. Preserve `linear` and its exact old state/behavior. `interaction_mlp` applies a per-type nonlinear row encoder **before** pooling, taking the assembled descriptor and live payload jointly (Linear→ReLU→Linear, explicit hidden width in YAML; use an `nn.Sequential` whose Linear modules are indices0 and2 so transfer omission keys are unambiguous). Existence proof: for two descriptors c in {0,1}, live v in {.25,.75}, the row feature `ReLU(v+c-1)` pooled across the pair is .375 versus .125 after reassignment. The semantic-row permutation, carrying context with rows, preserves the result. T17 implements this witness before claiming expressivity, plus absence/empty exact-zero gradients. Mean remains a full selectable family with either encoder; attention is preserved; historical linear-mean studies are not invalidated.

## Governance and current barrier

Use existing /workspace/hamlet only. No new branch/worktree/project checkout/source copy/deletion/.oracle actions, index/commit/push or subdelegation. Preserve all14checkouts. Source/test authoring NOT CLEARED: T16 owner is writing runner tests; no project imports/runtime/pytest/collection/compiler/linter/probes now. Read only stable NET/NF/BC/OP and existing test if any; author ONLY ignored readiness receipt. Preserve existing capabilities/options and owner rulings; only additions allowed without owner approval.

## Existing programme and qualification

25 of66packages qualified. T15 current sourceae0914af qualified full6845PASS16SKIP and6genuineclean-nativecaptures; docs/evidencef575ecef pushedexactremoteverified, CItests running (lint/configsuccess). All54requirements/22fresh final lenses remainopen. T16 dependencies notqualified yet, so no implementation. Original plan remainsbytefrozen SHA2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1.

## Finite readiness task

Identify exact existing constructor/factory/forward/static-context/state-dict interfaces, actual G01 gap versus alreadyworking controls, source/test budgets, required authored DATA/API handoffs. Reuse original B02 report /workspace/bac-review-2026-11-01/B02.md as prose only (do not follow probe/source links as sixth files). Do not start new design/plan/review cycles. No addedoptional programme. Write wave11-preparation/T17-interface-readiness.md and become stationary.


## Effective readiness handoff and source budget

Root adopts the existing P4 implementation seam in T17-interface-readiness.md addendum: additive from_resolved_encoder with required token_encoder_mode/token_encoder_hidden_width, preserving old constructors/state/computation/initialization through shared setup and central omission policy. Exact future context: NET750/NF250/read-only BC568/read-only OP294/test800 =5files/2662lines. These same paths supersede the earlier test350 projection. Complete source-verified DATA/API handoffs: T17-fixture-api-handoff.md SHA7595dd625f196f22433c9db32a29ce19c2ba164f2a7f437f8234f2916ab707ab and T17-env-public-api.md SHA41cb275e96e52f6e771889ba92138c4819c1bd02082903d6829b64267ec48e74. Consume them as prose/DATA only, not sixth implementation links. No source authoring until T16 actual qualification and root clearance. No new design loop or frozen-plan change.
