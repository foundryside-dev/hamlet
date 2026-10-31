"""Generic differential: two runs differing only in world 0's actions; worlds 1..N-1 must match.

Usage: diff_run2.py <config_dir> <level> <N> <steps> <seed> <A|B> <out.pt>
World 0 in run B cycles through EVERY action id (teleporting onto affordances for INTERACT and
onto ground items for GET); worlds 1..N-1 cycle WAIT + movement (or WAIT + custom actions).
"""

import hashlib
import sys
from pathlib import Path

import torch

from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

config_dir, level, n, steps, seed, mode, out = sys.argv[1:8]
n, steps, seed = int(n), int(steps), int(seed)

seed_all(seed)
universe = UniverseCompiler().compile(Path(config_dir), primary_level=level, use_cache=False)
env = VectorizedHamletEnv(universe=universe, level_name=level, num_agents=n, device="cpu")
seed_all(seed)
obs = env.reset()
mgr = env.item_manager
inv = env.item_inventory
reg = env.vfs_registry
C = env.items_per_world if (mgr is not None and hasattr(env, "items_per_world")) else 0
actions_all = list(env.action_space.actions)
names = {a.name: a.id for a in actions_all}
ids = [a.id for a in actions_all]
wait = names["WAIT"]
move_names = [nm for nm in ("UP", "DOWN", "LEFT", "RIGHT", "FORWARD", "BACKWARD") if nm in names]
if not move_names:
    move_names = [a.name for a in actions_all if a.name.startswith("MOVE")]
custom = [a.id for a in actions_all if a.name not in ("WAIT", "INTERACT") and a.name not in move_names and not a.name.startswith(("GET", "USE_SLOT", "DROP_SLOT"))]
if move_names:
    base_cycle = [wait, names[move_names[0]], names[move_names[1 % len(move_names)]], wait, names[move_names[2 % len(move_names)]], wait]
else:
    base_cycle = [wait] + custom[:3] + [wait]
aff_names = list(env.affordances.keys()) if hasattr(env, "affordances") and isinstance(env.affordances, dict) else []


def rng_hash():
    return hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest()[:16]


def world_snapshot(w, obs, rewards, dones):
    snap = {
        "obs": obs[w].clone(),
        "reward": float(rewards[w]),
        "done": bool(dones[w]),
        "meters": env.meters[w].clone(),
        "pos": env.positions[w].clone() if env.positions is not None and env.positions.dim() > 1 else None,
        "registry": {vid: reg.get(vid, reader="engine")[w].clone() for vid in reg.variables if reg.get(vid, reader="engine").dim() > 0},
    }
    if hasattr(env, "affordance_overrides") and env.affordance_overrides is not None:
        try:
            snap["aff_overrides"] = dict(env.affordance_overrides[w])
        except Exception:  # noqa: BLE001
            pass
    if getattr(env, "effect_manager", None) is not None:
        snap["effects"] = tuple(sorted(
            (e.effect_id, e.scope.value, int(e.duration_remaining), int(e.elapsed_ticks), float(e.intensity), e.target_entity_id - (w * C if e.scope.value == "item" else 0))
            for e in env.effect_manager.effects_in_world(w)
        ))
        pend = []
        for tick, items in env.effect_manager.scheduler.pending.items():
            for it in items:
                eff = it.context_overrides.get("effect")
                ew = eff.world if eff is not None else None
                if ew == w:
                    pend.append((tick - env.global_tick, it.scope, eff.effect_id))
        snap["pending"] = tuple(sorted(pend))
    if mgr is not None and hasattr(mgr, "worlds"):
        st = mgr.worlds[w]
        items = []
        for item in mgr.items_in_world(w):
            held = item.instance_id in st.held
            items.append((item.item_type, tuple(item.position), held, item.duration_remaining, item.vfs_index - w * C, tuple(sorted(item.holder_agent_ids))))
        snap["items"] = tuple(items)
        snap["inv_slots"] = inv.slots[w].clone() if inv is not None else None
        snap["arena"] = reg.item_vfs[w * C: (w + 1) * C].clone() if reg.item_vfs is not None else None
        snap["profiles"] = tuple(sorted((r - w * C, p) for r, p in reg.item_vfs_index_to_profile.items() if reg.item_world(r) == w))
        snap["timers"] = tuple(sorted(st.respawn_timers.items()))
        snap["cooldowns"] = tuple(sorted(st.cooldown_until.items()))
        snap["counts"] = tuple(sorted(st.rule_spawn_counts.items()))
        snap["sched"] = tuple(sorted(st.next_scheduled_tick.items()))
        snap["free"] = tuple(sorted(r - w * C for r in st.free_rows))
        snap["instance_ids"] = tuple(i.instance_id for i in mgr.items_in_world(w))
    return snap


def teleport(w, pos):
    if env.positions is None or env.positions.dim() < 2:
        return
    env.positions[w] = torch.as_tensor(pos, dtype=env.positions.dtype)


def perturb_world0(t):
    a = ids[t % len(ids)]
    name = actions_all[t % len(ids)].name
    if name == "INTERACT" and aff_names:
        p = env.affordances[aff_names[(t // len(ids)) % len(aff_names)]]
        teleport(0, (p[0] if p.dim() > 1 else p).tolist())
    elif name.startswith("GET") and mgr is not None and hasattr(mgr, "worlds"):
        ground = sorted(mgr.worlds[0].active.values(), key=lambda i: i.instance_id)
        if ground:
            teleport(0, ground[0].position)
    elif t % 3 == 0 and aff_names:
        # also interact with a rotating affordance on every third step for more coverage
        p = env.affordances[aff_names[t % len(aff_names)]]
        teleport(0, (p[0] if p.dim() > 1 else p).tolist())
        return names["INTERACT"] if "INTERACT" in names else a
    return a


snaps = []
zero = torch.zeros(n)
snaps.append({"t": -1, "rng": rng_hash(), "worlds": [world_snapshot(w, obs, zero, env.dones) for w in range(n)]})
for t in range(steps):
    actions = torch.tensor([base_cycle[(t + w) % len(base_cycle)] for w in range(n)], dtype=torch.long)
    if mode == "B":
        actions[0] = perturb_world0(t)
    obs, rewards, dones, info = env.step(actions)
    snaps.append({"t": t, "rng": rng_hash(), "worlds": [world_snapshot(w, obs, rewards, dones) for w in range(n)]})
obs = env.reset()
snaps.append({"t": 10_000, "rng": rng_hash(), "worlds": [world_snapshot(w, obs, zero, env.dones) for w in range(n)]})
torch.save(snaps, out)
print(f"{mode}: steps={steps} dones={env.dones.tolist()} actions={len(ids)} affs={len(aff_names)}")
