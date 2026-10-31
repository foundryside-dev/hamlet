import torch
import townlet.vfs.vtc as vtc
from harness import *
calls = [0]
orig = vtc._constant_value
def counting(ast):
    calls[0] += 1; return orig(ast)
vtc._constant_value = counting
expr = "where(uniform() < 0.5, -1, 0)"
def acts(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "WAIT": ca["writes"] = [write("aref", expr, composition="overwrite")]
p = make_pack("rc2", variables=lambda v: v["declarations"].append(decl("aref", type="agent_ref", initial_value=None)), actions=acts)
torch.manual_seed(0); try_compile(p); print("_constant_value calls per compile:", calls[0])
admitted = None
for s in range(300):
    torch.manual_seed(s)
    u, err = try_compile(p)
    if u is not None:
        admitted = (s, u); break
print("first global seed whose compile ADMITS the pack:", admitted and admitted[0])
if admitted:
    env = build_env(admitted[1], 4)
    rows = []
    for t in range(6):
        step(env, "WAIT"); rows.append(reg(env, "aref").tolist())
    print("aref per world after WAIT steps (world w should only ever hold -1 or w):", rows)
