"""Designer mechanics, VFS-only ones: 1 night hunger, 2 ticks since ate, 3 cooldown (record half + gated writes),
4 regen toward cap, 5 rising-edge reward, 6 persistent, 7 weather every K, 13 terminal on variable,
14 private reward, 15 moving average exposed."""

from harness import *  # noqa: F403

import torch


@probe("M1 hunger decays faster at night (rule on bar.satiation gated by a global is_night expression)")
def m1():
    p = make_pack(
        "m1",
        variables=lambda v: v["declarations"].extend(
            [decl("is_night", scope="global", type="bool", initial_value=False, expression="tick % 24 >= 18 or tick % 24 < 6")]
        ),
        rules=[rule("night_hunger", [rwrite("bar.satiation", "-0.05", clamp=[0.0, 1.0])], condition="is_night")],
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    prev = meter(env, "satiation").clone()
    for t in range(8):
        step(env, "WAIT")
        cur = meter(env, "satiation").clone()
        print(f"tick={int(reg(env,'tick')[0])} is_night={reg(env,'is_night').tolist()} dsat={(cur-prev).tolist()}")
        prev = cur
    # jump to night: set tick via many waits
    for t in range(12):
        step(env, "WAIT")
    prev = meter(env, "satiation").clone()
    for t in range(3):
        step(env, "WAIT")
        cur = meter(env, "satiation").clone()
        print(f"tick={int(reg(env,'tick')[0])} is_night={reg(env,'is_night').tolist()} dsat={(cur-prev).tolist()}")
        prev = cur


@probe("M2 ticks since last ate (variables.md:313 pattern; EAT via INTERACT at EAT position)")
def m2():
    p = make_pack(
        "m2",
        variables=lambda v: v["declarations"].extend(
            [
                decl(
                    "ticks_since_ate",
                    initial_value=-1.0,
                    expression="where(delta(bar.satiation) > 0.0, 0.0, lag(ticks_since_ate, 1) + 1.0)",
                    exposed=["agent"],
                    normalization={"kind": "minmax", "min": 0.0, "max": 100.0, "clip": True},
                )
            ]
        ),
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    print("t0", reg(env, "ticks_since_ate").tolist())
    for t in range(3):
        step(env, "WAIT")
        print("WAIT", reg(env, "ticks_since_ate").tolist(), "sat", meter(env, "satiation").tolist())
    env.positions[:] = torch.tensor([[2, 2], [2, 2]])
    step(env, ["INTERACT", "WAIT"])
    print("INTERACT@EAT agent0", reg(env, "ticks_since_ate").tolist(), "sat", meter(env, "satiation").tolist())
    step(env, "WAIT")
    print("WAIT", reg(env, "ticks_since_ate").tolist())
    # observe exposure
    spec = u.get_level(LEVEL).token_spec
    rows = [r for r in spec.row_layout() if r[0] == "variable_element"]
    print("variable_element rows", rows)


@probe("M3 cooldown on an action: record half (last_used <- tick) + gated writes (tick - last_used >= K)")
def m3():
    def actions(a):
        add_action(
            a,
            "STRIKE",
            [
                write("hit", "1.0", condition="tick - last_strike >= 3.0"),
                write("last_strike", "tick", composition="overwrite", condition="tick - last_strike >= 3.0", priority=1),
            ],
        )

    p = make_pack(
        "m3",
        variables=lambda v: v["declarations"].extend([decl("hit"), decl("last_strike", initial_value=-100.0)]),
        actions=actions,
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    for t in range(6):
        step(env, ["STRIKE", "WAIT"])
        print(f"tick={int(reg(env,'tick')[0])} hit={reg(env,'hit').tolist()} last={reg(env,'last_strike').tolist()}")
    masks = env.get_action_masks()
    print("mask row 0:", masks[0].tolist())


@probe("M3b cooldown masking: is there any declared surface to mask an action on a variable condition?")
def m3b():
    from townlet.config.actions_config import CustomActionConfig

    for key in ("enabled_when", "precondition", "condition", "available_when", "mask"):
        try:
            CustomActionConfig(name="X", description="d", enabled_by_default=True, **{key: "tick > 1"})
            print(key, "ACCEPTED")
        except Exception as exc:  # noqa: BLE001
            print(key, "refused:", short(str(exc), 160))


@probe("M4 resource regenerates toward a cap (rule additive_delta with clamp; and multiplicative approach)")
def m4():
    p = make_pack(
        "m4",
        variables=lambda v: v["declarations"].extend([decl("mana", initial_value=0.0), decl("mana2", initial_value=0.0)]),
        rules=[
            rule("mana_regen", [rwrite("mana", "0.3", clamp=[0.0, 1.0])]),
            rule("mana_regen2", [rwrite("mana2", "0.5 * (1.0 - mana2)", clamp=None)]),
        ],
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    for t in range(6):
        step(env, "WAIT")
        print(f"mana={reg(env,'mana').tolist()} mana2={[round(x,4) for x in reg(env,'mana2').tolist()]}")


@probe("M5 reward on the rising edge of a condition (rising_edge expression var -> DAC variable_bonuses)")
def m5():
    def drive(d):
        d["extrinsic"]["variable_bonuses"] = [{"variable": "rose", "weight": 5.0}]

    p = make_pack(
        "m5",
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
    for t in range(6):
        obs, rew, done, info = step(env, "WAIT")
        print(
            f"tick={int(reg(env,'tick')[0])} energy={[round(x,3) for x in meter(env,'energy').tolist()]} low={reg(env,'low_energy').tolist()} rose={reg(env,'rose').tolist()} reward={[round(x,3) for x in rew.tolist()]}"
        )


@probe("M6 variable persists across episodes (lifetime: persistent)")
def m6():
    p = make_pack(
        "m6",
        variables=lambda v: v["declarations"].extend([decl("lives_lost", lifetime="persistent", scope="global")]),
        rules=[rule("count", [rwrite("lives_lost", "1.0")])],
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    for t in range(3):
        step(env, "WAIT")
    print("before reset", reg(env, "lives_lost").tolist())
    env.reset()
    print("after reset", reg(env, "lives_lost").tolist())


@probe("M7 per-world global weather that changes every K ticks (rule overwrite uniform(), condition tick % K == 0)")
def m7():
    p = make_pack(
        "m7",
        variables=lambda v: v["declarations"].extend([decl("weather", scope="global", initial_value=0.0)]),
        rules=[rule("weather_roll", [rwrite("weather", "uniform(0.0, 3.0)", composition="overwrite")], condition="tick % 4 == 0")],
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 3)
    for t in range(9):
        step(env, "WAIT")
        print(f"tick={int(reg(env,'tick')[0])} weather={[round(x,3) for x in reg(env,'weather').tolist()]}")


@probe("M7b weather, deterministic variant: global expression over tick (floor via % and /)")
def m7b():
    p = make_pack(
        "m7b",
        variables=lambda v: v["declarations"].extend(
            [decl("weather", scope="global", initial_value=0.0, expression="((tick - tick % 4) / 4) % 3")]
        ),
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    for t in range(9):
        step(env, "WAIT")
        print(f"tick={int(reg(env,'tick')[0])} weather={reg(env,'weather').tolist()}")


@probe("M13 terminal condition on a variable (no declared surface? workaround: rule overwrites a lethal meter)")
def m13():
    p = make_pack(
        "m13",
        variables=lambda v: v["declarations"].extend([decl("doom")]),
        rules=[
            rule("doom_rises", [rwrite("doom", "1.0")]),
            rule("doom_kills", [rwrite("bar.health", "0.0", composition="overwrite")], condition="doom >= 3.0"),
        ],
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    for t in range(5):
        obs, rew, done, info = step(env, "WAIT")
        print(f"tick={int(reg(env,'tick')[0])} doom={reg(env,'doom').tolist()} health={meter(env,'health').tolist()} done={done.tolist()}")


@probe("M14 private variable (engine-only, unexposed) that drives a reward")
def m14():
    def drive(d):
        d["extrinsic"]["variable_bonuses"] = [{"variable": "secret", "weight": 1.0}]

    def actions(a):
        add_action(a, "PRAY", [write("secret", "1.0")])

    p = make_pack(
        "m14",
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
    print("variable_element census", spec.census.get("variable_element"), "bindings", [b.filler_ref for b in spec.slot_bindings if b.token_type == "variable_element"])
    for t in range(3):
        obs, rew, done, info = step(env, ["PRAY", "WAIT"])
        print(f"secret={reg(env,'secret').tolist()} reward={[round(x,3) for x in rew.tolist()]} 1.0/2.0/3.0 in obs row0? {[(obs[0]==v).any().item() for v in (1.0,2.0,3.0)]}")


@probe("M15 moving average of a meter exposed as an observation")
def m15():
    p = make_pack(
        "m15",
        variables=lambda v: v["declarations"].extend(
            [decl("energy_ma", initial_value=1.0, expression="moving_average(bar.energy, 4)", exposed=["agent"], normalization=MINMAX01)]
        ),
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    spec = u.get_level(LEVEL).token_spec
    rows = [r for r in spec.row_layout() if r[0] == "variable_element"]
    print("rows", rows)
    for t in range(5):
        obs, *_ = step(env, "WAIT")
        r = rows[-1]
        print(f"energy={[round(x,4) for x in meter(env,'energy').tolist()]} ma={[round(x,4) for x in reg(env,'energy_ma').tolist()]} obs[row]={[round(x,4) for x in obs[0, r[2]:r[3]].tolist()]}")


if __name__ == "__main__":
    import sys

    names = sys.argv[1:] or ["m1", "m2", "m3", "m3b", "m4", "m5", "m6", "m7", "m7b", "m13", "m14", "m15"]
    for n in names:
        globals()[n]()
