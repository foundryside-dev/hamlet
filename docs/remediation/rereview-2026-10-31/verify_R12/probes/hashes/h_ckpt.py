"""Item 5: checkpoint identity on effects/appearance hashes; format 7; cached 1.39 artifact."""
import sys, shutil, logging, warnings, copy
logging.disable(logging.CRITICAL); warnings.filterwarnings("ignore")
from pathlib import Path
import msgpack
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compiled import CompiledUniverse, COMPILED_SCHEMA_VERSION
from townlet.training.checkpoint_utils import attach_universe_metadata, assert_checkpoint_identity, CHECKPOINT_FORMAT_VERSION, validate_demo_checkpoint_payload
W = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/ckpt")
def cp(src, name):
    d = W / name; shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns(".compiled")); return d
def comp(d, lv, cache=False): return UniverseCompiler().compile(d, primary_level=lv, use_cache=cache)
def check(label, ck, u):
    try: print(f"{label}: ACCEPTED ({assert_checkpoint_identity(ck, u, force_new_vfs=False)})")
    except Exception as e: print(f"{label}: REFUSED {type(e).__name__}: {str(e)[:170]}")
print("CHECKPOINT_FORMAT_VERSION", CHECKPOINT_FORMAT_VERSION, "COMPILED_SCHEMA_VERSION", COMPILED_SCHEMA_VERSION)
d = cp("configs/test/items_smoke", "is"); u = comp(d, "L0_smoke")
ck = {"version": CHECKPOINT_FORMAT_VERSION}; attach_universe_metadata(ck, u)
print("stamped effects_hash", ck["effects_hash"][:12], "items_appearance_hash", ck["items_appearance_hash"][:12])
check("self", ck, u)
c2 = dict(ck); del c2["effects_hash"]; check("missing effects_hash key", c2, u)
c2 = dict(ck); del c2["items_appearance_hash"]; check("missing items_appearance_hash key", c2, u)
c2 = dict(ck); c2["version"] = 7; check("format 7", c2, u)
c2 = dict(ck); c2["effects_hash"] = None; check("effects_hash None vs digest", c2, u)
c2 = dict(ck); c2["items_appearance_hash"] = None; check("items_appearance_hash None vs digest", c2, u)
try:
    c2 = dict(ck); c2["version"] = 7; validate_demo_checkpoint_payload(c2); print("validate_demo_checkpoint_payload format7 ACCEPTED")
except Exception as e: print("validate_demo_checkpoint_payload format7 REFUSED", str(e)[:100])
# packs without effects / without appearance
d = cp("configs/static_epistemic_access", "sea"); u0 = comp(d, "L0_simple")
print("SEA effects_hash", u0.effects_hash, "items_appearance_hash", u0.get_level("L0_simple").items_appearance_hash)
ck0 = {"version": CHECKPOINT_FORMAT_VERSION}; attach_universe_metadata(ck0, u0); check("SEA self (None hashes)", ck0, u0)
# add effects to SEA
(d / "effects.yaml").write_text('version: "1.0"\neffect_definitions:\n  - id: e1\n    scope: agent\n    duration: 3\n    reapply_policy: renew\n    observable: true\n    on_spawn: []\n    on_tick: []\n    on_despawn: []\n    on_interrupt: []\nmax_active_effects:\n  global: 0\n  agent: 1\n  item: 0\n  affordance: 0\n')
try:
    u1 = comp(d, "L0_simple"); print("SEA+effects effects_hash", (u1.effects_hash or "None")[:12]); check("SEA ckpt vs SEA+effects", ck0, u1)
except Exception as e: print("SEA+effects compile:", type(e).__name__, str(e)[:200])
# cached artifact at 1.39
d = cp("configs/test/items_smoke", "cache"); u = comp(d, "L0_smoke", cache=True)
art = next((d / ".compiled").glob("*.msgpack")); raw = msgpack.unpackb(art.read_bytes(), raw=False, strict_map_key=False)
print("artifact keys has effects_hash:", "effects_hash" in raw, "version", raw.get("compiled_schema_version"))
raw139 = copy.deepcopy(raw); raw139["compiled_schema_version"] = "1.39"; raw139.pop("effects_hash", None)
for lvl in raw139["all_levels"].values(): lvl.pop("items_appearance_hash", None)
art.write_bytes(msgpack.packb(raw139, use_bin_type=True))
mt = art.stat().st_mtime
try:
    u2 = comp(d, "L0_smoke", cache=True)
    newraw = msgpack.unpackb(art.read_bytes(), raw=False, strict_map_key=False)
    print("1.39 cache -> compile(use_cache=True) returned; effects_hash", (u2.effects_hash or "None")[:12], "artifact rewritten to", newraw.get("compiled_schema_version"))
except Exception as e: print("1.39 cache -> compile REFUSED", type(e).__name__, str(e)[:200])
art.write_bytes(msgpack.packb(raw139, use_bin_type=True))
try:
    CompiledUniverse.from_dict(raw139); print("from_dict(1.39) ACCEPTED")
except Exception as e: print("from_dict(1.39) REFUSED", type(e).__name__, str(e)[:160])
raw140_missing = copy.deepcopy(raw); raw140_missing.pop("effects_hash")
try:
    CompiledUniverse.from_dict(raw140_missing); print("from_dict(1.40 without effects_hash) ACCEPTED")
except Exception as e: print("from_dict(1.40 without effects_hash) REFUSED", type(e).__name__, str(e)[:160])
