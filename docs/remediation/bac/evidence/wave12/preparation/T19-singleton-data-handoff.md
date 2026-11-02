# T19 singleton-action DATA handoff — static, compilation prerequisite explicit

This is only the finite DATA handoff for the current T19 singleton-entropy P2. No next packet or programme task follows. The existing lane pack can be narrowed on a **test-local authored DATA copy** without changing its grid/world/affordance mechanics. The exact candidate below is ready for root's focused compilation after writer closure. **It is not yet certified as a valid A=1 pack:** the allowed five implementations do not define the action-config grammar/compiler expansion for `substrate_actions.inherit: false`, and no existing YAML example of false was found under configs/tests. That is the precise unresolved point; do not call a prerequisite compilation refusal an entropy RED.

## Exact minimal candidate edits

Use the already source-verified public helpers from `tests.test_townlet.regressions.fixtures.episode_lanes`:

- `copy_authored_config(destination: Path, *, lifespan: int, num_agents: int) -> Path`; a bounded singleton setup can select lifespan10/N1 through those existing arguments.
- After the DATA edits below, `build_authored_population(config_dir: Path, *, num_agents: int, exploration: ExplorationStrategy) -> VectorizedPopulation`, supplying the caller's real exploration object, compiles the actual edited pack without cache, derives the real observation/action geometry, builds real ENV/POP and already calls population.reset once. No fake action_dim, token_spec, mask, compiled DTO or builder is needed.

Only **two files in the later test-local DATA copy** need this candidate change. No copy/edit/helper execution was performed during this static handoff.

1. Replace copied **`actions.yaml`** with the following complete document. It retains the existing version, WAIT description/default enablement and labels, retains the grid world elsewhere, suppresses inherited actions if that existing boolean grammar supports false, and removes the other custom declarations from this isolated singleton test pack:

```yaml
actions:
  version: '1.0'
  substrate_actions:
    inherit: false
  custom_actions:
  - name: WAIT
    description: Do nothing (pass turn)
    enabled_by_default: true
  labels:
    preset: gaming
```

2. In copied **`levels/L0_test/training.yaml`**, replace only **`training.enabled_actions.custom`** with the empty list, retaining its surrounding required mapping and every unrelated training field:

```yaml
training:
  enabled_actions:
    custom: []
```

This second block is a **subtree edit, not a complete replacement training document**. The source file currently names REST and END_LANE in that exact custom list. Those references must be removed when their declarations are removed; otherwise the proposed pack has dangling selected custom-action references. WAIT remains `enabled_by_default: true`. The empty custom-selection plus default-enabled WAIT pattern is already authored together in `configs/test/token_transfer_a/actions.yaml` and `levels/L0_transfer/training.yaml`; this handoff uses that observed DATA pattern rather than inventing explicit WAIT-list semantics.

Changing only the training list cannot establish A=1: the lane pack also currently inherits substrate actions and declares default-enabled END_LANE. Keeping all three declarations and merely disabling one policy choice likewise would not prove that the compiled vocabulary dimension is1. The candidate removes those declarations only in the new singleton test DATA copy; it does not alter the canonical lane pack or its existing2/5 scenarios.

## References and mechanics that must remain

All thirteen existing lane-pack YAML files were read completely as DATA. The only DATA reference to custom REST/END_LANE outside their declarations is the selected training custom list addressed above. END_LANE's declaration owns its bar.energy overwrite write, so removing that declaration removes its associated write as one complete authored item; do not leave a partial action/write object. `effects.yaml` has an empty effect_definitions list. No other lane DATA references WAIT/REST/END_LANE by name.

Keep **stratum.yaml unchanged**: grid, square8x8, clamp, manhattan, no diagonals. The aspatial example observed elsewhere is not an acceptable substitute for preserving these mechanics. Keep all environment/level affordance declarations, `training.enabled_affordances`, deployment/interactions/modulations, bar bounds/depletion/cascades, drive, variables, items, brain and curriculum intact. In particular:

- `drive.shaping` still references target_affordance EAT and completion affordance SLEEP.
- Environment and level modulations still reference WORK/SOCIALIZE.
- The environment and selected training retain all their current affordance names. Do not empty enabled_affordances or strip affordance declarations to try to force an action dimension; that would change world mechanics and could break these retained references.
- No direct writes to live meters, dones, step counts, reward state, action IDs, masks, networks or compiled metadata are part of this DATA route. Root should resolve WAIT by the existing `action_ids(env, names: Sequence[str]) -> torch.Tensor` helper if explicit selection is needed. UNEQUAL_ENDINGS is unsuitable after END_LANE is deliberately absent from this isolated vocabulary.

The uninspected compiler may still reject inheritance=false or emit an additional mandatory action. Root must establish `env.action_dim == 1`, the actual action vocabulary contains only WAIT, and actual eligible masks have width1 with WAIT legal. This handoff cannot assert those outcomes from YAML syntax alone. No sixth action-config/compiler/environment source was opened to fill that gap.

## Current public owned-episode/reset/cleanup sequence

LANES34–80 verifies both helper signatures and the builder's initial reset. Current POP794–867 verifies the subsequent owned-episode public order: after the returned fresh already-reset population, call `bind_episode_worlds(world_ids=(a concrete unique singleton world ID,), world_episode_seqs=(an explicit nonnegative sequence,))`, then `begin_batch_episode(index=an unused nonnegative batch ID, planned_horizon=10)`, then **population.reset()**, then actual `step_population(population.env)`. Do not separately env.reset, omit the required world binding, or step between begin and its required reset. These are source-verified API uses, not a new helper or an executed probe.

The confirmed singleton entropy check is reached only on the explicitly begun owned route: POP1365–1374 currently computes normalized Q-policy entropy using log(q_values.shape[-1]) and requires a finite eligible snapshot before env.step. Therefore a bare unowned population step would not exercise this P2 branch. Actual compiled A=1 must be established first; pinning a fabricated Q width or changing env.action_dim would evade the requested real-world capability.

Use existing public `flush_episode(agent_idx: int, reason: RunnerCompletionReason) -> EpisodeCompletion|None` to close each participating survivor with explicit `checkpoint` before cleanup reset; its source at POP1228–1273 is once-only and does not rewrite replay done. Reset refuses unfinished nonempty lanes. If a step fails before any actual transition, survival count remains empty and the inspected finalizer returns None before envelope construction. On a later episode use fresh explicit IDs/sequence and a new batch index; begin_batch_episode refuses reused batch IDs. No env/pop close/shutdown method is claimed from an uninspected base class. These cleanup conventions preserve actual successors/masks and existing lifecycle behavior without needing an authored terminal action or an invented exact WAIT lifetime.

## DATA digests and source attribution

Original lane DATA SHA256s below are for the unchanged repository files read here, **not** for a nonexistent edited/generated singleton pack:

| Relative to `configs/test/episode_lanes/` | SHA256 |
|---|---|
| `actions.yaml` |`cecb2673d71738c76486f849d4a93f8747cbb958c96b9f07dc0eccd190a4a484`|
| `brain.yaml` |`45fd26add306fc29a9ea0b913172e0ed636cf14ad5117bf44b03226011ff22a5`|
| `effects.yaml` |`dba0d3dec16ffe31f7e4ecbef0de7f0297d06aa5f4afd05fe4e2f9d1c555c688`|
| `environment.yaml` |`dbeab4158d34406cb59da7aeb2b68cd53bce8dea0691cc4c22989bd6947447a4`|
| `experiment.yaml` |`5ac85a4c4b82b3c70e0302e34dcbf64baa3e861127aa5425c8f98468cd848105`|
| `items.yaml` |`b7e8de3f8a153e7293b713ba81be3a318724d3688ac67df29bd622a302aadd26`|
| `stratum.yaml` |`9848f77098f4faa2d934dc8284ae37e47b33d34e6fc909187b2fb87b5c7022a8`|
| `variables.yaml` |`753a2b8a27eb7a9dc582f1f6c97617302d6c4c20e695f3cfd299f819ddd1cb31`|
| `levels/L0_test/affordances.yaml` |`d937ef40e4fa92ec89539386b9249944203ca82ba883892ef05695afc8f4e07c`|
| `levels/L0_test/bars.yaml` |`c55c7736c0c6ae948cdb8d597a1ea13c8087f19a04b91e341ff8c4a5d10cdc57`|
| `levels/L0_test/curriculum.yaml` |`e24d6f042e667615359ff43b8c6e2c84982695bfcd6c8ed5795f48a2eb3201e8`|
| `levels/L0_test/drive.yaml` |`1dfaca1e050a33fc1776b065481ce77f77789ea9b450a35ee3cf86171bb048e8`|
| `levels/L0_test/training.yaml` |`65e26fec1cb0697806c2767274becbb9cc7af54f3bea0e67ccb0e91934e47674`|

Additional authored DATA read for grammar examples: `configs/test/token_transfer_a/actions.yaml` SHA`0669a6fe6b0fe7993f8df34c56381087c6c7d5ba51053d2eeed83472951c1a93`; its `levels/L0_transfer/training.yaml` SHA`528bbb3a8bcb0d406005caefc538244c004f7667d0ac7aca1f20043feef9ac9a`. `configs/test/action_space/{aspatial,grid2d,continuous1d}/actions.yaml` each SHA`d9f4ae5d0f39422d2a2752c6b832387a522b970bb9d2fe2958e21a0fbbba6b08`, and `configs/test/action_space/aspatial/stratum.yaml` SHA`291e2403a4b23262061dd4a0bae5219f0e1f3d6a60fe3d958dbfced67ed735eb`; all still use inherit=true. DATA-only rg searches under configs/tests found no false example. The aspatial DATA was inspected only to reject changing world type as a purported minimal fix.

Five-path implementation/test inventory remains bounded at **3927 lines**: RR1017 SHA`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`; current POP2315 SHA`97e6c64c746414f1163b27a3c83329f8ccb2bce70676b53c1ffc34074caa9ede`; SINKS312 SHA`e6631eb7e2375165a1e1131eaf88999e8debb024d37ef736bf9eadcdacd3fbde`; HP126 SHA`237ca50b9deb1e585c7d37d1134896b4fe1a29dde12b4de7a401210e317c4db0`; LANES157 SHA`9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f`. Only those existing implementation paths supplied public API attribution. Imported action/config/compiler/environment/base/DTO implementations were not inspected; YAML DATA examples do not substitute for their grammar/semantic validation.

Only this requested ignored report was written (`.git/info/exclude:7` matches `/.superpowers/`). No compiler/runtime/import/helper execution, pytest/collection/lint/AST probe, source/YAML/index/tracker edit, commit/push, branch/worktree/project source copy/deletion or subdelegation occurred. All14 worktrees are preserved. Root owns the single focused fixture-compilation prerequisite and current T19 closure. Stationary.
