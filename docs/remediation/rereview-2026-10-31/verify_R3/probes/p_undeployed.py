import torch, yaml
from harness import *
NORM = {"kind": "minmax", "min": 0.0, "max": 100.0, "clip": True}
def mk(expr, name, exposed=True, undeploy=None):
    def variables(v):
        v["declarations"].append(decl("d", initial_value=0.0, expression=expr, exposed=("agent",) if exposed else (), normalization=NORM if exposed else None))
    p = make_pack(name, variables=variables)
    if undeploy:
        t = p / "levels" / LEVEL / "training.yaml"; d = yaml.safe_load(open(t))
        d["training"]["enabled_affordances"] = [a for a in d["training"]["enabled_affordances"] if a != undeploy]
        yaml.safe_dump(d, open(t, "w"), sort_keys=False)
    return p
for label, expr, exp, und in [
    ("typo name, exposed", 'distance_to_affordance("NOPE")', True, None),
    ("typo name, unexposed", 'distance_to_affordance("NOPE")', False, None),
    ("undeployed EAT, exposed", 'distance_to_affordance("EAT")', True, "EAT"),
    ("undeployed EAT, unexposed", 'distance_to_affordance("EAT")', False, "EAT"),
    ("undeployed EAT, in_range", 'where(in_range("EAT", 2.0), 1.0, 0.0)', True, "EAT"),
    ("min of two, one undeployed", 'min(distance_to_affordance("EAT"), distance_to_affordance("COOK"))', True, "EAT"),
]:
    p = mk(expr, "und_" + str(abs(hash(label)) % 10**6), exp, und)
    u, err = try_compile(p)
    if u is None:
        print(f"{label:32s} REFUSED {short(err, 250)}"); continue
    try:
        env = build_env(u, 2)
        print(f"{label:32s} COMPILES; reset ok; d={reg(env,'d').tolist()}")
    except Exception as e:
        print(f"{label:32s} COMPILES; RUNTIME {type(e).__name__}: {short(str(e), 160)}")
