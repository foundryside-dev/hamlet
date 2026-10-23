import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
from townlet.substrate.factory import SubstrateFactory
for pack, lvl in [("configs/test/gridnd_4d_pack", None), ("configs/aspatial_test", None)]:
    import os
    lv = os.listdir(REPO / pack / "levels")[0]
    u = UniverseCompiler().compile(REPO / pack, primary_level=lv, use_cache=False)
    sub = SubstrateFactory.build(u.stratum.stratum.substrate, device="cpu")
    print(pack, type(sub).__name__, "has width/height:", hasattr(sub, "width") and hasattr(sub, "height"), "items_catalog:", u.items_catalog is not None)
