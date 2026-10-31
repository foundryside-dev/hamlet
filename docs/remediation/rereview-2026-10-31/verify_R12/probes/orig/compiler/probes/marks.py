import sys, logging
logging.disable(logging.CRITICAL)
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
for p in sys.argv[1:]:
    pk=Path(p); lv=sorted(x.name for x in (pk/'levels').iterdir() if x.is_dir())[0]
    try:
        u=UniverseCompiler().compile(pk, primary_level=lv, use_cache=False)
        print(p, u.vfs_evaluation_marks)
    except Exception as e: print(p, "ERR", type(e).__name__)
