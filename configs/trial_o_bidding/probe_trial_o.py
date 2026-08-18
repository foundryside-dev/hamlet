"""Trial O runtime probe (protocol §6 leg (b)). Lives in the trial pack, never under src/townlet/.

Facets:
  1: a BID affordance writes the acting agent's bid meter, and only that agent's
  2: two agents' bids placed on the same tick are BOTH live (simultaneous collection)
  3: the clearing phase resolves the winner by comparison — swap test included
  4: award — the winner's wins meter moves, the loser's does not
  5: charge — the winner pays exactly its bid from credits, the loser pays nothing
  6: bid/wins/credits are observation fields tracking the values at their offsets
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_o_bidding")
LEVEL = "L0_auction"

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

print("== Facet 6 (first half): bid/wins/credits are compiled observation fields ==")
spec = universe.observation_spec
watch_fields = {}
offset = 0
for f in spec.fields:
    if any(k in f.name for k in ("bid", "wins", "credits")):
        watch_fields[f.name] = offset
        print(f"  field {f.name!r}: offset={offset} dims={f.dims}")
    offset += f.dims
print(f"  total_dims={spec.total_dims}")


def fresh_env() -> VectorizedHamletEnv:
    e = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=2, device=torch.device("cpu"))
    e.reset()
    return e


env = fresh_env()
print(f"  affordances in runtime: {sorted(env.affordances.keys())}")

i_bid = env.meter_name_to_index["bid"]
i_wins = env.meter_name_to_index["wins"]
i_credits = env.meter_name_to_index["credits"]

label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
INTERACT = label_to_action["INTERACT"]
WAIT = label_to_action["WAIT"]


def park(e: VectorizedHamletEnv, agent: int, name: str) -> None:
    e.positions[agent] = torch.tensor(e.affordances[name], device=e.device, dtype=e.positions.dtype)


def state(e: VectorizedHamletEnv) -> str:
    return " | ".join(
        f"a{i}: bid={round(e.meters[i, i_bid].item(), 4)} wins={round(e.meters[i, i_wins].item(), 4)} "
        f"credits={round(e.meters[i, i_credits].item(), 4)}"
        for i in range(2)
    )


def step(e: VectorizedHamletEnv, a0: int, a1: int):
    obs, *_ = e.step(torch.tensor([a0, a1]))
    return obs


print("\n== Facet 1: one agent bids; only that agent's bid meter moves ==")
park(env, 0, "BID_HIGH")
park(env, 1, "BID_LOW")
step(env, INTERACT, WAIT)
print(f"  after a0 INTERACT@BID_HIGH, a1 WAIT:   {state(env)}")
print("     <- expect a0 bid=0.3, a1 bid=0.0 (no cross-agent write)")

print("\n== Facet 2: both agents bid on the SAME tick; both bids live in the window ==")
env2 = fresh_env()
park(env2, 0, "BID_HIGH")
park(env2, 1, "BID_LOW")
obs = step(env2, INTERACT, INTERACT)
print(f"  after simultaneous INTERACT:           {state(env2)}")
print("     <- expect a0 bid=0.3 AND a1 bid=0.1, both standing (window open)")

print("\n== Facet 6 (second half): the encoded observation tracks the live bids ==")
for name, off in watch_fields.items():
    print(f"  obs[{off}] ({name}) a0={round(obs[0, off].item(), 6)} a1={round(obs[1, off].item(), 6)}")

print("\n== Facets 3/4/5: the window closes — compare, award, charge ==")
for k in range(4):
    obs = step(env2, WAIT, WAIT)
    print(f"  WAIT tick {k + 1}:                           {state(env2)}")
print("     <- expect exactly one clearing: a0 wins=1 credits=0.7 (paid its 0.3),")
print("        a1 wins=0 credits=1.0 (paid nothing), both bids expired to 0")
for name, off in watch_fields.items():
    print(f"  obs[{off}] ({name}) a0={round(obs[0, off].item(), 6)} a1={round(obs[1, off].item(), 6)}")

print("\n== Facet 3 swap test: same amounts, opposite agents — outcome must follow the amounts ==")
env3 = fresh_env()
park(env3, 0, "BID_LOW")
park(env3, 1, "BID_HIGH")
step(env3, INTERACT, INTERACT)
for _ in range(4):
    step(env3, WAIT, WAIT)
print(f"  after swapped bids + clearing:         {state(env3)}")
print("     <- expect a1 wins=1 credits=0.7, a0 wins=0 credits=1.0 (mirror of above)")

print("\n== Facet 3 no-bid guard: with no bids standing, clearing must award nobody ==")
env4 = fresh_env()
park(env4, 0, "BID_HIGH")
park(env4, 1, "BID_LOW")
step(env4, INTERACT, INTERACT)
for _ in range(12):
    step(env4, WAIT, WAIT)
print(f"  after 1 auction + 3 empty windows:     {state(env4)}")
print("     <- expect wins/credits unchanged from the single clearing (no repeat awards)")
