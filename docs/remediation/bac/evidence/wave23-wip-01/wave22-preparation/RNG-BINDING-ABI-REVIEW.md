# RNG binding ABI review

Spec verdict: changes required. Quality verdict: changes required before factory implementation.

Blocking: PW03-ABI-PROPOSAL step4 calls rng.snapshot/from_snapshot inside the actual OwnedWorldBackend.construct callback. Both public APIs invoke _quiescent; construct deliberately invokes factory(candidate_rng) inside candidate_rng.activate("model_init"). Consequently even none/count private construction fails before provider allocation. The clone-preflight proposal cannot compose with the required actual lifecycle. Static WS inspection is decisive; no runtime was executed.

Correction: add required-argument WorldRNGState.validate_binding(*, descriptor, world_id, cuda_devices)->None. Permit only quiescence or this exact instance's active context; retain cross-owner fail-fast, broken/coordinator quarantine, CUDA validation, and existing snapshot/restore quiescence. Validate expected and owned descriptor domain invariants and compare existing canonical _identity plus exact requested world and device inventory. Spectator roster/order is deliberately not stable identity. Do not implement duplicate identity hashing, clone the RNG, expose private fields, draw, or capture/install global streams. Factory still validates resolved policy and reconstructed expected descriptor before calling this bridge on the actual callback candidate, then passes that same candidate to real providers.

PW03 steps1–3 and5, required explicit ownership inputs, explicit shared None ownership, separate selector, current five-family capabilities and actual candidate ownership remain appropriate. Descriptor equality at factory preflight must concern expected descriptor made with the caller's roster; bridge comparison must permit different spectator rosters with the same exact requested ID. CPU bridge validation must not initialize/query CUDA absent requested devices. CUDA availability follows existing explicit initialized-domain contract.

The bridge proves binding/composability, not provider learning, bank isolation, runner integration, or full qualification. Those gates remain open.

Review provenance: root confirms this binding-owner was spawned as gpt-6-astra, reasoning_effort=medium, fork_turns=none. No additional agents spawned. Source references: WS (whole file), RP (whole file), PW03 prose proposal/brief and PW03-source-verified-api.md. No additional source file read.

Additional spec correction (root confirmation): proposal step1's blanket obs_dim>0 would narrow existing none-backend zero-column input support and descriptor observation_dim>=0 contract. Preserve nonnegative observation geometry where the selected existing nonrandom provider supports it; RND/adaptive/ICM retain their actual positive-dimension constructor constraints. This bridge does not implement the factory.
