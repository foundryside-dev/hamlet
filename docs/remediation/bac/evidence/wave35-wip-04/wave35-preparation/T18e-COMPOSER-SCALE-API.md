# T18e frozen real composer runtime-scale API

This public capsule supplies the actual current VTC/DAC seam to the ENV/RWC owner without opening VTC as an additional source. It describes the implemented primitive, not whole T18e acceptance. Production and regression sources are frozen after root and independent verification.

## Actual source identity and qualification

| Source | Whole lines | SHA256 |
|---|---:|---|
| src/townlet/vfs/vtc.py | 3510 | a2d14e8bf9d7363e36f5778182395a4e5110052ca5591efacb1c98d63dad4390 |
| src/townlet/environment/dac_engine.py | 977 | b129d7ac5cdbf7e6ed27dd6cd5f9529dc9e7d2e0154b43a4db028d7aef78e317 |
| tests/test_townlet/regressions/bac/test_intrinsic_scale_composer.py | 195 | 0ad34fdfb781a5679762a2eacfa4ff2d86a026967e5039fe514e81a2fce0e745 |

Fresh primitive context is exactly these three whole sources: 4682 actual lines within ceilings 3550+1000+350=4900. No RWC/ENV/config/registry/runtime/helper implementation body or introspection was added. Real config/registry construction comes from T18e-CONFIG-FIXTURE-API.md.

Root reports initial causal RED29, then actual GREEN29 PASS in 8.12831354 wall seconds. Independent Astra reports actual GREEN29 PASS in 7.56000137 wall seconds and fixed three-source/spec/quality review APPROVED with zero owning material findings. These are the **same 29 regression cases verified twice**, not 58 distinct cases. Both root and independent custody verifiers report PASS for 798 sources, 573 configs, 13 artifacts, three pytest processes, 14 registry MAIN1 identities, source/index/import/thread checks. This author executed only permitted scoped Black/Ruff checks, both exit0; no runtime/import/test/probe/compile/git/index operation was performed here.

Root supplies these exact custody receipts and adjacent result files containing commands and log hashes:

- /workspace/bac-review-2026-11-01/qualification/wave34-r12-owned/owned-custody.json
- /workspace/bac-review-2026-11-01/qualification/wave34-r12-owned/owned-result.json
- /workspace/bac-review-2026-11-01/qualification/wave34-r12-independent/independent-custody.json
- /workspace/bac-review-2026-11-01/qualification/wave34-r12-independent/independent-result.json

## Exact callable seam

Public imports and construction remain:

```python
from townlet.vfs.vtc import VTCRewardProgram
from townlet.environment.dac_engine import DACEngine

program = VTCRewardProgram()
```

VTCRewardProgram is a fieldless frozen dataclass. Its actual public bound signature is:

```python
apply(
    self,
    *,
    reward_backend: Any,
    step_counts: torch.Tensor,
    dones: torch.Tensor,
    meters: torch.Tensor,
    intrinsic_raw: torch.Tensor,
    runtime_intrinsic_scale: torch.Tensor,
    reward_context: Mapping[str, Any],
) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]
```

The actual DAC constructor remains:

```python
DACEngine(
    dac_config: DriveAsCodeConfig,
    vfs_registry: VariableRegistry,
    device: torch.device,
    num_agents: int,
    bar_index_map: dict[str, int],
)
```

The actual DAC public bound reward signature is:

```python
calculate_rewards(
    self,
    step_counts: torch.Tensor,
    dones: torch.Tensor,
    meters: torch.Tensor,
    intrinsic_raw: torch.Tensor,
    *,
    runtime_intrinsic_scale: torch.Tensor,
    **kwargs,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]
```

Both scale arguments are required with no default. VTC calls the actual backend once with the four original named tensor arguments plus runtime_intrinsic_scale=runtime_intrinsic_scale and **dict(reward_context). VTC does not multiply, clone, normalize or mask input raw/scale. Keep runtime_intrinsic_scale out of reward_context; a duplicate keyword is an error, not an alternate transport. No config field, modifier alias, adapter, fallback or old-caller mode exists.

Use full population ordering N=engine.num_agents. Scale must be a torch.Tensor of exact shape (N,), dtype torch.float32, on the engine-selected device, with every value finite and >=0. A scalar, eligible-row-only vector, broadcastable rank-two tensor, Python list or other dtype is not accepted or converted. Raw and scale are independent inputs; do not pre-multiply in runtime/RWC/POP, fold scale into drive base, or take a per-world/whole-population mean. Existing argument geometry remains step_counts[N], dones[N], meters[N,meter_count], intrinsic_raw[N]; normal callers supply long step counts, bool dones and float32 meter/raw tensors on the selected device. The new validation contract specifically validates scale and does not claim broader new raw/step/done/shape hardening.

## Actual validation order

DAC validates before extrinsic/intrinsic/shaping computation:

1. Scale is a torch.Tensor, otherwise TypeError naming runtime_intrinsic_scale.
2. Scale shape exactly (num_agents,), otherwise ValueError naming runtime_intrinsic_scale.
3. Scale dtype exactly torch.float32, otherwise TypeError naming runtime_intrinsic_scale.
4. Existing meters, intrinsic_raw and dones device checks, in that order, then scale device check. Mismatch raises RuntimeError; the new scale error names runtime_intrinsic_scale.
5. Scale values are finite, then nonnegative; either failure raises ValueError naming runtime_intrinsic_scale.

Device comparison uses existing DAC semantics: types must match; CUDA with no index means index0; explicit CUDA indices must agree; matching non-CUDA device types are accepted by that existing comparator. This primitive does not add a step_counts device check or broaden that comparator. Meta-vs-CPU mismatch is verified without assuming GPU availability. Omission fails Python's required-argument contract at either entrypoint.

## Actual arithmetic, results and diagnostics

On each non-done row, actual DAC composition is:

```
provider raw * runtime scale * authored intrinsic.base_weight * real compiled modifier product
```

Runtime scale is multiplied exactly once inside DAC. The authored base and modifier product remain independent. Existing DAC then masks intrinsic on dones, computes genuine shaping with existing context and masks shaping on dones; genuine extrinsic strategy keeps its existing behavior. Canonical DAC total remains extrinsic + intrinsic + shaping. No retirement bonus or inactive-on-entry masking is introduced here.

The returned tuple is (total_reward, intrinsic_weight, components). All values are population tensors, and actual VTC verifies total and weight shapes match dones.shape, requires a dict containing its original expected component names, and validates every component tensor against that shape. It permits additional components. It returns the actual backend objects unchanged.

| Result | Actual meaning |
|---|---|
| total_reward | Existing extrinsic + final effective intrinsic + shaping |
| intrinsic_weight | Only the compiled authored modifier product; excludes raw, scale, drive base and terminal masking |
| components['extrinsic'] | Actual existing extrinsic term |
| components['intrinsic'] | Raw * runtime scale * drive base * modifier product, then existing done mask |
| components['intrinsic_raw'] | Historical raw * drive base, before runtime scale, modifiers and done mask |
| components['shaping'] | Actual summed shaping, then existing done mask |
| components['provider_intrinsic_raw'] | Original provider raw, cloned into owned storage, before all scale/base/modifier/done operations |
| components['runtime_intrinsic_scale'] | Original validated runtime factor, cloned into owned storage, before done masking |

The two added provenance keys have truthful unmasked values on done rows. Existing intrinsic_raw and modifier-only weights also retain their original unmasked diagnostics. Later ENV inactive-entry handling must act under its own explicit accepted-step contract; do not reinterpret these primitive done diagnostics as proof of retirement or inactive-row acceptance.

DAC clones original raw and scale; it does not mutate input tensors or detach the clones. Multiplication allocates reward tensors. Returned provider raw/scale own storage distinct from caller inputs, each other and the remaining reward/component tensors. Mutating input raw/scale after composition cannot change captured outputs; mutating either returned provenance tensor cannot alter caller inputs or other result tensors. Tensors remain mutable ordinary PyTorch tensors and preserve autograd links; this is owned storage, not read-only tensor authority. Live raw and scale gradients propagate through the real composer, and terminal effective intrinsic gradients are zero. Ordinary PyTorch rules still apply when mutating tensors retained for a later backward pass.

Qualified real control uses fresh validated DriveAsCodeConfig, real VariableRegistry, actual compiled energy modifier2, base .25, actual constant extrinsic1 and energy efficiency shaping .1. Raw2 and scale.5 produce intrinsic.5 and total1.6 before separate ENV retirement. Scale0 produces intrinsic0/total1.1; scale1 or independent base.5 produces intrinsic1/total2.1. Regression independently varies raw/base/scale/modifier and covers heterogeneous rows, terminal nonzero scale, omission/malformed validation, mutation ownership and autograd. No mocked effective modifier or replacement composer is used.

## Direct consumer gap and remaining acceptance

Direct existing VTC/DAC callers that omit runtime_intrinsic_scale must migrate to the explicit current contract in the coherent unreleased integration. Existing **kwargs transport does not make omission valid. Exact-key component consumers must directly accept the two provenance keys. Existing VTC base-component names remain valid. No compatibility default or fallback should be introduced to make old consumers pass.

This primitive does not qualify current ENV/RWC runtime attachment, all five actual providers or both scopes, eligible-row event order, stats/admission once, zero-scale service work, predecessor/successor equality or ICM identity, parent clock/custody/service, current native resume, retirement/inactive masking, canonical replay capture, full-suite/coverage/learning/hardware gates or global BAC completion. All remain mandatory original integration obligations. The root/independent overlapping GREEN29 and approved bounded review establish only this finite actual composer seam. No capability reduction, repository-green claim or whole-T18e closure is implied.
