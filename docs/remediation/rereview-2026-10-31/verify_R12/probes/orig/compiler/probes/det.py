import sys, shutil, msgpack, logging
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
pack, level, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
shutil.rmtree(pack/".compiled", ignore_errors=True)
UniverseCompiler().compile(pack, primary_level=level, use_cache=True)
shutil.copy(pack/".compiled"/f"universe-{level}.msgpack", out)
