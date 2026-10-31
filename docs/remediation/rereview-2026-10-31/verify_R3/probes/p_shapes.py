"""Attack derived shape rules: compile + step + hand-check values."""
import torch, sys
from harness import *
from townlet.determinism import seed_all

def base_decls():
    return [
        decl("flag", type="bool", initial_value=True),
        decl("gflag", scope="global", type="bool", initial_value=False),
        decl("gstat", scope="global", initial_value=0.25),
        decl("ascalar", initial_value=0.5),
        decl("vecv", type="vec2f", initial_value=[1.0, 2.0]),
        decl("vec3", type="vec3f", initial_value=[1.0, 2.0, 2.0]),
        decl("gvec", scope="global", type="vec2f", initial_value=[4.0, 6.0]),
        decl("vni", type="vecNf", dims=3, initial_value=[1.0, 2.0, 3.0]),
        decl("vni4", type="vecNf", dims=4, initial_value=[1.0, 2.0, 3.0, 4.0]),
        decl("t1", type="tensor1d", shape=[3], initial_value_mode="zeros", initial_value_params=None),
    ]

def cell(label, scope, rtype, expr, hand=None, extra=()):
    name = "sh_" + str(abs(hash((scope, expr))) % 10**8)
    def variables(v):
        decls = base_decls() + list(extra)
        decls.append(decl("x", scope=scope, type=rtype, initial_value=(False if rtype == "bool" else 0.0), expression=expr))
        v["declarations"].extend(decls)
    try:
        p = make_pack(name, variables=variables)
    except Exception as e:
        print(f"{label:58s} PACK ERR {e}"); return
    u, err = try_compile(p)
    if u is None:
        m = err.replace("\n", " ")
        i = m.find(expr[:20])
        print(f"{label:58s} REFUSED: {short(m[max(0, m.find('Variable')):], 260)}"); return
    try:
        seed_all(1)
        env = build_env(u, 3)
        v0 = reg(env, "x").clone()
        step(env, "WAIT")
        v1 = reg(env, "x").clone()
        msg = f"OK reset={[round(float(z), 4) for z in v0.flatten()[:3]]} step1={[round(float(z), 4) for z in v1.flatten()[:3]]} shape={tuple(v1.shape)}"
        if hand is not None:
            h = hand(env)
            msg += f" hand={[round(float(z), 4) for z in torch.as_tensor(h).flatten()[:3]]} {'MATCH' if torch.allclose(v1.float(), torch.as_tensor(h).float().expand_as(v1), equal_nan=True) else 'MISMATCH'}"
        print(f"{label:58s} {msg}")
    except Exception as e:
        print(f"{label:58s} COMPILES, RUNTIME {type(e).__name__}: {short(str(e), 200)}")

E = lambda env: meter(env, "energy")
pos = lambda env: env.positions.float()
eat = lambda env: env.affordances["EAT"].float()
cases = [
    # vectors through pointwise functions (payload label removed)
    ("agent: vecv + 1.0", "agent", "scalar", "vecv + 1.0"),
    ("agent: abs(vecv)", "agent", "scalar", "abs(vecv)"),
    ("agent: sum(vecv)", "agent", "scalar", "sum(vecv)"),
    ("agent: max_all(vecv, vecv)", "agent", "scalar", "max_all(vecv, vecv)"),
    ("agent: mean(vecv, vecv)", "agent", "scalar", "mean(vecv, vecv)"),
    ("agent: where(flag, vecv, vecv)", "agent", "scalar", "where(flag, vecv, vecv)"),
    ("agent: clamp(vecv, 0.0, 1.0)", "agent", "scalar", "clamp(vecv, 0.0, 1.0)"),
    ("agent: count_where(vecv)", "agent", "scalar", "count_where(vecv)"),
    ("agent: vecv == vecv (bool)", "agent", "bool", "vecv == vecv"),
    ("agent: argmax(vecv, vecv)", "agent", "scalar", "argmax(vecv, vecv)"),
    ("agent: perlin_noise(vecv)", "agent", "scalar", "perlin_noise(vecv)"),
    ("agent: uniform(vecv)", "agent", "scalar", "uniform(vecv)"),
    ("agent: t1 + 0.0", "agent", "scalar", "t1 + 0.0"),
    ("agent: gather(t1, 0)", "agent", "scalar", "gather(t1, 0)"),
    # vector functions
    ("agent: distance(vecv, gvec) (global vec)", "agent", "scalar", "distance(vecv, gvec)", lambda env: torch.full((3,), (9 + 16) ** 0.5)),
    ("agent: distance(gvec, gvec) only global", "agent", "scalar", "distance(gvec, gvec)"),
    ("global: distance(gvec, gvec)", "global", "scalar", "distance(gvec, gvec)", lambda env: torch.zeros(3)),
    ("global: gather(gvec, 1)", "global", "scalar", "gather(gvec, 1)", lambda env: torch.full((3,), 6.0)),
    ("agent: gather(vecv, 5) out of range", "agent", "scalar", "gather(vecv, 5)"),
    ("agent: gather(vecv, -1)", "agent", "scalar", "gather(vecv, -1)"),
    ("agent: gather(vecv, ascalar*4)", "agent", "scalar", "gather(vecv, floor(ascalar * 4.0))"),
    ("agent: distance(vecv, vec3) widths 2/3", "agent", "scalar", "distance(vecv, vec3)"),
    ("agent: distance(vni, vni4) vecN widths 3/4", "agent", "scalar", "distance(vni, vni4)"),
    ("agent: distance(vecv, vni) vec2 vs vecN3", "agent", "scalar", "distance(vecv, vni)"),
    ("agent: manhattan_distance(vecv, gvec)", "agent", "scalar", "manhattan_distance(vecv, gvec)", lambda env: torch.full((3,), 7.0)),
    ("agent: within_radius(vecv, gvec, 5.0)", "agent", "bool", "within_radius(vecv, gvec, 5.0)", lambda env: torch.full((3,), True)),
    ("agent: nearest(vecv, gvec)", "agent", "scalar", "nearest(vecv, gvec)"),
    # broadcast stats
    ("agent: mean(bar.energy, gstat)", "agent", "scalar", "mean(bar.energy, gstat)", lambda env: (E(env) + 0.25) / 2),
    ("agent: mean(bar.energy, 1.0)", "agent", "scalar", "mean(bar.energy, 1.0)", lambda env: (E(env) + 1.0) / 2),
    ("agent: variance(bar.energy, gstat, 1.0)", "agent", "scalar", "variance(bar.energy, gstat, 1.0)", lambda env: torch.stack([E(env), torch.full((3,), 0.25), torch.ones(3)]).var(0, unbiased=False)),
    ("agent: argmax(gstat, bar.energy)", "agent", "scalar", "argmax(gstat, bar.energy)", lambda env: (E(env) > 0.25).long()),
    ("agent: count_where(flag, gflag)", "agent", "scalar", "count_where(flag, gflag)", lambda env: torch.ones(3)),
    ("global: mean(gstat, 1.0)", "global", "scalar", "mean(gstat, 1.0)", lambda env: torch.full((3,), 0.625)),
    ("global: mean(bar.energy, gstat) (agent in global)", "global", "scalar", "mean(bar.energy, gstat)"),
    # where with mixed shapes
    ("agent: where(gflag, bar.energy, gstat)", "agent", "scalar", "where(gflag, bar.energy, gstat)", lambda env: torch.full((3,), 0.25)),
    ("global: where(flag, gstat, 0.0)", "global", "scalar", "where(flag, gstat, 0.0)"),
    ("agent: where(flag, 1.0, 0.0) (agent cond only)", "agent", "scalar", "where(flag, 1.0, 0.0)", lambda env: torch.ones(3)),
    # nested
    ("agent: max(distance_to_affordance(EAT), uniform())", "agent", "scalar", 'max(distance_to_affordance("EAT"), uniform())'),
    ("agent: sigmoid(distance(vecv, gvec))", "agent", "scalar", "sigmoid(distance(vecv, gvec))", lambda env: torch.sigmoid(torch.full((3,), 5.0))),
    ("agent: dist_to_aff(EAT) - dist_to_aff(EAT,euclid)", "agent", "scalar", 'distance_to_affordance("EAT") - distance_to_affordance("EAT", "euclidean")', lambda env: (pos(env) - eat(env)).abs().sum(-1) - (pos(env) - eat(env)).pow(2).sum(-1).sqrt()),
    ("agent: gather(direction_to_affordance(EAT), 0)", "agent", "scalar", 'gather(direction_to_affordance("EAT"), 0)', lambda env: torch.where((pos(env) - eat(env)).abs().sum(-1) > 0, (eat(env) - pos(env))[:, 0] / (pos(env) - eat(env)).abs().sum(-1), torch.zeros(3))),
    ("agent: distance(direction_to_affordance(EAT), vecv)", "agent", "scalar", 'distance(direction_to_affordance("EAT"), vecv)'),
    ("global: distance_to_affordance(EAT) (global)", "global", "scalar", 'distance_to_affordance("EAT")'),
    ("global: uniform() global", "global", "scalar", "uniform()"),
    ("agent: uniform() literal-only agent", "agent", "scalar", "uniform()"),
    ("agent: uniform(gstat, 1.0) global args, agent scope", "agent", "scalar", "uniform(gstat, 1.0)"),
    # history of a spatial value
    ("agent: lag(distance_to_affordance(EAT), 1)", "agent", "scalar", 'lag(distance_to_affordance("EAT"), 1)'),
    ("agent: ema(in_range(EAT,1.0), 0.5)", "agent", "scalar", 'ema(where(in_range("EAT", 1.0), 1.0, 0.0), 0.5)'),
    ("agent: lag(uniform(), 1)", "agent", "scalar", "lag(uniform(), 1)"),
]
only = sys.argv[1:]
for c in cases:
    if only and not any(o in c[0] for o in only): continue
    cell(*c)
# history of a spatial value via a named variable
cell("agent: lag(dvar, 1) where dvar=distance_to_affordance", "agent", "scalar", "lag(dvar, 1)",
     extra=[decl("dvar", initial_value=0.0, expression='distance_to_affordance("EAT")')])
cell("agent: ema(dvar, 0.5) where dvar=distance_to_affordance", "agent", "scalar", "ema(dvar, 0.5)",
     extra=[decl("dvar", initial_value=0.0, expression='distance_to_affordance("EAT")')])
