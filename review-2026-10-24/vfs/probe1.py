"""Probe 1: witness baseline (3381043d2e), lifetimes (4597/5f99/0268), agent_private (83a0),
phase names (cebe), global tensor leading dim (f54b), H1 write-side coincidence, H2 random reset."""

import torch
from harness import *  # noqa: F403


@probe("A. witness ADVANCE/WAIT end to end (hamlet-3381043d2e)")
def probe_a():
    u = compile_pack(BASE)
    env = build_env(u, num_agents=2)
    print("actions:", [a.name for a in env.action_space.actions], "enabled:", env.action_space.enabled_action_names)
    spec = u.get_level("L0_simple").token_spec
    rows = [r for r in spec.row_layout() if r[0] == "variable_element"]
    print("variable_element rows:", rows)
    print("t0 public", reg(env, "public_state").tolist(), "hidden", reg(env, "hidden_score").tolist())
    obs, r, d, info = step(env, "ADVANCE")
    print("t1 public", reg(env, "public_state").tolist(), "hidden", reg(env, "hidden_score").tolist(), "reward", r.tolist())
    obs, r, d, info = step(env, "ADVANCE")
    print("t2 public", reg(env, "public_state").tolist(), "hidden", reg(env, "hidden_score").tolist(), "reward", r.tolist())
    obs, r, d, info = step(env, "WAIT")
    print("t3 (WAIT) public", reg(env, "public_state").tolist(), "hidden", reg(env, "hidden_score").tolist())
    typ, slot, start, end = rows[0]
    print("obs public_state row slice per agent:", obs[:, start:end].tolist())
    # mixed actions: agent0 ADVANCE, agent1 WAIT
    step(env, actions=torch.tensor([action_index(env, "ADVANCE"), action_index(env, "WAIT")]))
    print("t4 mixed public", reg(env, "public_state").tolist())
    env.reset()
    print("after reset public", reg(env, "public_state").tolist(), "hidden", reg(env, "hidden_score").tolist())


@probe("B. lifetimes tick/episode/persistent on agent + global (4597/5f99/0268)")
def probe_b():
    def vars_(v):
        v["declarations"] += [
            decl("acc_tick", lifetime="tick"),
            decl("acc_episode", lifetime="episode"),
            decl("acc_persist", lifetime="persistent"),
            decl("g_tick", scope="global", lifetime="tick"),
            decl("g_episode", scope="global", lifetime="episode"),
            decl("g_persist", scope="global", lifetime="persistent"),
        ]

    def acts(a):
        adv = next(x for x in a["custom_actions"] if x["name"] == "ADVANCE")
        adv["writes"] += [write("acc_tick", "1.0"), write("acc_episode", "1.0"), write("acc_persist", "1.0")]

    p = make_pack("lifetimes", variables=vars_, actions=acts)
    u = compile_pack(p)
    env = build_env(u, num_agents=2)
    for t in range(3):
        step(env, "ADVANCE")
        print(f"t{t+1}", {n: reg(env, n).tolist() for n in ("acc_tick", "acc_episode", "acc_persist")})
    # globals: write directly as engine then step
    for n in ("g_tick", "g_episode", "g_persist"):
        env.vfs_registry.set_engine_value(n, torch.tensor(5.0))
    step(env, "WAIT")
    print("globals after engine write + step:", {n: reg(env, n).item() for n in ("g_tick", "g_episode", "g_persist")})
    env.reset()
    print("after reset:", {n: reg(env, n).tolist() for n in ("acc_tick", "acc_episode", "acc_persist", "g_tick", "g_episode", "g_persist")})


@probe("C. agent_private: hidden is absent from obs; exposed refuses (83a043a9b9)")
def probe_c():
    def vars_(v):
        v["declarations"].append(decl("secret", scope="agent_private", initial_value=99.0))

    p = make_pack("agent_private_hidden", variables=vars_)
    u = compile_pack(p)
    env = build_env(u, num_agents=2)
    obs = env._get_observations()
    print("total_dims", u.get_level("L0_simple").token_spec.total_dims, "rows", [r for r in u.get_level("L0_simple").token_spec.row_layout() if r[0] == "variable_element"])
    print("99.0 present anywhere in obs?", bool((obs == 99.0).any()), "0.99?", bool(torch.isclose(obs, torch.tensor(0.99)).any()))
    try:
        env.vfs_registry.get("secret", reader="agent")
        print("agent read of secret: ALLOWED (bad)")
    except PermissionError as e:
        print("agent read refused:", e)

    def vars2(v):
        v["declarations"].append(decl("secret", scope="agent_private", initial_value=99.0, exposed=("agent",), normalization=dict(MINMAX)))

    p2 = make_pack("agent_private_exposed", variables=vars2)
    try:
        compile_pack(p2)
        print("exposed agent_private COMPILED (bad)")
    except Exception as e:
        print("exposed agent_private refused:", type(e).__name__, str(e)[:400])


@probe("D. phase names: unknown phase, late phase (passive_depletion), never-run phase (compute_rewards) (cebe51077a)")
def probe_d():
    for phase in ("my_custom_phase", "apply_passive_depletion", "apply_social_residue_effects", "compute_rewards", "emit_telemetry"):
        def acts(a, phase=phase):
            adv = next(x for x in a["custom_actions"] if x["name"] == "ADVANCE")
            adv["writes"] = [write("public_state", "1.0", phase=phase)]

        p = make_pack(f"phase_{phase}", actions=acts)
        try:
            u = compile_pack(p)
        except Exception as e:
            print(f"phase={phase}: COMPILE refused {type(e).__name__}: {str(e)[:300]}")
            continue
        try:
            env = build_env(u, num_agents=2)
            step(env, "ADVANCE")
            step(env, "ADVANCE")
            print(f"phase={phase}: compile OK, 2x ADVANCE -> public_state {reg(env, 'public_state').tolist()}")
        except Exception as e:
            print(f"phase={phase}: compile OK, RUNTIME {type(e).__name__}: {str(e)[:300]}")


@probe("E. exposed global tensor2d [2,2] at num_agents 2 and 3 (f54b887148); tensorNd (8b5af63108)")
def probe_e():
    def vars_(v):
        v["declarations"].append(decl("grid", scope="global", type="tensor2d", shape=[2, 2], initial_value=[[1.0, 2.0], [3.0, 4.0]], exposed=("agent",), normalization=dict(MINMAX)))
        v["declarations"].append(decl("cube", scope="global", type="tensorNd", shape=[3, 3, 3], initial_value_mode="ones", exposed=("agent",), normalization=dict(MINMAX)))
        v["declarations"].append(decl("hidden_cube", scope="global", type="tensorNd", shape=[2, 2, 2, 2], initial_value_mode="eye" if False else "zeros"))

    p = make_pack("global_tensor", variables=vars_)
    u = compile_pack(p)
    spec = u.get_level("L0_simple").token_spec
    rows = [r for r in spec.row_layout() if r[0] == "variable_element"]
    print("variable_element rows:", len(rows), "census", spec.census)
    for n in (2, 3):
        env = build_env(u, num_agents=n)
        obs, *_ = step(env, "WAIT")
        g = reg(env, "grid")
        print(f"num_agents={n}: obs shape {tuple(obs.shape)}, grid {g.tolist()}, cube sum {reg(env, 'cube').sum().item()} hidden_cube shape {tuple(reg(env, 'hidden_cube').shape)}")
        # value lanes for grid elements
        typ, slot, start, end = rows[0]
        print("  first grid element row (agent0):", obs[0, start:end].tolist()[:8])


@probe("F. H1: action write to global tensor1d[2] / zone var at num_agents=2 vs 3 (write-side coincidence)")
def probe_f():
    for n in (2, 3):
        def vars_(v):
            v["extents"] = {"num_zones": 2}
            v["declarations"] += [
                decl("gvec", scope="global", type="tensor1d", shape=[2], initial_value=[0.0, 0.0]),
                decl("zone_heat", scope="zone", initial_value=0.0),
                decl("gscalar", scope="global", initial_value=0.0),
            ]

        def acts(a):
            adv = next(x for x in a["custom_actions"] if x["name"] == "ADVANCE")
            adv["writes"] = [write("gvec", "1.0"), write("zone_heat", "1.0")]

        p = make_pack(f"h1_{n}", variables=vars_, actions=acts)
        try:
            u = compile_pack(p)
            env = build_env(u, num_agents=n)
            step(env, actions=torch.tensor([action_index(env, "ADVANCE")] + [action_index(env, "WAIT")] * (n - 1)))
            print(f"num_agents={n}: agent0 ADVANCE only -> gvec {reg(env, 'gvec').tolist()} zone_heat {reg(env, 'zone_heat').tolist()}")
        except Exception as e:
            print(f"num_agents={n}: {type(e).__name__}: {str(e)[:400]}")
    # global scalar target
    def acts2(a):
        adv = next(x for x in a["custom_actions"] if x["name"] == "ADVANCE")
        adv["writes"] = [write("gscalar", "1.0")]

    def vars2(v):
        v["declarations"].append(decl("gscalar", scope="global", initial_value=0.0))

    p = make_pack("h1_scalar", variables=vars2, actions=acts2)
    try:
        u = compile_pack(p)
        env = build_env(u, num_agents=2)
        step(env, "ADVANCE")
        print("global scalar target: OK ->", reg(env, "gscalar").item())
    except Exception as e:
        print("global scalar target:", type(e).__name__, str(e)[:300])


@probe("G. H2: random tensor resets to the same draw (reset identity)")
def probe_g():
    def vars_(v):
        v["declarations"].append(decl("noise", scope="global", type="tensor1d", shape=[4], initial_value_mode="random_uniform", initial_value_params={"low": 0.0, "high": 1.0}))

    p = make_pack("random_reset", variables=vars_)
    u = compile_pack(p)
    env = build_env(u, num_agents=2)
    a = reg(env, "noise").tolist()
    env.vfs_registry.set_engine_value("noise", torch.zeros(4))
    env.reset()
    b = reg(env, "noise").tolist()
    env.reset()
    c = reg(env, "noise").tolist()
    print("draw0", a, "\nafter reset", b, "\nafter reset2", c, "\nidentical:", a == b == c)


if __name__ == "__main__":
    for fn in (probe_a, probe_b, probe_c, probe_d, probe_e, probe_f, probe_g):
        fn()
