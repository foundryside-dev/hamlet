"""Hand-check newly admitted f_matrix cells in rules and action writes, and draw distributions."""
import torch
from harness import *
from townlet.determinism import seed_all
def decls():
    return [decl("vecv", type="vec2f", initial_value=[1.0, 2.0]), decl("vecw", type="vec2f", initial_value=[4.0, 6.0]),
            decl("gt", scope="global", initial_value=0.0), decl("at", initial_value=0.0), decl("abool", type="bool", initial_value=False)]
def run(label, ctx, expr, check, n=4, tgt="at"):
    kw = {"variables": lambda v: v["declarations"].extend(decls())}
    if ctx == "rule":
        kw["rules"] = [rule("r", [rwrite(tgt, expr, composition="overwrite")])]
    else:
        kw["actions"] = lambda a: [ca.__setitem__("writes", [write(tgt, expr, composition="overwrite")]) for ca in a["custom_actions"] if ca["name"] == "WAIT"]
    p = make_pack("val_" + str(abs(hash((ctx, expr, tgt))) % 10**8), **kw)
    u, err = try_compile(p)
    if u is None: print(f"{label:45s} REFUSED {short(err, 200)}"); return
    seed_all(1); env = build_env(u, n); e0 = meter(env, "energy").clone(); step(env, "WAIT")
    v = reg(env, tgt).float()
    ok, info = check(v, e0)
    print(f"{label:45s} {'OK ' if ok else 'BAD'} {info}")
for ctx in ["rule", "action"]:
    run(f"{ctx}: gather(vecv, 1)", ctx, "gather(vecv, 1)", lambda v, e: (torch.allclose(v, torch.full_like(v, 2.0)), v.tolist()))
    run(f"{ctx}: distance(vecv, vecw)", ctx, "distance(vecv, vecw)", lambda v, e: (torch.allclose(v, torch.full_like(v, 5.0)), v.tolist()))
    run(f"{ctx}: within_radius(vecv, vecw, 4.9)", ctx, "within_radius(vecv, vecw, 4.9)", lambda v, e: (bool((v == 0).all()), v.tolist()), tgt="abool")
    run(f"{ctx}: uniform(bar.energy, 1.0) N=2048", ctx, "uniform(bar.energy, 1.0)", lambda v, e: (bool(((v >= e) & (v < 1.0)).all()) and v.unique().numel() > 2000, f"min={v.min():.4f} max={v.max():.4f} energy0={e[0]:.4f} unique={v.unique().numel()}"), n=2048)
    run(f"{ctx}: normal_dist(0.0, 1.0) N=4096", ctx, "normal_dist(0.0, 1.0)", lambda v, e: (abs(float(v.mean())) < 0.06 and abs(float(v.std()) - 1) < 0.05, f"mean={v.mean():.4f} std={v.std():.4f}"), n=4096)
    run(f"{ctx}: global target uniform(0,1) N=2048", ctx, "uniform(0.0, 1.0)", lambda v, e: (bool(((v >= 0) & (v < 1)).all()) and v.unique().numel() > 2000 and abs(float(v.mean()) - .5) < .03, f"mean={v.mean():.4f} unique={v.unique().numel()}"), n=2048, tgt="gt")
