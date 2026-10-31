import torch
from harness import *
for expr in ["where(uniform() < 0.5, -1, 0)", "where(uniform() < 0.5, -1, -1)", "where(uniform() < 2.0, -1, 0)"]:
    def acts(a, expr=expr):
        for ca in a["custom_actions"]:
            if ca["name"] == "WAIT": ca["writes"] = [write("aref", expr, composition="overwrite")]
    p = make_pack("rc_" + str(abs(hash(expr)) % 10**6), variables=lambda v: v["declarations"].append(decl("aref", type="agent_ref", initial_value=None)), actions=acts)
    res = []
    for s in range(8):
        torch.manual_seed(s)
        before = torch.get_rng_state().clone()
        u, err = try_compile(p)
        res.append(("OK" if u else "REF") + ("*" if not torch.equal(before, torch.get_rng_state()) else ""))
    print(f"{expr:36s} compile outcomes over 8 global seeds (* = compile consumed global RNG): {res}")
    if err: print("   ", short(err[err.find(' - [') if ' - [' in err else 0:], 250))
