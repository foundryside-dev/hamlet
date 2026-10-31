"""Item 3b clamp on bool/ref; 3c persistent refs."""
import sys, re
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/authoring/probes")
from harness import *  # noqa
import harness
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/clamp"); harness.PACKS.mkdir(parents=True, exist_ok=True)
def res(p):
    u, err = try_compile(p)
    if err:
        c = re.findall(r"\[([A-Z_\-]+)\]", err); i = err.find(" - "); return f"REFUSED {c[:1]} {err[i+3:i+150]}".replace("\n", " ")
    try:
        env = build_env(u, 2); step(env, "WAIT"); return "COMPILED+RAN"
    except Exception as e: return f"RUNTIME {type(e).__name__}: {str(e)[:120]}"
TYPES = {"bool": ("true", False), "agent_ref": ("agent_id", None), "item_ref": ("-1", None), "affordance_ref": ("-1", None), "effect_ref": ("-1", None)}
for t, (expr, init) in TYPES.items():
    for prog in ["action", "rule"]:
        for clamp in ([0.0, 1.0], None):
            d = decl("x", scope="agent", type=t, initial_value=init)
            if prog == "action":
                p = make_pack("c", variables=lambda v, d=d: v["declarations"].append(d), actions=lambda a: add_action(a, "POKE", [write("x", expr, composition="overwrite", clamp=clamp)]))
            else:
                p = make_pack("c", variables=lambda v, d=d: v["declarations"].append(d), rules=[rule("r", [rwrite("x", expr, composition="overwrite", clamp=clamp)])])
            print(f"clamp {t:15} {prog:6} clamp={clamp}: {res(p)}", flush=True)
# composition clamp on bool with clamp set / null
for clamp in ([0.0, 1.0], None):
    d = decl("x", scope="agent", type="bool", initial_value=False)
    p = make_pack("c", variables=lambda v: v["declarations"].append(d), rules=[rule("r", [rwrite("x", "true", composition="clamp", clamp=clamp)])])
    print(f"composition=clamp bool clamp={clamp}: {res(p)}")
# global scope bool clamp
d = decl("g", scope="global", type="bool", initial_value=False)
p = make_pack("c", variables=lambda v: v["declarations"].append(d), rules=[rule("r", [rwrite("g", "true", composition="overwrite", clamp=[0.0, 1.0])])])
print(f"global bool rule clamp: {res(p)}")
# persistent refs
for t in ["agent_ref", "item_ref", "affordance_ref", "effect_ref"]:
    for scope in ["agent", "global"]:
        d = decl("pr", scope=scope, type=t, lifetime="persistent", initial_value=None)
        p = make_pack("c", variables=lambda v, d=d: v["declarations"].append(d))
        print(f"persistent {t:15} scope={scope}: {res(p)}")
