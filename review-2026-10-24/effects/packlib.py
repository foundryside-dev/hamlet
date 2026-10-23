import shutil, traceback, yaml, torch
from pathlib import Path
BASE = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects/pack_probe")
VAR = BASE.parent / "variants"
BUDGET = {"global": 1, "agent": 4, "item": 0, "affordance": 1}
def effect(id, on_tick=None, on_spawn=None, scope="agent", duration=20, policy="renew", observable=True, on_despawn=None, on_interrupt=None):
    return dict(id=id, scope=scope, duration=duration, reapply_policy=policy, observable=observable,
                on_spawn=on_spawn or [], on_tick=on_tick or [], on_despawn=on_despawn or [], on_interrupt=on_interrupt or [])
def make_pack(name, effects, extra_vars=None, budget=None, keep_smoke=False):
    d = VAR / name
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(BASE, d)
    shutil.rmtree(d / ".compiled", ignore_errors=True)
    ey = {"version": "1.0", "effect_definitions": effects, "max_active_effects": budget or BUDGET}
    (d / "effects.yaml").write_text(yaml.safe_dump(ey, sort_keys=False))
    if extra_vars:
        v = yaml.safe_load((d / "variables.yaml").read_text())
        v["variables"]["declarations"].extend(extra_vars)
        if "extents" in (extra_vars_extents := {}): pass
        (d / "variables.yaml").write_text(yaml.safe_dump(v, sort_keys=False))
    return d
def var(id, scope="agent", type="scalar", writable=("engine",), readable=("engine", "agent"), initial=0.0, lifetime="episode", exposed=()):
    return dict(id=id, scope=scope, type=type, lifetime=lifetime, semantic_type="custom", readable_by=list(readable), writable_by=list(writable), exposed_to=list(exposed), initial_value=initial)
def compile_env(d, num_agents=2):
    from townlet.universe.compiler import UniverseCompiler
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    u = UniverseCompiler().compile(d, primary_level="L0_effects")
    env = VectorizedHamletEnv.from_universe(u, level_name="L0_effects", num_agents=num_agents, device="cpu")
    env.reset()
    return u, env
def bars(env):
    return {n: env.meters[:, i] for n, i in env.meter_name_to_index.items()}
def spawn(env, eid, target=0, intensity=1.0):
    m = env.effect_manager
    return m.spawn_effect(eid, target_entity_id=target, intensity=intensity, current_step=env.global_tick, bars=bars(env), vfs_registry=env.vfs_registry, agent_positions=env.positions, item_manager=env.item_manager)
def wait(env):
    return env.step(torch.full((env.num_agents,), env.action_dim - 1, dtype=torch.long))
def run(label, fn):
    print(f"\n=== {label}")
    try:
        fn()
    except Exception as e:
        msg = str(e).splitlines()
        print(f"  !! {type(e).__name__}: " + " // ".join(m.strip()[:260] for m in msg[:4]))
