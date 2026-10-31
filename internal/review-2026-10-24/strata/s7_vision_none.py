"""H9: vision_support: none is unusable; active_vision 'local' residual."""
import shutil, sys
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
src = Path("configs/test/action_space/grid2d"); dst = Path(sys.argv[1]) / "vision_none"
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".compiled"))
p = dst / "stratum.yaml"; p.write_text(p.read_text().replace("vision_support: global", "vision_support: none"))
level = sorted(x.name for x in (dst / "levels").iterdir())[0]
try:
    UniverseCompiler().compile(dst, primary_level=level); print("compiled OK (unexpected)")
except Exception as e:
    print("vision_support: none ->", type(e).__name__, str(e)[:400])
