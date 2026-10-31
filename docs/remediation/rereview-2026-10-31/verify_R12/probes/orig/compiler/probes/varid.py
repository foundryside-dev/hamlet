import sys, shutil, logging
logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
P = Path(sys.argv[1])
for vid in ["bar.energy", "item.x", "a b", "1x", "x-y", "True", "and", "énergie", "abs", "STEAL"]:
    d = P/"vid"; shutil.rmtree(d, ignore_errors=True); shutil.copytree("configs/static_epistemic_access", d, ignore=shutil.ignore_patterns('.compiled'))
    p = d/"variables.yaml"; t = p.read_text()
    t = t.replace("  - id: hidden_score", f"  - id: '{vid}'\n    scope: agent\n    type: scalar\n    lifetime: episode\n    semantic_type: custom\n    readable_by: [engine, agent]\n    writable_by: [engine]\n    exposed_to: [agent]\n    normalization: {{kind: minmax, min: 0.0, max: 1.0, clip: true}}\n    initial_value: 0.5\n  - id: hidden_score", 1)
    p.write_text(t)
    try:
        u = UniverseCompiler().compile(d, primary_level="L0_simple", use_cache=False)
        env = u.create_environment(num_agents=2, level_name="L0_simple", device="cpu"); env.reset(); env.step(torch.zeros(2, dtype=torch.long))
        print(f"{vid!r}: compiled+ran (declared, exposed)")
    except CompilationError as e:
        print(f"{vid!r}: REFUSED {e.issues[0].format()[-140:]}")
    except Exception as e:
        print(f"{vid!r}: {type(e).__name__} {str(e)[:140]}")
