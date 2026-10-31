import torch
from harness import *
from harness import WT
from townlet.environment.vectorized_env import VectorizedHamletEnv
p = PACKS / "sp_gridnd_4d"
u = compile_pack(p, "L0_test")
env = VectorizedHamletEnv.from_universe(u, level_name="L0_test", num_agents=2, device="cpu")
print("affordances", env.affordances)
print("positions", env.positions)
try:
    env.reset()
except Exception as e:
    print("reset:", e)
print("d_aff", reg(env, "d_aff"), "d_euc", reg(env, "d_euc"))
print("positions", env.positions, env.positions.dtype)
