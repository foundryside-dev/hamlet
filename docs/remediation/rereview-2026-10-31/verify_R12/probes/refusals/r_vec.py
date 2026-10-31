"""Item 3a: vector/tensor target constant-only rule, every type, both programs."""
import sys, re
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/authoring/probes")
from harness import *  # noqa
import harness
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/refusals_" + (sys.argv[2] if len(sys.argv) > 2 else "x")); harness.PACKS.mkdir(parents=True, exist_ok=True)
import torch

TYPES = {
  "vec2i": dict(initial_value=[0, 0]), "vec3i": dict(initial_value=[0, 0, 0]),
  "vec2f": dict(initial_value=[0.0, 0.0]), "vec3f": dict(initial_value=[0.0, 0.0, 0.0]),
  "vecNi": dict(dims=3, initial_value=[0, 0, 0]), "vecNf": dict(dims=3, initial_value=[0.0, 0.0, 0.0]),
  "tensor1d": dict(shape=[3], initial_value_mode="zeros"), "tensor2d": dict(shape=[2, 2], initial_value_mode="zeros"),
  "tensor3d": dict(shape=[2, 1, 2], initial_value_mode="zeros"), "tensorNd": dict(shape=[2, 1, 1, 2], initial_value_mode="zeros"),
}
def mk(t, scope="agent"):
    kw = dict(TYPES[t]); d = decl("tgt", scope=scope, type=t, **kw)
    if "initial_value_mode" in kw: d.pop("initial_value", None)
    return d
COMMON = [decl("av", scope="agent", type="scalar", initial_value=0.25), decl("gv", scope="global", type="scalar", initial_value=0.5),
          decl("kconst", scope="global", type="scalar", initial_value=0.0, expression="2.0"),
          decl("kconst2", scope="global", type="scalar", initial_value=0.0, expression="kconst + 1.0"),
          decl("ib", scope="agent", type="bool", initial_value=True)]
EXPRS_F = ["1.0", "where(true, 1.0, 2.0)", "if true then 3.0 else 0.0", "1.0 + 2.0", "kconst", "kconst2", "av", "gv", "tick", "agent_id", "bar.energy", "where(ib, 1.0, 2.0)", "max(1.0, 2.0)"]
def run(t, prog, expr, scope="agent"):
    is_int = t.endswith("i")
    e = expr if not is_int else expr.replace("1.0", "1").replace("2.0", "2").replace("3.0", "3").replace("0.0", "0")
    decls = COMMON + [mk(t, scope)]
    if prog == "action":
        p = make_pack("vec", variables=lambda v: v["declarations"].extend(decls),
                      actions=lambda a: add_action(a, "POKE", [write("tgt", e, composition="overwrite")]))
    else:
        p = make_pack("vec", variables=lambda v: v["declarations"].extend(decls), rules=[rule("r", [rwrite("tgt", e, composition="overwrite")])])
    u, err = try_compile(p)
    if err:
        code = re.findall(r"\[([A-Z_\-]+)\]", err); return f"REFUSED {code[:1]} " + ("(element-payload)" if "has elements" in err else err[err.find(' - ')+3:][:90].replace("\n", " "))
    try:
        env = build_env(u, 2)
        step(env, "POKE" if prog == "action" else "WAIT")
        v = env.vfs_registry.get("tgt", reader="engine")
        return f"RAN -> {v.flatten().tolist()[:6]}"
    except Exception as ex:
        return f"RUNTIME {type(ex).__name__}: {str(ex)[:120]}"
if __name__ == "__main__":
    types = sys.argv[1].split(",") if len(sys.argv) > 1 else list(TYPES)
    for t in types:
        for prog in ["action", "rule"]:
            for expr in EXPRS_F:
                print(f"{t:9} {prog:6} {expr:28} {run(t, prog, expr)}", flush=True)
    # global-scope vector target, rule only
    for expr in ["1.0", "gv", "kconst"]:
        print(f"vec2f(global) rule {expr:22} {run('vec2f', 'rule', expr, scope='global')}", flush=True)
