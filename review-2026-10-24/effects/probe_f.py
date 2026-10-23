import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects")
from packlib import *
import yaml
def p():
    d = make_pack("affcol2", [effect("x")])
    aff = yaml.safe_load((d / "levels/L0_effects/affordances.yaml").read_text())
    aff["affordances"]["affordances"][1]["interactions"] = aff["affordances"]["affordances"][0]["interactions"]
    aff["affordances"]["affordances"][1]["deployment"] = aff["affordances"]["affordances"][0]["deployment"]
    (d / "levels/L0_effects/affordances.yaml").write_text(yaml.safe_dump(aff, sort_keys=False))
    compile_env(d); print("  identical incl. position: compiled OK")
run("AC2 affordance identical in every declared parameter incl. position", p)
