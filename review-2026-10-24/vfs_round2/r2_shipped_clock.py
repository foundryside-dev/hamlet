"""R2: the shipped default_curriculum clock (day_phase: expression tick, persistent) vs engine time_of_day."""
import math
from harness import *  # noqa

LEVEL = "L3_temporal_mechanics"


@probe("R2 default_curriculum L3 day_phase vs time_of_day")
def main():
    from townlet.universe.compiler import UniverseCompiler
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    u = UniverseCompiler().compile(REPO / "configs" / "default_curriculum", primary_level=LEVEL)
    env = VectorizedHamletEnv.from_universe(u, level_name=LEVEL, num_agents=1, device="cpu")
    wait = action_index(env, "WAIT")

    def decode(obs):
        sin, cos = ve_rows(env, obs, agent=0)["day_phase"][1:3]
        hour = (math.atan2(sin, cos) / (2 * math.pi) * 24) % 24
        return round(hour, 2)

    obs = env.reset()
    print(f"reset: obs day_phase hour={decode(obs)} registry day_phase={reg(env,'day_phase').item():.0f} "
          f"time_of_day={env.time_of_day} global_tick={env.global_tick}")
    for k in range(30):
        obs, r, d, info = env.step(torch.tensor([wait]))
        if k < 3 or k > 26:
            print(f"step{k+1}: obs day_phase hour={decode(obs)} time_of_day(gates opening hours)={env.time_of_day} global_tick={env.global_tick}")
    obs = env.reset()
    print(f"reset#2: obs day_phase hour={decode(obs)} registry day_phase={reg(env,'day_phase').item():.0f} time_of_day={env.time_of_day}")
    obs, *_ = env.step(torch.tensor([wait]))
    print(f"reset#2+step1: obs day_phase hour={decode(obs)} time_of_day={env.time_of_day}")


main()
