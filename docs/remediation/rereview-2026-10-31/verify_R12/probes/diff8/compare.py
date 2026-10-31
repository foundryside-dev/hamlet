import sys, torch
a = torch.load(sys.argv[1], weights_only=False); b = torch.load(sys.argv[2], weights_only=False)
print("actions equal:", a["actions"] == b["actions"], "| base:", a["actions"], "| new:", b["actions"] if a["actions"] != b["actions"] else "")
ta, tb = a["trace"], b["trace"]
assert len(ta) == len(tb)
keys = set().union(*ta, *tb)
bad = {}
for t, (x, y) in enumerate(zip(ta, tb)):
    for k in set(x) | set(y):
        if k not in x or k not in y:
            bad.setdefault(k, f"missing on one side at tick {t}"); continue
        if not (x[k].shape == y[k].shape and x[k].dtype == y[k].dtype and torch.equal(x[k], y[k])):
            bad.setdefault(k, f"first diff tick {t}")
print("keys:", len(keys), "| divergent:", bad if bad else "NONE (bitwise identical)")
