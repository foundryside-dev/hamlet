import sys, shutil, logging, traceback
logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
d = Path(sys.argv[1]); shutil.rmtree(d, ignore_errors=True); shutil.copytree("configs/static_epistemic_access", d, ignore=shutil.ignore_patterns('.compiled'))
t = (d/"actions.yaml").read_text().replace("  - name: ADVANCE", "  - name: ''"); (d/"actions.yaml").write_text(t)
u = UniverseCompiler().compile(d, primary_level="L0_simple", use_cache=False)
print("compiled; actions:", [a.name for a in u.get_level("L0_simple").runtime_action_space.actions])
try:
    env = u.create_environment(num_agents=2, level_name="L0_simple", device="cpu")
except Exception as e:
    tb = traceback.extract_tb(e.__traceback__)
    print("env build:", type(e).__name__, str(e).splitlines()[0]); [print("   ", Path(f.filename).name, f.lineno, f.name) for f in tb[-6:]]
