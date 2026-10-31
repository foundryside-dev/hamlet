"""Shared pack builders for the vfs_runtime re-review probes (on top of harness.py)."""
from harness import *  # noqa: F401,F403
from harness import make_pack, compile_pack, build_env, decl, write, reg, step, action_index, probe  # noqa: F401

import torch

PHASE = "apply_transition_rules"


def rules_file(rules):
    return {"transition_rules.yaml": {"version": "1.0", "transition_rules": rules}}


def rule(rid, writes, phase=PHASE, condition=None):
    return {"id": rid, "phase": phase, "condition": condition, "writes": writes}


def rwrite(var, expr, composition="additive_delta", condition=None, clamp=None):
    return {"variable_id": var, "expression": expr, "composition": composition, "condition": condition, "clamp": clamp, "effect": None}


def set_advance(a, writes):
    for ca in a["custom_actions"]:
        if ca["name"] == "ADVANCE":
            ca["writes"] = writes


def effect_file(effects, budgets=None):
    return {"effects.yaml": {"version": "1.0", "effect_definitions": effects,
                             "max_active_effects": budgets or {"global": 2, "agent": 2, "item": 0, "affordance": 2}}}


def effect(eid, on_tick, scope="agent", on_spawn=(), duration=5, on_despawn=()):
    return {"id": eid, "scope": scope, "duration": duration, "reapply_policy": "renew", "observable": True,
            "on_spawn": list(on_spawn), "on_tick": list(on_tick), "on_despawn": list(on_despawn), "on_interrupt": []}


def sea(name, decls=(), writes=None, rules=None, effects=None, aff_cmds=None, budgets=None):
    """Clone the SEA witness with extra declarations, ADVANCE writes, rules, effects, SLEEP on_start commands."""
    def variables(v):
        v["declarations"].extend(decls)

    def affordances(payload):
        for a in payload["affordances"]:
            if a["name"] == "SLEEP":
                a["interactions"]["on_start"] = aff_cmds

    files = {}
    if rules is not None:
        files.update(rules_file(rules))
    if effects is not None:
        files.update(effect_file(effects, budgets))
    pack = make_pack(f"r_{name}", variables=variables, actions=(lambda a: set_advance(a, writes)) if writes is not None else None,
                     affordances=affordances if aff_cmds is not None else None, extra_files=files or None)
    return pack


def compile_sea(name, **kw):
    return compile_pack(sea(name, **kw))


def setreg(env, name, values):
    env.vfs_registry.set(name, torch.tensor(values, dtype=env.vfs_registry.get(name, reader="engine").dtype), writer="engine")


def spawn(env, eid, w, intensity=0.5):
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    return env.effect_manager.spawn_effect(eid, w, intensity, env.global_tick, bars=bars, vfs_registry=env.vfs_registry,
                                           item_manager=env.item_manager, world=w)


def try_compile(label, fn):
    try:
        u = fn()
        print(f"  {label}: COMPILES")
        return u
    except Exception as exc:  # noqa: BLE001
        text = str(exc)
        lines = [l.strip() for l in text.splitlines() if "[" in l and "]" in l] or [text[:300]]
        print(f"  {label}: REFUSED {type(exc).__name__}: {lines[0][:420]}")
        return None


def try_run(label, fn):
    try:
        out = fn()
        print(f"  {label}: RAN -> {out}")
        return out
    except Exception as exc:  # noqa: BLE001
        print(f"  {label}: RUNTIME {type(exc).__name__}: {str(exc)[:400]}")
        return None


def acts(env, name, n=None):
    n = n or env.num_agents
    return torch.full((n,), action_index(env, name), dtype=torch.long)
