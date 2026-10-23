"""Which checkpoint-compared hashes move when stratum.yaml changes behaviourally?"""
import shutil, re
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.training.checkpoint_utils import DEMO_CHECKPOINT_KEYS
S = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/compiler/packs")
base = S / "gate"; L = "L0_simple"
COMPARED = ["drive_hash", "brain_hash", "curriculum_hash", "bars_hash", "affordances_hash", "training_hash", "vfs_hash", "layout_hash", "token_type_schema_hash", "action_schema_hash", "transition_graph_hash", "observation_schema_hash", "variable_schema_hash"]
def hashes(p):
    u = UniverseCompiler().compile(p, primary_level=L, use_cache=False); lv = u.get_level(L)
    h = {k: getattr(lv, k, None) or getattr(u, k, None) for k in COMPARED}
    h.update({"stratum_hash": u.stratum_hash, "actions_hash": u.actions_hash, "environment_hash": u.environment_hash, "action_count": lv.action_metadata.total_actions, "total_dims": lv.token_spec.total_dims})
    return h
h0 = hashes(base)
def variant(name, file, old, new):
    p = S / f"gate_{name}"; shutil.rmtree(p, ignore_errors=True); shutil.copytree(base, p)
    f = p / file; t = f.read_text(); assert old in t, (file, old); f.write_text(t.replace(old, new, 1))
    h = hashes(p)
    moved = [k for k in h if h[k] != h0[k]]
    gated = [k for k in moved if k in COMPARED or k == "action_count"]
    print(f"{name:34s} moved={moved}\n{'':34s} checkpoint-gated movers={gated or 'NONE -> resume silently accepted'}")
variant("stratum_boundary_clamp_to_wrap", "stratum.yaml", "boundary: clamp", "boundary: wrap")
variant("stratum_metric_manhattan_to_cheb", "stratum.yaml", "distance_metric: manhattan", "distance_metric: chebyshev")
variant("stratum_diagonals_true_to_false", "stratum.yaml", "diagonals: true", "diagonals: false")
variant("actions_wait_enabled_default_false", "actions.yaml", "enabled_by_default: true", "enabled_by_default: false")
