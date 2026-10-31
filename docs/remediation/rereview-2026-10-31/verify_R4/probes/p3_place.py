"""Area 3: per-world placement (D2)."""
import yaml, torch, re
from harness import *  # noqa
from harness import HERE, WT, BASE, make_pack, compile_pack, try_compile, build_env, short, load_yaml, dump_yaml
from townlet.determinism import seed_all
print("townlet at", __import__("townlet").__file__)
L1 = "L1_full_observability"

print("\n### distinct affordances per world; agents never on an affordance (L1 randomize true, N=64, 100 resets)")
u = compile_pack(make_pack("pl_base"), L1); seed_all(1); env = build_env(u, 64)
bad_aff = bad_agent = 0; layouts = set()
for k in range(100):
    env.reset()
    cells = [tuple(v.tolist()) for v in env.affordances.values()]
    if len(set(cells)) != len(cells): bad_aff += 1
    if any(tuple(p.tolist()) in set(cells) for p in env.positions): bad_agent += 1
    layouts.add(tuple(cells))
print(f"  resets with a duplicated affordance cell: {bad_aff}; with an agent on an affordance: {bad_agent}; distinct layouts: {len(layouts)}; in-bounds: {bool((env.positions>=0).all() and (env.positions<8).all())}")

print("\n### capacity boundary at compile (grid W x H; deployed affordances + 1)")
def grid_pack(name, w, h, n_aff, randomize=True):
    p = make_pack(name)
    s = load_yaml(p / "stratum.yaml"); s["stratum"]["substrate"]["grid"]["width"] = w; s["stratum"]["substrate"]["grid"]["height"] = h; dump_yaml(p / "stratum.yaml", s)
    for lvl in (p / "levels").iterdir():
        a = load_yaml(lvl / "affordances.yaml"); affs = a["affordances"]["affordances"]
        base = [x for x in affs if x["name"] == "EAT"][0]
        while len(affs) < n_aff:
            c = dict(base); c["name"] = f"X{len(affs)}"; affs.append(c)
        a["affordances"]["affordances"] = affs[:max(n_aff, 0)] if n_aff <= len(affs) else affs
        dump_yaml(lvl / "affordances.yaml", a)
        t = load_yaml(lvl / "training.yaml"); t["training"]["enabled_affordances"] = [x["name"] for x in a["affordances"]["affordances"]][:n_aff]; t["training"]["randomize_affordances"] = randomize; dump_yaml(lvl / "training.yaml", t)
    return p
for w, h, n in [(4, 4, 15), (4, 4, 16), (4, 4, 14), (3, 3, 8), (3, 3, 9)]:
    uu, err = try_compile(grid_pack(f"cap_{w}{h}_{n}", w, h, n), L1)
    if uu is None:
        m = re.search(r"\[([A-Z_\-]+)\] (\S+)", err); print(f"  {w}x{h} cells={w*h} deployed={n}: REFUSED {m.group(1) if m else ''} @{m.group(2).split('/')[-1] if m else ''} :: {short(err[err.find(' - ')+3:].replace(chr(10),' '), 160)}")
    else:
        try:
            seed_all(2); e = build_env(uu, 3); cells = [tuple(v.tolist()) for v in e.affordances.values()]
            print(f"  {w}x{h} cells={w*h} deployed={n}: COMPILED; env ok; distinct affordances={len(set(cells))==len(cells)}; agent on affordance={any(tuple(p.tolist()) in set(cells) for p in e.positions)} agents={e.positions.tolist()}")
        except Exception as ex:
            print(f"  {w}x{h} cells={w*h} deployed={n}: COMPILED; RUNTIME {type(ex).__name__}: {short(str(ex), 160)}")
# deployed vs declared: 14 declared, 2 deployed on a 2x2 grid
p = grid_pack("cap_declared", 2, 2, 14)
for lvl in (p / "levels").iterdir():
    t = load_yaml(lvl / "training.yaml"); t["training"]["enabled_affordances"] = ["EAT", "SLEEP"]; dump_yaml(lvl / "training.yaml", t)
uu, err = try_compile(p, L1); print("  2x2 with 14 declared / 2 deployed:", "COMPILED" if uu else "REFUSED " + short(err[err.find(' - ')+3:].replace(chr(10), ' '), 160))
if uu:
    try:
        seed_all(2); e = build_env(uu, 4); print("    env ok affordances", {k: v.tolist() for k, v in e.affordances.items()}, "agents", e.positions.tolist())
    except Exception as ex:
        print("    RUNTIME", type(ex).__name__, short(str(ex), 200))
# randomize false on a full grid: compiles? agent spawn on an affordance?
p = grid_pack("cap_fixed", 4, 4, 16, randomize=False)
for lvl in (p / "levels").iterdir():
    a = load_yaml(lvl / "affordances.yaml")
    for i, x in enumerate(a["affordances"]["affordances"]): x["deployment"] = {"type": "fixed", "positions": [[i % 4, i // 4]]}
    dump_yaml(lvl / "affordances.yaml", a)
uu, err = try_compile(p, L1); print("  4x4 randomize false, 16 fixed affordances filling the grid:", "COMPILED" if uu else "REFUSED " + short(err[err.find(' - ')+3:].replace(chr(10), ' '), 200))
if uu:
    try:
        seed_all(2); e = build_env(uu, 4); cells = {tuple(v.tolist()) for v in e.affordances.values()}
        print("    env ok; agents on affordances:", [tuple(p.tolist()) in cells for p in e.positions])
    except Exception as ex:
        print("    RUNTIME", type(ex).__name__, short(str(ex), 200))

print("\n### compile capacity vs substrate.get_capacity on 3D grid and gridnd")
from townlet.universe.validation.feasibility import grid_capacity_for_substrate
for pack, lvl in [(WT / "configs/differential/div003_cubic_partial", "L2_partial_observability"), (WT / "configs/test/gridnd_4d_pack", None)]:
    lvl = lvl or [p.name for p in (pack / "levels").iterdir()][0]
    uu = compile_pack(pack, lvl); e = uu.create_environment(num_agents=1, level_name=lvl, device="cpu")
    print(f"  {pack.name}: compile={grid_capacity_for_substrate(uu.stratum_config.substrate) if hasattr(uu, 'stratum_config') else '?'} runtime={e.substrate.get_capacity()}")

print("\n### randomize false uses declared positions exactly")
p = make_pack("fixed_l1")
t = load_yaml(p / "levels" / L1 / "training.yaml"); t["training"]["randomize_affordances"] = False; dump_yaml(p / "levels" / L1 / "training.yaml", t)
uu = compile_pack(p, L1); seed_all(3); e = build_env(uu, 3)
declared = {a["name"]: a["deployment"]["positions"][0] for a in load_yaml(p / "levels" / L1 / "affordances.yaml")["affordances"]["affordances"]}
print("  all equal declared:", all(e.affordances[k].tolist() == v for k, v in declared.items()), "| agents on an affordance:", [tuple(q.tolist()) in {tuple(x) for x in declared.values()} for q in e.positions])

print("\n### same-seed reproducibility; N-dependence; global RNG use")
def layout(n, seed=5):
    seed_all(seed); e = build_env(u, n); return {k: v.clone() for k, v in e.affordances.items()}, e.positions.clone()
l2a, p2a = layout(2); l2b, p2b = layout(2); l5, p5 = layout(5)
print("  same seed N=2 twice: layout equal", all(torch.equal(l2a[k], l2b[k]) for k in l2a), "agents equal", torch.equal(p2a, p2b))
print("  layout N=2 vs N=5 equal:", all(torch.equal(l2a[k], l5[k]) for k in l2a), "| world 0/1 agent pos N=2 vs N=5 equal:", torch.equal(p2a, p5[:2]), p2a.tolist(), p5[:2].tolist())
seed_all(5); e = build_env(u, 4); s0 = torch.get_rng_state().clone(); e.reset(); print("  reset consumes torch global RNG:", not torch.equal(s0, torch.get_rng_state()))
import inspect
src = inspect.getsource(type(e)._sample_free_cells) + inspect.getsource(type(e)._sample_distinct_cells)
print("  generator=None / randperm / randint in placement code:", src.count("generator=None"), src.count("randperm"), src.count("randint"))
