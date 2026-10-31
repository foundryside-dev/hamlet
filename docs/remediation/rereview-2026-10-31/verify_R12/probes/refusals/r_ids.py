"""Item 4d: identifier grammar edge ids; keyword-prefixed ids end to end."""
import sys, re
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/authoring/probes")
from harness import *  # noqa
import harness
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/ids"); harness.PACKS.mkdir(parents=True, exist_ok=True)
def run(decls, read=None):
    p = make_pack("ids", variables=lambda v: v["declarations"].extend(decls))
    u, err = try_compile(p)
    if err:
        c = re.findall(r"\[([A-Z_\-]+)\]", err); i = err.find(" - "); return f"REFUSED {c[:1]} {err[i+3:i+170]}".replace("\n", " ")
    env = build_env(u, 2); step(env, "WAIT")
    return "OK" + ("" if read is None else f" {read}={env.vfs_registry.get(read, reader='engine').tolist()}")
for vid in ["_x", "x_", "X1", "__", "x1_y2", "énergie", "ñ", "x​", "true", "false", "and", "or", "not", "if", "then", "else", "True", "NOT", "nullref", "where", "min", "abs"]:
    print(f"declare {vid!r:12}: {run([decl(vid, initial_value=0.0)])}")
# reference each admitted edge id in an expression
for vid in ["_x", "x_", "X1", "__", "True", "where", "abs"]:
    print(f"read {vid!r:12}: {run([decl(vid, initial_value=0.5), decl('probe', initial_value=0.0, expression=f'{vid} + 1.0')], read='probe')}")
# keyword-prefixed ids: admitted by the grammar, misread by the parser
print("notable (bool true) + able (bool true), probe = if notable then 7 else 3:",
      run([decl("able", type="bool", initial_value=True), decl("notable", type="bool", initial_value=True),
           decl("probe", initial_value=0.0, expression="if notable then 7.0 else 3.0")], read="probe"))
print("notable alone, probe = if notable then 7 else 3:",
      run([decl("notable", type="bool", initial_value=True), decl("probe", initial_value=0.0, expression="if notable then 7.0 else 3.0")], read="probe"))
print("true_count declared + read:", run([decl("true_count", initial_value=1.0), decl("probe", initial_value=0.0, expression="true_count + 1.0")], read="probe"))
print("falsey declared + read:", run([decl("falsey", initial_value=1.0), decl("probe", initial_value=0.0, expression="falsey * 2.0")], read="probe"))
print("nothing (scalar) + hing (bool false): probe = where(nothing > 0.0, 1.0, 2.0):",
      run([decl("nothing", initial_value=5.0), decl("hing", type="bool", initial_value=False), decl("probe", initial_value=0.0, expression="where(nothing > 0.0, 1.0, 2.0)")], read="probe"))
