import torch
from harness import *
import r3pack
from r3pack import build, make_env, ILEVEL
def base(v):
    v["declarations"].extend([decl("atarget", initial_value=0.0), decl("gtarget", scope="global", initial_value=0.0),
                              decl("coin_t", lifetime="tick", initial_value=0.0, expression="uniform()"),
                              decl("coin_e", initial_value=0.0, expression="uniform()")])
def show(label, p, level=LEVEL):
    u, err = try_compile(p, level)
    print(f"{label:55s}", "COMPILES" if u else "REFUSED " + short(err.replace("\n", " ")[err.find(" - ") if " - " in err else 0:], 330))
    return u
show("rule_a distance_to_affordance", make_pack("rf1", variables=base, rules=[rule("r", [rwrite("atarget", 'distance_to_affordance("EAT")', composition="overwrite")])]))
show("action in_range condition", make_pack("rf2", variables=base, actions=lambda a: add_action(a, "PROBE", [write("atarget", "1.0", composition="overwrite", condition='in_range("EAT", 1.0)')])))
show("rule reads tick-lifetime random var", make_pack("rf3", variables=base, rules=[rule("r", [rwrite("atarget", "coin_t", composition="overwrite")])]))
show("rule reads episode random var", make_pack("rf4", variables=base, rules=[rule("r", [rwrite("atarget", "coin_e", composition="overwrite")])]))
show("rule lag(coin_e,1)", make_pack("rf5", variables=base, rules=[rule("r", [rwrite("atarget", "lag(coin_e, 1)", composition="overwrite")])]))
# spawn predicates (items_smoke)
show("spawn when: uniform() < 0.5", build("rf6", when="uniform() < 0.5"), ILEVEL)
show("spawn when: normal_dist() > 0.0", build("rf7", when="normal_dist() > 0.0"), ILEVEL)
show("spawn when: g_rand > 0.3 (episode random global)", build("rf8", when="g_rand > 0.3"), ILEVEL)
show("spawn when: a_two > 3.0 (episode random agent)", build("rf9", when="a_two > 3.0"), ILEVEL)
show("spawn when: distance_to_affordance(...) > 1", build("rf10", when='distance_to_affordance("energy_station") > 1.0'), ILEVEL)
# docs weather example
w = decl("weather", scope="global", initial_value=0.0, expression="where(tick % 4 == 0, uniform(0.0, 3.0), lag(weather, 1))", exposed=("agent",), normalization={"kind": "minmax", "min": 0.0, "max": 3.0, "clip": True})
u = show("docs weather example", make_pack("rf11", variables=lambda v: v["declarations"].append(w)))
if u:
    env = build_env(u, 3); vals = [reg(env, "weather").tolist()]
    for t in range(9): step(env, "WAIT"); vals.append([round(x, 3) for x in reg(env, "weather").tolist()])
    print("   weather by tick:", vals)
