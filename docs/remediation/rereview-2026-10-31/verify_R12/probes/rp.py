"""repro variant: copy pack, literal edits, compile (no cache), env, step. Prints code@location for refusals.
Usage: rp.py src level work [file old new]...   old='@CREATE' creates file; old='@DELETE' deletes file."""
import sys, shutil, logging, traceback, os
logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
import townlet
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
assert os.environ.get("EXPECT_WT", "") in townlet.__file__, townlet.__file__
src, level, d = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns('.compiled'))
args = sys.argv[4:]
for i in range(0, len(args), 3):
    f, old, new = args[i:i+3]
    p = d/f
    if old == "@CREATE": p.parent.mkdir(parents=True, exist_ok=True); p.write_text(new.encode().decode("unicode_escape")); continue
    if old == "@DELETE": p.unlink(); continue
    old = old.encode().decode("unicode_escape")
    t = p.read_text(); assert old in t, (f, old); p.write_text(t.replace(old, new.encode().decode("unicode_escape"), 1))
def where(e):
    tb = traceback.extract_tb(e.__traceback__)[-1]; return f"{Path(tb.filename).name}:{tb.lineno}"
def short(loc):
    if loc is None: return None
    return str(loc).replace(str(d) + "/", "")
try:
    u = UniverseCompiler().compile(d, primary_level=level, use_cache=False)
except CompilationError as e:
    for m in e.issues[:4]:
        print(f"REFUSED [{m.code}] @{short(m.location)} :: {m.message[:300]}")
    sys.exit(0)
except Exception as e:
    print(f"BARE {type(e).__name__} @{where(e)}: {str(e)[:250]}"); sys.exit(0)
print("COMPILED")
if os.environ.get("NOSTEP"): sys.exit(0)
try:
    env = u.create_environment(num_agents=2, level_name=level, device="cpu"); env.reset()
    g = torch.Generator().manual_seed(0)
    for t in range(int(os.environ.get("STEPS", "6"))):
        env.step(torch.randint(0, env.action_dim, (2,), generator=g))
    print("RAN OK")
except Exception as e:
    print(f"RUNTIME {type(e).__name__} @{where(e)}: {str(e)[:250]}")
