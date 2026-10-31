"""Item 4c: custom action named after every engine/substrate action, per substrate."""
import sys, shutil, logging, re
logging.disable(logging.CRITICAL)
import warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import yaml
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
W = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/actnames")
def prep(src, edits):
    d = W / "p"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns(".compiled"))
    for f, fn in edits:
        p = d / f; data = yaml.safe_load(p.read_text()); fn(data); p.write_text(yaml.safe_dump(data, sort_keys=False))
    return d
def comp(d, level):
    try:
        u = UniverseCompiler().compile(d, primary_level=level, use_cache=False); return u, None
    except CompilationError as e:
        m = e.issues[0]; return None, f"{m.code} @{str(m.location).replace(str(d)+'/', '')}"
    except Exception as e:
        return None, f"BARE {type(e).__name__}: {str(e)[:100]}"
def stratum_edit(fn): return ("stratum.yaml", lambda d: fn(d["stratum"]["substrate"]))
CASES = [
  ("grid2d diag (SEA)", "configs/static_epistemic_access", "L0_simple", []),
  ("grid2d no-diag (SEA)", "configs/static_epistemic_access", "L0_simple", [stratum_edit(lambda s: s["grid"].update(diagonals=False))]),
  ("grid3d cubic (SEA)", "configs/static_epistemic_access", "L0_simple", [stratum_edit(lambda s: s["grid"].update(topology="cubic", depth=3))]),
  ("items_smoke", "configs/test/items_smoke", "L0_smoke", []),
  ("gridnd 4d", "configs/test/gridnd_4d_pack", "L0_test", []),
  ("continuous1d", "configs/test/action_space/continuous1d", None, []),
  ("continuous2d", "configs/test/action_space/continuous1d", None, [stratum_edit(lambda s: s["continuous"].update(dimensions=2, bounds=[[0.0, 10.0]]*2)), ("levels/%L/training.yaml", lambda d: d["training"].update(randomize_affordances=True))]),
  ("continuous3d", "configs/test/action_space/continuous1d", None, [stratum_edit(lambda s: s["continuous"].update(dimensions=3, bounds=[[0.0, 10.0]]*3)), ("levels/%L/training.yaml", lambda d: d["training"].update(randomize_affordances=True))]),
  ("continuousnd4", "configs/test/action_space/continuous1d", None, [stratum_edit(lambda s: (s.update(type="continuousnd"), s["continuous"].update(dimensions=4, bounds=[[0.0, 10.0]]*4))), ("levels/%L/training.yaml", lambda d: d["training"].update(randomize_affordances=True)), ("actions.yaml", lambda d: [c.update(name="IDLE") for c in d["actions"]["custom_actions"] if c["name"] == "WAIT"])]),
  ("aspatial_test", "configs/aspatial_test", None, []),
]
ONLY = sys.argv[1:]
for label, src, level, edits in CASES:
    if ONLY and label not in ONLY: continue
    src = Path(src)
    level = level or sorted(p.name for p in (src / "levels").iterdir() if p.is_dir())[0]
    edits = [(f.replace("%L", level), fn) for f, fn in edits]
    d = prep(src, edits)
    u, err = comp(d, level)
    if err: print(f"{label}: BASE REFUSED {err}"); continue
    names = [a.name for a in u.get_level(level).runtime_action_space.actions]
    customs = [c["name"] for c in yaml.safe_load((d / "actions.yaml").read_text())["actions"]["custom_actions"]]
    print(f"{label}: actions {names} customs {customs}")
    if not customs:
        edits = edits + [("actions.yaml", lambda dd: dd["actions"]["custom_actions"].append({"name": "PROBE", "description": "p", "enabled_by_default": True}))]
        customs = ["PROBE"]
    victim = customs[-1]
    engine_names = [n for n in names if n not in customs] + ["GET", "USE_SLOT_0", "DROP_SLOT_0", "USE_SLOT_9", "INTERACT", "WAIT"]
    results = []
    for n in dict.fromkeys(engine_names):
        d2 = prep(src, edits + [("actions.yaml", lambda dd, n=n: [c.update(name=n) for c in dd["actions"]["custom_actions"] if c["name"] == victim])])
        u2, err2 = comp(d2, level)
        results.append(f"{n}={'OK' if err2 is None else err2}")
    print("   " + "; ".join(results))
