"""Compare two diff_worlds.py snapshot files; report first divergence per field for worlds 1..N-1."""

import sys

import torch

a = torch.load(sys.argv[1], weights_only=False)
b = torch.load(sys.argv[2], weights_only=False)
ignore = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
start = 0 if 'all' in ignore else 1
n = len(a[0]["worlds"])


def same(x, y):
    if isinstance(x, torch.Tensor):
        return isinstance(y, torch.Tensor) and x.shape == y.shape and torch.equal(x, y)
    if isinstance(x, dict):
        return isinstance(y, dict) and x.keys() == y.keys() and all(same(x[k], y[k]) for k in x)
    if isinstance(x, (list, tuple)):
        return isinstance(y, (list, tuple)) and len(x) == len(y) and all(same(a, b) for a, b in zip(x, y))
    return x == y


first = {}
rng_div = None
for sa, sb in zip(a, b, strict=True):
    if rng_div is None and sa["rng"] != sb["rng"]:
        rng_div = sa["t"]
    for w in range(start, n):
        for key in sa["worlds"][w]:
            if key in ignore or (w, key) in first or key not in sb["worlds"][w]:
                continue
            if not same(sa["worlds"][w][key], sb["worlds"][w][key]):
                first[(w, key)] = (sa["t"], sa["worlds"][w][key], sb["worlds"][w][key])

asym = set(a[0]["worlds"][0]) ^ set(b[0]["worlds"][0])
print(f"rng stream first diverges at step {rng_div}; keys only on one side: {sorted(asym)}")
if not first:
    print("NO DIVERGENCE in worlds 1..N-1")
for (w, key), (t, va, vb) in sorted(first.items(), key=lambda kv: (kv[1][0], kv[0])):
    ra = va if not isinstance(va, torch.Tensor) else f"tensor{tuple(va.shape)} ne={int((va != vb).sum())}"
    rb = vb if not isinstance(vb, torch.Tensor) else ""
    print(f"world {w} {key}: first differs at step {t}: A={ra!s:.200} B={rb!s:.200}")
