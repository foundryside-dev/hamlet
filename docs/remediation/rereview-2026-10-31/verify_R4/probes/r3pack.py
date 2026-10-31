"""R3 verifier: random-draw pack on items_smoke (items + effects + VFS draws everywhere)."""

from __future__ import annotations

from harness import *  # noqa: F401,F403
from harness import WT, make_pack, decl, write, rule, rwrite, add_action, compile_pack

import torch

ITEMS_BASE = WT / "configs" / "test" / "items_smoke"
ILEVEL = "L0_smoke"
NORM = {"kind": "minmax", "min": -5.0, "max": 15.0, "clip": True}


def rand_decls(extra=()):
    return [
        decl("g_rand", scope="global", initial_value=0.0, expression="uniform(0.0, 1.0)"),
        decl("a_rand", initial_value=0.0, expression="normal_dist(bar.energy, 0.1)", exposed=("agent",), normalization=NORM),
        decl("a_two", initial_value=0.0, expression="uniform() + 10.0 * uniform()"),
        decl("a_read2", initial_value=0.0, expression="a_rand + a_rand"),
        decl("g_target", scope="global", initial_value=0.0),
        decl("a_target", initial_value=0.0),
        decl("a_seen", initial_value=0.0),
        decl("sv", initial_value=0.0),
        *extra,
    ]


def build(name="r3rnd", extra_decls=(), extra_rules=(), when="g_rand > 0.3", decl_order_reverse=False):
    decls = rand_decls(extra_decls)
    if decl_order_reverse:
        decls = list(reversed(decls))

    def variables(v):
        v["declarations"].extend(decls)

    def actions(a):
        for ca in a["custom_actions"]:
            if ca["name"] == "WAIT":
                ca["writes"] = [write("a_target", "uniform(-1.0, 0.0)", composition="overwrite")]

    def affordances(payload):
        for aff in payload["affordances"]:
            if aff["name"] == "energy_station":
                aff["interactions"]["on_start"].append({"spawn_effect": "e1", "target": "target", "intensity": "0.5"})

    def effects(e):
        e["effect_definitions"] = [
            {
                "id": "e1",
                "scope": "agent",
                "duration": 4,
                "reapply_policy": "renew",
                "observable": True,
                "on_spawn": [],
                "on_tick": [
                    {"sample": "uniform", "params": {"min": 0.0, "max": 1.0}, "store_in": "sv"},
                    {"modify": "bar.energy", "value": "bar.energy - 0.01 * uniform()"},
                ],
                "on_despawn": [],
                "on_interrupt": [],
            }
        ]
        e["max_active_effects"] = {"global": 0, "agent": 2, "item": 0, "affordance": 0}

    rules = [
        rule("rg", [rwrite("g_target", "uniform(0.0, 3.0)", composition="overwrite")], condition="tick % 4 == 0"),
        rule("rseen", [rwrite("a_seen", "a_rand", composition="overwrite")]),
        *extra_rules,
    ]
    pack = make_pack(name, variables=variables, actions=actions, affordances=affordances, effects=effects, rules=rules, base=ITEMS_BASE, level=ILEVEL)
    # periodic apple respawn gated on a random expression variable
    import yaml

    p = pack / "levels" / ILEVEL / "items.yaml"
    payload = yaml.safe_load(open(p))
    payload["items"][0]["schedule"]["period"] = 3
    payload["items"][0]["when"] = when
    payload["items"][2]["schedule"]["period"] = 5
    yaml.safe_dump(payload, open(p, "w"), sort_keys=False)
    return pack


def make_env(pack, n, seed, level=ILEVEL):
    from townlet.determinism import seed_all
    from townlet.environment.vectorized_env import VectorizedHamletEnv

    seed_all(seed)
    u = compile_pack(pack, level)
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=n, device="cpu")
    seed_all(seed)
    obs = env.reset()
    return env, obs


def snap(env, w, obs, rewards, dones):
    r = env.vfs_registry
    items = sorted((it.item_type, it.instance_id - 0, tuple(it.position) if it.position is not None else None, tuple(sorted(it.holder_agent_ids))) for it in env.item_manager.items_in_world(w)) if env.item_manager else ()
    eff = tuple(sorted((e.effect_id, int(e.duration_remaining), float(e.intensity)) for e in env.effect_manager.effects_in_world(w))) if env.effect_manager else ()
    return {
        "obs": obs[w].clone(),
        "reward": float(rewards[w]),
        "done": bool(dones[w]),
        "meters": env.meters[w].clone(),
        "pos": env.positions[w].clone(),
        "registry": {vid: r.get(vid, reader="engine")[w].clone() for vid in r.variables},
        "items": items,
        "effects": eff,
    }
