import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
u, env = compile("configs/default_curriculum", "L3_temporal_mechanics")
lvl = u.get_level("L3_temporal_mechanics")
print("vfs vars with 'progress':", [v.id for v in lvl.vfs_variables if "progress" in v.id])
refs = [b.filler_ref for t in env.token_spec.types for b in t.slot_bindings]
print("token filler refs mentioning progress:", [r for r in refs if "progress" in r])
print("multi_tick affordances in L3:", [a.name for a in lvl.affordances.affordances if a.interaction_type == "multi_tick"])
print("has_multi_tick:", env.vtc_interaction_progress_program.has_multi_tick_affordances())
