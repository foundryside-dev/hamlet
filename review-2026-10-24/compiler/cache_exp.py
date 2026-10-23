"""Cache staleness experiments on a scratch copy of configs/simple."""
import os, shutil, time, logging
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
logging.basicConfig(level=logging.INFO, format="%(message)s")
S = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/compiler/packs")
pack = S / "cache_pack"
L = "L0_simple"
def compile_(p=pack):
    import io
    logger = logging.getLogger("townlet.universe.compiler")
    buf = io.StringIO(); h = logging.StreamHandler(buf); logger.addHandler(h)
    u = UniverseCompiler().compile(p, primary_level=L, use_cache=True)
    logger.removeHandler(h)
    served = "from cache" in buf.getvalue()
    return u, ("CACHE-HIT" if served else "RECOMPILED")
u0, s = compile_(); print("1 first compile:", s)
u1, s = compile_(); print("2 second compile:", s, "compiled_at same:", u0.metadata.compiled_at == u1.metadata.compiled_at)
# nested level yaml comment-only change
f = pack / "levels" / L / "bars.yaml"; time.sleep(0.01)
f.write_text(f.read_text() + "\n# comment only\n"); u2, s = compile_(); print("3 nested comment-only edit:", s)
# nested level yaml content change
txt = f.read_text(); f.write_text(txt.replace("initial: 1.0", "initial: 0.9", 1)); u3, s = compile_(); print("4 nested content edit:", s, "bars_hash moved:", u2.all_levels[L].bars_hash != u3.all_levels[L].bars_hash)
# content edit with mtime set back to old value (hash must catch it)
old = os.stat(f); txt = f.read_text(); f.write_text(txt.replace("initial: 0.9", "initial: 0.8", 1)); os.utime(f, (old.st_atime, old.st_mtime - 100)); u4, s = compile_(); print("5 content edit, mtime pushed back:", s)
# delete an optional file (effects.yaml)
(pack / "effects.yaml").unlink(); u5, s = compile_(); print("6 deleted effects.yaml:", s, "effect catalog:", u5.compiled_effect_catalog)
# add a new nested yaml in a subfolder (a duplicate drive -> should refuse)
sub = pack / "levels" / L / "mechanics"; sub.mkdir(); shutil.copy(pack / "levels" / L / "drive.yaml", sub / "rewards.yml")
try:
    u6, s = compile_(); print("7 added duplicate drive in nested subfolder:", s)
except Exception as exc:
    print("7 added duplicate drive in nested subfolder: REFUSED", type(exc).__name__, str(exc).splitlines()[0][:100]); [print("    ", l[:160]) for l in str(exc).splitlines() if "first declared" in l or "rewards.yml" in l]
shutil.rmtree(sub)
# copy the whole pack (with .compiled) elsewhere -> experiment_dir?
copy = S / "cache_pack_copy"; shutil.rmtree(copy, ignore_errors=True); shutil.copytree(pack, copy)
u7, s = compile_(copy); print("8 cp -r pack with .compiled to new path:", s, "experiment_dir:", u7.experiment_dir)
# edit the copied pack's cache artifact schema version
import msgpack
art = copy / ".compiled" / f"universe-{L}.msgpack"
d = msgpack.unpackb(art.read_bytes(), raw=False, strict_map_key=False); d["compiled_schema_version"] = "1.28"; art.write_bytes(msgpack.packb(d, use_bin_type=True))
u8, s = compile_(copy); print("9 compile() against a 1.28-labelled artifact:", s)
