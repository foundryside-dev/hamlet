# P3 phase/role observation matrix v1

- Any fork-guard (guard-only, forbidden Torch/CUDA): start/end use inherited module
  origin/dictionary witness only. No runtime getters. intra_op/inter_op/debug are
  unavailable with explicit reason and raw provenance; torch_observation is
  forbidden-inherited-module-witness, cuda_observation forbidden.
- Torch absent at START: do not import; not-loaded, uninitialized, all three facts
  unavailable with reason, including a role whose later work requires Torch.
- Torch absent at END: observer/uninitialized may retain not-loaded/unavailable;
  a work role (observer=work or torch_policy=work) refuses missing runtime facts.
- Loaded Torch, nonwork/uninitialized role: no Torch functions or getattr hooks;
  inspect already-loaded torch.cuda module dictionary _initialized exact bool.
  Missing/nonbool refuses; no-initialize role refuses True. Facts unavailable with
  reason; loaded-without-calls. Marker False=>uninitialized, True=>initialized.
  This is loaded Torch marker evidence, never proof about every native CUDA context.
- Loaded Torch, work role: getter observations only; exact intra_op/inter_op/debug
  values must equal sealed role. Observe already-loaded cuda.is_initialized;
  no-initialize refuses True. No setters/import/RNG/device discovery calls.
- Every measured fact is exact typed and equals sealed role config; unavailable
  never substitutes for a mandatory work END fact. Real hardware qualification and
  per-case work/initialization transitions remain owned obligations/P4/P5.
