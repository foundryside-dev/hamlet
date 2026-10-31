import sys, shutil, logging, time, resource
logging.disable(logging.CRITICAL)
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
d = Path(sys.argv[1]); old, new = sys.argv[2], sys.argv[3]; f = sys.argv[4]
shutil.rmtree(d, ignore_errors=True); shutil.copytree("configs/test/items_smoke", d, ignore=shutil.ignore_patterns('.compiled'))
t = (d/f).read_text(); assert old in t; (d/f).write_text(t.replace(old, new))
t0 = time.time()
try:
    u = UniverseCompiler().compile(d, primary_level="L0_smoke", use_cache=False)
    print(f"{new}: compiled in {time.time()-t0:.1f}s total_dims={u.get_level('L0_smoke').token_spec.total_dims} census={u.get_level('L0_smoke').token_spec.census} maxrss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024}MB")
except Exception as e:
    print(f"{new}: {type(e).__name__} {str(e)[:300]}")
