
> 🔴 **Recovered from archive 2026-08-26 — STILL OPEN, but HALF OF THIS TICKET IS NOW FALSE.**
>
> Recovered because `docs/product/roadmap.md:446` cites `docs/bugs/JANK-08` as known debt on an
> active roadmap bet, and that link was dangling. Re-verified against source 2026-08-26:
>
> **The `dueling` half is CONFIRMED OPEN, and the roadmap's phrasing — "declared brain flags
> unused by training logic" — is accurate as stated.** The chain: `config/brain_config.py:432`
> declares `dueling` in the architecture `Literal`; shipped packs use it (`configs/simple/`,
> `configs/L5_multi_agent/`, three trial packs); `population/vectorized.py:157` sets
> `self.is_dueling`; and `grep -rn "is_dueling" src/ tests/` returns **exactly one hit — the
> assignment itself. Zero readers.** The update path (`vectorized.py:983-993`) branches only on
> `is_recurrent`.
>
> ⚠️ **Refinement: the dueling *math* is not broken.** `DuelingQNetwork.forward`
> (`agent/networks.py:388-412`) does the V+A aggregation internally and returns a flat
> `[batch, action_dim]` Q, so the shared `gather()` is correct. The defect is a **dead declared
> flag**, not incorrect training — which makes this ticket's own "or remove the flags" branch
> the applicable remedy. For a declarative product, declared-but-inert config is the worst
> failure mode; that is why the roadmap tracks it.
>
> ⛔ **The `structured` half is OBSOLETE — do not act on it.** Three of its claims are now false:
> there is no `network_type` constructor parameter (`VectorizedPopulation.__init__` takes
> `brain_config` only); `"structured"` is not in the architecture `Literal` and has no
> `_build_network` branch, so `StructuredQNetwork` is **unreachable from any config**; and the
> `ObservationActivity` it says the network is built with **no longer exists**, deleted by the
> unit-3 token cut.
>
> **Two instances this ticket misses.** `vectorized.py:160` sets `self.is_set_encoder` — also
> zero readers, and worse, `set_encoder` is now a build-time hard error
> (`vectorized.py:400-407`), so it is a declared-and-refused architecture whose flag is still
> computed. `vectorized.py:163` sets `self.is_token_set`, the only such flag with a real reader
> (`vectorized.py:1308`) — and that is a checkpoint path, not the training path.
>
> **Line drift:** flags `:151` → **157/160/163**; recurrent buffer branch `:210` → **:213**;
> `StructuredQNetwork` `networks.py:418` → **:784**.

Title: VectorizedPopulation structured/dueling flags exist but training path treats all networks identically

Severity: medium
Status: open

Ticket Type: JANK
Subsystem: training/population + agent/networks
Affected Version/Branch: main

Affected Files:
- `src/townlet/population/vectorized.py:151`
- `src/townlet/population/vectorized.py:210`
- `src/townlet/agent/networks.py:418`

Description:
- `VectorizedPopulation` supports multiple architecture types via `brain_config.architecture.type` and `network_type` (feedforward, recurrent, dueling, structured) and sets flags like `self.is_recurrent` and `self.is_dueling`.
- However, the core training loop in `step_population()` and the feedforward Q-update logic treat all non-recurrent architectures identically:
  - The same DQN loss/target computation and action selection code is used regardless of whether the underlying network is “structured” or “dueling”.
  - `self.is_dueling` is set but never consulted when computing Q-values or when interpreting the network output shape.
- For `StructuredQNetwork` in particular:
  - The network is built with `ObservationActivity` to handle semantic groups, but `VectorizedPopulation` simply calls `self.q_network(obs)` and `gather()`s over the resulting Q-values like any other network, with no special handling or tests validating group-wise masking behavior in the population context.

Reproduction:
- Use a `brain_config` whose architecture type is `"dueling"` or construct a `VectorizedPopulation` with `network_type="structured"` when `brain_config` is absent (in theory).
- Observe that:
  - `self.is_dueling` is set accordingly.
  - Training and action selection logic does not branch on `is_dueling` or architecture type; it always assumes a flat Q-vector per agent.

Expected Behavior:
- Either:
  - Architecture-specific flags like `is_dueling` and “structured” modes should drive concrete differences in training logic (e.g., where value vs advantage outputs are combined, or how masking is applied), **or**
  - These flags and legacy `network_type` entry points should be removed in favor of a single, well-tested Brain As Code path.

Actual Behavior:
- The code gives the impression that dueling/structured architectures are first-class citizens in population training, but the training logic is essentially architecture-agnostic and assumes a simple flat Q-output.

Root Cause:
- Architecture diversity was added via `NetworkFactory` and `brain_config`, but the population training loop was only minimally updated—enough to handle recurrent vs non-recurrent, not enough to reflect dueling/structured nuances.

Risk:
- Future changes to dueling or structured heads (e.g., multiple output heads, separate value/advantage) may require training logic that is not in place; the current flags may lull maintainers into thinking the path is fully supported.

Proposed Directions:
- Short-term:
  - Clarify in docs/comments that dueling/structured architectures are currently trained using the same scalar Q-value loss as simple networks, and that their additional structure is entirely inside the network.
  - Optionally, remove `is_dueling` if it remains unused after review, and route all architectural differences through `NetworkFactory`.
- Long-term:
  - Add architecture-aware training hooks if/when the dueling/structured networks adopt non-trivial output semantics that differ from simple Q-heads.

Tests:
- Add targeted tests for StructuredQNetwork and dueling architectures in the context of `VectorizedPopulation`, verifying that output shapes and training steps behave as expected (or explicitly document limitations).

Owner: training/population + agent/networks
Links:
- `docs/tasks/TASK-005-BRAIN-AS-CODE.md`
