import math, torch, warnings
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate
from townlet.substrate.gridnd import GridNDSubstrate
from townlet.substrate.continuous import Continuous2DSubstrate
from townlet.substrate.base import pairwise_axis_deltas
print("== (c) radius from longest axis on 8x6, vision_range 0.3")
g = Grid2DSubstrate(8, 6, "clamp", "manhattan", enable_diagonals=True)
print("  radius:", g._token_vision_radius(0.3), " longest->", max(1, math.ceil(0.3*8/2)), " shorter->", max(1, math.ceil(0.3*6/2)))
print("  floor: vision_range=0.0 ->", g._token_vision_radius(0.0), "; 1x1 grid ->", Grid2DSubstrate(1,1,"clamp","manhattan")._token_vision_radius(0.5))
print("== (b) wrap shortest path, even(8) and odd(7) spans")
for span in (8, 7):
    gw = Grid2DSubstrate(span, span, "wrap", "manhattan")
    s = torch.tensor([[0, 0]]); e = torch.tensor([[span-1, 0], [span//2, 0], [1, 0]])
    d = pairwise_axis_deltas(s, e, gw._token_axis_sizes(torch.device("cpu")))
    print(f"  span={span}: entity x={[span-1, span//2, 1]} -> delta x={d[0,:,0].tolist()}  (|d|<=span/2: {bool((d.abs()<=span/2).all())})")
    vis_ab = gw.visible(s, e, 0.3); vis_ba = torch.stack([gw.visible(e[i:i+1], s, 0.3)[0] for i in range(3)]).squeeze(1)
    print(f"    visible sym: {vis_ab[0].tolist()} vs {vis_ba.tolist()}")
    ego = gw.egocentric_delta(s, e)
    print(f"    egocentric x: {ego[0,:,0].tolist()}  within [-1,1]: {bool((ego.abs()<=1).all())}")
print("== (d) denominators: normalize vs egocentric on 8x6 (and 1-wide axis)")
g86 = Grid2DSubstrate(8, 6, "clamp", "manhattan")
p = torch.tensor([[7, 5]]); o = torch.tensor([[0, 0]])
print("  normalize([7,5]) =", g86.normalize_positions(p).tolist(), " ego(0->[7,5]) =", g86.egocentric_delta(o, p).tolist())
g1 = Grid2DSubstrate(1, 5, "clamp", "manhattan")
print("  1-wide: normalize([0,4]) =", g1.normalize_positions(torch.tensor([[0,4]])).tolist(), " ego =", g1.egocentric_delta(torch.tensor([[0,0]]), torch.tensor([[0,4]])).tolist())
c = Continuous2DSubstrate(-5.0, 5.0, 0.0, 20.0, boundary="wrap", movement_delta=1.0, interaction_radius=1.0, action_discretization={"num_directions":8,"num_magnitudes":3}, distance_metric="euclidean")
cp = torch.tensor([[5.0, 20.0]]); co = torch.tensor([[-5.0, 0.0]])
print("  continuous normalize([5,20]) =", c.normalize_positions(cp).tolist(), " ego under wrap(-5,0 -> 5,20) =", c.egocentric_delta(co, cp).tolist(), "(wrap: full extent == 0 delta)")
print("== (h) bounce / sticky semantics")
for cls, args in ((Grid2DSubstrate, (8, 8)), (Grid3DSubstrate, (8, 8, 3))):
    b = cls(*args, boundary="bounce", distance_metric="manhattan")
    pos = torch.zeros((2, b.position_dim), dtype=torch.long); pos[1, 0] = args[0]-1
    d = torch.zeros((2, b.position_dim)); d[0, 0] = -1; d[1, 0] = 1
    print(f"  {cls.__name__} bounce: x=0 step -1 ->", b.apply_movement(pos, d)[0].tolist(), "; x=7 step +1 ->", b.apply_movement(pos, d)[1].tolist())
b1 = Grid2DSubstrate(1, 1, "bounce", "manhattan")
print("  Grid2D 1x1 bounce: x=0 step +1 ->", b1.apply_movement(torch.tensor([[0,0]]), torch.tensor([[1.,0.]])).tolist(), " (in bounds?)")
b1n = GridNDSubstrate([1,1,1,1], "bounce", "manhattan")
print("  GridND 1^4 bounce: step +1 ->", b1n.apply_movement(torch.zeros((1,4),dtype=torch.long), torch.tensor([[1.,0,0,0]])).tolist())
cb = Continuous2DSubstrate(0.0, 10.0, 0.0, 10.0, boundary="bounce", movement_delta=1.0, interaction_radius=1.0, action_discretization={"num_directions":8,"num_magnitudes":3}, distance_metric="euclidean")
print("  Continuous bounce: x=9.8 raw delta +0.5 ->", cb.apply_movement(torch.tensor([[9.8, 5.0]]), torch.tensor([[0.5, 0.0]])).tolist(), "; x=0.2 delta -0.5 ->", cb.apply_movement(torch.tensor([[0.2, 5.0]]), torch.tensor([[-0.5, 0.0]])).tolist())
cs = Continuous2DSubstrate(0.0, 10.0, 0.0, 10.0, boundary="sticky", movement_delta=1.0, interaction_radius=1.0, action_discretization={"num_directions":8,"num_magnitudes":3}, distance_metric="euclidean")
print("  Continuous sticky: x=9.8 delta +0.5 ->", cs.apply_movement(torch.tensor([[9.8, 5.0]]), torch.tensor([[0.5, 0.0]])).tolist())
gs = Grid2DSubstrate(8, 8, "sticky", "manhattan")
print("  Grid2D sticky diagonal at corner (0,0) UP_RIGHT [1,-1] ->", gs.apply_movement(torch.tensor([[0,0]]), torch.tensor([[1.,-1.]])).tolist(), "(per-axis sticky: x moves, y stays)")
gc = Grid2DSubstrate(8, 8, "clamp", "manhattan")
print("  Grid2D clamp same ->", gc.apply_movement(torch.tensor([[0,0]]), torch.tensor([[1.,-1.]])).tolist())
print("== every family x boundary x metric constructs?")
fams = []
for bnd in ("clamp","wrap","bounce","sticky"):
    for met in ("manhattan","euclidean","chebyshev"):
        for diag in (True, False):
            Grid2DSubstrate(8,6,bnd,met,enable_diagonals=diag); Grid3DSubstrate(4,5,3,bnd,met,enable_diagonals=diag)
        GridNDSubstrate([3,4,5,6],bnd,met)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            Continuous2DSubstrate(0,10,0,5,boundary=bnd,movement_delta=0.5,interaction_radius=1.0,action_discretization={"num_directions":8,"num_magnitudes":3},distance_metric=met)
        fams.append((bnd,met))
print("  constructed", len(fams), "boundary x metric combos for Grid2D/Grid3D/GridND/Continuous2D with no error")
print("== (e) movement delta order deterministic & matches names (Grid3D diag, GridND)")
g3 = Grid3DSubstrate(8,8,3,"clamp","manhattan",enable_diagonals=True)
print("  Grid3D:", [(a.name, a.delta) for a in g3.get_default_actions()])
print("  GridND 4D:", [(a.name, a.delta) for a in GridNDSubstrate([5,5,5,5],"clamp","manhattan").get_default_actions()][:4], "...")
