"""Null and scripted policy survival on default_curriculum, 8 agents, CPU, one episode each."""
from pathlib import Path
import torch
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

def run(u, level, policy):
    torch.manual_seed(0)
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=8, device=torch.device("cpu"))
    env.reset()
    wait_id = env.action_space.get_action_by_name("WAIT").id
    interact_id = env.action_space.get_action_by_name("INTERACT").id
    deltas = env._movement_deltas  # [A, 2]
    e_idx = env.meter_name_to_index["energy"]
    total = torch.zeros(8); ext = torch.zeros(8); shp = torch.zeros(8); sleeps = 0
    for t in range(1000):
        live = ~env.dones
        if policy == "wait":
            a = torch.full((8,), wait_id, dtype=torch.long)
        elif policy == "random":
            m = env.get_action_masks().float()
            m[~live] = 0; m[~live, wait_id] = 1
            a = torch.multinomial(m, 1).squeeze(1)
        else:  # scripted sleeper: when energy < 0.35 walk to nearest SLEEP and INTERACT, else WAIT
            a = torch.full((8,), wait_id, dtype=torch.long)
            beds = env.affordances["SLEEP"].reshape(-1, 2).to(torch.long)
            pos = env.positions.to(torch.long)
            energy = env.meters[:, e_idx]
            for i in range(8):
                if not live[i] or energy[i] >= 0.35:
                    continue
                d = (beds - pos[i]).abs().sum(1); bed = beds[d.argmin()]
                diff = bed - pos[i]
                if int(diff.abs().sum()) == 0:
                    a[i] = interact_id; continue
                step = torch.sign(diff).to(deltas.dtype)
                match = ((deltas == step).all(1)).nonzero()
                a[i] = int(match[0]) if len(match) else wait_id
        obs, r, dones, info = env.step(a)
        sleeps += sum(1 for v in info["successful_interactions"].values() if v == "SLEEP")
        total += r; c = info["reward_components"]; ext += c["extrinsic"]; shp += c["shaping"]
        if bool(dones.all()):
            break
    print(f"{level} {policy:8s} survival={env.step_counts.tolist()} return(mean)={total.mean():.1f} "
          f"extrinsic={ext.mean():.1f} shaping={shp.mean():.2f} sleeps={sleeps}")

for level in ["L1_full_observability", "L2_partial_observability"]:
    u = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level=level, use_cache=False)
    for policy in ["wait", "random", "sleeper"]:
        run(u, level, policy)
