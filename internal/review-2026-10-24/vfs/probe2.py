"""Probe 2: expressions (c6c6), cascades/social residue (cb0c), bare vfs.X writes (b9a3), dtype (2ca2),
eye (8c35), vec types (b5cd), observable key (0071), eager staleness, num_affordances inert,
normalization kinds, policy immutability, immutable writes, effects schema, pair H1, shape hash."""

import torch
from harness import *  # noqa: F403


def try_compile(name, **kw):
    p = make_pack(name, **kw)
    try:
        u = compile_pack(p)
        print(f"[{name}] compiled OK")
        return u
    except Exception as e:
        msg = str(e)
        # keep the last diagnostic lines
        print(f"[{name}] REFUSED {type(e).__name__}: {msg[-700:] if len(msg) > 700 else msg}")
        return None


@probe("A. expressions: bare same-scope ref, vfs. prefix, self-accumulator, agent->global ref (c6c6c241c5)")
def probe_a():
    # (i) bare same-scope static
    u = try_compile("expr_bare", variables=lambda v: v["declarations"].append(decl("derived", expression="public_state * 2.0")))
    if u:
        env = build_env(u, 2)
        step(env, "ADVANCE"); step(env, "ADVANCE")
        print("   derived after 2 ADVANCE:", reg(env, "derived").tolist(), "public", reg(env, "public_state").tolist())
    # (ii) vfs. prefix
    try_compile("expr_vfs_prefix", variables=lambda v: v["declarations"].append(decl("derived", expression="vfs.public_state * 2.0")))
    # (iii) self accumulator
    try_compile("expr_self_acc", variables=lambda v: v["declarations"].append(decl("counter", expression="counter + 1.0")))
    # (iv) agent expression referencing a global static
    try_compile("expr_agent_reads_global", variables=lambda v: v["declarations"].append(decl("scaled", expression="public_state * immutable_scale")))
    # (v) global expression referencing a global static (immutable_scale)
    u = try_compile("expr_global_reads_global", variables=lambda v: v["declarations"].append(decl("g2", scope="global", expression="immutable_scale * 2.0")))
    if u:
        env = build_env(u, 2); step(env, "WAIT"); print("   g2:", reg(env, "g2").item())
    # (vi) tensor expression
    try_compile("expr_tensor", variables=lambda v: v["declarations"].append(decl("t", scope="global", type="tensor1d", shape=[2], initial_value=[0.0, 0.0], expression="max(t, 1.0)")))
    # (vii) global expression referencing agent bar -> should refuse shape
    try_compile("expr_global_reads_bar", variables=lambda v: v["declarations"].append(decl("gb", scope="global", expression="bar.energy * 2.0")))
    # (viii) global expression referencing an agent-scope variable
    try_compile("expr_global_reads_agent", variables=lambda v: v["declarations"].append(decl("gb", scope="global", expression="public_state * 2.0")))


@probe("B. cascades cannot target VFS; social_residue as per-tick VFS passive dynamic (cb0ccdaa98)")
def probe_b():
    def casc(path):
        import yaml
        bars = load_yaml(path)
        bars["bars"]["cascades"] = [{"source": "public_state", "target": "energy", "threshold": 0.5, "rate": 0.1}]
        dump_yaml(path, bars)

    p = make_pack("cascade_vfs")
    try:
        casc(p / "levels/L0_simple/bars.yaml")
        compile_pack(p)
        print("cascade with VFS source: COMPILED")
    except Exception as e:
        print("cascade with VFS source: REFUSED", str(e)[-500:])
    # social residue rule: decay public_state 10%/tick; also tensor var decay
    rules = {
        "version": "1.0",
        "social_residue": [
            {"id": "decay", "kind": "institutional_rule", "phase": "apply_social_residue_effects", "reads": ["public_state"], "condition": None,
             "writes": [{"variable_id": "public_state", "expression": "public_state * 0.5", "composition": "overwrite", "condition": None, "clamp": None, "effect": None, "scope": "agent"}]},
            {"id": "tdecay", "kind": "institutional_rule", "phase": "apply_social_residue_effects", "reads": ["heat"], "condition": None,
             "writes": [{"variable_id": "heat", "expression": "heat * 0.5", "composition": "overwrite", "condition": None, "clamp": None, "effect": None, "scope": None}]},
        ],
    }
    u = try_compile("social_decay", variables=lambda v: v["declarations"].append(decl("heat", scope="global", type="tensor1d", shape=[3], initial_value=[8.0, 8.0, 8.0])), extra_files={"transition_rules.yaml": rules})
    if u:
        for n in (2, 3):
            env = build_env(u, n)
            step(env, "ADVANCE")
            print(f"   n={n} after ADVANCE(+1 then *0.5): public", reg(env, "public_state").tolist(), "heat", reg(env, "heat").tolist())
            step(env, "WAIT")
            print(f"   n={n} after WAIT: public", reg(env, "public_state").tolist(), "heat", reg(env, "heat").tolist())


@probe("C. bare vfs.X write from affordance with 2 interacting agents (b9a3bcbde2)")
def probe_c():
    def affs(a):
        sleep = next(x for x in a["affordances"] if x["name"] == "SLEEP")
        sleep["interactions"]["on_start"] = [{"modify": "vfs.public_state", "value": "vfs.public_state + 5.0"}]
    u = try_compile("bare_vfs_write", affordances=affs)
    if u is None:
        return
    env = build_env(u, 2)
    env.positions[:] = env.affordances["SLEEP"].to(env.positions.dtype)
    step(env, "INTERACT")
    print("   both agents INTERACT at SLEEP, vfs.public_state + 5.0 ->", reg(env, "public_state").tolist())
    # target.vfs form
    def affs2(a):
        sleep = next(x for x in a["affordances"] if x["name"] == "SLEEP")
        sleep["interactions"]["on_start"] = [{"modify": "target.vfs.public_state", "value": "target.vfs.public_state + 5.0"}]
    u = try_compile("target_vfs_write", affordances=affs2)
    if u:
        env = build_env(u, 2)
        env.positions[:] = env.affordances["SLEEP"].to(env.positions.dtype)
        step(env, "INTERACT")
        print("   target.vfs.public_state + 5.0 ->", reg(env, "public_state").tolist())
    # global via bare vfs.X with 2 agents
    def affs3(a):
        sleep = next(x for x in a["affordances"] if x["name"] == "SLEEP")
        sleep["interactions"]["on_start"] = [{"modify": "vfs.gcount", "value": "vfs.gcount + 1.0"}]
    u = try_compile("global_vfs_write", variables=lambda v: v["declarations"].append(decl("gcount", scope="global")), affordances=affs3)
    if u:
        env = build_env(u, 2)
        env.positions[:] = env.affordances["SLEEP"].to(env.positions.dtype)
        step(env, "INTERACT")
        print("   global vfs.gcount + 1.0 with 2 agents ->", reg(env, "gcount").item())


@probe("D. set_engine_value dtype coercion; VTC bool->scalar write; set() on immutable (2ca2cb373f)")
def probe_d():
    u = try_compile("dtype", variables=lambda v: v["declarations"].extend([decl("flag", type="bool", initial_value=False), decl("num", initial_value=0.0)]))
    env = build_env(u, 2)
    try:
        env.vfs_registry.set_engine_value("flag", torch.tensor([0.7, 2.5]))
        print("   set_engine_value float->bool coerced; stored:", reg(env, "flag").tolist())
    except Exception as e:
        print("   set_engine_value float->bool refused:", e)
    try:
        env.vfs_registry.set("flag", torch.tensor([0.7, 2.5]), writer="engine")
        print("   set() float->bool accepted")
    except Exception as e:
        print("   set() float->bool refused:", str(e)[:120])
    # VTC write bool expression into scalar var
    u = try_compile("vtc_bool_to_scalar", variables=lambda v: v["declarations"].append(decl("num")), actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("num", "bar.energy > 0.5", composition="overwrite")]))
    if u:
        env = build_env(u, 2); step(env, "ADVANCE"); print("   num after bool-expression overwrite:", reg(env, "num").tolist())
    # immutable: set_engine_value and action write
    u = compile_pack(BASE); env = build_env(u, 2)
    try:
        env.vfs_registry.set_engine_value("immutable_scale", torch.tensor(0.5))
        print("   set_engine_value on writable_by [] ACCEPTED (bad)")
    except PermissionError as e:
        print("   set_engine_value on writable_by []:", e)
    try_compile("write_immutable", actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("readable_unexposed", "1.0")]))


@probe("E. initial_value_mode eye (8c354c90bb); vec types (b5cd718368); observable key (0071c78ee9)")
def probe_e():
    u = try_compile("eye_ok", variables=lambda v: v["declarations"].append(decl("m", scope="global", type="tensor2d", shape=[3, 3], initial_value_mode="eye")))
    if u:
        env = build_env(u, 2); print("   eye 3x3:", reg(env, "m").tolist())
    try_compile("eye_bad", variables=lambda v: v["declarations"].append(decl("m", scope="global", type="tensor2d", shape=[2, 3], initial_value_mode="eye")))
    try_compile("eye_exposed", variables=lambda v: v["declarations"].append(decl("m", scope="global", type="tensor2d", shape=[2, 2], initial_value_mode="eye", exposed=("agent",), normalization=dict(MINMAX))))
    # vec types hidden
    def vecs(v):
        v["declarations"] += [
            decl("v2i", type="vec2i", initial_value=[1, 2]), decl("v3i", type="vec3i", initial_value=[1, 2, 3]),
            decl("vni", type="vecNi", dims=4, initial_value=[1, 2, 3, 4]), decl("vnf", type="vecNf", dims=4, initial_value=[1.0, 2.0, 3.0, 4.0]),
            decl("v2f", type="vec2f", initial_value=[0.5, 0.5], exposed=("agent",), normalization=dict(MINMAX)),
            decl("gvnf", scope="global", type="vecNf", dims=2, initial_value=[1.0, 2.0], exposed=("agent",), normalization=dict(MINMAX)),
        ]
    u = try_compile("vec_types", variables=vecs)
    if u:
        env = build_env(u, 2); obs, *_ = step(env, "WAIT")
        print("   shapes:", {n: (tuple(reg(env, n).shape), str(reg(env, n).dtype)) for n in ("v2i", "v3i", "vni", "vnf", "v2f", "gvnf")})
        print("   variable_element rows:", [r for r in u.get_level("L0_simple").token_spec.row_layout() if r[0] == "variable_element"])
    try_compile("vec_int_exposed", variables=lambda v: v["declarations"].append(decl("v2i", type="vec2i", initial_value=[1, 2], exposed=("agent",), normalization=dict(MINMAX))))
    try_compile("observable_key", variables=lambda v: v["declarations"].append(decl("x", observable=True)))
    # mark_and_sweep with only an agent expression, no global expression
    u = try_compile("marks_agent_only", variables=lambda v: v["declarations"].append(decl("derived", expression="public_state + 1.0")))
    if u:
        env = build_env(u, 2); step(env, "ADVANCE"); print("   marks:", u.vfs_evaluation_marks, "derived:", reg(env, "derived").tolist())


@probe("F. eager evaluation: expression over action-written global static is stale?")
def probe_f():
    def vars_(v):
        v["evaluation_mode"] = "eager"
        v["declarations"] += [decl("gcount", scope="global", initial_value=0.0), decl("gtwice", scope="global", expression="gcount * 2.0")]
    rules = {"version": "1.0", "social_residue": [
        {"id": "inc", "kind": "institutional_rule", "phase": "apply_social_residue_effects", "reads": ["gcount"], "condition": None,
         "writes": [{"variable_id": "gcount", "expression": "gcount + 1.0", "composition": "overwrite", "condition": None, "clamp": None, "effect": None, "scope": None}]}]}
    u = try_compile("eager_stale", variables=vars_, extra_files={"transition_rules.yaml": rules})
    if u:
        env = build_env(u, 2)
        for t in range(3):
            step(env, "WAIT"); print(f"   t{t+1} gcount {reg(env, 'gcount').item()} gtwice {reg(env, 'gtwice').item()}")
    # same in mark_and_sweep
    def vars2(v):
        v["declarations"] += [decl("gcount", scope="global", initial_value=0.0), decl("gtwice", scope="global", expression="gcount * 2.0")]
    u = try_compile("mas_control", variables=vars2, extra_files={"transition_rules.yaml": rules})
    if u:
        env = build_env(u, 2)
        for t in range(3):
            step(env, "WAIT"); print(f"   [mark_and_sweep] t{t+1} gcount {reg(env, 'gcount').item()} gtwice {reg(env, 'gtwice').item()}")
    # eager with agent expression over agent static
    def vars3(v):
        v["evaluation_mode"] = "eager"
        v["declarations"].append(decl("derived", expression="public_state * 2.0"))
    try_compile("eager_agent_static", variables=vars3)


@probe("G. extents.num_affordances inert; zone/group/message storage; pair H1")
def probe_g():
    def vars_(v):
        v["extents"] = {"num_affordances": 99, "num_groups": 2, "num_message_slots": 3}
        v["declarations"] += [decl("aff_wear", scope="affordance"), decl("grp", scope="group"), decl("msg", scope="message", type="message_token", dims=2, initial_value=[0.0, 0.0]), decl("trust", scope="pair")]
    u = try_compile("extents", variables=vars_)
    if u:
        env = build_env(u, 2)
        print("   affordance rows:", tuple(reg(env, "aff_wear").shape), "(declared extent 99, level has 4 affordances)")
        print("   group", tuple(reg(env, "grp").shape), "msg", tuple(reg(env, "msg").shape), "pair", tuple(reg(env, "trust").shape))
    for n in (2, 3):
        u = try_compile(f"pair_h1_{n}", variables=lambda v: v["declarations"].append(decl("trust", scope="pair")), actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("trust", "1.0")]))
        if u:
            try:
                env = build_env(u, n)
                step(env, actions=torch.tensor([action_index(env, "ADVANCE")] + [action_index(env, "WAIT")] * (n - 1)))
                print(f"   pair n={n} agent0 ADVANCE -> trust {reg(env, 'trust').tolist()}")
            except Exception as e:
                print(f"   pair n={n}: {type(e).__name__}: {str(e)[:200]}")
    # group var at num_groups == num_agents
    u = try_compile("group_h1", variables=lambda v: (v.__setitem__("extents", {"num_groups": 2}), v["declarations"].append(decl("grp", scope="group"))), actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("grp", "1.0")]))
    if u:
        env = build_env(u, 2)
        step(env, actions=torch.tensor([action_index(env, "ADVANCE"), action_index(env, "WAIT")]))
        print("   group(2) n=2 agent0 ADVANCE -> grp", reg(env, "grp").tolist())


@probe("H. normalization kinds at exposure; policy immutability; effects schema agent var; shape hash")
def probe_h():
    for kind, extra in (("none", {}), ("zscore", {"mean": 0.0, "std": 1.0}), ("masked_value", {"mask_value": -1.0, "fill_value": 0.0}), ("one_hot", {"categories": 3}), ("rank_scaled", {}), ("minmax", {"min": 0.0, "max": 1.0, "clip": False}), ("log_scaled", {"min": 0.0, "max": 10.0, "clip": True}), ("cyclical_sin_cos", {"period": 4.0}), ("binary", {"threshold": 0.5})):
        u = try_compile(f"norm_{kind}", variables=lambda v, kind=kind, extra=extra: v["declarations"].append(decl("x", exposed=("agent",), normalization={"kind": kind, **extra})))
        if u:
            try:
                env = build_env(u, 2); obs, *_ = step(env, "ADVANCE")
                rows = [r for r in u.get_level("L0_simple").token_spec.row_layout() if r[0] == "variable_element"]
                print(f"   {kind}: runtime OK, rows {len(rows)}, x row agent0 {obs[0, rows[-1][2]:rows[-1][3]].tolist()}")
            except Exception as e:
                print(f"   {kind}: RUNTIME {type(e).__name__}: {str(e)[:200]}")
    # policy immutability
    u = compile_pack(BASE); env = build_env(u, 2)
    vd = env.vfs_registry.variables["hidden_score"]
    vd.exposed_to.append("agent"); vd.readable_by.append("agent")
    try:
        env.vfs_registry.get("hidden_score", reader="agent"); print("   mutated DTO -> agent read ALLOWED (bad)")
    except PermissionError as e:
        print("   mutated DTO lists; policy snapshot still refuses:", str(e)[:80])
    # effects schema: affordance referencing agent var via vfs.X and global via vfs.X
    for label, expr in (("agent_var", "target.bar.energy + vfs.public_state"), ("global_var", "target.bar.energy + vfs.immutable_scale"), ("target_agent_var", "target.bar.energy + target.vfs.public_state")):
        def affs(a, expr=expr):
            s = next(x for x in a["affordances"] if x["name"] == "SLEEP")
            s["interactions"]["on_start"] = [{"modify": "target.bar.energy", "value": expr}]
        try_compile(f"effschema_{label}", affordances=affs)
    # shape hash
    from townlet.vfs.schema import VariableDef
    from townlet.vfs.schema_hashes import compute_variable_schema_hash
    base = dict(id="t", scope="global", type="tensor2d", lifetime="episode", readable_by=["engine"], writable_by=["engine"], default=None)
    h1 = compute_variable_schema_hash([VariableDef(shape=[2, 2], **base)], {})
    h2 = compute_variable_schema_hash([VariableDef(shape=[4, 4], **base)], {})
    h3 = compute_variable_schema_hash([VariableDef(shape=[2, 2], initial_value_mode="ones", **base)], {})
    print("   variable_schema_hash [2,2] vs [4,4] equal:", h1 == h2, "; zeros vs ones equal:", h1 == h3)


if __name__ == "__main__":
    import sys
    sel = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    for fn in (probe_a, probe_b, probe_c, probe_d, probe_e, probe_f, probe_g, probe_h):
        if sel is None or fn.__name__.endswith(sel):
            fn()
