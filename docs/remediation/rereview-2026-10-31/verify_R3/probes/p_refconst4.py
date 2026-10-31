import torch
from harness import *
from r3pack import ITEMS_BASE, ILEVEL
expr = "max(-1, where(uniform() < 0.5, -1, 0))"
def acts(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "WAIT": ca["writes"] = [write("aref", expr, composition="overwrite")]
p = make_pack("rc4", variables=lambda v: v["declarations"].append(decl("aref", type="agent_ref", initial_value=None)), actions=acts, base=ITEMS_BASE, level=ILEVEL)
outcomes = []; admitted = None
for s in range(16):
    torch.manual_seed(s); u, err = try_compile(p, ILEVEL); outcomes.append("OK" if u else "REF")
    if u is not None and admitted is None: admitted = u
print("compile outcome by global seed 0..15:", outcomes)
if admitted is not None:
    env = build_env(admitted, 4, level=ILEVEL); rows = []
    for t in range(6):
        step(env, "WAIT"); rows.append(reg(env, "aref").tolist())
    print("runtime aref per world after WAIT (world w may hold only -1 or w):", rows)
