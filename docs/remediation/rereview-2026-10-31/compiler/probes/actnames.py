import sys, shutil, logging, traceback
logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
for nm in ["''", "UP", "INTERACT", "'a b'", "ünï", "'1'", "'x'"]:
    d = Path(sys.argv[1]); shutil.rmtree(d, ignore_errors=True); shutil.copytree("configs/static_epistemic_access", d, ignore=shutil.ignore_patterns('.compiled'))
    t = (d/"actions.yaml").read_text().replace("  - name: ADVANCE", f"  - name: {nm}"); (d/"actions.yaml").write_text(t)
    try:
        u = UniverseCompiler().compile(d, primary_level="L0_simple", use_cache=False)
    except (CompilationError, ValueError) as e:
        print(nm, "REFUSED", type(e).__name__, (e.issues[0].format() if isinstance(e, CompilationError) else str(e))[-160:]); continue
    names = [a.name for a in u.get_level("L0_simple").runtime_action_space.actions]
    try:
        env = u.create_environment(num_agents=2, level_name="L0_simple", device="cpu"); env.reset()
        for i in range(env.action_dim): env.step(torch.full((2,), i))
        print(nm, "OK runtime; actions", names)
    except Exception as e:
        print(nm, "COMPILED then RUNTIME", type(e).__name__, str(e).splitlines()[0][:150], names)
