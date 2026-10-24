"""R16: shipped L5_multi_agent — exposed variables nothing writes; pair/affordance storage nothing writes.
NOTE: compiling configs/L5_multi_agent in place refreshed its gitignored .compiled cache (stale schema 1.26)."""
from harness import *  # noqa
from townlet.universe.compiler import UniverseCompiler

u = UniverseCompiler().compile(REPO / "configs/L5_multi_agent", primary_level="L5_multi_agent")
env = build_env(u, num_agents=2, level="L5_multi_agent")
w = action_index(env, "WAIT")
for k in range(3):
    obs, *_ = env.step(torch.tensor([w, w]))
print("census", u.get_level("L5_multi_agent").token_spec.census)
print(ve_rows(env, obs, agent=0))
print("trust", reg(env, "trust").tolist(), "occupied_by", reg(env, "occupied_by").tolist())
