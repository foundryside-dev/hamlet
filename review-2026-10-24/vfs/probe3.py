"""Probe 3: item-scoped accessor (f2a37a8c8a), item expression refusal (de52c40c03), item-var write/read, lag check."""

import torch
from harness import *  # noqa: F403

ITEMS = REPO / "configs" / "test" / "items_smoke"


@probe("A. item-scoped variables: registry.get vs read_item (f2a37a8c8a)")
def probe_a():
    from townlet.universe.compiler import UniverseCompiler
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    u = UniverseCompiler().compile(ITEMS, primary_level="L0_smoke")
    env = VectorizedHamletEnv.from_universe(u, level_name="L0_smoke", num_agents=2, device="cpu")
    env.reset()
    print("registry variables:", list(env.vfs_registry.variables))
    for name in ("freshness", "durability", "food.freshness"):
        try:
            env.vfs_registry.get(name, reader="engine"); print(f"   get({name!r}) OK")
        except Exception as e:
            print(f"   get({name!r}) -> {type(e).__name__}: {e}")
    print("   item_profile_map:", env.vfs_registry.item_profile_map, "index->profile:", env.vfs_registry.item_vfs_index_to_profile)
    live = sorted(env.vfs_registry.item_vfs_index_to_profile.items())
    if live:
        idx, prof = live[0]
        var = next(iter(env.vfs_registry.item_profile_map[prof]))
        print(f"   read_item({prof},{var},{idx}) =", env.vfs_registry.read_item(prof, var, idx, reader="engine"))
        try:
            env.vfs_registry.read_item(prof, var, idx, reader="agent"); print("   agent read_item OK")
        except PermissionError as e:
            print("   agent read_item refused:", e)
        try:
            env.vfs_registry.write_item(prof, var, 5.0, idx, writer="engine"); print("   write_item ok ->", env.vfs_registry.read_item(prof, var, idx, reader="engine"))
        except Exception as e:
            print("   write_item:", type(e).__name__, e)
    try:
        env.vfs_registry.write_item("food", "freshness", torch.tensor([1.0, 2.0]), live[0][0] if live else 0, writer="engine"); print("   write_item with 2-element tensor ACCEPTED")
    except Exception as e:
        print("   write_item with 2-element tensor:", type(e).__name__, str(e)[:120])
    # item var ids collide with registry ids? declare a registry var named 'freshness'
    obs = env._get_observations()
    print("   obs shape", tuple(obs.shape), "item rows", [r for r in u.get_level("L0_smoke").token_spec.row_layout() if r[0] in ("item", "variable_element")][:6])


@probe("B. item-profile expression refuses at DTO (de52c40c03)")
def probe_b():
    import yaml
    p = make_pack("item_expr", base=ITEMS)
    payload = load_yaml(p / "variables.yaml")
    fresh = next(d for d in payload["variables"]["declarations"] if d["id"] == "freshness")
    fresh["expression"] = "bar.energy * 100"
    dump_yaml(p / "variables.yaml", payload)
    try:
        compile_pack(p, level="L0_smoke"); print("   COMPILED (bad)")
    except Exception as e:
        print("   refused:", str(e)[-400:])
    # item var with non-episode lifetime / tensor
    p = make_pack("item_tick", base=ITEMS)
    payload = load_yaml(p / "variables.yaml")
    fresh = next(d for d in payload["variables"]["declarations"] if d["id"] == "freshness")
    fresh["lifetime"] = "tick"
    dump_yaml(p / "variables.yaml", payload)
    try:
        compile_pack(p, level="L0_smoke"); print("   item lifetime tick COMPILED (bad)")
    except Exception as e:
        print("   item lifetime tick refused:", str(e)[-200:])


@probe("C. item variable id colliding with registry id; duplicate ids across profiles")
def probe_c():
    p = make_pack("item_collide", base=ITEMS)
    payload = load_yaml(p / "variables.yaml")
    payload["variables"]["declarations"].append(decl("freshness", scope="agent", initial_value=1.0))
    dump_yaml(p / "variables.yaml", payload)
    try:
        u = compile_pack(p, level="L0_smoke"); print("   registry 'freshness' + item food.freshness COMPILED; registry vars:", [v.id for v in u.get_level("L0_smoke").vfs_variables])
    except Exception as e:
        print("   refused:", str(e)[-300:])


if __name__ == "__main__":
    for fn in (probe_a, probe_b, probe_c):
        fn()
