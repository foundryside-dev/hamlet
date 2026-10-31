from r3pack import *
p = build()
env, obs = make_env(p, 4, 7)
r = env.vfs_registry
for v in ["g_rand","a_rand","a_two","a_read2","g_target","a_target","a_seen","sv"]:
    print(v, r.get(v, reader="engine").tolist())
print([a.name for a in env.action_space.actions])
print(env.affordances, env.positions)
print(len(env.item_manager.items_in_world(0)), env.item_manager.items_in_world(0)[:1])
