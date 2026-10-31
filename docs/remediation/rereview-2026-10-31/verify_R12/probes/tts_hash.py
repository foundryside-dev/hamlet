"""Item 9: token_type_schema_hash on every compilable level of every shipped pack (compile from a copy, no cache)."""
import sys, shutil, logging, warnings, json
logging.disable(logging.CRITICAL); warnings.filterwarnings("ignore")
from pathlib import Path
import townlet
from townlet.universe.compiler import UniverseCompiler
root = Path(sys.argv[1]); out = Path(sys.argv[2]); work = Path(sys.argv[3])
print("townlet from", townlet.__file__, file=sys.stderr)
packs = sorted({p.parent for p in (root / "configs").rglob("levels") if p.is_dir() and ".compiled" not in p.parts})
res = {}
for pack in packs:
    levels = sorted(x.name for x in (pack / "levels").iterdir() if x.is_dir() and not x.name.startswith("."))
    d = work / pack.relative_to(root).as_posix().replace("/", "__")
    shutil.rmtree(d, ignore_errors=True); shutil.copytree(pack, d, ignore=shutil.ignore_patterns(".compiled"))
    for lv in levels:
        key = f"{pack.relative_to(root)}::{lv}"
        try:
            u = UniverseCompiler().compile(d, primary_level=lv, use_cache=False)
            res[key] = u.get_level(lv).token_type_schema_hash[:16]
        except Exception as e:
            msg = str(e).splitlines()
            res[key] = "REFUSED " + type(e).__name__ + ": " + (msg[1] if len(msg) > 1 else msg[0])[:160]
out.write_text(json.dumps(res, indent=1))
