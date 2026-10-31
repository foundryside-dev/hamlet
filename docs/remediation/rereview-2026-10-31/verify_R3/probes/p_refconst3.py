import torch
from harness import *
for expr in ["max(-1, where(uniform() < 0.5, -1, 0))", "-1 + where(uniform() < 0.5, 0, 1)"]:
    def acts(a, expr=expr):
        for ca in a["custom_actions"]:
            if ca["name"] == "WAIT": ca["writes"] = [write("aref", expr, composition="overwrite")]
    p = make_pack("rc3_" + str(abs(hash(expr)) % 10**6), variables=lambda v: v["declarations"].append(decl("aref", type="agent_ref", initial_value=None)), actions=acts)
    outcomes = []; admitted = None
    for s in range(24):
        torch.manual_seed(s)
        u, err = try_compile(p)
        outcomes.append("OK" if u else "REF")
        if u is not None and admitted is None: admitted = u
    print(f"{expr:42s} outcomes by global seed 0..23: {outcomes}")
    if err: print("    last refusal:", short(err[err.find(' - [') if ' - [' in err else 0:].replace(chr(10), ' '), 260))
    if admitted is not None:
        env = build_env(admitted, 4); rows = []
        for t in range(6):
            step(env, "WAIT"); rows.append(reg(env, "aref").tolist())
        print("    runtime aref per world (world w may hold only -1 or w):", rows)
