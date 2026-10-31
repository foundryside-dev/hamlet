import sys, shutil, logging
logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
d = Path(sys.argv[1]); shutil.rmtree(d, ignore_errors=True); shutil.copytree("configs/static_epistemic_access", d, ignore=shutil.ignore_patterns('.compiled'))
t = (d/"actions.yaml").read_text().replace("  - name: ADVANCE", "  - name: UP"); (d/"actions.yaml").write_text(t)
u = UniverseCompiler().compile(d, primary_level="L0_simple", use_cache=False)
lv = u.get_level("L0_simple")
up = [a for a in lv.runtime_action_space.actions if a.name == "UP"][0]
print("UP:", up.type, up.source, "writes:", up.writes)
print("action write program:", [ (w.variable_id) for w in lv.transition_schedule.action_write_program.writes])
env = u.create_environment(num_agents=1, level_name="L0_simple", device="cpu"); env.reset()
for _ in range(3): env.step(torch.tensor([up.id]))
print("public_state after 3x UP:", env.vfs_registry.get("public_state", reader="engine") if hasattr(env, "vfs_registry") else "?")
