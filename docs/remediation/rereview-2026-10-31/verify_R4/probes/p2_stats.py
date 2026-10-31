"""Area 2: statistical sanity + edge cases of vfs/random_draws.py, driven directly."""
import os, sys, math, time
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
from pathlib import Path
HERE = Path(__file__).resolve().parent; WT = HERE.parent / "wt"; sys.path.insert(0, str(WT / "src"))
import torch, townlet
assert str(WT) in townlet.__file__
from townlet.vfs.random_draws import VFSRandomness, reference_uniform, _UNIFORM_BITS, _MASK64
torch.set_printoptions(precision=6)
dev = torch.device("cpu")

def stream(seed, episode, tick, worlds, site="var:x", shape=None):
    r = VFSRandomness(seed); r._episode = episode
    return r.instant(tick=tick, worlds=worlds, device=dev).stream(site, shape or (worlds,))

print("### reference_uniform vs kernel")
ok = True
for seed, ep, tick, site, ordn, w, el in [(0, 1, 0, "var:x", 0, 0, 0), (42, 3, 17, "rule:r:0:expression", 2, 5, 7), (-1, 1, 2**40, "a", 0, 3, 0), (2**63, 2, 5, "action:WAIT:0:condition", 1, 1, 3)]:
    r = VFSRandomness(seed); r._episode = ep
    s = r.instant(tick=tick, worlds=w + 1, device=dev).stream(site, (w + 1, el + 1))
    for _ in range(ordn):
        s.uniform("uniform", torch.zeros(()))
    got = s.uniform("uniform", torch.zeros(()))[w, el].item()
    ref = reference_uniform(seed=seed, episode=ep, tick=tick, site=site, ordinal=ordn, world=w, element=el)
    ok &= abs(got - ref) < 1e-9
    print(f"  seed={seed} ep={ep} tick={tick} site={site} ord={ordn} w={w} el={el}: kernel={got:.9f} ref={ref:.9f} {'OK' if abs(got-ref)<1e-9 else 'MISMATCH'}")
print("  all match:", ok)

print("\n### uniform / normal at 1e6 samples (W=1e6 worlds, one tick)")
N = 1_000_000
u = stream(7, 1, 3, N).uniform("uniform", torch.zeros(()))
print(f"  uniform mean={u.double().mean():.5f} (0.5) var={u.double().var():.6f} (0.083333) min={u.min():.3e} max={u.max():.8f} <1: {bool((u<1).all())} >=0: {bool((u>=0).all())}")
hist = torch.histc(u.double(), bins=100, min=0, max=1); chi2 = ((hist - N / 100) ** 2 / (N / 100)).sum().item()
print(f"  100-bin chi2={chi2:.1f} (df=99, expect ~99 +- 14)")
nrm = stream(7, 1, 3, N).normal("normal_dist", torch.zeros(()))
print(f"  normal mean={nrm.double().mean():.5f} (0) var={nrm.double().var():.5f} (1) skew={((nrm.double()-nrm.double().mean())**3).mean()/nrm.double().std()**3:.4f} kurt={((nrm.double()-nrm.double().mean())**4).mean()/nrm.double().std()**4:.4f} (3) finite: {bool(torch.isfinite(nrm).all())}")
print(f"  normal |x|>4: {int((nrm.abs()>4).sum())} (expect ~63)")

print("\n### 1000 ticks x 1000 worlds: cross-tick/world correlation")
T, W = 1000, 1000
r = VFSRandomness(7); r._episode = 1
grid = torch.stack([r.instant(tick=t, worlds=W, device=dev).stream("var:x", (W,)).uniform("uniform", torch.zeros(())) for t in range(T)]).double()
print(f"  mean={grid.mean():.5f} var={grid.var():.6f}")
def corr(a, b): return float(((a - a.mean()) * (b - b.mean())).mean() / (a.std() * b.std()))
print(f"  corr adjacent ticks: {corr(grid[:-1].flatten(), grid[1:].flatten()):+.5f}")
print(f"  corr adjacent worlds: {corr(grid[:, :-1].flatten(), grid[:, 1:].flatten()):+.5f}")
print(f"  corr tick t vs t+37: {corr(grid[:-37].flatten(), grid[37:].flatten()):+.5f}")
# sites and elements
s2 = r.instant(tick=5, worlds=W, device=dev)
a = s2.stream("var:a", (W,)).uniform("uniform", torch.zeros(())).double(); b = s2.stream("var:b", (W,)).uniform("uniform", torch.zeros(())).double()
print(f"  corr sites var:a vs var:b same instant: {corr(a, b):+.5f}")
e = s2.stream("rule:r:0", (W, 14)).uniform("uniform", torch.zeros(())).double()
print(f"  corr adjacent elements: {corr(e[:, :-1].flatten(), e[:, 1:].flatten()):+.5f}; corr element0 vs var:a (same instant, different site): {corr(e[:,0], a):+.5f}")
st = s2.stream("var:two", (W,)); d1 = st.uniform("uniform", torch.zeros(())).double(); d2 = st.uniform("uniform", torch.zeros(())).double()
print(f"  corr two draws in one expression (ordinal 0 vs 1): {corr(d1, d2):+.5f}; equal: {bool((d1==d2).any())}")
# episodes
r2 = VFSRandomness(7); r2._episode = 2
ep2 = r2.instant(tick=0, worlds=W, device=dev).stream("var:x", (W,)).uniform("uniform", torch.zeros(())).double()
print(f"  corr episode1 vs episode2 same tick/site: {corr(grid[0], ep2):+.5f}")
# seeds
sA = stream(1, 1, 0, W).uniform("uniform", torch.zeros(())).double(); sB = stream(2, 1, 0, W).uniform("uniform", torch.zeros(())).double()
print(f"  corr seed1 vs seed2: {corr(sA, sB):+.5f}")

print("\n### repeats across (world, tick) at N=4096 worlds x 4096 ticks vs 2^24 resolution")
Wn, Tn = 4096, 64
vals = torch.stack([r.instant(tick=t, worlds=Wn, device=dev).stream("var:x", (Wn,)).uniform("uniform", torch.zeros(())) for t in range(Tn)]).flatten()
n = vals.numel(); distinct = torch.unique(vals).numel()
expected_collisions = n * (n - 1) / 2 / (1 << _UNIFORM_BITS)
print(f"  n={n} distinct={distinct} repeats={n-distinct}; birthday expectation ~{expected_collisions:.0f} (24-bit grid)")
# values must be multiples of 2^-24 exactly
print(f"  every value a multiple of 2^-24: {bool(((vals.double() * (1<<24)) % 1 == 0).all())}")
# world-wise: are any two worlds identical over the 64 ticks?
rows = vals.reshape(Tn, Wn).T
print(f"  identical world rows (64 ticks): {Wn - torch.unique(rows, dim=0).shape[0]}")

print("\n### edge cases")
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.parser import ExpressionParser
P = ExpressionParser()
def ev(expr, worlds=8, seed=3, tick=1):
    ctx = ExecutionContext(bars={}, vfs={}, temporal={}, device=dev)
    ctx.draws = stream(seed, 1, tick, worlds)
    return Evaluator(ctx).evaluate(P.parse(expr))
for expr in ["uniform(5.0, 2.0)", "uniform(3.0, 3.0)", "normal_dist(0.0, 0.0)", "normal_dist(0.0, -2.0)", "uniform(-1e30, 1e30)", "uniform(0.0, 1e-45)"]:
    v = ev(expr); print(f"  {expr:24} -> {v[:4].tolist()} finite={bool(torch.isfinite(v).all())}")
# ticks: int64 overflow in mixing? large tick and episode
for tick in [0, 2**31, 2**40, 2**62, 2**63 - 1, 2**63, 2**64 - 1, 2**64, 2**70]:
    try:
        v = stream(3, 1, tick, 4).uniform("uniform", torch.zeros(())); ref = reference_uniform(seed=3, episode=1, tick=tick, site="var:x", ordinal=0, world=2, element=0)
        print(f"  tick={tick}: {v.tolist()} ref(w2)={ref:.7f} match={abs(float(v[2])-ref)<1e-9}")
    except Exception as e:
        print(f"  tick={tick}: {type(e).__name__}: {str(e)[:120]}")
for ep in [0, 1, 10**6, 2**40, 2**63, 2**64 + 5]:
    try:
        v = stream(3, ep, 1, 2).uniform("uniform", torch.zeros(())); print(f"  episode={ep}: {v.tolist()}")
    except Exception as e:
        print(f"  episode={ep}: {type(e).__name__}: {str(e)[:120]}")
for seed in [0, -1, -2**63, 2**64 - 1, 2**64, 2**100]:
    try:
        r0 = VFSRandomness(seed); v = r0.instant(tick=0, worlds=2, device=dev).stream("s", (2,)).uniform("uniform", torch.zeros(()))
        print(f"  seed={seed}: state={r0.state()} v={v.tolist()}")
    except Exception as e:
        print(f"  seed={seed}: {type(e).__name__}: {str(e)[:120]}")
print("  seed -1 == seed 2^64-1:", torch.equal(stream(-1, 1, 0, 4).uniform('u', torch.zeros(())), stream(2**64 - 1, 1, 0, 4).uniform('u', torch.zeros(()))))
print("  seed 0 vs seed 2^64 (aliases):", torch.equal(stream(0, 1, 0, 4).uniform('u', torch.zeros(())), stream(2**64, 1, 0, 4).uniform('u', torch.zeros(()))))
print("  tick 0 vs tick 2^64 (aliases):", torch.equal(stream(3, 1, 0, 4).uniform('u', torch.zeros(())), stream(3, 1, 2**64, 4).uniform('u', torch.zeros(()))))
# restore
r0 = VFSRandomness(5)
for bad in [{"seed": -1, "episode": 0}, {"seed": 1}, {"seed": 1, "episode": True}, {"seed": 1.0, "episode": 0}, {"seed": 2**70, "episode": 1}]:
    try:
        r0.restore(bad); print(f"  restore({bad}) -> accepted; state={r0.state()}")
    except Exception as e:
        print(f"  restore({bad}) -> {type(e).__name__}: {str(e)[:100]}")
try:
    VFSRandomness(True)
except Exception as e:
    print("  VFSRandomness(True):", type(e).__name__)
print("  torch.initial_seed() default range:", torch.initial_seed(), "(int64 non-negative)")
# many resets
r0 = VFSRandomness(5); [r0.reset() for _ in range(100000)]; print("  100000 resets: episode =", r0.episode)
# cuda shr semantics check (CPU only here): negative int64 logical shift
from townlet.vfs.random_draws import _shr
t = torch.tensor([-1, -(2**63)], dtype=torch.int64); print("  _shr(-1, 40) =", _shr(t, 40).tolist(), "(expect 16777215, 8388608)")
# perf
t0 = time.time(); [stream(1, 1, t, 256).uniform("u", torch.zeros(())) for t in range(1000)]; print(f"  1000 draws of 256 worlds: {time.time()-t0:.3f}s")
