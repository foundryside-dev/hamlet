"""R14: boundaries — (a) done agents keep evaluating/publishing expressions and receiving rule writes;
(b) an empty variables roster."""
from harness import *  # noqa

MM = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}


@probe("R14a done agent: expressions, rules, publication")
def a():
    def vars_(v):
        v["declarations"] += [decl("age", lifetime="episode", initial_value=0.0),
                              decl("e_energy", exposed=("agent",), normalization=MM, expression="bar.energy * 10.0")]
    rules = {"transition_rules.yaml": {"version": "1.0", "social_residue": [
        {"id": "aging", "kind": "social_residue", "phase": "apply_social_residue_effects", "reads": ["age"], "condition": None,
         "writes": [{"variable_id": "age", "expression": "1.0", "composition": "additive_delta", "condition": None,
                     "clamp": None, "effect": None}]}]}}
    u = compile_pack(make_pack("r14a", variables=vars_, extra_files=rules))
    env = build_env(u, num_agents=2)
    env.reset()
    idx = env.meter_name_to_index["energy"]
    env.meters[0, idx] = 0.0  # lethal_min -> agent 0 terminal on next step
    for k in range(3):
        obs, r, d, info = step(env, "WAIT")
        rows = ve_rows(env, obs)
        print(f"step{k+1}: dones={d.tolist()} energy={[round(x, 3) for x in env.meters[:, idx].tolist()]} "
              f"age={reg(env,'age').tolist()} e_energy={[round(x, 3) for x in reg(env,'e_energy').tolist()]} "
              f"e_energy obs row agent0={rows['e_energy'][0]} reward={[round(x, 3) for x in r.tolist()]}")


@probe("R14b empty declarations roster")
def b():
    def vars_(v):
        v["declarations"] = []
    def acts(a):
        for ca in a["custom_actions"]:
            ca.pop("writes", None)
    def drive(dest):
        edit_yaml(dest / "levels/L0_simple/drive.yaml",
                  lambda p: p["drive"].update({"extrinsic": {"type": "constant_base_with_shaped_bonus", "base": 1.0,
                                                              "bar_bonuses": [], "variable_bonuses": [], "apply_modifiers": []}}))
    pack = make_pack("r14b", variables=vars_, actions=acts)
    drive(pack)
    u = compile_pack(pack)
    lvl = u.get_level("L0_simple")
    print(f"compile OK: census={lvl.token_spec.census} total_dims={lvl.token_spec.total_dims} vfs_hash={lvl.vfs_hash[:12]}")
    env = build_env(u, num_agents=1)
    obs, r, d, _ = step(env, "WAIT")
    print(f"step OK: obs shape={tuple(obs.shape)} registry ids={list(env.vfs_registry.variables)}")


a()
b()
