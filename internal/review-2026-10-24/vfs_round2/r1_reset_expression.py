"""R1: reset() does not evaluate expressions; tick clock lags one step behind engine time."""
from harness import *  # noqa

MM2 = {"kind": "minmax", "min": 0.0, "max": 2.0, "clip": True}
MM100 = {"kind": "minmax", "min": 0.0, "max": 100.0, "clip": True}


def vars_(v):
    v["declarations"] += [
        decl("e_energy", exposed=("agent",), normalization=MM2, expression="bar.energy * 2.0"),
        decl("g_persist_tick", scope="global", lifetime="persistent", exposed=("agent",), normalization=MM100, expression="tick"),
        decl("g_episode_tick", scope="global", lifetime="episode", exposed=("agent",), normalization=MM100, expression="tick"),
        decl("tick_mirror", scope="global", lifetime="tick", exposed=("agent",), normalization=MM100, expression="tick + 1.0",
             initial_value=0.0),
    ]


@probe("R1 reset evaluates nothing; clock lag")
def main():
    pack = make_pack("r1_reset_expr", variables=vars_)
    u = compile_pack(pack)
    env = build_env(u, num_agents=2)
    obs = env.reset()

    def show(label, obs):
        r = ve_rows(env, obs, agent=0)
        print(f"{label}: global_tick={env.global_tick} registry tick={reg(env,'tick').item():.0f} "
              f"e_energy reg={reg(env,'e_energy').tolist()} (true 2*energy={[round(2*x,4) for x in env.meters[:, env.meter_name_to_index['energy']].tolist()]}) "
              f"g_persist_tick={reg(env,'g_persist_tick').item():.0f} g_episode_tick={reg(env,'g_episode_tick').item():.0f} "
              f"tick_mirror={reg(env,'tick_mirror').item():.0f}")
        print(f"   obs rows (presence,lane0,lane1): e_energy={r['e_energy']} g_persist_tick={r['g_persist_tick']} "
              f"g_episode_tick={r['g_episode_tick']} tick_mirror={r['tick_mirror']}")

    show("reset#1", obs)
    for k in range(5):
        obs, *_ = step(env, "WAIT")
        show(f"step{k+1}", obs)
    obs = env.reset()
    show("reset#2", obs)
    obs, *_ = step(env, "WAIT")
    show("reset#2+step1", obs)


main()
