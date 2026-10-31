"""Closure checks for the original review's VFS/compiler findings that touch the authoring surface."""

from harness import *  # noqa: F403

import torch


def chk(label, fn):
    print(f"\n--- {label}")
    try:
        print(fn())
    except Exception as exc:  # noqa: BLE001
        print("EXC", type(exc).__name__, short(str(exc), 400))


def refuses(name, **kw):
    p = make_pack(name, **kw)
    u, err = try_compile(p, kw.get("level", LEVEL))
    return "COMPILED (unexpected)" if u else "REFUSED: " + short(err.split(" - ", 1)[-1].replace("\n", " "), 300)


def main():
    # V3 evaluation_mode gone; V4 extents gone; V9 zone gone
    chk("V3 evaluation_mode key", lambda: refuses("v3", variables=lambda v: v.update({"evaluation_mode": "eager"})))
    chk("V4 extents key", lambda: refuses("v4", variables=lambda v: v.update({"extents": {"num_affordances": 3}})))
    chk("V9 zone scope", lambda: refuses("v9", variables=lambda v: v["declarations"].append(decl("zh", scope="zone"))))
    # V5 variable id equal to a meter name
    chk("V5 variable id == meter name", lambda: refuses("v5", variables=lambda v: v["declarations"].append(decl("energy"))))
    # V7 agent expression reads a global
    def v7():
        p = make_pack("v7", variables=lambda v: v["declarations"].extend([decl("g", scope="global", initial_value=2.0), decl("a", expression="g * bar.energy")]))
        u, err = try_compile(p)
        if err:
            return "REFUSED " + short(err, 200)
        env = build_env(u, 2)
        step(env, "WAIT")
        return f"a={reg(env,'a').tolist()} (expect 2*energy)"

    chk("V7 agent reads global", v7)
    # V1 action writes at non-action phases refuse at compile
    for ph in ("apply_transition_rules", "apply_passive_depletion", "compute_rewards", "emit_telemetry", "my_phase"):
        chk(f"V1 action write at {ph}", lambda ph=ph: refuses("v1", variables=lambda v: v["declarations"].append(decl("x")), actions=lambda a: add_action(a, "P", [write("x", "1.0", phase=ph)])))
    # V1b rule at a phase the env never runs
    for ph in ("compute_rewards", "emit_telemetry", "apply_modulations"):
        chk(f"V1b rule at {ph}", lambda ph=ph: refuses("v1b", variables=lambda v: v["declarations"].append(decl("x")), rules=[rule("r", [rwrite("x", "1.0")], phase=ph)]))
    # V2 action write to a global / affordance target
    chk("V2 action write to global target", lambda: refuses("v2", variables=lambda v: v["declarations"].append(decl("g", scope="global")), actions=lambda a: add_action(a, "P", [write("g", "1.0")])))
    chk("V2b action write to affordance target (no claim)", lambda: refuses("v2b", variables=lambda v: v["declarations"].append(decl("af", scope="affordance")), actions=lambda a: add_action(a, "P", [write("af", "1.0")])))
    # V8 old spelling writes refuse
    chk("V8 vfs.x write target in action", lambda: refuses("v8", variables=lambda v: v["declarations"].append(decl("x")), actions=lambda a: add_action(a, "P", [write("vfs.x", "1.0")])))
    chk("V8b self.vfs.x in interaction", lambda: refuses("v8b", variables=lambda v: v["declarations"].append(decl("x")), affordances=lambda a: a["affordances"][1]["interactions"]["on_start"].append({"modify": "self.vfs.x", "value": "1.0"})))
    # V12 hash moves on shape / initializer
    def v12():
        hs = []
        for name, extra in (("v12a", {"shape": [2, 2]}), ("v12b", {"shape": [4, 4]}), ("v12c", {"shape": [2, 2], "initial_value_mode": "ones"})):
            kw = dict(extra)
            if "initial_value_mode" not in kw:
                kw["initial_value_mode"] = "zeros"
            p = make_pack(name, variables=lambda v, kw=kw: v["declarations"].append(decl("t", type="tensor2d", **kw)))
            u, err = try_compile(p)
            if err:
                return "REFUSED " + short(err, 200)
            lv = u.get_level(LEVEL)
            hs.append((name, lv.vfs_hash[:8], getattr(lv, "variables_hash", "")[:8] if hasattr(lv, "variables_hash") else ""))
        return hs

    chk("V12 vfs_hash moves with tensor shape and initializer", v12)
    # V13 random initializer redraws on reset
    def v13():
        p = make_pack("v13", variables=lambda v: v["declarations"].append(decl("noise", type="tensor1d", shape=[3], initial_value_mode="random_uniform", initial_value_params={"low": 0.0, "high": 1.0})))
        u, err = try_compile(p)
        if err:
            return "REFUSED " + short(err, 200)
        env = build_env(u, 1)
        a = reg(env, "noise").clone()
        env.reset()
        b = reg(env, "noise").clone()
        return f"draw0={a.flatten().tolist()[:3]} draw1={b.flatten().tolist()[:3]} identical={torch.equal(a,b)}"

    chk("V13 random initializer redraw on reset", v13)
    # V14 expression sees transition-rule write same tick
    def v14():
        p = make_pack("v14", variables=lambda v: v["declarations"].extend([decl("gc", scope="global"), decl("g2", scope="global", expression="gc * 2.0")]), rules=[rule("inc", [rwrite("gc", "1.0")])])
        u, err = try_compile(p)
        if err:
            return "REFUSED " + short(err, 200)
        env = build_env(u, 1)
        out = []
        for _ in range(3):
            step(env, "WAIT")
            out.append((reg(env, "gc").tolist(), reg(env, "g2").tolist()))
        return out

    chk("V14 expression sees rule write same tick", v14)
    # C4 bogus curriculum_levels / cue on nonexistent meter
    chk("C4 bogus curriculum_levels", lambda: refuses("c4", extra_files=None) if False else (lambda: (lambda p: (lambda u, e: "COMPILED (dead field)" if u else "REFUSED " + short(e.split(" - ", 1)[-1], 200))(*try_compile(p)))(_c4_pack()))())
    # C5 RecordingConfig extra
    def c5():
        from townlet.config.training_v2_config import RecordingConfig

        try:
            RecordingConfig(enabled=False, typo_key=1)
            return "ACCEPTED typo key (extra=allow still)"
        except Exception as exc:  # noqa: BLE001
            return "refused: " + short(str(exc), 120)

    chk("C5 RecordingConfig extra", c5)
    # C7 presentation in a non-conventional file and undeclared meter
    def c7():
        p = make_pack("c7", extra_files={"display.yaml": {"version": "1.0", "meters": {"NO_SUCH_METER": {"label": "x"}}, "affordances": {}}})
        u, err = try_compile(p)
        return "COMPILED (unchecked)" if u else "REFUSED " + short(err.split(" - ", 1)[-1], 200)

    chk("C7 presentation undeclared meter in display.yaml", c7)
    # C1 items_appearance survives to_dict/from_dict
    def c1():
        from townlet.universe.compiled import CompiledUniverse

        p = make_pack("c1", base=WT / "configs/test/items_smoke", level="L0_smoke")
        u = compile_pack(p, "L0_smoke")
        d = u.to_dict()
        u2 = CompiledUniverse.from_dict(d)
        return f"fresh={u.get_level('L0_smoke').items_appearance is not None} roundtrip={u2.get_level('L0_smoke').items_appearance is not None}"

    chk("C1 items_appearance round trip", c1)
    # C3 max_items_per_agent 0 keeps catalog
    def c3():
        p = make_pack("c3", base=WT / "configs/test/items_smoke", level="L0_smoke")
        path = p / "items.yaml"
        payload = load_yaml(path)
        payload["items"]["max_items_per_agent"] = 0
        dump_yaml(path, payload)
        u, err = try_compile(p, "L0_smoke")
        return "COMPILED catalog kept: items_hash=%s" % (u.get_level("L0_smoke").items_hash if hasattr(u.get_level("L0_smoke"), "items_hash") else "?") if u else "REFUSED " + short(err.split(" - ", 1)[-1], 250)

    chk("C3 max_items_per_agent 0", c3)
    # C8 identity: two parameter-identical exposed variables under token_set vs feedforward
    def c8():
        twin = lambda v: v["declarations"].extend([decl("a1", exposed=["agent"], normalization=MINMAX01), decl("a2", exposed=["agent"], normalization=MINMAX01)])
        p = make_pack("c8ff", variables=twin)
        u, err = try_compile(p)
        r1 = "COMPILED" if u else "REFUSED " + short(err.split(" - ", 1)[-1], 160)

        def brain(path):
            b = load_yaml(path / "brain.yaml")
            b["architecture"] = "token_set"
            if "token_set" not in b:
                b["token_set"] = {"d_model": 32, "aggregator": "mean", "mlp_hidden": [32]}
            dump_yaml(path / "brain.yaml", b)

        p2 = make_pack("c8ts", variables=twin)
        brain(p2)
        u2, err2 = try_compile(p2)
        r2 = "COMPILED" if u2 else "REFUSED " + short(err2.split(" - ", 1)[-1], 200)
        return f"feedforward: {r1} | token_set: {r2}"

    chk("C8 identity discriminator", c8)


def _c4_pack():
    def exp(p):
        e = load_yaml(p / "experiment.yaml")
        e["experiment"]["curriculum_levels"] = ["BOGUS_LEVEL"]
        dump_yaml(p / "experiment.yaml", e)
        return p

    return exp(make_pack("c4"))


if __name__ == "__main__":
    main()
