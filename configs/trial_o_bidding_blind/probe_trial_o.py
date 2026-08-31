"""Trial O (Adversarial bidding) runtime probe.

Lives in the trial pack, never under src/townlet/ (protocol §6).

Drives two agents onto two different BID affordance tiles in the SAME tick, then reads
back, from the live VFS registry, the meter tensor and the encoded observation:
  - each agent's submitted bid          (facets O3, O8)
  - the clearing price                  (facets O5, O8)
  - who was awarded, and that the good is consumed exactly once  (facets O2, O6)
  - money before/after                  (facet O7)
and repeats with the high bid held by the OTHER agent to test order-independence (O4).
"""

from __future__ import annotations

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path(__file__).resolve().parent
LEVEL = "L5_multi_agent"
AUCTION_FIELDS = ("prize_available", "prize_holder", "scan_index", "clearing_price", "auction_awarded", "bid", "last_bid", "won_auction")


def build():
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL)
    env = VectorizedHamletEnv.from_universe(
        universe,
        level_name=LEVEL,
        num_agents=3,
        device=torch.device("cpu"),
    )
    return universe, env


def action_id(env, name):
    for a in env.action_space.actions:
        if a.name == name:
            return a.id
    raise KeyError(f"{name} not in {[a.name for a in env.action_space.actions]}")


def read(env, var):
    return env.vfs_registry.get(var, reader="engine")


def money(env):
    idx = env.meter_name_to_index["money"]
    return env.meters[:, idx].clone()


def obs_slices(universe):
    out = {}
    for f in universe.observation_spec.fields:
        if f.name in AUCTION_FIELDS:
            out[f.name] = (f.start_index, f.end_index)
    return out


def run_round(high_agent: int, low_agent: int, label: str):
    """Fresh env; put `high_agent` on BID_HIGH, `low_agent` on BID_LOW, both INTERACT same tick."""
    universe, env = build()
    env.reset()
    interact = action_id(env, "INTERACT")
    wait = action_id(env, "WAIT")

    hi_pos = env.affordances["BID_HIGH"].to(env.positions.dtype)
    lo_pos = env.affordances["BID_LOW"].to(env.positions.dtype)
    env.positions[high_agent] = hi_pos
    env.positions[low_agent] = lo_pos

    before = money(env)
    actions = torch.full((env.num_agents,), wait, dtype=torch.long, device=env.device)
    actions[high_agent] = interact
    actions[low_agent] = interact

    obs = env.step(actions)
    if isinstance(obs, tuple):
        obs = obs[0]
    after = money(env)

    print(f"--- {label}: high=agent{high_agent} low=agent{low_agent} ---")
    print(f"  positions          : {env.positions.tolist()}")
    print(f"  BID_HIGH tile      : {hi_pos.tolist()}   BID_LOW tile: {lo_pos.tolist()}")
    print(f"  vfs.last_bid       : {read(env, 'last_bid').tolist()}      <- O3 (agent-chosen amounts)")
    print(f"  vfs.clearing_price : {read(env, 'clearing_price').tolist()}          <- O5 (max over agents)")
    print(f"  vfs.prize_available: {read(env, 'prize_available').tolist()}          <- O2 (good consumed)")
    print(
        f"  vfs.prize_holder   : {read(env, 'prize_holder').tolist()}         "
        "<- O2/O6 (single agent index holding the good; -1 = unowned)"
    )
    print(f"  vfs.auction_awarded: {read(env, 'auction_awarded').tolist()}")
    print(f"  vfs.won_auction    : {read(env, 'won_auction').tolist()}      <- O6 (unique winner)")
    print(f"  money before       : {before.tolist()}")
    print(f"  money after        : {after.tolist()}")
    print(f"  money delta        : {(after - before).tolist()}      <- O7 (winner charged, losers not)")

    sl = obs_slices(universe)
    print(f"  observation tensor shape: {tuple(obs.shape)}")
    for name in AUCTION_FIELDS:
        if name in sl:
            s, e = sl[name]
            print(f"    obs[:, {s}:{e}] ({name:<16}) = {obs[:, s:e].flatten().tolist()}")
    return {
        "clearing_price": float(read(env, "clearing_price").item()),
        "won": read(env, "won_auction").tolist(),
        "holder": float(read(env, "prize_holder").item()),
        "last_bid": read(env, "last_bid").tolist(),
        "delta": (after - before).tolist(),
        "obs": obs.clone(),
        "slices": sl,
        "env": env,
        "universe": universe,
    }


# --- Facet O3, verified through the ACTION CHANNEL only -----------------------
# No direct writes to env.positions anywhere in this round: the two bidders WALK to
# their chosen bid tiles using movement action ids, then both INTERACT on one tick.
DELTAS = {0: (0, -1), 1: (0, 1), 2: (-1, 0), 3: (1, 0), 4: (-1, -1), 5: (1, -1), 6: (-1, 1), 7: (1, 1)}


def step_toward(pos, goal):
    """Return the movement action id that best closes the gap, or None if already there."""
    dx = int(goal[0]) - int(pos[0])
    dy = int(goal[1]) - int(pos[1])
    if dx == 0 and dy == 0:
        return None
    sx = (dx > 0) - (dx < 0)
    sy = (dy > 0) - (dy < 0)
    for aid, (ddx, ddy) in DELTAS.items():
        if (ddx, ddy) == (sx, sy):
            return aid
    raise AssertionError(f"no action for delta {(sx, sy)}")


def run_walked_round(agent_hi: int, agent_lo: int, label: str, max_walk: int = 30):
    universe, env = build()
    env.reset()
    interact = action_id(env, "INTERACT")
    wait = action_id(env, "WAIT")
    goals = {agent_hi: env.affordances["BID_HIGH"].tolist(), agent_lo: env.affordances["BID_LOW"].tolist()}

    print(f"--- {label} (walked; env.positions never written by the probe) ---")
    print(f"  start positions : {env.positions.tolist()}")
    print(f"  goals           : agent{agent_hi} -> BID_HIGH {goals[agent_hi]}, agent{agent_lo} -> BID_LOW {goals[agent_lo]}")

    walked = 0
    action_log = []
    while walked < max_walk:
        acts = torch.full((env.num_agents,), wait, dtype=torch.long, device=env.device)
        moving = False
        for ag, goal in goals.items():
            a = step_toward(env.positions[ag].tolist(), goal)
            if a is not None:
                acts[ag] = a
                moving = True
        if not moving:
            break
        action_log.append(acts.tolist())
        env.step(acts)
        walked += 1

    print(f"  walked {walked} ticks with movement actions only; action ids issued: {action_log}")
    print(f"  positions after walk: {env.positions.tolist()}")
    assert env.positions[agent_hi].tolist() == goals[agent_hi], "high bidder did not reach BID_HIGH"
    assert env.positions[agent_lo].tolist() == goals[agent_lo], "low bidder did not reach BID_LOW"

    before = money(env)
    acts = torch.full((env.num_agents,), wait, dtype=torch.long, device=env.device)
    acts[agent_hi] = interact
    acts[agent_lo] = interact
    print(f"  contested tick: both bidders issue INTERACT (id {interact}); actions = {acts.tolist()}")
    obs = env.step(acts)
    if isinstance(obs, tuple):
        obs = obs[0]
    after = money(env)

    print(f"  vfs.last_bid       : {read(env, 'last_bid').tolist()}   <- O3 via action choice alone")
    print(f"  vfs.clearing_price : {float(read(env, 'clearing_price'))}")
    print(f"  vfs.prize_holder   : {float(read(env, 'prize_holder'))}")
    print(f"  vfs.won_auction    : {read(env, 'won_auction').tolist()}")
    print(f"  money delta        : {(after - before).tolist()}")
    print(f"  energy after walk  : {env.meters[:, env.meter_name_to_index['energy']].tolist()}")
    return {
        "last_bid": read(env, "last_bid").tolist(),
        "won": read(env, "won_auction").tolist(),
        "holder": float(read(env, "prize_holder")),
    }


def main():
    universe, env = build()
    print("=== compiled artifact ===")
    print("observation total_dims:", universe.observation_spec.total_dims)
    print("auction observation fields (name, start, end, semantic_type):")
    for f in universe.observation_spec.fields:
        if f.name in AUCTION_FIELDS:
            print(f"   {f.name:<18} [{f.start_index}:{f.end_index}] {f.semantic_type} scope={f.scope} uuid={f.uuid}")
    act = universe.observation_activity
    print("active dims:", act.active_dim_count, "of", act.total_dims)
    for f in universe.observation_spec.fields:
        if f.name in AUCTION_FIELDS:
            print(f"   active_mask[{f.start_index}:{f.end_index}] ({f.name}) =", list(act.active_mask[f.start_index : f.end_index]))
    print("actions:", [(a.id, a.name) for a in env.action_space.actions])
    print("num_agents:", env.num_agents, " meters shape:", tuple(env.meters.shape))
    print("effect catalog:", sorted(env.effect_manager.catalog.effects.keys()))
    print("declared scope of auction_clearing:", env.effect_manager.catalog.effects["auction_clearing"].scope)
    print("affordances deployed:", sorted(env.affordances.keys()))
    env.reset()
    print("global_effects after reset:", len(env.effect_manager.global_effects))
    print()

    r1 = run_round(high_agent=1, low_agent=0, label="ROUND 1 (agent1 bids high)")
    print()
    r2 = run_round(high_agent=0, low_agent=1, label="ROUND 2 (agent0 bids high — bidders swapped)")
    print()
    print("=== order-independence check (facet O4) ===")
    print("round1 last_bid:", r1["last_bid"], "-> winner", r1["won"])
    print("round2 last_bid:", r2["last_bid"], "-> winner", r2["won"])
    print("clearing price identical:", r1["clearing_price"], r2["clearing_price"])
    print("prize_holder round1/round2:", r1["holder"], r2["holder"])
    print("winner follows the HIGH BID, not the agent index / loop order:", r1["won"].index(1.0) == 1 and r2["won"].index(1.0) == 0)
    print()
    print("=== ROUND 0: facet O3 through the ACTION CHANNEL (no probe writes to env.positions) ===")
    w1 = run_walked_round(agent_hi=1, agent_lo=0, label="WALKED ROUND A (agent1 walks to BID_HIGH)")
    print()
    w2 = run_walked_round(agent_hi=0, agent_lo=1, label="WALKED ROUND B (agent0 walks to BID_HIGH)")
    print()
    print("  O3 summary — same INTERACT action, different DESTINATION chosen by movement actions:")
    print("    walked A last_bid:", w1["last_bid"], "-> winner", w1["won"], "holder", w1["holder"])
    print("    walked B last_bid:", w2["last_bid"], "-> winner", w2["won"], "holder", w2["holder"])
    print()
    print("=== ROUND 3: the clearing phase keeps running with NO bids (unowned state) ===")
    universe3, env3 = build()
    env3.reset()
    interact = action_id(env3, "INTERACT")
    wait = action_id(env3, "WAIT")
    env3.positions[2] = env3.affordances["BID_LOW"].to(env3.positions.dtype)
    a = torch.full((env3.num_agents,), wait, dtype=torch.long, device=env3.device)
    a[2] = interact
    env3.step(a)
    print(
        "  tick 1 (agent2 bids 1.0): clearing_price",
        float(read(env3, "clearing_price")),
        "prize_holder",
        float(read(env3, "prize_holder")),
        "won",
        read(env3, "won_auction").tolist(),
        "money",
        money(env3).tolist(),
    )
    a_all_wait = torch.full((env3.num_agents,), wait, dtype=torch.long, device=env3.device)
    env3.step(a_all_wait)
    print(
        "  tick 2 (nobody bids)    : clearing_price",
        float(read(env3, "clearing_price")),
        "prize_holder",
        float(read(env3, "prize_holder")),
        "prize_available",
        float(read(env3, "prize_available")),
        "won",
        read(env3, "won_auction").tolist(),
        "money",
        money(env3).tolist(),
    )
    print("  clearing effect still standing:", {k: [x.effect_id for x in v] for k, v in env3.effect_manager.agent_effects.items()})
    print()
    print("=== ROUND 4: TIE — two agents bid the SAME amount (uniqueness of the award) ===")
    _, env4 = build()
    env4.reset()
    interact = action_id(env4, "INTERACT")
    wait = action_id(env4, "WAIT")
    env4.positions[0] = env4.affordances["BID_HIGH"].to(env4.positions.dtype)
    env4.positions[1] = env4.affordances["BID_HIGH"].to(env4.positions.dtype)
    before4 = money(env4)
    a4 = torch.full((env4.num_agents,), wait, dtype=torch.long, device=env4.device)
    a4[0] = interact
    a4[1] = interact
    env4.step(a4)
    print("  last_bid      :", read(env4, "last_bid").tolist())
    print("  clearing_price:", float(read(env4, "clearing_price")))
    print("  prize_holder  :", float(read(env4, "prize_holder")))
    print("  won_auction   :", read(env4, "won_auction").tolist())
    print("  money delta   :", (money(env4) - before4).tolist())
    print("  awarded exactly once:", sum(read(env4, "won_auction").tolist()) == 1.0)
    print()
    print("=== where the clearing effect actually lives (declared scope: global) ===")
    e = r2["env"]
    print("global_effects:", [x.effect_id for x in e.effect_manager.global_effects])
    print("agent_effects :", {k: [x.effect_id for x in v] for k, v in e.effect_manager.agent_effects.items()})


if __name__ == "__main__":
    main()
