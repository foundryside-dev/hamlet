"""R12: `num_agents` is a batch of independent worlds (agents_per_world is always 1; agent token
capacity 0), but global VFS storage is one [1, ...] slab shared by the whole batch: agent 0's
interaction in world 0 changes what agent 1 observes (and is rewarded on) in world 1."""
from harness import *  # noqa

MM = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}


def vars_(v):
    v["declarations"].append(decl("visits", scope="global", exposed=("agent",), normalization=MM, initial_value=0.0))


def affs(a):
    for aff in a["affordances"]:
        if aff["name"] == "SLEEP":
            aff["interactions"]["on_start"].append({"modify": "vfs.visits", "value": "vfs.visits + 1.0"})


def drive(dest):
    edit_yaml(dest / "levels/L0_simple/drive.yaml",
              lambda p: p["drive"]["extrinsic"].update({"variable_bonuses": [{"variable": "visits", "weight": 1.0}]}))


@probe("R12 global state couples 'independent worlds'")
def main():
    pack = make_pack("r12_global_cross_world", variables=vars_, affordances=affs)
    drive(pack)
    u = compile_pack(pack)
    lvl = u.get_level("L0_simple")
    print(f"token census: {lvl.token_spec.census}  (agent capacity 0 => each batch row is its own world)")
    env = build_env(u, num_agents=2)
    obs = env.reset()
    sleep_pos = env.affordances["SLEEP"]
    sleep_pos = sleep_pos[0] if sleep_pos.dim() > 1 else sleep_pos
    env.positions[0] = sleep_pos.to(env.positions.dtype)
    # agent 1 parked far away on a non-affordance cell
    occupied = {tuple((p[0] if p.dim() > 1 else p).tolist()) for p in env.affordances.values()}
    far = next((x, y) for x in range(7, -1, -1) for y in range(7, -1, -1) if (x, y) not in occupied)
    env.positions[1] = torch.tensor(far, dtype=env.positions.dtype)
    interact, wait = action_index(env, "INTERACT"), action_index(env, "WAIT")
    print(f"agent0 @ SLEEP {env.positions[0].tolist()}, agent1 @ {env.positions[1].tolist()} (no affordance)")
    obs, r, d, info = env.step(torch.tensor([interact, wait]))
    rows = ve_rows(env, obs)
    print(f"after [INTERACT, WAIT]: successful_interactions={info['successful_interactions']} visits={reg(env, 'visits').item()}")
    print(f"   visits token row  agent0={rows['visits'][0]}  agent1={rows['visits'][1]}")
    print(f"   reward            agent0={r[0].item():.3f}   agent1={r[1].item():.3f}  (agent1 did nothing in its own world)")


main()
