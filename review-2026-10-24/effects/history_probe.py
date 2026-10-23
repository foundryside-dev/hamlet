import torch
from townlet.world.expression.history import TemporalHistory
h = TemporalHistory({"bar.x": 3}, torch.device("cpu"))
# Simulate VFS evaluator order: evaluate (lag/delta) THEN push current.
vals = [1.0, 2.0, 4.0, 8.0, 16.0]
for step, v in enumerate(vals):
    cur = torch.tensor([v])
    l1 = h.lag("bar.x", 1, torch.zeros(1)).item()
    l0 = h.lag("bar.x", 0, torch.zeros(1)).item()
    l3 = h.lag("bar.x", 3, torch.zeros(1)).item()
    ma2 = h.moving_average("bar.x", 2, cur).item()
    ma3 = h.moving_average("bar.x", 3, cur).item()
    hh = h.has_history("bar.x", 1)
    print(f"step {step} cur={v}: lag1={l1} lag0={l0} lag3={l3} ma2={ma2:.3f} ma3={ma3:.3f} has1={None if hh is None else hh.item()}")
    h.push("bar.x", cur)
print("expected: lag1 at step s == vals[s-1]; ma2 at step s == mean(vals[s-1], vals[s]); lag3 at step 3 == vals[0]")
# edge: evaluator order
hb = TemporalHistory({"bar.b": 2}, torch.device("cpu"))
seq = [False, True, True, False]
for step, b in enumerate(seq):
    cur = torch.tensor([b])
    r = hb.edge("bar.b", cur, rising=True).item(); f = hb.edge("bar.b", cur, rising=False).item()
    print(f"edge step {step} cur={b}: rising={r} falling={f}")
    hb.push("bar.b", cur)
