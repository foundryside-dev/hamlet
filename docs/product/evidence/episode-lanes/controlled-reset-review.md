# Astra scoped review: PDR-0160

**Verdict: APPROVE the second CPU-only controlled-reset comparison recipe.** No blocking defect in the proposed comparison control. This approves producing and qualifying a fresh recipe family; it does not accept the implementation, qualify an unrun bank, repair production RNG isolation, or excuse the original failed banks.

Reviewed PDR SHA-256: `229c529c7a048115afe58c44bc5aff7fadb9c4973b278e8fa8d0e94a46c7d4e0`.
Approved-plan SHA-256 confirmed: `159ab22fc58bb43a5c2e9756c5bfbc9546f10ecb1d5a42145a357b104acb1b6c`.
Execution HEAD during evidence capture: `5141b7bd613de259bc6a0ab4d81e1235506db06a`; shared worktree contains concurrent implementation edits. This is not a clean-candidate review. Full consulted file/source/bank hashes are retained in `checks.json`. Source navigation used the fresh primary Loomweave map at `880f9c90f65aa646a0da04d7ca2ef92e48f85caa`, followed by reading the execution worktree's actual bodies.

The intervention is causally appropriate for the stated question: compare accounting, normalization, composition and target behavior under matched authored world inputs while allowing real learner trajectories to diverge. It blocks the replay-size → shared Torch RNG → next reset layout path externally. Restoring each run's own incoming CPU RNG preserves that run's learner state across the intervention; it does not force candidate learner RNG to equal the parent's. Both sides receive the same changed recipe, including the parent and intermediate cuts. Numerical results from this recipe must not be presented as equivalent to an uncontrolled production run.

The PRD explicitly permits a PDR when an excluded seam becomes a prerequisite (`docs/product/prds/0005-truthful-episode-lanes.md:104,126`), while requiring exact causal attribution. The amendment preserves the original failed experiment and prospectively defines a fresh control (`PDR-0160:38–69`). No source RNG repair is needed to answer this bounded comparison question. This satisfies the scope boundary without weakening world-input equality or retroactively authorizing the original mismatch.

## Confidence Assessment

**Overall Confidence: High** for recipe soundness; final numerical qualification remains unassessed.

| Finding | Confidence | Basis |
|---|---|---|
| Original standard E3→P1 bank violates input identity | High | Independently recomputed 80 predecessor and 80 successor hash changes for each Double-DQN setting; other six recipes have zero. Actions, ticks, dones and config inventories remain exact. `check.py` / `checks.json`. |
| Retained countercontrols support shared CPU RNG coupling | High | Both standard sides agree after samples 1–2 and diverge after sample 3; buffer sizes are `[2,4,6,8,10]` versus `[2,4,5,6,7]`. Candidate reset supplied with parent RNG exactly matches parent reset, including positions, affordances, meters and observations. PER has unchanged Torch RNG and matching natural resets. Independently asserted all four JSON records. |
| Source matches the proposed explanation | High | `src/townlet/training/replay_buffer.py:299` uses real `torch.randperm`; PER uses `np.random.choice` at `prioritized_replay_buffer.py:298`; population reset invokes real environment reset at `population/vectorized.py:315`; environment reset initializes layout/positions at `environment/vectorized_env.py:743`. |
| CPU fork restores the caller and creates common exogenous reset randomness | High | Inspected installed PyTorch 2.11.0 implementation; independent small probe starts from retained parent/P1 post-episode states, draws under seed 43, verifies common draws and exact caller CPU-state restoration. No new numerical bank generated. |
| New full bank will satisfy all acceptance coordinates | Insufficient Data | Not produced at review time; approval is prospective and conditional on the existing qualification contract. |

## Risk Assessment

**Implementation Risk: Low** for an external CPU-only fixture; **Reversibility: Easy** by abandoning the new recipe while retaining artifacts.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Treating matched-reset evidence as natural-production behavior or RNG repair | High | Medium | Label the recipe and every result as controlled CPU evidence; retain original failure; keep production RNG isolation separately scoped. |
| Applying `fork_rng(devices=[])` outside CPU fixtures | Medium | Medium if reused | Explicitly say “caller CPU Torch RNG state.” `torch.manual_seed` seeds devices generally, whereas this context saves/restores CPU only. Existing helper fixes environment, learner and RND to CPU. No CUDA restoration claim is approved. |
| Changing instruments between source cuts, rewriting original banks, or admitting whole streams | High | Low with prescribed receipts | Freeze/hash the new recipe instrument before execution, use it identically for all five source cuts, preserve old manifests/banks, refuse any unexplained coordinate or changed world input. |
| Missing real sample/target or normalization proof behind reconciled totals | High | Medium | Keep independent 63-row eligible ledger, 18 once-only completions, RMS/DAC references, actual sampler identities and terminal/nonterminal/truncation target witnesses required by the original contract. |

## Information Gaps

1. New controlled-reset instrument, source-cut receipts and final candidate are not yet available; this is intentional preregistration review.
2. The population agent's combined `attribution-review.json/md` was not yet present when inspected. The four underlying countercontrol files and original eight-bank comparisons were directly checked instead.
3. I did not independently re-execute all real population countercontrol episodes. Their exact retained values were validated, their source explanation checked, and the CPU restoration mechanism independently probed. Final review must examine the complete produced bank and candidate.

## Caveats & Required Follow-ups

Before relying on the new family for qualification:

- Retain this verdict and freeze the amendment/new instrument identity before creating its parent or candidate bank. Preserve original registration and failed banks byte-for-byte.
- Make the CPU-only interpretation explicit in the amendment/receipt. This is a documentation clarification of the inherited CPU recipe, not a requirement to implement device RNG isolation.
- Execute one identical, source-resolved instrument against clean parent, E2, E3, P1 and final candidate. Record CPU RNG restoration, reset seeds and all world-input/config identities; reject mismatch.
- Preserve the original typed finite, per-coordinate causal contract. Continue requiring actual optimizer updates/parameter changes, 63 eligible rows, 18 completions, real samples and independent RMS/DAC/target checks. Review mutated negative controls and all PRD gates at final acceptance.
- Interpret reset-state restoration as a deliberately changed comparison recipe. It removes reset consumption from the learner RNG stream compared with the old family; that is acceptable only because every compared source uses the same new fixture and the old family remains separately reported.

Assumptions: all eight fixtures remain CPU-only, actions remain authored, reset is called after legitimate completion, and no producer is replaced. Limitations: no CUDA, convergence, arbitrary-world reset isolation, full implementation, delivery or recovery-exit verdict is supplied here.
