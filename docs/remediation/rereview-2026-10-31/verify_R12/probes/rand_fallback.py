"""Item 4a: randomize_affordances: true is not position-free when runtime capacity forces a fallback."""
import sys, shutil, logging
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
src, level, d, n = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), int(sys.argv[4])
edits = sys.argv[5:]
shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns('.compiled'))
for i in range(0, len(edits), 3):
    f, old, new = edits[i:i+3]; old = old.encode().decode("unicode_escape"); p = d/f; t = p.read_text(); assert old in t, old; p.write_text(t.replace(old, new.encode().decode("unicode_escape"), 1))
u = UniverseCompiler().compile(d, primary_level=level, use_cache=False)
print("COMPILED; randomize_affordances =", u.get_level(level).training.randomize_affordances)
try:
    env = u.create_environment(num_agents=n, level_name=level, device="cpu"); env.reset()
    print("env built; env.randomize_affordances now", env.randomize_affordances, "affordance positions:", {k: v.tolist() for k, v in list(env.affordances.items())[:4]})
except Exception as e:
    print("RUNTIME", type(e).__name__, str(e)[:200])
