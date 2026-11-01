# Future T15 interface/preparation provenance

This is bounded source-verified preparation or technical design review, not T15 implementation, executable acceptance or owner approval for any reduction. Original T15-constructor-factory-bridge.md SHA256 `ffe98bb8fa69aef0c1f338d4816375530e69499956999bb2351ace574e81b789`; its actual earlier read/runtime identities remain explicit. T14 status in the body records its historical preparation time.

# Coordinator source-verified factory bridge

Root independently opened exactly one complete bridge implementation for this receipt: `src/townlet/environment/env_factory.py`, 81 lines, SHA256 `ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232`, at HEAD `b3003550b7c1dad76a52e596b2af01658fa2b92d`. No imports/runtime or source/index changes. The five-file supplier worker must consume this as prose and must not open a sixth source.

`from_universe(env_cls, universe, *, level_name, num_agents, device)` at lines56–81 validates only explicit level_name/device conversion and returns `env_cls(universe=universe, level_name=level_name, num_agents=num_agents, device=torch_device)` directly. It does not manufacture a wrapper, substitute a fake environment/training carrier, bypass the supplied class initializer or remove level.training. Combined with the supplier worker's separately verified real VectorizedHamletEnv classmethod/base initializer, this closes the visible delegation boundary. It does not independently validate external CompiledUniverse DTO implementations or claim arbitrary duck-typed objects are compiled environments.

The factory source hash and tracked status remain unchanged. This source bridge is static evidence, not test/constructor runtime acceptance or a new capability policy.
