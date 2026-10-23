"""d76684f549 agent-scoped variant on effects_smoke."""
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
u = UniverseCompiler().compile(Path("configs/test/effects_smoke"), primary_level="L0_effects")
env = VectorizedHamletEnv.from_universe(u, level_name="L0_effects", num_agents=2, device="cpu")
env.reset()
m = env.effect_manager
bars = {n: env.meters[:, i] for n, i in env.meter_name_to_index.items()}
m.spawn_effect("energy_regen", target_entity_id=1, intensity=1.0, current_step=0, bars=bars, vfs_registry=env.vfs_registry)
wait = env.action_dim - 1
env.step(torch.full((2,), wait))
print("before reset:", [(e.effect_id, str(e.scope), e.target_entity_id, e.elapsed_ticks, e.duration_remaining) for e in m.get_all_active_effects()])
env.reset()
print("after reset:", [(e.effect_id, str(e.scope), e.target_entity_id, e.elapsed_ticks, e.duration_remaining) for e in m.get_all_active_effects()])
e0 = env.meters[:, env.meter_name_to_index["energy"]].clone()
env.step(torch.full((2,), wait))
print("energy delta per agent after one WAIT post-reset:", (env.meters[:, env.meter_name_to_index["energy"]] - e0).tolist())
