import sys, shutil, logging, os, time
logging.disable(logging.CRITICAL)
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
src, level, work = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
def fresh_vs_cache(name, fn):
    d = work/"c"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns('.compiled'))
    UniverseCompiler().compile(d, primary_level=level, use_cache=True)
    time.sleep(0.05)
    fn(d)
    try:
        c = UniverseCompiler().compile(d, primary_level=level, use_cache=True); cr = "OK " + c.metadata.compiled_at
    except CompilationError as e: cr = "REFUSED " + e.issues[0].format()[-120:]
    try:
        f = UniverseCompiler().compile(d, primary_level=level, use_cache=False); fr = "OK " + f.metadata.compiled_at
    except CompilationError as e: fr = "REFUSED " + e.issues[0].format()[-120:]
    print(f"{name}\n   cache-path: {cr}\n   fresh:      {fr}")
fresh_vs_cache("add empty level dir levels/L9", lambda d: (d/"levels/L9").mkdir())
fresh_vs_cache("add levels/L9/README.md", lambda d: ((d/"levels/L9").mkdir(), (d/"levels/L9/README.md").write_text("x")))
fresh_vs_cache("add uppercase .YAML variables fragment", lambda d: (d/"extra.YAML").write_text("variables:\n  declarations: [{bogus: 1}]\n"))
def old_mtime_reorder(d):
    f = d/"levels"/level/"affordances.yaml"
    st = f.stat(); t = f.read_text()
    f.write_text(t.replace("        energy: 0.15\n        money: 0.03", "        money: 0.03\n        energy: 0.15"))
    os.utime(f, (st.st_atime - 1000, st.st_mtime - 1000))
fresh_vs_cache("key reorder with mtime set back", old_mtime_reorder)
