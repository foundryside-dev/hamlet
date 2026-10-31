"""Tree-level YAML mutation fuzzer: compile, then build env and step. Records non-coded/unlocated refusals and runtime crashes."""
import sys, random, shutil, logging, traceback, re, signal, json
logging.disable(logging.CRITICAL)
from pathlib import Path
import yaml, torch
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

base_src, level, work, seed, n = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
rng = random.Random(seed)
files = sorted(p for p in base_src.rglob("*.y*ml") if ".compiled" not in p.parts)
VALUES = [None, -1, 0, 1, 2.5, -0.5, 10**9, 1e308, float("nan"), "", "ünï_cødé", "x y", "bar.energy + ", "1/0", [], {}, True, False, [1, 2], {"a": 1}, "nope", "agent", "global", "item", 0.0]

def paths(node, prefix=()):
    yield prefix
    if isinstance(node, dict):
        for k, v in node.items(): yield from paths(v, prefix + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node): yield from paths(v, prefix + (i,))

def get(node, path):
    for p in path: node = node[p]
    return node


def perturb(v):
    if isinstance(v, bool): return not v
    if isinstance(v, int): return rng.choice([0, -1, -v, v + 1, v * 1000, 10**7, 1])
    if isinstance(v, float): return rng.choice([0.0, -v, v * 10, 1e-12, 1e12, -1.0, 1.0, float("inf"), 0.5])
    if isinstance(v, str): return rng.choice(["", v + "_x", v.upper(), "ünï", v + " + 1", "1.0", "0", "x" * 300, v.replace(" ", "")])
    if isinstance(v, list): return rng.choice([[], v + v[:1], v[::-1], v[:1]])
    if isinstance(v, dict): return {} if rng.random() < 0.5 else v
    return v

def mutate(doc):
    ps = [p for p in paths(doc) if p]
    if not ps: return None
    path = rng.choice(ps)
    parent = get(doc, path[:-1]); key = path[-1]
    new = perturb(parent[key])
    parent[key] = new
    return f"set {path} = {new!r}"[:200]

def handler(signum, frame): raise TimeoutError("timeout")
signal.signal(signal.SIGALRM, handler)
LOC = re.compile(r":\d+$")
results = {}
for i in range(n):
    d = work / "f"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(base_src, d, ignore=shutil.ignore_patterns(".compiled"))
    f = rng.choice(files); rel = f.relative_to(base_src)
    docs = list(yaml.safe_load_all((d/rel).read_text()))
    di = rng.randrange(len(docs))
    if docs[di] is None: continue
    desc = []
    for _ in range(rng.choice([1, 1, 2])):
        m = mutate(docs[di])
        if m: desc.append(m)
    (d/rel).write_text(yaml.safe_dump_all(docs, sort_keys=False, allow_unicode=True))
    tag = f"{rel}: {'; '.join(desc)}"
    signal.alarm(60)
    try:
        u = UniverseCompiler().compile(d, primary_level=level, use_cache=False)
        try:
            env = u.create_environment(num_agents=2, level_name=level, device="cpu")
            env.reset()
            g = torch.Generator().manual_seed(1)
            for t in range(4):
                env.step(torch.randint(0, env.action_dim, (2,), generator=g))
            kind = "OK"
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            kind = f"RUNTIME {type(e).__name__} @{Path(tb.filename).name}:{tb.lineno}"
            results.setdefault(kind, []).append(tag + f" || {str(e)[:200]}")
    except CompilationError as e:
        bad = [m for m in e.issues if not m.code or not m.location or not LOC.search(m.location)]
        if bad:
            kind = "UNLOCATED " + ",".join(sorted({str(m.code) for m in bad}))
            results.setdefault(kind, []).append(tag + f" || {bad[0].format()[:250]}")
        else:
            kind = "REFUSED"
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1]
        kind = f"BARE {type(e).__name__} @{Path(tb.filename).name}:{tb.lineno}"
        results.setdefault(kind, []).append(tag + f" || {str(e)[:200]}")
    finally:
        signal.alarm(0)
    results.setdefault("_count_" + kind.split(" ")[0], []).append(1)
for k in sorted(results):
    if k.startswith("_count_"): print(k, len(results[k])); continue
    print("==", k, len(results[k]))
    for t in results[k][:3]: print("    ", t[:600])
