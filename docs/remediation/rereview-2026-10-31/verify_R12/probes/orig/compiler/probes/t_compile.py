import time, sys, logging
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
t=time.time()
u=UniverseCompiler().compile(Path(sys.argv[1]), primary_level=sys.argv[2], use_cache=False)
print(time.time()-t, u.get_level(sys.argv[2]).token_spec.total_dims)
