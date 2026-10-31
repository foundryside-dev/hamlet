"""Function admission matrix: context-sensitive functions x authoring contexts (full compile each)."""

from harness import *  # noqa: F403

import sys

CONTEXTS = ["gexpr", "aexpr", "rule_g", "rule_a", "action", "effect", "interaction"]

# (expr, result type) -- the declared variable type used for expression contexts
FUNCS = [
    ("lag(bar.energy, 1)", "scalar"),
    ("delta(bar.energy)", "scalar"),
    ("ema(bar.energy, 0.5)", "scalar"),
    ("moving_average(bar.energy, 3)", "scalar"),
    ("rate_of_change(bar.energy, 3)", "scalar"),
    ("rising_edge(flag)", "bool"),
    ("falling_edge(flag)", "bool"),
    ("lag(tick, 1)", "scalar"),
    ("lag(gstat, 1)", "scalar"),
    ("elapsed_ticks()", "scalar"),
    ("elapsed_ticks(gstat)", "scalar"),
    ("time_in_window(tick, 2, 6)", "bool"),
    ("phase_sin(tick, 24)", "scalar"),
    ("uniform(0.0, 1.0)", "scalar"),
    ("uniform(bar.energy, 1.0)", "scalar"),
    ("normal_dist(0.0, 1.0)", "scalar"),
    ("perlin_noise(tick, 0.0, 1)", "scalar"),
    ("gather(vecv, 0)", "scalar"),
    ("one_hot(1, 3)", "scalar"),
    ("distance_to_affordance(\"EAT\")", "scalar"),
    ("in_range(\"EAT\", 2.0)", "bool"),
    ("distance(vecv, vecv)", "scalar"),
    ("within_radius(vecv, vecv, 1.0)", "bool"),
    ("sigmoid(bar.energy)", "scalar"),
    ("threshold(bar.energy, 0.2, 0.8)", "bool"),
    ("count_where(flag, flag)", "scalar"),
    ("masked_add(bar.energy, 1.0, flag)", "scalar"),
    ("where(flag, 1.0, 0.0)", "scalar"),
    ("argmax(bar.energy, bar.health)", "scalar"),
    ("max_all(bar.energy, bar.health)", "scalar"),
    ("variance(bar.energy, bar.health)", "scalar"),
    ("all(flag, flag)", "bool"),
    ("abs(gstat - 0.5)", "scalar"),
    ("clamp01(gstat)", "scalar"),
    ("gstat * ascalar", "scalar"),
]


def base_decls():
    return [
        decl("flag", type="bool", initial_value=False),
        decl("gstat", scope="global", initial_value=0.5),
        decl("ascalar", initial_value=0.5),
        decl("vecv", type="vec2f", initial_value=[1.0, 2.0]),
        decl("gtarget", scope="global", initial_value=0.0),
        decl("atarget", initial_value=0.0),
        decl("gbool", scope="global", type="bool", initial_value=False),
        decl("abool", type="bool", initial_value=False),
    ]


def build(ctx, expr, rtype):
    name = f"fx_{ctx}"
    tgt_a = "abool" if rtype == "bool" else "atarget"
    tgt_g = "gbool" if rtype == "bool" else "gtarget"
    kw = {}
    if ctx == "gexpr":
        kw["variables"] = lambda v: v["declarations"].extend(base_decls() + [decl("gx", scope="global", type=rtype, initial_value=(False if rtype == "bool" else 0.0), expression=expr)])
    elif ctx == "aexpr":
        kw["variables"] = lambda v: v["declarations"].extend(base_decls() + [decl("ax", type=rtype, initial_value=(False if rtype == "bool" else 0.0), expression=expr)])
    elif ctx == "rule_g":
        kw["variables"] = lambda v: v["declarations"].extend(base_decls())
        kw["rules"] = [rule("r", [rwrite(tgt_g, expr, composition="overwrite")])]
    elif ctx == "rule_a":
        kw["variables"] = lambda v: v["declarations"].extend(base_decls())
        kw["rules"] = [rule("r", [rwrite(tgt_a, expr, composition="overwrite")])]
    elif ctx == "action":
        kw["variables"] = lambda v: v["declarations"].extend(base_decls())
        kw["actions"] = lambda a: add_action(a, "PROBE", [write(tgt_a, expr, composition="overwrite")])
    elif ctx == "effect":
        kw["variables"] = lambda v: v["declarations"].extend(base_decls())

        def effects(e):
            e["effect_definitions"] = [
                {
                    "id": "fx",
                    "scope": "agent",
                    "duration": 5,
                    "reapply_policy": "renew",
                    "observable": True,
                    "on_spawn": [],
                    "on_tick": [{"modify": tgt_a, "value": expr}],
                    "on_despawn": [],
                    "on_interrupt": [],
                }
            ]
            e["max_active_effects"] = {"global": 0, "agent": 1, "item": 0, "affordance": 0}

        kw["effects"] = effects
    elif ctx == "interaction":
        kw["variables"] = lambda v: v["declarations"].extend(base_decls())

        def aff(a):
            a["affordances"][1]["interactions"]["on_start"].append({"modify": tgt_a, "value": expr})

        kw["affordances"] = aff
    return make_pack(name, **kw)


def main():
    ctxs = sys.argv[1:] or CONTEXTS
    for ctx in ctxs:
        for expr, rtype in FUNCS:
            p = build(ctx, expr, rtype)
            u, err = try_compile(p)
            if u:
                print(f"{ctx:12s} | {expr:42s} | OK", flush=True)
            else:
                msg = err.split(" - ", 1)[-1].replace("\n", " ")
                print(f"{ctx:12s} | {expr:42s} | REFUSED {short(msg, 230)}", flush=True)


if __name__ == "__main__":
    main()
