import shutil, logging, re
logging.disable(logging.CRITICAL)
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.schema_hashes import compute_expression_schema_hash
PACK_H = ["brain_hash","pack_brain_hash","experiment_hash","stratum_hash","environment_hash","actions_hash","items_hash","variables_hash"]
LVL_H = ["token_type_schema_hash","layout_hash","action_schema_hash","transition_graph_hash","vfs_hash","observation_schema_hash","variable_schema_hash","drive_hash","curriculum_hash","bars_hash","affordances_hash","training_hash"]
def hashes(pack, level):
    u = UniverseCompiler().compile(pack, primary_level=level, use_cache=False)
    h = {k: getattr(u, k) for k in PACK_H}
    lv = u.get_level(level)
    h.update({k: getattr(lv, k) for k in LVL_H})
    p = u.compiled_vfs_profiles
    h["expression_schema_hash"] = compute_expression_schema_hash(global_profile=p.global_profile, agent_profile=p.agent_profile)
    h["config_hash(cache)"] = u.metadata.config_hash
    return h
def copy(src, dst):
    dst = Path(dst); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.compiled')); return dst
def sub(path, old, new, count=1):
    t = Path(path).read_text()
    assert old in t, (path, old)
    Path(path).write_text(t.replace(old, new, count))
def run_matrix(base_src, level, edits, work, prep=None):
    base = copy(base_src, work/"base")
    if prep: prep(base)
    h0 = hashes(base, level)
    for name, kind, fn in edits:
        d = copy(base, work/"edit")
        try:
            fn(d)
            h = hashes(d, level)
            moved = [k for k in h if h[k] != h0[k]]
            print(f"[{kind:4}] {name:60} moved={moved}")
        except Exception as e:
            print(f"[{kind:4}] {name:60} ERROR {type(e).__name__}: {str(e)[:300]}")
