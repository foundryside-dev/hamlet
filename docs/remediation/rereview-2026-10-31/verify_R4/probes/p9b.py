import torch
from harness import *  # noqa
from harness import WT, make_pack, decl, write, try_compile, build_env, step, reg, short
from townlet.determinism import seed_all
from townlet.universe.validation.feasibility import grid_capacity_for_substrate
from townlet.config.stratum_config import StratumConfig
import yaml
for pack, lvl in [("configs/differential/div003_cubic_partial", "L2_partial_observability"), ("configs/test/gridnd_4d_pack", None)]:
    p = WT / pack; lvl = lvl or [x.name for x in (p / "levels").iterdir()][0]
    sc = StratumConfig.model_validate(yaml.safe_load(open(p / "stratum.yaml")))
    from townlet.universe.compiler import UniverseCompiler
    u = UniverseCompiler().compile(p, primary_level=lvl, use_cache=False); e = u.create_environment(num_agents=1, level_name=lvl, device="cpu")
    print(f"  {p.name}: compile capacity={grid_capacity_for_substrate(sc.stratum.substrate)} runtime get_capacity={e.substrate.get_capacity()}")
# occupancy claim with a random condition
def variables(v): v["declarations"].append(decl("occ", scope="affordance", type="agent_ref", initial_value=None))
for expr in ["agent_id", "-1"]:
    def actions(a, expr=expr):
        for ca in a["custom_actions"]:
            if ca["name"] == "REST":
                ca["source_affordance"] = "EAT"; ca["writes"] = [write("occ", expr, composition="claim_if_free", condition="uniform() < 0.5", phase="resolve_affordance_access_and_occupancy")]
    u, err = try_compile(make_pack("occ_" + expr.strip("-"), variables=variables, actions=actions))
    if u is None: print(f"  claim_if_free {expr} with random condition: REFUSED {short(err[err.find(' - ')+3:].replace(chr(10),' '), 260)}"); continue
    try:
        seed_all(1); env = build_env(u, 6)
        for w in range(6): env.positions[w] = env.affordances["EAT"].clone()
        env.meters[:, env.meter_name_to_index["money"]] = 100.0
        step(env, "REST"); print(f"  claim_if_free {expr} with random condition: RAN occ={reg(env,'occ').tolist()}")
    except Exception as ex:
        print(f"  claim_if_free {expr}: RUNTIME {type(ex).__name__}: {short(str(ex), 200)}")
