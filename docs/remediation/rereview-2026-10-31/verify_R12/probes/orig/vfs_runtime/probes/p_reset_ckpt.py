"""Reset ordering, random redraw, tick-lifetime visibility, persistent save/restore (incl. refs), checkpoint identity."""
from common import *  # noqa
import sys
import torch
from harness import ve_rows

NORM = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}


@probe("R1 reset: persistent expression at instant 0; tick-lifetime write visible in obs then reset; random redraw per reset; tick row")
def r1():
    decls = [
        decl("pcount", scope="global", lifetime="persistent", initial_value=0.0),
        decl("pexp", scope="global", lifetime="persistent", initial_value=0.0, expression="pcount * 10.0"),
        decl("pacc", scope="global", lifetime="persistent", initial_value=0.0, expression="lag(pacc, 1) + 1.0"),
        decl("hit", lifetime="tick", initial_value=0.0, exposed=("agent",), normalization=NORM),
        decl("hit_exp", lifetime="tick", initial_value=0.0, expression="hit * 2.0", exposed=("agent",), normalization=NORM),
        decl("noise", type="tensor1d", shape=[2], lifetime="episode", initial_value_mode="random_uniform", initial_value_params={"low": 0.0, "high": 1.0}),
        decl("tnoise", type="tensor1d", shape=[1], lifetime="tick", initial_value_mode="random_uniform", initial_value_params={"low": 0.0, "high": 1.0}),
        decl("texp", scope="global", initial_value=0.0, expression="tick + 0.0", exposed=("agent",), normalization=NORM),
    ]
    rules = [rule("rp", [rwrite("pcount", "1.0")])]
    writes = [write("hit", "1.0", composition="overwrite")]
    u = compile_sea("reset1", decls=decls, rules=rules, writes=writes)
    env = build_env(u, num_agents=2)
    r = env.vfs_registry
    obs = env._get_observations()
    print("  instant 0: pcount", r.get("pcount", reader="engine").tolist(), "pexp", r.get("pexp", reader="engine").tolist(), "pacc", r.get("pacc", reader="engine").tolist(), "tick", r.get("tick", reader="engine").tolist())
    print("  obs rows at reset:", ve_rows(env, obs, agent=0))
    n0 = r.get("noise", reader="engine").clone(); t0 = r.get("tnoise", reader="engine").clone()
    obs, *_ = env.step(acts(env, "ADVANCE"))
    print("  after ADVANCE: hit", r.get("hit", reader="engine").tolist(), "hit_exp", r.get("hit_exp", reader="engine").tolist(), "obs rows:", ve_rows(env, obs, agent=0))
    t1 = r.get("tnoise", reader="engine").clone()
    obs, *_ = env.step(acts(env, "WAIT"))
    print("  after WAIT: hit", r.get("hit", reader="engine").tolist(), "hit_exp", r.get("hit_exp", reader="engine").tolist(), "obs rows:", ve_rows(env, obs, agent=0))
    print("  tick-lifetime random redrawn each step:", not torch.equal(t0, t1), " episode noise unchanged within episode:", torch.equal(n0, r.get("noise", reader="engine")))
    for _ in range(3):
        env.step(acts(env, "WAIT"))
    print("  before reset: pcount", r.get("pcount", reader="engine").tolist(), "pexp", r.get("pexp", reader="engine").tolist(), "pacc", r.get("pacc", reader="engine").tolist(), "tick", r.get("tick", reader="engine").tolist())
    obs = env.reset()
    print("  after reset: pcount", r.get("pcount", reader="engine").tolist(), "pexp", r.get("pexp", reader="engine").tolist(), "pacc", r.get("pacc", reader="engine").tolist(), "tick", r.get("tick", reader="engine").tolist(), "texp", r.get("texp", reader="engine").tolist())
    print("  episode noise redrawn on reset:", not torch.equal(n0, r.get("noise", reader="engine")))
    print("  obs rows after reset:", ve_rows(env, obs, agent=0))


@probe("R2 persistent save/restore incl. agent_ref/item-free; restore then reset evaluates persistent expression from restored value")
def r2():
    decls = [
        decl("pcount", scope="global", lifetime="persistent", initial_value=0.0),
        decl("pexp", scope="global", lifetime="persistent", initial_value=0.0, expression="pcount * 10.0"),
        decl("pref", type="agent_ref", lifetime="persistent", initial_value=None),
        decl("pflag", type="bool", lifetime="persistent", initial_value=False),
        decl("pvec", type="vecNf", dims=2, lifetime="persistent", initial_value=[0.0, 0.0]),
        decl("ecount", scope="global", lifetime="episode", initial_value=0.0),
    ]
    rules = [rule("rp", [rwrite("pcount", "1.0"), rwrite("ecount", "1.0")]), rule("rr", [rwrite("pref", "agent_id", composition="overwrite"), rwrite("pflag", "true", composition="overwrite"), rwrite("pvec", "1.0")])]
    u = compile_sea("ckpt", decls=decls, rules=rules)
    env = build_env(u, num_agents=3)
    r = env.vfs_registry
    for _ in range(4):
        env.step(acts(env, "WAIT"))
    state = r.persistent_state()
    print("  snapshot keys:", sorted(state), {k: (v.dtype, tuple(v.shape)) for k, v in state.items()})
    env2 = build_env(u, num_agents=3)
    r2_ = env2.vfs_registry
    r2_.restore_persistent_state(state)
    print("  restored pcount", r2_.get("pcount", reader="engine").tolist(), "pexp (pre-reset)", r2_.get("pexp", reader="engine").tolist(), "pref", r2_.get("pref", reader="engine").tolist(), "pflag", r2_.get("pflag", reader="engine").tolist())
    env2.reset()
    print("  after reset: pcount", r2_.get("pcount", reader="engine").tolist(), "pexp", r2_.get("pexp", reader="engine").tolist(), "ecount", r2_.get("ecount", reader="engine").tolist(), "pref", r2_.get("pref", reader="engine").tolist(), "pvec", r2_.get("pvec", reader="engine").tolist())
    # wrong world ref in a snapshot
    bad = dict(state); bad["pref"] = torch.tensor([1, 1, 1])
    try_run("  restore with cross-world ref", lambda: r2_.restore_persistent_state(bad))
    # N mismatch
    env3 = build_env(u, num_agents=2)
    try_run("  restore N=3 snapshot into N=2 env", lambda: env3.vfs_registry.restore_persistent_state(state))
    # checkpoint identity gate on vfs hash
    from townlet.training.checkpoint_utils import assert_checkpoint_vfs_hash
    print("  level vfs_hash:", u.get_level("L0_simple").vfs_hash if hasattr(u.get_level("L0_simple"), "vfs_hash") else "n/a")


@probe("R3 two reset() calls in a row and reset after partial deaths: dones cleared, dead world state re-initialized, history reseeded")
def r3():
    from townlet.universe.compiler import UniverseCompiler
    u = UniverseCompiler().compile(PACKS / "r_iso", primary_level="L0_simple", use_cache=False)
    env = build_env(u, num_agents=3)
    r = env.vfs_registry
    e = env.meter_name_to_index["energy"]
    for _ in range(3):
        env.step(acts(env, "ADVANCE"))
    env.meters[1, e] = 0.005
    env.step(acts(env, "ADVANCE")); env.step(acts(env, "ADVANCE"))
    print("  dones before reset:", env.dones.tolist(), "pers:", r.get("pers", reader="engine").tolist())
    obs = env.reset()
    print("  after reset dones:", env.dones.tolist(), " av", r.get("av", reader="engine").tolist(), " lagged", r.get("lagged", reader="engine").tolist(), " acc", r.get("acc", reader="engine").tolist(), " pers", r.get("pers", reader="engine").tolist(), " smooth", r.get("smooth", reader="engine").tolist())
    obs2 = env.reset()
    print("  second reset ok; pers", r.get("pers", reader="engine").tolist(), " history seeded:", env.vfs_evaluator._history.seeded if env.vfs_evaluator._history else None)
    env.step(acts(env, "ADVANCE"))
    print("  step after double reset: acc", r.get("acc", reader="engine").tolist(), "lagged", r.get("lagged", reader="engine").tolist())


if __name__ == "__main__":
    which = sys.argv[1:] or ["r1", "r2", "r3"]
    for name in which:
        globals()[name]()
