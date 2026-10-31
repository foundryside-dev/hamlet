"""fresh compile vs cache-served load: deep field compare + env step compare."""
import sys, shutil, logging, dataclasses, math
logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
from pydantic import BaseModel
from townlet.universe.compiler import UniverseCompiler

def deep(a, b, p, out, depth=0):
    if depth > 40: return
    if a is b: return
    if isinstance(a, torch.Tensor) or isinstance(b, torch.Tensor):
        if not (isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor)) or a.shape != b.shape or a.dtype != b.dtype or not torch.equal(a, b):
            out.append(f"TENSOR {p}")
        return
    if type(a) != type(b):
        out.append(f"TYPE {p}: {type(a).__name__} vs {type(b).__name__}"); return
    if isinstance(a, BaseModel):
        da, db = a.model_dump(), b.model_dump()
        if da != db: out.append(f"PYD {p}")
        # also private/extra attrs like when_ast
        for k in set(vars(a)) | set(vars(b)):
            pass
        for k in (getattr(a, '__pydantic_private__', None) or {}):
            deep(a.__pydantic_private__[k], b.__pydantic_private__.get(k), p+"."+k, out, depth+1)
        return
    if dataclasses.is_dataclass(a):
        for f in dataclasses.fields(a):
            deep(getattr(a, f.name), getattr(b, f.name), p+"."+f.name, out, depth+1)
        return
    if isinstance(a, dict) or hasattr(a, 'items') and hasattr(a, 'keys'):
        if set(a.keys()) != set(b.keys()):
            out.append(f"KEYS {p}: {sorted(map(str,set(a.keys())^set(b.keys())))[:5]}"); return
        for k in a.keys(): deep(a[k], b[k], f"{p}[{k!r}]", out, depth+1)
        return
    if isinstance(a, (list, tuple)):
        if len(a) != len(b): out.append(f"LEN {p}"); return
        for i, (x, y) in enumerate(zip(a, b)): deep(x, y, f"{p}[{i}]", out, depth+1)
        return
    if isinstance(a, (set, frozenset)):
        if a != b: out.append(f"SET {p}")
        return
    if isinstance(a, float) and math.isnan(a) and math.isnan(b): return
    if isinstance(a, (str, int, float, bool, type(None), Path)) or hasattr(a, '__eq__') and type(a).__eq__ is not object.__eq__:
        try:
            eq = a == b
            if isinstance(eq, torch.Tensor): eq = bool(eq.all())
        except Exception as e:
            out.append(f"EQERR {p} {e}"); return
        if not eq: out.append(f"DIFF {p}: {repr(a)[:80]} vs {repr(b)[:80]}")
        return
    if hasattr(a, '__dict__'):
        deep(vars(a), vars(b), p, out, depth+1); return
    if hasattr(a, '__slots__'):
        for s in a.__slots__: deep(getattr(a, s, None), getattr(b, s, None), p+"."+s, out, depth+1)
        return
    out.append(f"OPAQUE {p} {type(a).__name__}")

def run_env(u, level, n=3, steps=40):
    torch.manual_seed(123)
    env = u.create_environment(num_agents=n, level_name=level, device="cpu")
    obs = env.reset(); trace=[obs.clone()]
    g = torch.Generator().manual_seed(7)
    for t in range(steps):
        a = torch.randint(0, env.action_dim, (n,), generator=g)
        o, r, d, info = env.step(a)
        trace += [o.clone(), r.clone(), d.clone()]
    return trace

pack, level = Path(sys.argv[1]), sys.argv[2]
work = Path(sys.argv[3])
shutil.rmtree(work, ignore_errors=True); shutil.copytree(pack, work); shutil.rmtree(work/".compiled", ignore_errors=True)
C = UniverseCompiler()
fresh = C.compile(work, primary_level=level, use_cache=True)  # writes cache
loaded = UniverseCompiler().compile(work, primary_level=level, use_cache=True)
assert loaded is not fresh
out=[]
deep(fresh, loaded, "U", out)
print(f"{pack} {level}: {len(out)} field diffs")
for line in out[:40]: print("  ", line)
try:
    ta, tb = run_env(fresh, level), run_env(loaded, level)
    bad = [i for i,(x,y) in enumerate(zip(ta,tb)) if not torch.equal(x,y)]
    print("  env trace equal:", not bad, bad[:5])
except Exception as e:
    print("  env ERR", type(e).__name__, str(e)[:200])
