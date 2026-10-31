"""hamlet-d76684f549: effects survive env.reset()."""
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv

u = UniverseCompiler().compile(Path("configs/trial002_money_log_gdp"), primary_level="L0_simple")
env = VectorizedHamletEnv.from_universe(u, level_name="L0_simple", num_agents=2, device="cpu")
money_idx = env.meter_name_to_index["money"]
print("affordances:", list(env.affordances.keys()))
env.reset()
pos = env.affordances["WORK"]
env.positions[0] = pos
n = env.action_dim
interact, wait = n - 2, n - 1
acts = torch.full((2,), wait, dtype=torch.long); acts[0] = interact
env.step(acts)
print("after INTERACT money:", env.meters[:, money_idx].tolist())
print("effects before reset:", [(e.effect_id, str(e.scope), e.elapsed_ticks) for e in env.effect_manager.get_all_active_effects()])
env.reset()
print("after reset money:", env.meters[:, money_idx].tolist())
print("effects after reset:", [(e.effect_id, str(e.scope), e.elapsed_ticks) for e in env.effect_manager.get_all_active_effects()])
env.step(torch.full((2,), wait, dtype=torch.long))
print("after WAIT money:", env.meters[:, money_idx].tolist())
print("effects after step:", [(e.effect_id, str(e.scope), e.elapsed_ticks) for e in env.effect_manager.get_all_active_effects()])
