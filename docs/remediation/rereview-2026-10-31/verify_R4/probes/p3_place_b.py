import re, torch
from harness import *  # noqa
from harness import make_pack, compile_pack, try_compile, build_env, short, load_yaml, dump_yaml
from townlet.determinism import seed_all
L1 = "L1_full_observability"
def grid_pack(name, w, h, randomize=True):
    p = make_pack(name)
    s = load_yaml(p / "stratum.yaml"); s["stratum"]["substrate"]["grid"]["width"] = w; s["stratum"]["substrate"]["grid"]["height"] = h; dump_yaml(p / "stratum.yaml", s)
    for lvl in (p / "levels").iterdir():
        t = load_yaml(lvl / "training.yaml"); t["training"]["randomize_affordances"] = randomize; dump_yaml(lvl / "training.yaml", t)
    return p
for w, h in [(3, 5), (2, 7), (4, 4), (1, 15), (1, 14)]:
    uu, err = try_compile(grid_pack(f"capb_{w}{h}", w, h), L1)
    if uu is None:
        m = re.search(r"\[([A-Z_\-]+)\] (\S+)", err); print(f"  {w}x{h} cells={w*h} deployed=14: REFUSED {m.group(1)} @{m.group(2).split('/')[-1]} :: {short(err[err.find(' - ')+3:].replace(chr(10),' '), 230)}")
    else:
        try:
            ok = True; onaff = False
            seed_all(2); e = build_env(uu, 50)
            for _ in range(30):
                e.reset(); cells = [tuple(v.tolist()) for v in e.affordances.values()]
                ok &= len(set(cells)) == len(cells); onaff |= any(tuple(p.tolist()) in set(cells) for p in e.positions)
            print(f"  {w}x{h} cells={w*h} deployed=14: COMPILED; 30 resets N=50: distinct={ok} agent-on-affordance={onaff}")
        except Exception as ex:
            print(f"  {w}x{h}: COMPILED; RUNTIME {type(ex).__name__}: {short(str(ex), 160)}")
# runtime guard when the compile is bypassed: env with capacity < affordances+1
uu = compile_pack(grid_pack("capb_44b", 4, 4), L1); e = build_env(uu, 2)
e.substrate.width = 3; e.substrate.height = 4
try:
    e.reset(); print("  bypass (capacity 12 < 15): reset ran")
except Exception as ex:
    print("  bypass (capacity 12 < 15): ", type(ex).__name__, short(str(ex), 120))
# does the compile count use levels' deployed counts with the primary level only? Give L0_0 a 2x2-overflow: compile L1 (14 deployed, 16 cells) while L0_0 deploys 14 too -> both refuse at 2x7? covered. Check location:
uu, err = try_compile(grid_pack("capb_27", 2, 7), L1); print("  locations in refusal:", re.findall(r"@?(levels/\S+?:\d+)|(training\.yaml:\d+)", err)[:6])
