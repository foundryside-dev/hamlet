## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_strata.md`
(F-numbers) and filigree ids.

| id | sev | gap | source |
|---|---|---|---|
| S1 | P1 | Action mask ignores `boundary`; wrap and bounce unreachable by any masked policy | F1 |
| S2 | P1 | Continuous2D applies `movement_delta` twice | F2 |
| S3 | P1 | Over-capacity grid silently disables randomization; affordances at origin until reset; random-deployment packs crash on reset | F3 |
| S4 | P1 | Items never spawn off Grid2D/Grid3D; every placement path is rank 2 | F4, hamlet-6c49488b22 |
| S5 | P2 | Fixed affordance positions never bounds-checked at compile | F5 |
| S6 | P2 | Custom `WAIT` with writes silently dropped on GridND/ContinuousND | F6 |
| S7 | P2 | `action_discretization` required everywhere, consumed only by Continuous2D | F7 |
| S8 | P2 | Velocity lane unbounded (−7 on wrap, world units on continuous) | F8 |
| S9 | P2 | `vision_support: none` unusable; `active_vision: local` residual | F9 |
| S10 | P2 | `[-2]/[-1]` ordering contract false after composition; STRATA.md §5 says code relies on it | F10 |
| S11 | P2 | Engine branches on `velocity_x/y/z/magnitude` variable names | F11 |
| S12 | P3 | `SubstrateActionValidator` tautological; dead `hex` branch | F12 |
| S13 | P3 | No boundary masking at all on GridND/continuous | F13 |
| S14 | P3 | `math`/`cardinal` labels wrong sign; dead label helpers | F14 |
| S15 | P3 | Grid2D bounce lacks clamp; zero-legal-action rows possible; rank limits in constructors | F15, F16, F19 |
| S16 | P3 | Residue: dead `_encode_*`, `get_valid_neighbors`, meter-cost literals, `_layout`, blanket whitelist | F17, F18 |
