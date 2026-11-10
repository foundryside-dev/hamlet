### T18d: Construct all five selected providers and own continuation

**Interfaces:** Implement RP `build_exploration`/`ExplorationRuntime` using the existing explicitly parameterized epsilon/RND/adaptive classes and T18b/T18c constructors. Current provider-tagged state validates complete selected policy before installation; HC receipts retain actual old provider as archival provenance; live execution always uses the repaired authored selector and restores only its matching available subtree.

- [ ] Add `test_factory_constructs_selected_provider`, `test_provider_state_kind_and_scale`: all five real provider classes are selected by the authored drive; rnd fixed scale and adaptive current scale differ as declared; none scale/raw contribution0; epsilon tensors use training epsilon exactly; wrong provider state refuses without mutation. Repeated owned adaptive completion identity advances survival/annealing only once.
- [ ] Run `test_exploration_factory.py` red, including every current strategy save/load and old epsilon/RND/adaptive adapter signatures.
- [ ] Implement the facade/delegation, common reward/service/epsilon/state access and once-only completion ownership; keep old provider APIs callable. Old state records its actual historical provider as archival provenance; approved A restores matching available substate under the repaired authored selector and archives incompatible provider substate without executing the wrong selector or changing recorded old rewards.
- [ ] Run green, asserting all provider defaults/derived values are explicit and scale never hides in a duplicate modifier/replay multiplication.
- [ ] Review and commit `feat(exploration): construct declared providers with owned state`.
