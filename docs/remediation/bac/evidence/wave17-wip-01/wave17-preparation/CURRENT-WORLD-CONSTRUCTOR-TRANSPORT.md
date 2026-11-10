# Current world constructor transport

Source-verified constructor-only candidate R1 tree6f46f449, following the durable world-identity producer. Exactly four counted files total4305 lines: ENV2343, CU1663, EF88, test211. Source hashes: ENV f2b50300ae9d51fa9d6e4b069091ddd1064ce09f3f5e24df1c5917453237c784; CU d8e2734b0845c7d23ac79180a724b216d7c881e079352356f108cb294d2b7384; EF aa1b2cdf00ed25fcc63b57b944876504d77219d147b3265e820ff2ad88b2d2f0; test daad8f762000886969762d52e2a415cc4a853d875621daf24449b9815bc61592. No tracked documentation, source or tests were changed for this contract.

## Actual public entry points

```python
compiled.create_environment(
    *, num_agents: int, level_name: str, device: str | torch.device,
    world_roster: WorldRosterDeclaration, training_seed: int,
    lane_world_ids: tuple[str, ...],
)
env_factory.from_universe(
    env_cls: type[VectorizedHamletEnv], universe: CompiledUniverse,
    *, level_name: str, num_agents: int, device: torch.device | str,
    world_roster: WorldRosterDeclaration, training_seed: int,
    lane_world_ids: tuple[str, ...],
) -> VectorizedHamletEnv
VectorizedHamletEnv.from_universe(
    universe: CompiledUniverse,
    *, level_name: str, num_agents: int, device: torch.device | str,
    world_roster: WorldRosterDeclaration, training_seed: int,
    lane_world_ids: tuple[str, ...],
) -> VectorizedHamletEnv
```

Every displayed argument is required, with no defaults. CU delegates to the ENV classmethod; the classmethod passes its actual cls and universe to standalone EF; EF constructs env_cls. Subclasses therefore retain their actual constructor class through the shared route. EF rejects absent explicit level and normalizes string devices with torch.device, preserving actual torch devices. The classmethod also retains its explicit-level check. No inferred level/seed/world IDs, old-signature probing, automatic bootstrap/reset/activation or fabricated role owners exist.

The same actual roster declaration, integer seed and requested lane tuple are forwarded unchanged. ENV's existing constructor validates declaration type, exact nonempty unique lane IDs, exact positive integer world count, exact nonnegative integer seed and full declared membership/cardinality before construction randomness. Explicit device refusal and selected-level lookup remain constructor responsibilities before later subsystem initialization. Fresh public views expose requested world_ids, zero accepted_episode_seqs, fresh-unbound world_phase and semantic_execution_identity. That identity binds actual compiled.execution_hash, declaration semantic membership and explicit seed; reversed requested lanes do not rewrite the authored declaration or change semantic membership. This does not establish stochastic simulator reorder independence.

Current compiled schema1.42, metadata/native payloads, expected effective-policy validation, authored/selected identities, cache loaders/rebuild behavior and all preexisting affordance/meter helpers are unchanged. This packet adds only constructor transport and the shared pure factory route; it does not re-resolve policy or redesign configuration.

## Verification status and remaining work

Received root R0:88 collected; intended CU/EF unexpected-world_roster TypeError failures and classmethod factory-bypass failure established causal RED, with an existing device=None refusal passing. Received root R1: covering7 PASS; all six constructor-transport mypy errors closed, leaving seven global errors in two oracle/POP files. Root reports fresh Astra actual-source specification and quality APPROVE with no findings. Owner Black/Ruff on the four counted paths PASS. These root/reviewer receipts are attributed results, not executions by this contract author.

At writing, root full193, fresh independent Astra88 and compiler CLI remain pending; no success is inferred. Constructor assertions alone do not qualify actual runtime family breadth, private learned/RNG state, native initialized-owner restoration or restart/E2E behavior. Separately named obligations remain oracle constructor/reset integration; POP reservation/reset-observation/activation consumption; VFS accepted-world identity rather than scalar-reset/row keys; actual T23 immutable run-world-roster.json manifest custody; genuine owner/sink preparation and boundary/restore integration; full runtime/native/learning/restart gates and final BAC acceptance. Passing this bounded packet does not close those tasks.

## Proposed public identity-contract replacement paragraph

The earlier R3 producer receipt described the then-current classmethod directly constructing cls; that routing statement is historical. In current constructor-transport R1 tree6f46f449, VectorizedHamletEnv.from_universe retains required explicit level/world_roster/training_seed/lane_world_ids and delegates its actual cls and universe through standalone env_factory.from_universe. EF preserves explicit-level validation and string/torch device normalization, then forwards the exact declaration, seed and requested lane order into env_cls. CompiledUniverse.create_environment now requires and forwards those same three world inputs. Existing fresh-world validation and lifecycle authority remain in ENV; this route neither bootstraps nor resets/activates an episode. Current ENV source SHA256 is f2b50300ae9d51fa9d6e4b069091ddd1064ce09f3f5e24df1c5917453237c784; the prior R3 direct-construction source hash remains historical provenance.

## Root final qualification receipt
At exactR1tree6f46f449b2c851dc8838e00f48e7fddc8e436dc1/base86ee, all193jointPASS0warnings217.6558wall (88new+54world+51compiled), covering7PASS38.6506wall, freshAstraindependent88PASS12.5377wall/custodyPASS. Counts overlap, notsummed. Allfive non-mypyguardsPASS includingCLI335.9045wall; globalmypyFAIL7errorsoracle/POP only, sixconstructorerrorsclosed. Actualsource/index/import/threads/185source573config13artifact/registrycustodyPASS, allsessionsclosed. This updates earlierpendingstatements; boundedconstructorhandoff, notfullBACrelease.
