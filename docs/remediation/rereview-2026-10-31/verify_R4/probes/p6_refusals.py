"""Area 6: the new compile refusals and attempts to evade them from every expression source."""
import re, yaml, torch
from harness import *  # noqa
from harness import HERE, WT, make_pack, decl, write, rule, rwrite, try_compile, build_env, step, reg, short, load_yaml, dump_yaml
print("townlet at", __import__("townlet").__file__)
L1 = "L1_full_observability"
ASP = WT / "configs/aspatial_test"; ASPL = [p.name for p in (ASP / "levels").iterdir()][0]
NORM = {"kind": "minmax", "min": 0.0, "max": 100.0, "clip": True}

def outcome(pk, level=L1, n=2, act="WAIT"):
    u, err = try_compile(pk, level)
    if u is None:
        codes = re.findall(r"\[([A-Z_\-]+)\] (\S+?):(\d+)", err)
        return "REFUSED " + ", ".join(f"[{c}] {f.split('/')[-1]}:{l}" for c, f, l in codes[:3]) + " :: " + short(err[err.find(" - ") + 3:].replace("\n", " "), 150)
    try:
        env = build_env(u, n, level=level); step(env, act); return "COMPILED+RAN"
    except Exception as ex:
        return f"COMPILED; RUNTIME {type(ex).__name__}: {short(str(ex), 150)}"

def var_pack(name, expr, base=None, level=L1, extra=()):
    kw = dict(base=base, level=level) if base else {}
    return make_pack(name, variables=lambda v: v["declarations"].extend([*extra, decl("d", initial_value=0.0, expression=expr)]), **kw)

print("\n### EXPRESSION-POSITION-ASPATIAL (aspatial_test) from every source")
print("  variable:", outcome(var_pack("asp_v", 'distance_to_affordance("EAT")', base=ASP, level=ASPL), level=ASPL))
print("  variable nested:", outcome(var_pack("asp_n", 'max(0.0, min(1.0, distance_to_affordance("EAT")))', base=ASP, level=ASPL), level=ASPL))
print("  variable in_range:", outcome(var_pack("asp_i", 'where(in_range("EAT", 1.0), 1.0, 0.0)', base=ASP, level=ASPL), level=ASPL))
aff_names = [a["name"] for a in load_yaml(ASP / "levels" / ASPL / "affordances.yaml")["affordances"]["affordances"]]
print("  (aspatial affordances:", aff_names, ")")
print("  rule:", outcome(make_pack("asp_r", base=ASP, level=ASPL, variables=lambda v: v["declarations"].append(decl("t", initial_value=0.0)), rules=[rule("r", [rwrite("t", f'distance_to_affordance("{aff_names[0]}")', composition="overwrite")])]), level=ASPL))
def eff_asp(e):
    e["effect_definitions"] = [{"id": "e1", "scope": "agent", "duration": 2, "reapply_policy": "renew", "observable": False, "on_spawn": [],
                                "on_tick": [{"modify": "bar.energy", "value": f'bar.energy - 0.001 * distance_to_affordance("{aff_names[0]}")'}], "on_despawn": [], "on_interrupt": []}]
    e["max_active_effects"] = {"global": 0, "agent": 2, "item": 0, "affordance": 0}
if (ASP / "effects.yaml").exists():
    print("  effect on_tick:", outcome(make_pack("asp_e", base=ASP, level=ASPL, effects=eff_asp), level=ASPL))
else:
    print("  effect: aspatial_test has no effects.yaml; skipped (covered on default_curriculum below)")
def inter_asp(payload):
    payload["affordances"][0]["interactions"]["on_start"].append({"modify": "bar.energy", "value": f'bar.energy + 0.0 * distance_to_affordance("{aff_names[0]}")'})
print("  interaction on_start:", outcome(make_pack("asp_x", base=ASP, level=ASPL, affordances=inter_asp), level=ASPL))

print("\n### EXPRESSION-AFFORDANCE-UNKNOWN from every source (default_curriculum L1)")
print("  variable:", outcome(var_pack("unk_v", 'distance_to_affordance("NOPE")')))
print("  variable nested in where/max:", outcome(var_pack("unk_n", 'max(0.0, where(true, distance_to_affordance("NOPE"), 0.0))')))
print("  direction_to_affordance gather:", outcome(var_pack("unk_d", 'gather(direction_to_affordance("NOPE"), 0)')))
print("  in_range:", outcome(var_pack("unk_i", 'where(in_range("NOPE", 2.0), 1.0, 0.0)')))
print("  inlined chain (d2 := d + 1, d := dist(NOPE)):", outcome(make_pack("unk_c", variables=lambda v: v["declarations"].extend([decl("d", initial_value=0.0, expression='distance_to_affordance("NOPE")'), decl("d2", initial_value=0.0, expression="d + 1.0")]))))
print("  lower-case name 'eat':", outcome(var_pack("unk_lc", 'distance_to_affordance("eat")')))
print("  rule write:", outcome(make_pack("unk_r", variables=lambda v: v["declarations"].append(decl("t", initial_value=0.0)), rules=[rule("r", [rwrite("t", 'distance_to_affordance("NOPE")', composition="overwrite")])])))
print("  rule condition:", outcome(make_pack("unk_rc", variables=lambda v: v["declarations"].append(decl("t", initial_value=0.0)), rules=[rule("r", [rwrite("t", "1.0", composition="overwrite", condition='in_range("NOPE", 1.0)')])])))
def act_unk(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["writes"] = [write("t", 'distance_to_affordance("NOPE")', composition="overwrite")]
print("  action write:", outcome(make_pack("unk_a", variables=lambda v: v["declarations"].append(decl("t", initial_value=0.0)), actions=act_unk)))
def act_cond(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["writes"] = [write("t", "1.0", composition="overwrite", condition='in_range("NOPE", 1.0)')]
print("  action write condition:", outcome(make_pack("unk_ac", variables=lambda v: v["declarations"].append(decl("t", initial_value=0.0)), actions=act_cond)))
def eff_unk(e):
    e["effect_definitions"] = [{"id": "e1", "scope": "agent", "duration": 2, "reapply_policy": "renew", "observable": False, "on_spawn": [],
                                "on_tick": [{"modify": "bar.energy", "value": 'bar.energy - 0.001 * distance_to_affordance("NOPE")'}], "on_despawn": [], "on_interrupt": []}]
    e["max_active_effects"] = {"global": 0, "agent": 2, "item": 0, "affordance": 0}
print("  effect on_tick value:", outcome(make_pack("unk_e", effects=eff_unk)))
def eff_cond(e):
    e["effect_definitions"] = [{"id": "e1", "scope": "agent", "duration": 2, "reapply_policy": "renew", "observable": False, "on_spawn": [],
                                "on_tick": [{"if": 'in_range("NOPE", 1.0)', "do": [{"modify": "bar.energy", "value": "bar.energy - 0.001"}]}], "on_despawn": [], "on_interrupt": []}]
    e["max_active_effects"] = {"global": 0, "agent": 2, "item": 0, "affordance": 0}
print("  effect if-condition:", outcome(make_pack("unk_ec", effects=eff_cond)))
def inter_unk(payload):
    payload["affordances"][0]["interactions"]["on_start"].append({"modify": "bar.mood", "value": 'bar.mood + 0.0 * distance_to_affordance("NOPE")'})
print("  interaction on_start value:", outcome(make_pack("unk_x", affordances=inter_unk)))
ITEMS = WT / "configs/test/items_smoke"; IL = "L0_smoke"
def item_when(pk):
    p = pk / "levels" / IL / "items.yaml"; d = load_yaml(p); d["items"][0]["when"] = 'distance_to_affordance("NOPE") > 1.0'; dump_yaml(p, d); return pk
print("  item spawn when:", outcome(item_when(make_pack("unk_w", base=ITEMS, level=IL)), level=IL))
def item_hook(pk):
    p = pk / "items.yaml"; d = load_yaml(p); txt = p.read_text(); return pk
print("  items.yaml top-level keys:", list(load_yaml(ITEMS / "items.yaml").keys()))
# false positive: prose that parses as an expression, in a description / telemetry_label
def desc(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["description"] = 'distance_to_affordance("NOPE")'
print("  prose (action description) that parses:", outcome(make_pack("unk_desc", actions=desc)))
print("  telemetry_label that parses:", outcome(make_pack("unk_tl", variables=lambda v: v["declarations"].append(decl("t", initial_value=0.0)), rules=[rule("r", [dict(rwrite("t", "1.0", composition="overwrite"))], )], extra_files={}) if False else make_pack("unk_tl2", variables=lambda v: v["declarations"].append(decl("t", initial_value=0.0, description='in_range("NOPE", 1.0)')))))

print("\n### EXPRESSION-AFFORDANCE-UNDEPLOYED: levels deploying different sets; level-scoped sources")
def undeploy(pk, level, name):
    t = pk / "levels" / level / "training.yaml"; d = load_yaml(t); d["training"]["enabled_affordances"] = [a for a in d["training"]["enabled_affordances"] if a != name]; dump_yaml(t, d); return pk
print("  pack var names EAT; L0_0 does not deploy EAT; compile L1:", outcome(undeploy(var_pack("und_a", 'distance_to_affordance("EAT")'), "L0_0_minimal", "EAT")))
print("  pack var names EAT; L1 does not deploy EAT; compile L1:", outcome(undeploy(var_pack("und_b", 'distance_to_affordance("EAT")'), L1, "EAT")))
def inter_eat(payload):
    for aff in payload["affordances"]:
        if aff["name"] == "SLEEP": aff["interactions"]["on_start"].append({"modify": "bar.mood", "value": 'bar.mood + 0.0 * distance_to_affordance("EAT")'})
print("  L1 interaction names EAT (level-scoped), all deploy EAT:", outcome(make_pack("und_c", affordances=inter_eat)))
print("  L1 interaction names EAT (level-scoped), L0_0 does not deploy EAT:", outcome(undeploy(make_pack("und_d", affordances=inter_eat), "L0_0_minimal", "EAT")))
print("  effect names EAT, L0_0 does not deploy EAT:", outcome(undeploy(make_pack("und_e", effects=lambda e: eff_unk(e) or e["effect_definitions"][0]["on_tick"].__setitem__(0, {"modify": "bar.energy", "value": 'bar.energy - 0.001 * distance_to_affordance("EAT")'})), "L0_0_minimal", "EAT")))
gnd = WT / "configs/test/gridnd_4d_pack"; gl = [p.name for p in (gnd / "levels").iterdir()][0]
print("  gridnd_4d_pack (enabled_affordances: []) var names EAT:", outcome(var_pack("und_g", 'distance_to_affordance("EAT")', base=gnd, level=gl), level=gl))

print("\n### EXPRESSION-VECTOR-WIDTH / EXPRESSION-INDEX-RANGE and evasions")
VEC = [decl("v2", type="vec2f", initial_value=[1.0, 2.0]), decl("v3", type="vec3f", initial_value=[1.0, 2.0, 3.0]), decl("gv3", scope="global", type="vec3f", initial_value=[1.0, 2.0, 3.0]),
       decl("idx", initial_value=5.0), decl("t13", type="tensor1d", shape=[3], initial_value=[1.0, 2.0, 3.0]), decl("vn4", type="vecNf", dims=4, initial_value=[1.0, 2.0, 3.0, 4.0])]
for label, expr in [("distance(v2, v3)", "distance(v2, v3)"), ("distance(v2, gv3)", "distance(v2, gv3)"), ("distance(v3, direction_to_affordance(EAT)) [3 vs 2, computed arg]", 'distance(v3, direction_to_affordance("EAT"))'),
                    ("distance(direction_to_affordance(EAT), v3) [computed first]", 'distance(direction_to_affordance("EAT"), v3)'), ("manhattan_distance(t13, vn4)", "manhattan_distance(t13, vn4)"),
                    ("within_radius(v2, v3, 1.0)", "where(within_radius(v2, v3, 1.0), 1.0, 0.0)"), ("nearest(v2, v3)", "nearest(v2, v3)"),
                    ("gather(v2, 5)", "gather(v2, 5)"), ("gather(v2, -1)", "gather(v2, -1)"), ("gather(v2, 2+3) [folded?]", "gather(v2, 2 + 3)"), ("gather(v2, 1+1) [=2, out of range]", "gather(v2, 1 + 1)"),
                    ("gather(v2, 5.0) [float literal]", "gather(v2, 5.0)"), ("gather(v2, 2) [boundary]", "gather(v2, 2)"), ("gather(v2, 1) [ok]", "gather(v2, 1)"),
                    ("gather(direction_to_affordance(EAT), 7)", 'gather(direction_to_affordance("EAT"), 7)'), ("gather(t13, 3)", "gather(t13, 3)"), ("gather(vn4, 4)", "gather(vn4, 4)"),
                    ("scatter(v2, 5, 1.0)", "gather(scatter(v2, 5, 1.0), 0)")]:
    print(f"  {label:58} {outcome(var_pack('vw_' + str(abs(hash(label)) % 10**6), expr, extra=VEC))}")
# a rule reading vectors
print("  rule: distance(v2, v3):", outcome(make_pack("vw_r", variables=lambda v: v["declarations"].extend([*VEC, decl("t", initial_value=0.0)]), rules=[rule("r", [rwrite("t", "distance(v2, v3)", composition="overwrite")])])))
print("  rule: gather(v2, 5):", outcome(make_pack("vw_r2", variables=lambda v: v["declarations"].extend([*VEC, decl("t", initial_value=0.0)]), rules=[rule("r", [rwrite("t", "gather(v2, 5)", composition="overwrite")])])))
