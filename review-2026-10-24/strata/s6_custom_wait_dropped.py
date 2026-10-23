"""H6: a custom WAIT (with writes) is silently dropped on substrates that emit WAIT themselves."""
import shutil, sys, yaml
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
src = Path("configs/test/gridnd_4d_pack"); dst = Path(sys.argv[1]) / "gridnd_wait"
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".compiled"))
bars = yaml.safe_load((dst / "levels/L0_test/bars.yaml").read_text()); meter = bars["bars"]["meters"][0]["name"]
a = dst / "actions.yaml"; d = yaml.safe_load(a.read_text())
d["actions"]["custom_actions"] = [{"name": "WAIT", "description": "custom wait that writes", "enabled_by_default": True, "source_affordance": None,
    "writes": [{"variable_id": meter, "expression": "0.5", "condition": None, "composition": "additive_delta", "phase": "apply_action_effects", "priority": 0, "clamp": None, "telemetry_label": "wait_bonus"}]}]
a.write_text(yaml.safe_dump(d))
u = UniverseCompiler().compile(dst, primary_level="L0_test")
acts = u.get_level("L0_test").runtime_action_space.actions
print("declared custom WAIT with a write to", meter)
print("WAIT entries after compile:", [(x.id, x.source, x.type, x.writes) for x in acts if x.name == "WAIT"])
print("any diagnostics? (compile succeeded silently)")
