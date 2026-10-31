"""Isolation + determinism on a pack that exercises every runtime path at once:
rules (global/agent/affordance), effects with sample + history-free reads, history operators (lag/ema/delta/rising_edge),
random_uniform init (tick + episode lifetime), agent_ref writes, tick-lifetime action write, exposed expressions.

Usage: p_isolation.py build        -> writes the pack
       p_isolation.py run N STEPS SEED MODE OUT   (MODE A: all worlds cycle; B: world 0 perturbed)
       p_isolation.py trace N STEPS SEED          -> world-0 per-step trace (for N=1 vs N>1)
"""
from common import *  # noqa
import hashlib
import sys
import torch

NORM = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}


def build():
    decls = [
        decl("g", scope="global", initial_value=0.0),
        decl("av", initial_value=0.0, exposed=("agent",), normalization=NORM),
        decl("aff_v", scope="affordance", initial_value=0.0),
        decl("aref", type="agent_ref", initial_value=None),
        decl("flag", type="bool", initial_value=False),
        decl("hit", lifetime="tick", initial_value=0.0, exposed=("agent",), normalization=NORM),
        decl("noise_t", type="tensor1d", shape=[2], lifetime="tick", initial_value_mode="random_uniform", initial_value_params={"low": 0.0, "high": 1.0}),
        decl("noise_e", type="tensor1d", shape=[2], lifetime="episode", initial_value_mode="random_normal", initial_value_params={"mean": 0.0, "std": 1.0}),
        decl("sv", initial_value=0.0),
        decl("pers", lifetime="persistent", initial_value=0.0),
        # expressions
        decl("lagged", initial_value=0.0, expression="lag(av, 2) + delta(bar.energy)", exposed=("agent",), normalization=NORM),
        decl("smooth", initial_value=0.0, expression="ema(bar.energy, 0.3) + moving_average(g, 3)", exposed=("agent",), normalization=NORM),
        decl("edge", type="bool", initial_value=False, expression="rising_edge(flag)"),
        decl("acc", initial_value=0.0, expression="where(edge, 0.0, lag(acc, 1) + 1.0)"),
        decl("gexp", scope="global", initial_value=0.0, expression="g * 2.0 + tick"),
        decl("ag", initial_value=0.0, expression="gexp + av + public_state", exposed=("agent",), normalization=NORM),
    ]
    writes = [
        write("public_state", "1.0"),
        write("hit", "1.0", composition="overwrite"),
        write("av", "bar.energy * 2.0", composition="additive_delta", condition="public_state > 1.0"),
        write("aref", "agent_id", composition="overwrite"),
        write("flag", "not flag", composition="overwrite"),
    ]
    rules = [
        rule("rg", [rwrite("g", "1.0")]),
        rule("raff", [rwrite("aff_v", "g + aff_v * 0.5", composition="additive_delta", clamp=[0.0, 50.0])]),
        rule("rsv", [rwrite("sv", "sv * 0.5 + bar.energy", composition="overwrite")], phase="apply_passive_depletion"),
        rule("rp", [rwrite("pers", "1.0")], condition="flag"),
        rule("rprio", [rwrite("av", "100.0", composition="priority_write")], condition="av > 1000.0"),
    ]
    effects = [
        effect("e1", [{"sample": "uniform", "params": {"min": 0.0, "max": 1.0}, "store_in": "sv"},
                      {"modify": "av", "value": "av + intensity"}], scope="agent", duration=3),
        effect("eg", [{"modify": "g", "value": "g + 10.0"}], scope="global", duration=2),
    ]
    aff_cmds = [{"modify": "bar.energy", "value": "bar.energy + 0.3"}, {"spawn_effect": "e1", "target": "target", "intensity": "0.5"},
                {"modify": "av", "value": "av + 1.0"}]
    return sea("iso", decls=decls, writes=writes, rules=rules, effects=effects, aff_cmds=aff_cmds)


def rng_hash():
    return hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest()[:16]


def snapshot(env, w, obs, rewards, dones):
    r = env.vfs_registry
    return {
        "obs": obs[w].clone(), "reward": float(rewards[w]), "done": bool(dones[w]),
        "meters": env.meters[w].clone(), "pos": env.positions[w].clone(),
        "registry": {vid: r.get(vid, reader="engine")[w].clone() for vid in r.variables},
        "effects": tuple(sorted((e.effect_id, e.scope.value, int(e.duration_remaining), int(e.elapsed_ticks), float(e.intensity))
                                for e in env.effect_manager.effects_in_world(w))),
    }


def run(n, steps, seed, mode, out):
    from townlet.determinism import seed_all
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    from townlet.universe.compiler import UniverseCompiler
    pack = PACKS / "r_iso"
    seed_all(seed)
    u = UniverseCompiler().compile(pack, primary_level="L0_simple", use_cache=False)
    env = VectorizedHamletEnv(universe=u, level_name="L0_simple", num_agents=n, device="cpu")
    seed_all(seed)
    obs = env.reset()
    names = {a.name: a.id for a in env.action_space.actions}
    cycle = [names["WAIT"], names["ADVANCE"], names["UP"], names["ADVANCE"], names["RIGHT"], names["WAIT"]]
    ids = [a.id for a in env.action_space.actions]
    zero = torch.zeros(n)
    snaps = [{"t": -1, "rng": rng_hash(), "worlds": [snapshot(env, w, obs, zero, env.dones) for w in range(n)]}]
    for t in range(steps):
        a = torch.tensor([cycle[(t + w) % len(cycle)] for w in range(n)], dtype=torch.long)
        if mode == "B":
            a[0] = ids[t % len(ids)]
            if env.action_space.actions[t % len(ids)].name == "INTERACT" or t % 4 == 0:
                env.positions[0] = env.affordances["SLEEP"].to(env.positions.dtype)
                a[0] = names["INTERACT"]
            if t % 5 == 2:
                spawn(env, "eg", 0)
        obs, rewards, dones, info = env.step(a)
        snaps.append({"t": t, "rng": rng_hash(), "worlds": [snapshot(env, w, obs, rewards, dones) for w in range(n)]})
    obs = env.reset()
    snaps.append({"t": 10_000, "rng": rng_hash(), "worlds": [snapshot(env, w, obs, zero, env.dones) for w in range(n)]})
    for t in range(4):
        a = torch.tensor([cycle[(t + w) % len(cycle)] for w in range(n)], dtype=torch.long)
        obs, rewards, dones, info = env.step(a)
        snaps.append({"t": 10_001 + t, "rng": rng_hash(), "worlds": [snapshot(env, w, obs, rewards, dones) for w in range(n)]})
    torch.save(snaps, out)
    print(f"{mode}: N={n} steps={steps} dones={env.dones.tolist()}")


if __name__ == "__main__":
    if sys.argv[1] == "build":
        p = build()
        compile_pack(p)
        print("built", p)
    elif sys.argv[1] == "run":
        n, steps, seed, mode, out = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6]
        run(n, steps, seed, mode, out)
