"""Mechanics round 2: rule->meter crash variants, action write->meter, m2/m5/m14 fixes, M8 spatial, M9 closed-by-variable,
M10 opening hours vs declared period."""

from harness import *  # noqa: F403

import torch

L3 = "L3_temporal_mechanics"


@probe("R1 transition rule targeting a meter at apply_passive_depletion (VFS.md:1441 example, verbatim shape)")
def r1():
    p = make_pack(
        "r1",
        rules=[
            {
                "id": "energy_base_depletion",
                "phase": "apply_passive_depletion",
                "condition": None,
                "writes": [rwrite("bar.energy", "-0.005", clamp=[0.0, 1.0])],
            }
        ],
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    prog = u.get_level(LEVEL).transition_schedule.transition_rule_program
    print("compiled rule targets:", [(r.rule_id, r.variable_id, r.phase) for r in prog.rules])
    env = build_env(u, 2)
    try:
        step(env, "WAIT")
        print("stepped OK energy", meter(env, "energy").tolist())
    except Exception as exc:  # noqa: BLE001
        print("STEP CRASH:", type(exc).__name__, short(str(exc), 200))


@probe("R2 transition rule targeting a meter at apply_transition_rules (VFS.md:1691 low_health_hits_mood shape)")
def r2():
    p = make_pack(
        "r2",
        rules=[rule("low_health_hits_mood", [rwrite("bar.mood", "-0.01", clamp=[0.0, 1.0])], condition="bar.health < 2.0")],
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    try:
        step(env, "WAIT")
        print("stepped OK mood", meter(env, "mood").tolist())
    except Exception as exc:  # noqa: BLE001
        print("STEP CRASH:", type(exc).__name__, short(str(exc), 200))


@probe("R3 action write targeting a meter (VFS.md:1052 / :1274 shape) at runtime")
def r3():
    def actions(a):
        add_action(
            a,
            "REST_IN_BED",
            [
                write("bar.energy", "0.3 * comfort", phase="apply_action_effects", clamp=[0.0, 1.0]),
                write("bar.mood", "0.1 * comfort", phase="apply_action_effects", clamp=[0.0, 1.0]),
            ],
        )

    p = make_pack(
        "r3",
        variables=lambda v: v["declarations"].extend([decl("comfort", initial_value=0.5)]),
        actions=actions,
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    e0 = meter(env, "energy").clone()
    step(env, ["REST_IN_BED", "WAIT"])
    print("d energy", (meter(env, "energy") - e0).tolist(), "mood", meter(env, "mood").tolist())


@probe("M2b ticks since last slept (SLEEP at (0,0), no opening hours)")
def m2b():
    p = make_pack(
        "m2b",
        variables=lambda v: v["declarations"].extend(
            [decl("ticks_since_slept", initial_value=-1.0, expression="where(delta(bar.energy) > 0.0, 0.0, lag(ticks_since_slept, 1) + 1.0)")]
        ),
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    for t in range(2):
        step(env, "WAIT")
        print("WAIT", reg(env, "ticks_since_slept").tolist())
    env.positions[:] = torch.tensor([[0, 0], [0, 0]])
    step(env, ["INTERACT", "WAIT"])
    print("INTERACT@SLEEP agent0", reg(env, "ticks_since_slept").tolist(), "energy", [round(x, 3) for x in meter(env, "energy").tolist()])
    for t in range(2):
        step(env, "WAIT")
        print("WAIT", reg(env, "ticks_since_slept").tolist())


@probe("M5b rising-edge reward falls back after one tick")
def m5b():
    def drive(d):
        d["extrinsic"]["variable_bonuses"] = [{"variable": "rose", "weight": 5.0}]

    p = make_pack(
        "m5b",
        variables=lambda v: v["declarations"].extend(
            [
                decl("low_energy", type="bool", initial_value=False, expression="bar.energy < 0.95"),
                decl("rose", type="bool", initial_value=False, expression="rising_edge(low_energy)"),
            ]
        ),
        drive=drive,
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    out = []
    for t in range(9):
        obs, rew, done, info = step(env, "WAIT")
        out.append((int(reg(env, "tick")[0]), reg(env, "rose")[0].item(), round(rew[0].item(), 2)))
    print(out)


@probe("M14b private variable drives reward, no observation row")
def m14b():
    def drive(d):
        d["extrinsic"]["variable_bonuses"] = [{"variable": "secret", "weight": 1.0}]

    def actions(a):
        add_action(a, "PRAY", [write("secret", "1.0")])

    p = make_pack(
        "m14b",
        variables=lambda v: v["declarations"].extend([decl("secret", readable=("engine",), initial_value=0.0)]),
        actions=actions,
        drive=drive,
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    spec = u.get_level(LEVEL).token_spec
    print("census", spec.census, "ve rows", [r for r in spec.row_layout() if r[0] == "variable_element"])
    base = None
    for t in range(3):
        obs, rew, done, info = step(env, ["PRAY", "WAIT"])
        print(f"secret={reg(env,'secret').tolist()} reward={[round(x,3) for x in rew.tolist()]} reward gap={round((rew[0]-rew[1]).item(),3)}")
    try:
        env.vfs_registry.get("secret", reader="agent")
        print("agent read ALLOWED (bad)")
    except PermissionError as exc:
        print("agent read refused:", short(str(exc), 120))


@probe("M8 distance to nearest food as an observed agent expression (spatial functions in a variable expression)")
def m8():
    for expr in ("distance_to_affordance(\"EAT\")", "in_range(\"EAT\", 2.0)", "min(distance_to_affordance(\"EAT\"), distance_to_affordance(\"COOK\"))"):
        p = make_pack(
            "m8",
            variables=lambda v: v["declarations"].extend(
                [decl("d_food", initial_value=0.0, expression=expr, exposed=["agent"], normalization={"kind": "minmax", "min": 0.0, "max": 16.0, "clip": True})]
            ),
        )
        u, err = try_compile(p)
        print(expr, "->", "COMPILED" if u else "REFUSED " + short(err, 500))


@probe("M9 affordance closed by a variable: any declared spelling?")
def m9():
    for key, val in (
        ("availability", {"variable": "shop_open"}),
        ("available_when", "shop_open"),
        ("condition", "shop_open"),
        ("enabled_when", "shop_open"),
        ("availability", [{"meter": "energy", "min": 0.5}]),
    ):
        def aff(a, key=key, val=val):
            a["affordances"][0][key] = val

        p = make_pack(
            "m9",
            variables=lambda v: v["declarations"].extend([decl("shop_open", scope="global", type="bool", initial_value=True)]),
            affordances=aff,
        )
        u, err = try_compile(p)
        print(key, "->", "COMPILED" if u else "REFUSED " + short(err, 220))


@probe("M10 opening hours keyed to a declared clock period of 48 (L3): EAT open 2..6")
def m10():
    def variables(v):
        for d in v["declarations"]:
            if d["id"] == "day_phase":
                d["normalization"]["period"] = 48

    def aff(a):
        for x in a["affordances"]:
            if x["name"] == "EAT":
                x["opening_hours"] = {"enabled": True, "schedule": [{"start": 2, "end": 6}]}

    p = make_pack("m10", variables=variables, affordances=aff, level=L3)
    u, err = try_compile(p, L3)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 1, L3)
    print("day_length", env.day_length)
    opens = []
    for t in range(52):
        h = env.time_of_day
        opens.append((int(env.global_tick), h, env._is_affordance_open("EAT")))
        step(env, "WAIT")
    print("ticks where EAT is open:", [x[0] for x in opens if x[2]])
    print("(hour, open) at 24..31:", [(x[1], x[2]) for x in opens[24:32]])
    spec = u.get_level(L3).token_spec
    print("affordance payload schema has open_hour lanes:", [f for f in spec.types[2].payload_features if f.startswith("open_hour")][:3], "... count", sum(1 for f in spec.types[2].payload_features if f.startswith("open_hour")) if hasattr(spec.types[2], "payload_features") else "n/a")


@probe("M10b literal day_length: 48 with a 24-period clock, and opening hour 'end' > 28")
def m10b():
    def aff(a):
        for x in a["affordances"]:
            if x["name"] == "EAT":
                x["opening_hours"] = {"enabled": True, "schedule": [{"start": 30, "end": 40}]}

    p = make_pack("m10b", affordances=aff, level=L3)
    u, err = try_compile(p, L3)
    print("start 30 end 40 ->", "COMPILED" if u else "REFUSED " + short(err, 300))


if __name__ == "__main__":
    import sys

    names = sys.argv[1:] or ["r1", "r2", "r3", "m2b", "m5b", "m14b", "m8", "m9", "m10", "m10b"]
    for n in names:
        globals()[n]()
