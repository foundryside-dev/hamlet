"""Leg-(b) probe for PRD-0001 Trial B (blind re-run) — the spreading organism.

Executes the pre-committed accepted-evidence checks for facets B-F1..B-F8 plus
the A.4 non-gating probes N1..N5. Lives in the trial pack directory, never under
src/townlet/ (protocol §6).

    UV_CACHE_DIR=.uv-cache uv run python configs/trial_b_blind_organism/probe_trial_b.py
"""

from __future__ import annotations

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_b_blind_organism")
LEVEL = "L1_spread"
DECLARED_ROOT = (0, 0, 0, 0, 0)
DECLARED_WAREHOUSE = (2, 2, 2, 2, 2)


def hdr(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def occupied(t: torch.Tensor) -> list[tuple[int, ...]]:
    return [tuple(int(v) for v in row) for row in (t > 0.5).nonzero(as_tuple=False)]


def manhattan(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return sum(abs(x - y) for x, y in zip(a, b, strict=True))


def build():
    u = UniverseCompiler().compile(PACK, primary_level=LEVEL)
    env = VectorizedHamletEnv(universe=u, level_name=LEVEL, num_agents=1, device=torch.device("cpu"))
    return u, env


def act_id(u, name: str) -> int:
    for a in u.runtime_action_space.actions:
        if a.name == name:
            return a.id
    raise KeyError(name)


def cells(env) -> torch.Tensor:
    return env.vfs_registry.get("organism_cells", reader="engine")


def main() -> None:
    u, env = build()
    lvl = u.get_level(LEVEL)
    interact = act_id(u, "INTERACT")

    def ap_of(name: str):
        return env.get_affordance_positions()["positions"][name]

    # ------------------------------------------------------------------ B-F1
    hdr("B-F1  premise: 5-D gridnd, exactly ONE organism / decision locus")
    env.reset()
    print(f"substrate class        : {type(env.substrate).__name__}")
    print(f"substrate_type (meta)  : {u.metadata.substrate_type}")
    print(f"dimension_sizes        : {env.substrate.dimension_sizes}")
    print(f"position_dim           : {u.metadata.position_dim}")
    print(f"grid_cells             : {u.metadata.grid_cells}")
    print(f"action_count           : {u.metadata.action_count}")
    print(f"action names           : {[a.name for a in u.runtime_action_space.actions]}")
    print(f"positions tensor shape : {tuple(env.positions.shape)}  <- agent dim = " f"{env.positions.shape[0]}")
    print(f"env.num_agents         : {env.num_agents}")
    print(f"declared population    : {lvl.training.population.size}")
    print(f"active_temporal        : {lvl.curriculum.curriculum.active_temporal}")
    env.positions = torch.tensor([[0, 0, 0, 0, 0]], dtype=torch.long)
    p0 = env.positions.tolist()
    env.step(torch.tensor([act_id(u, "DIM3_POS")]))
    p1 = env.positions.tolist()
    env.step(torch.tensor([act_id(u, "DIM4_POS")]))
    p2 = env.positions.tolist()
    print(f"motion on axis>=2      : {p0} -> {p1} (DIM3_POS) -> {p2} (DIM4_POS)")

    # --------------------------------------------------------------- B-F3/F2
    hdr("B-F3  rooted at point A  /  B-F2  extent is ONE entity's cell set")
    env.reset()
    c = cells(env)
    occ0 = occupied(c)
    print("container variable     : organism_cells (global scope, tensorNd)")
    print(f"container shape        : {tuple(c.shape)}  ({c.numel()} cells)")
    print(f"occupied at reset      : {occ0}")
    print(f"occupied_count(reset)  : {len(occ0)}")
    print(f"declared root          : {DECLARED_ROOT}")
    print(f"B-F3 root == declared  : {occ0 == [DECLARED_ROOT]}")
    print(f"cells are 5-tuples     : {all(len(x) == 5 for x in occ0)}")
    print(f"NOT a union of agent positions: positions tensor is " f"{tuple(env.positions.shape)}, a different variable")
    env.positions = torch.tensor([list(ap_of("GROW"))], dtype=torch.long)
    env.step(torch.tensor([interact]))
    occ1 = occupied(cells(env))
    print(f"occupied_count after one declared growth decision : {len(occ1)}")
    print(f"B-F2 occupied_count > 1 at some tick              : {len(occ1) > 1}")
    print(f"sample occupied cells  : {occ1[:3]} ... {occ1[-2:]}")

    # ------------------------------------------------------------------ B-F4
    hdr("B-F4  the food warehouse")
    print(f"affordance_ids         : {u.metadata.affordance_ids}")
    print(f"meter_names            : {u.metadata.meter_names}")
    wh = ap_of("WAREHOUSE")
    print(f"WAREHOUSE position     : {wh}  (len={len(wh)})")
    print(f"declared warehouse     : {list(DECLARED_WAREHOUSE)}")
    print(f"matches declared       : {list(wh) == list(DECLARED_WAREHOUSE)}")
    print(f"distinct from root     : {tuple(wh) != DECLARED_ROOT}")
    print(f"GROW positions declared in YAML    : " f"{len(lvl.affordances.affordances[0].deployment.positions)}")
    print(f"GROW positions deployed at runtime : 1 (tensor shape " f"{tuple(env.affordances['GROW'].shape)})")

    # ------------------------------------------------------------------ B-F5
    hdr("B-F5  spread: growth / adjacency / accumulation")
    # NOTE: global VFS survives reset() (see N1), so each facet below gets a
    # FRESH environment to guarantee the declared initial state.
    _, env = build()
    env.reset()
    env.positions = torch.tensor([list(DECLARED_ROOT)], dtype=torch.long)
    series = [occupied(cells(env))]
    for _ in range(4):
        env.step(torch.tensor([interact]))
        series.append(occupied(cells(env)))
    counts = [len(s) for s in series]
    grew = counts[0] == 1 and counts[-1] > counts[0]
    print(f"occupied_count series  : {counts}")
    print(f"(1) growth  count(0)==1 and count(N)>count(0) : {grew}")
    new_cells = sorted(set(series[1]) - set(series[0]))
    prev = set(series[0])
    non_adj = [x for x in new_cells if min(manhattan(x, p) for p in prev) != 1]
    print(f"(2) adjacency: newly occupied at t=1 : {len(new_cells)} cells")
    print(f"    not adjacent to any t=0 cell     : {len(non_adj)}")
    if non_adj:
        worst = max(non_adj, key=lambda x: min(manhattan(x, p) for p in prev))
        print(f"    example: prev={DECLARED_ROOT} new={worst} " f"manhattan={min(manhattan(worst, p) for p in prev)}")
    print(f"    ADJACENCY HOLDS : {not non_adj}")
    accum = all(set(series[i]) <= set(series[i + 1]) for i in range(len(series) - 1))
    print(f"(3) accumulation occupied(t) subset occupied(t+1) : {accum}")
    print(f"B-F5 all three hold : {grew and not non_adj and accum}")

    # ------------------------------------------------------------------ B-F6
    hdr("B-F6  is the spread directable by the policy?")

    # Both arms must actually GROW, so that what is compared is the DIRECTION of
    # growth and not merely whether growth occurred.  The single deployed GROW
    # instance sits at the root, so each arm excursions out along a different
    # axis, returns, and then grows.
    def grow_after(axis_pos: str, axis_neg: str) -> list[tuple[int, ...]]:
        _, e = build()
        e.reset()
        e.positions = torch.tensor([list(DECLARED_ROOT)], dtype=torch.long)
        e.step(torch.tensor([act_id(u, axis_pos)]))
        e.step(torch.tensor([act_id(u, axis_neg)]))
        pos_at_grow = e.positions.tolist()
        e.step(torch.tensor([interact]))
        return pos_at_grow, sorted(occupied(cells(e)))

    pos_a, set_a = grow_after("DIM0_POS", "DIM0_NEG")
    pos_b, set_b = grow_after("DIM3_POS", "DIM3_NEG")
    print(f"arm A (+axis0 then back) grew at {pos_a}: occupied_count={len(set_a)}")
    print(f"arm B (+axis3 then back) grew at {pos_b}: occupied_count={len(set_b)}")
    print(f"both arms actually grew (count > 1)   : " f"{len(set_a) > 1 and len(set_b) > 1}")
    print(f"sets DIFFER (required for B-F6)       : {set_a != set_b}")
    print(f"symmetric difference size             : " f"{len(set(set_a) ^ set(set_b))}")

    # ------------------------------------------------------------------ B-F7
    hdr("B-F7  reaching the warehouse produces a declared consequence")
    bi = {m.name: m.index for m in u.meter_metadata.meters}["biomass"]
    _, env = build()
    env.reset()
    env.positions = torch.tensor([[0, 0, 0, 0, 0]], dtype=torch.long)
    b0 = float(env.meters[0, bi])
    _, r_ctrl, _, i_ctrl = env.step(torch.tensor([interact]))
    b1 = float(env.meters[0, bi])
    print(f"CONTROL   pos=[0,0,0,0,0] interacted={i_ctrl['successful_interactions']}")
    print(f"          biomass {b0} -> {b1}   reward vector = {r_ctrl.tolist()}")
    env.positions = torch.tensor([list(DECLARED_WAREHOUSE)], dtype=torch.long)
    b2 = float(env.meters[0, bi])
    _, r_wh, _, i_wh = env.step(torch.tensor([interact]))
    b3 = float(env.meters[0, bi])
    print(f"WAREHOUSE pos={list(DECLARED_WAREHOUSE)} " f"interacted={i_wh['successful_interactions']}")
    print(f"          biomass {b2} -> {b3}   reward vector = {r_wh.tolist()}")
    print(f"meter delta at warehouse {b3 - b2:+.4f}   control {b1 - b0:+.4f}")
    print(f"reward delta (warehouse - control) : " f"{float(r_wh[0]) - float(r_ctrl[0]):+.6f}")
    print(f"B-F7 non-zero declared consequence : {abs(b3 - b2) > 0}")

    # ------------------------------------------------------------------ B-F8
    hdr("B-F8  observability of own extent AND warehouse location")
    spec, act = u.observation_spec, u.observation_activity
    print(f"total_dims             : {spec.total_dims}")
    print(f"active_dim_count       : {act.active_dim_count}")
    for f in spec.fields:
        print(f"  {f.name:24s} dims={f.dims:4d} [{f.start_index}:{f.end_index}] " f"sem={f.semantic_type:10s} feature={f.feature}")
    ext = next(f for f in spec.fields if f.name == "organism_cells")
    whf = next(f for f in spec.fields if f.name == "warehouse_position")
    for f in (ext, whf):
        seg = act.active_mask[f.start_index : f.end_index]
        print(f"active slots {f.name:20s} : {sum(seg)}/{len(seg)}")
    _, env = build()
    o0 = env.reset()
    v0 = o0[0, ext.start_index : ext.end_index]
    env.positions = torch.tensor([list(ap_of("GROW"))], dtype=torch.long)
    o1, _, _, _ = env.step(torch.tensor([interact]))
    v1 = o1[0, ext.start_index : ext.end_index]
    print(f"extent obs sum before growth : {float(v0.sum())}")
    print(f"extent obs sum after  growth : {float(v1.sum())}")
    print(f"extent-bound values CHANGE   : {bool((v0 != v1).any())}")
    wv = o1[0, whf.start_index : whf.end_index]
    print(f"warehouse-bound obs values   : {wv.tolist()}")
    print(f"declared warehouse coord     : {list(DECLARED_WAREHOUSE)}")
    print(f"encodes declared coordinate  : " f"{[float(x) for x in wv] == [float(x) for x in DECLARED_WAREHOUSE]}")

    # ------------------------------------------------------- A.4 (non-gating)
    hdr("N1  double reset (non-gating)")
    _, env = build()
    env.reset()
    print(f"occupied_count after reset #1 : {len(occupied(cells(env)))}")
    env.positions = torch.tensor([list(ap_of("GROW"))], dtype=torch.long)
    env.step(torch.tensor([interact]))
    print(f"occupied_count after growth   : {len(occupied(cells(env)))}")
    env.reset()
    n2 = len(occupied(cells(env)))
    sz = float(env.vfs_registry.get("organism_size", reader="engine"))
    print(f"occupied_count after reset #2 : {n2}")
    print(f"organism_size after reset #2  : {sz}")
    print(f"DECLARED INITIAL STATE RESTORED : {n2 == 1 and sz == 1.0}")
    print("  -> global-scope VFS is lifetime=persistent and survives reset()")

    hdr("N2  boundary cases (non-gating)")
    _, env = build()
    env.reset()
    env.positions = torch.tensor([[2, 2, 2, 2, 2]], dtype=torch.long)
    env.step(torch.tensor([act_id(u, "DIM0_POS")]))
    print(f"clamp at upper boundary   : {env.positions.tolist()}")
    env.positions = torch.tensor([[0, 0, 0, 0, 0]], dtype=torch.long)
    env.step(torch.tensor([act_id(u, "DIM0_NEG")]))
    print(f"clamp at lower boundary   : {env.positions.tolist()}")
    env.positions = torch.tensor([list(ap_of("GROW"))], dtype=torch.long)
    env.step(torch.tensor([interact]))
    n_a = len(occupied(cells(env)))
    env.step(torch.tensor([interact]))
    n_b = len(occupied(cells(env)))
    print(f"growth into occupied cells: {n_a} -> {n_b} (saturated/idempotent)")

    hdr("N3  obs bounds across the probe run (non-gating)")
    o = env.reset()
    lo, hi, finite = float(o.min()), float(o.max()), True
    for _ in range(15):
        o, _, _, _ = env.step(torch.tensor([interact]))
        lo, hi = min(lo, float(o.min())), max(hi, float(o.max()))
        finite = finite and bool(torch.isfinite(o).all())
    print(f"observation min/max : {lo:.4f} / {hi:.4f}   all finite: {finite}")
    for f in spec.fields:
        seg = o[0, f.start_index : f.end_index]
        if float(seg.min()) < 0.0 or float(seg.max()) > 1.0:
            print(f"  OUT OF [0,1]: {f.name} -> min={float(seg.min()):.3f} " f"max={float(seg.max()):.3f}")

    hdr("N4  random-policy smoke, 5 episodes (non-gating)")
    _, env = build()
    g = torch.Generator().manual_seed(42)
    for ep in range(5):
        env.reset()
        rs, term = [], False
        for _ in range(20):
            a = torch.randint(0, u.metadata.action_count, (1,), generator=g)
            _, r, d, _ = env.step(a)
            rs.append(float(r[0]))
            if bool(d[0]):
                term = True
                break
        print(
            f"  ep{ep}: steps={len(rs)} terminated={term} "
            f"reward min/max={min(rs):+.4f}/{max(rs):+.4f} "
            f"constant={len(set(rs)) == 1} finite={all(abs(x) < 1e30 for x in rs)}"
        )

    hdr("N5  reward-relevance note (non-gating)")
    d = lvl.drive
    print(f"extrinsic type     : {d.extrinsic.type}")
    print(f"bar_bonuses        : {[b.bar for b in d.extrinsic.bar_bonuses]}")
    print(f"variable_bonuses   : {d.extrinsic.variable_bonuses}")
    print(f"shaping            : " f"{[(s.type, getattr(s, 'target_affordance', None)) for s in d.shaping]}")
    print("organism_cells / organism_size in a reward component: NO")


if __name__ == "__main__":
    main()
