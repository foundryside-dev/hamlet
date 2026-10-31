import traceback, torch
from harness import *
for label, t1decl, expr in [
  ("tensor1d zeros-mode", decl("t1", type="tensor1d", shape=[3], initial_value_mode="zeros"), "gather(t1, 0)"),
  ("tensor1d literal", decl("t1", type="tensor1d", shape=[3], initial_value=[1.0, 2.0, 3.0]), "gather(t1, 2)"),
  ("vec2f via initial_value_mode? n/a; vecv literal, x reads gather + flag", decl("t1", type="vec2f", initial_value=[1.0, 2.0]), "gather(t1, 1)"),
  ("vec bool compare !=", decl("t1", type="vec2f", initial_value=[1.0, 2.0]), "t1 != t1"),
  ("vec bool compare > gvec", decl("t1", type="vec2f", initial_value=[1.0, 2.0]), "t1 > 0.5"),
]:
    rtype = "bool" if "compare" in label else "scalar"
    p = make_pack("t1_" + str(abs(hash(label)) % 10**6), variables=lambda v: v["declarations"].extend([t1decl, decl("x", type=rtype, initial_value=(False if rtype=="bool" else 0.0), expression=expr)]))
    u, err = try_compile(p)
    if u is None: print(label, "REFUSED", short(err.replace("\n"," "), 300)); continue
    try:
        env = build_env(u, 2); step(env, "WAIT"); print(label, "OK", reg(env, "x").tolist())
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-3:]
        print(label, "RUNTIME", type(e).__name__, e, [f"{f.filename.split('/src/')[-1]}:{f.lineno}" for f in tb])
