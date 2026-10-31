import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects")
from packlib import *
import torch, yaml
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
u = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L3_temporal_mechanics")
keys = sorted(u.effects_schema)
print("default_curriculum effects_schema has tick?", [k for k in keys if "tick" in k], "| sample:", keys[:6], "...", len(keys), "keys")
print("registry-side variables include tick?", "tick" in u.get_level("L3_temporal_mechanics").token_spec.__class__.__name__ or "n/a")

def p_distance_vec():
    d = make_pack("distvec", [effect("dv", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.01 * distance(vfs.position, vfs.position)"}])])
    compile_env(d); print("  compiled OK")
run("AA distance() on vec2f variables (its intended input)", p_distance_vec)

def p_distance_scalar():
    d = make_pack("distscalar", [effect("ds", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.1 * distance(bar.energy, bar.health)"}])])
    u, env = compile_env(d, 3); env.meters[0, 0] = 0.0; spawn(env, "ds"); wait(env)
    print("  compiled OK; distance over per-agent scalars collapses batch (one value for all):", env.meters[:, env.meter_name_to_index['health']].tolist())
run("AB distance() on scalar bars", p_distance_scalar)

def p_aff_collision():
    d = make_pack("affcol", [effect("x")])
    aff = yaml.safe_load((d / "levels/L0_effects/affordances.yaml").read_text())
    aff["affordances"]["affordances"][1]["interactions"] = aff["affordances"]["affordances"][0]["interactions"]
    (d / "levels/L0_effects/affordances.yaml").write_text(yaml.safe_dump(aff, sort_keys=False))
    compile_env(d); print("  BED and FOOD now identical in every declared parameter except name/position: compiled OK")
run("AC affordance identity collision", p_aff_collision)
