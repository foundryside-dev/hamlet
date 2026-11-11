# T18e canonical composer readiness report

Read-only source extraction, 2026-11-10. This report is the only written artifact. It prepares the original T18e work; it does not implement it, choose an implementation, or claim test/CI/acceptance completion. Existing task baseline is 47d82ee6 as supplied by the brief, not independently queried. Root's evolving RP source was not read.

## Scope and measured inventory

Read AGENTS.md, T18e-COMPOSER-READINESS-BRIEF.md, and T18e-original-task.md. The originally requested spelling `exactT18e-original-task.md` does not exist in this directory; the brief's named `T18e-original-task.md` was read. Owner zero-backwards-compatibility guidance supersedes the original observation-only compatibility bullet. No fallback, old-provider adapter, capability reduction, fake end-to-end path, or standalone replacement composer is proposed.

Exactly three implementation files entered this review. Whole-file line charges and SHA-256:

| File | Actual lines | Eventual ceiling | SHA-256 |
| --- | ---: | ---: | --- |
| src/townlet/vfs/vtc.py | 3508 | 3550 | a27e205ec3531292e56c5b743d5f70b5208a060282278b47a1dc6ee3f7470951 |
| src/townlet/environment/dac_engine.py | 956 | 1000 | c6ad4338f82aa2c905a32d66f666ef7725f02b8f1aef470d76a68e6185bb44e6 |
| src/townlet/environment/reward_calculator.py | 57 | 70 | 21c5de34bcf20589826e18ad88554d54caa65aaf8ea22aae82d51874585c6c5c |
| New narrow primitive regression test, reserved only; not created/read | 0 | 350 | none |
| Total | 4521 | 4970 | three measured sources; four eventual named slots |

The fourth reservation is not authorization to implement or run tests now. No ENV, RP, BANK, provider, context, helper, or existing test implementation source was read. No imports, introspection, compilation, runtime probes, tests, git/index operations, branches, worktrees, installations, or source copies were performed. The report destination is the ignored destination designated by the brief; ignore state was not independently queried because git operations were prohibited.

## Current composer API capsule for a separate ENV owner

These are exact current source facts, not the future runtime ABI.

`townlet.vfs.vtc.VTCRewardProgram` (vtc.py:2116–2171) is a frozen dataclass with no instance fields. The inspected source itself supplies the direct public factory `VTCRewardProgram()`; there is no reward-program compile helper to discover. Its ClassVar `expected_components` is `("extrinsic", "intrinsic", "intrinsic_raw", "shaping")`.

The public bound method is:

```python
apply(self, *, reward_backend: Any,
      step_counts: torch.Tensor, dones: torch.Tensor,
      meters: torch.Tensor, intrinsic_raw: torch.Tensor,
      reward_context: Mapping[str, Any]
) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]
```

The real call is `reward_backend.calculate_rewards(step_counts=step_counts, dones=dones, meters=meters, intrinsic_raw=intrinsic_raw, **dict(reward_context))` (2138–2144). It does not pre-scale, clone, normalize, mask, or recompose raw rewards. It validates returned total and weights are tensors exactly matching `dones.shape`, requires a dict containing the four named components, and validates every component (including additional keys) is a tensor of that shape. It permits extra component keys. It does not validate input shape, dtype, finiteness, device, or numerical composition. It returns the backend's three objects unchanged.

`townlet.environment.dac_engine.DACEngine` constructor (56–92) takes `dac_config: DriveAsCodeConfig`, `vfs_registry: VariableRegistry`, `device: torch.device`, `num_agents: int`, `bar_index_map: dict[str, int]`. It compiles real modifiers, extrinsic strategy, and shaping functions and reads composition logging fields. Its public method (848–956) is:

```python
calculate_rewards(self, step_counts: torch.Tensor,
                  dones: torch.Tensor, meters: torch.Tensor,
                  intrinsic_raw: torch.Tensor, **kwargs
) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]
```

Documented data: step_counts/dones/raw are `[num_agents]`; meters is `[num_agents, meter_count]`; dones is agent death flags. DAC checks meters/raw/dones device against its configured device (CUDA default index treated as zero). It does not validate step_counts device and does not use step_counts in this method. A later owner must preserve full-population tensor ordering; active-row provider values are scattered into that ordering by current RWC.

`RewardCalculator(env)` stores env. `_calculate_shaped_rewards(self, *, active_on_entry: torch.Tensor) -> torch.Tensor` is the current facade (reward_calculator.py:19–57). It expects these env attributes/methods, directly observed here:

- `num_agents`, `device`, `exploration_module`, `_get_observations()`;
- `positions`, `_get_affordance_positions()`, `_get_last_action_affordances()`, `_get_affordance_streaks()`, `_get_unique_affordances_used()`;
- `enable_temporal_mechanics`, and `time_of_day` when enabled;
- `vtc_reward_program`, `dac_engine`, `step_counts`, `dones`, `meters`;
- writable `intrinsic_weights` and `_last_reward_components`.

It supplies reward_context keys `agent_positions` (positions cast to device/float32), `affordance_positions`, `last_action_affordance`, `affordance_streak`, `unique_affordances_used`, plus `current_hour=torch.tensor(env.time_of_day, device=env.device)` when temporal mechanics are enabled. These feed genuine authored DAC shaping. It calls the bound program once with full env tensors (45–52), stores returned weights/components (54–55), and returns that exact total tensor (57). This is the canonical sink visible within scope. Later ENV return values and replay storage are not visible here and remain to be proven.

## Actual intrinsic, drive, component, and retirement semantics

DAC's actual arithmetic (908–956), for each live row, is:

1. `extrinsic = self.extrinsic_fn(meters=meters, dones=dones)`.
2. Clone caller raw; multiply by `dac_config.intrinsic.base_weight`.
3. Start `intrinsic_weight` at ones; multiply outputs of the real compiled modifiers listed by `dac_config.intrinsic.apply_modifiers` and present in `self.modifiers`.
4. Multiply intrinsic by that modifier product; zero intrinsic on `dones`.
5. Sum real shaping functions with `meters`, `dones`, and context; zero shaping on `dones`.
6. `total_reward = extrinsic + intrinsic + shaping_total`.

Modifier compilation (93–148) sorts configured ranges by min, gets a configured bar via bar_index_map or a VFS variable via registry reader `"engine"`, starts from the final range's multiplier, and applies earlier half-open ranges via torch.where. Do not bypass these compiled functions with a mocked effective weight. Listed modifier names missing from the compiled dict are currently skipped; that existing behavior is a fact, not a new hardening work item.

Important distinctions for the later owner:

- Returned `intrinsic_weights` is currently **only the authored modifier product**, despite the docstring's description of effective weights. It excludes drive base, raw value, terminal mask, and any runtime scale. Do not infer its numerical meaning from its name.
- `components["intrinsic"]` is final drive-base/modifier-scaled, terminal-masked intrinsic.
- `components["intrinsic_raw"]` is **raw times drive base**, before modifiers. It is not the provider's unweighted raw, and it is not terminal masked. A nonzero raw on a done row therefore remains visible in this diagnostic component while final intrinsic is zero.
- `components["extrinsic"]` and `["shaping"]` are their actual compositional terms; total is their sum with final intrinsic.
- The composer contains no RMS/statistical normalization, predictor admission, or provider training. `meters` are described as normalized input, which is distinct from novelty normalization. Novelty normalization ownership cannot be inferred without the qualified runtime/provider capsule.
- No retirement term/bonus or retirement normalization occurs in these three sources. Existing extrinsic strategies zero on dones; intrinsic and shaping do likewise. Retirement handling outside these sources is unverified, must remain separate from the demonstrated pre-retirement formula, and cannot be rewritten or certified from this extraction.

## Exact runtime-scale and phase gaps

There is no `runtime_intrinsic_scale` occurrence in any of the three implementation files.

- VTC has no explicit runtime-scale input or named pass-through. Its generic reward_context expansion could transport an arbitrary key today, but that is not an explicit scale contract.
- DAC has no named runtime-scale argument, validation, or multiplication. Supplying that name only through current **kwargs would forward it to shaping functions and would not scale intrinsic at all. It does not fix the gap.
- RWC has no runtime scale resolution/data input or pass-through, no intrinsic_context parameter, and no ExplorationRuntime invocation.
- For live raw=2, drive base=.25, modifier=2, current arithmetic gives intrinsic=1; with extrinsic=1 and shaping=.1, total=2.1. Desired runtime=.5 gives intrinsic=.5 and total=1.6 before separate retirement. These are source-derived arithmetic expectations, not executed test results.
- Runtime scale zero currently cannot suppress this intrinsic through a named runtime-scale input. Future zero-scale proof must exercise actual provider families and real composition rather than replacing the composer or merely injecting zero raw.

Current provider invocation (RWC:22–27): allocate full zero raw on env.device; if exploration_module exists and any active_on_entry row is true, fetch `_get_observations()` at the moment rewards are calculated, call `env.exploration_module.compute_intrinsic_rewards(observations[active_on_entry], update_stats=True)` once, and scatter into raw on those active rows. RWC does not select a family, establish provider identity, capture predecessor/action/successor, or own RND predictor admission. The brief identifies this reward call as successor phase; source here proves current-time observation acquisition, while actual post-physics ordering requires separate ENV evidence. The temporal-hour comment says ENV flips to the next hour only after reward calculation; it is a comment, not independent ENV verification.

The brief requires all five currently selected families preserved. RWC exposes only the one direct observation-only call shape; it cannot establish which five actual providers are bound or their qualified ABI. The original test bullet names RND/adaptive/count/ICM; that list must not be used to discard the fifth selected family. Root's stable public runtime capsule must enumerate all five and their actual raw/scale/normalization contracts after its RP writer finishes.

Required later phase invariants: observation providers reward successor observations; ICM consumes true predecessor/action/successor; RND predictor admission stays predecessor phase; every eligible reward event updates normalization stats once; POP diagnostic novelty must neither replace/recompose canonical rewards nor re-update RMS. No inspected composer code performs those provider operations; only RWC's single `update_stats=True` request is visible. It is not proof of the provider's internal update count.

## Finite original acceptance map and bounded dependency order

| Original acceptance | Existing visible anchor | Remaining evidence/work |
| --- | --- | --- |
| Real scale-once arithmetic and drive independence | VTC:2127–2148; DAC:908–956 | Explicit scale seam and single multiplication; real base/modifier/shaping regression, distinct scale/base controls, components/weights semantics made explicit |
| Runtime scale zero and terminal mask | DAC:929–939; RWC active-row scatter | Zero-scale primitive and genuine runtime family cases; retain done masking and diagnostic component distinction |
| Actual ENV→RWC→DAC provider and components | RWC:23–27,45–57 | Stable runtime invocation; ENV accepted-step context capture; observed actual provider binding; canonical return and replay equality |
| Distinguishable predecessor/successor and ICM identity | RWC currently reads only present observations | True owned transition context and ICM identity delivery; successor observation-family phase and predecessor RND admission proof |
| One stats update per event; POP diagnostic isolation | Single RWC update_stats=True invocation | Runtime/provider instrumentation and real sink evidence; POP behavior outside scope |
| Red/green original intrinsic composition tests | No test source permitted | Separate authorization and bounded actual test setup; no results claimed here |
| Review/commit and global release gates | None in this readonly task | Later review/commit authorization and full original integration; global BAC gates remain open |

Dependency-coherent proposed sequencing, subject to later authorization:

1. Root supplies its settled public runtime ABI capsule and the missing real fixture/setup facts below. This must come from the qualified RP/runtime owner; do not read its actively changing source or reconstruct it through introspection.
2. A bounded scaling primitive slice uses these three named sources plus one explicitly named new real composer regression test of at most 350 lines: ceilings 3550+1000+70+350=4970, four files within user <=5 files/5000 lines. It introduces a precise runtime-scale DAC/VTC contract and proves genuine `VTCRewardProgram().apply(reward_backend=real_DAC, ...)` arithmetic through compiled drive config/modifiers/shaping. Preserve provider raw, drive base, authored modifiers, canonical components, and separate retirement behavior. Exact API change and component/weight meanings need to be settled and recorded by that implementing slice; this report does not choose them. A scalar/tensor scale ABI must come from qualified runtime facts, not guessing.
3. Freeze that primitive API and publish its public data/results capsule so a separate ENV integration owner need not open VTC3508 as an extra file. Then separately budget ENV/RWC/qualified-runtime integration and its real regression evidence using actual whole-file counts before reads. Adding ENV2403 to the four ceilings here would exceed 5000; it is not permitted in this primitive slice. Do not hide a sixth source, helper body, source copy, or indirect introspection under a fixture name. If later actual integration cannot fit its independently declared <=5/5000 budget, root must supply a narrower public dependency capsule or assign another bounded owner rather than quietly widening.
4. Full original ENV→RWC→DAC canonical replay and phase/stat evidence remains mandatory after primitive proof. A primitive-only test is not end-to-end acceptance. No new global VFS work is implied by touching the narrow VTC reward wrapper.

## Missing facts to request from the qualified owner

These are explicit blockers to designing faithful test setup/integration within the current source budget, not permission to open helper implementations:

- A real `DriveAsCodeConfig` construction/validation capsule with exact public constructor/import, accepted field names and required composition fields. DAC accesses config.intrinsic.base_weight/apply_modifiers, config.modifiers with source/ranges, config.extrinsic strategy fields, config.shaping, and config.composition.log_components/log_modifiers. The imported `townlet.config.drive_as_code.DriveAsCodeConfig` body was not read. Public setup must show how to author base=.25, a real modifier=2, extrinsic=1, and shaping=.1 using accepted schema rather than a fabricated object/monkeypatched backend.
- A real `VariableRegistry` public construction/registration capsule (imported from townlet.vfs.registry) suitable for that config, or an already qualified fixture capsule providing the genuine config/registry. Its constructor is not inferable from the import or DAC's registry reads. A bar-backed modifier can avoid an unnecessary variable lookup but does not authorize inventing registry setup.
- Settled ExplorationRuntime public import, bound env attribute, exact invocation/result types, raw/scale scalar-or-tensor shape/device/ownership, update_stats policy, family enumeration, and normalization ownership. RP source remains unread while root works on it.
- Settled `IntrinsicTransitionContext` public construction/data ownership capsule: predecessor, accepted action, successor, active/terminal identity and ordering, plus real ENV capture placement and replay/sink API. No context or ENV implementation source was read here.
- Existing retirement public behavior and exact canonical sink/replay placement, so the integration owner can preserve real retirement separately and compare the appropriate before/after-retirement quantities.

All five selected families, real drive effects, phase identity, stats-once semantics, POP diagnostic isolation, and canonical replay remain owed. Global BAC final 54 requirements, 22 lenses, learning/coverage/hardware gates remain open. This report establishes only bounded source facts and missing seams.
