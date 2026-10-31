"""R12 doc sweep at 39825727.

(a) The original authoring-lens d_docs.py checks, with each block re-located by CONTENT
    (the doc line numbers moved in 39825727).
(b) A generic sweep of every fenced yaml block in the five docs that is a variables
    declaration fragment or a transition_rules document: splice into a scratch copy of
    configs/default_curriculum, compile, step 2 ticks, classify.

Run: PYTHONPATH=verify_R12/wt/src CUDA_VISIBLE_DEVICES= verify_R12/wt/.venv/bin/python docs_sweep.py [a|b]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "orig" / "authoring" / "probes"))
from harness import *  # noqa: E402,F403
from harness import WT  # noqa: E402

import townlet  # noqa: E402
import yaml  # noqa: E402

assert str(WT.resolve()) in str(Path(townlet.__file__).resolve()), townlet.__file__

DOCS = {
    "VFS.md": WT / "docs/architecture/VFS.md",
    "variables.md": WT / "docs/config-schemas/variables.md",
    "declarations.md": WT / "docs/config-schemas/declarations.md",
    "transition_rules.md": WT / "docs/config-schemas/transition_rules.md",
    "expressions.md": WT / "docs/config-schemas/expressions.md",
}


def blocks(doc):
    text = DOCS[doc].read_text()
    for m in re.finditer(r"```yaml\n(.*?)```", text, flags=re.DOTALL):
        line = text[: m.start()].count("\n") + 1
        ctx = "\n".join(text[: m.start()].splitlines()[-14:])
        yield line, m.group(1), ctx


def find(doc, needle):
    """(line, parsed) of the first yaml block of `doc` whose text contains `needle`."""
    for line, body, _ in blocks(doc):
        if needle in body:
            return line, yaml.safe_load(body)
    raise KeyError((doc, needle))


RESULTS: list[tuple[str, str]] = []


def run_block(label, *, decls=(), rules=None, actions=None, affordances=None, curriculum=None, level=LEVEL, steps=2, extra=None, check=None, act=None, replace_ids=True):
    kw = {}
    if decls:
        ids = {d.get("id") for d in decls if isinstance(d, dict)}

        def mut(v, decls=decls, ids=ids):
            if replace_ids:
                v["declarations"] = [d for d in v["declarations"] if d.get("id") not in ids]
            v["declarations"].extend(list(decls))

        kw["variables"] = mut
    if rules is not None:
        kw["rules"] = rules
    if actions is not None:
        kw["actions"] = actions
    if affordances is not None:
        kw["affordances"] = affordances
    if curriculum is not None:
        kw["curriculum"] = curriculum
    if extra:
        kw["extra_files"] = extra
    kw["level"] = level
    p = make_pack("sw_" + re.sub(r"\W+", "_", label)[:48], **kw)
    u, err = try_compile(p, level)
    if err:
        msg = err.split(" - ", 1)[-1].replace("\n", " ")
        code = re.search(r"\[([A-Z0-9_\-]+)\]", err)
        out = f"REFUSED [{code.group(1) if code else '?'}] {short(msg, 300)}"
        RESULTS.append((label, out))
        print(f"--- {label}\n    {out}", flush=True)
        return None
    try:
        env = build_env(u, 2, level)
        for _ in range(steps):
            step(env, act or "WAIT")
        out = "OK " + (str(check(env)) if check else "")
        RESULTS.append((label, out))
        print(f"--- {label}\n    {short(out, 400)}", flush=True)
        return env
    except Exception as exc:  # noqa: BLE001
        out = f"CRASH {type(exc).__name__}: {short(str(exc), 300)}"
        RESULTS.append((label, out))
        print(f"--- {label}\n    {out}", flush=True)
        return None


ILLUSTRATIVE = [
    decl("public_reputation", initial_value=0.5),
    decl("was_observed", type="bool", initial_value=True),
    decl("chosen_action", initial_value=1.0),
    *(decl(n, scope="global", initial_value=1.0, writable=()) for n in ("STEAL", "CALL_AMBULANCE", "HELP")),
]


def part_a():
    print("\n######## (a) original d_docs checks, located by content ########")
    ln, v = find("variables.md", "item_profiles: [default_item]")
    run_block(f"variables.md:{ln} day_phase as whole declaration", extra={"variables.yaml": v}, check=lambda e: reg(e, "day_phase").tolist())

    ln, frags = find("variables.md", "time_since_last_sleep")
    frag = dict(frags[0])
    missing = [k for k in ("type", "semantic_type", "readable_by", "writable_by", "exposed_to") if k not in frag]
    print(f"    [variables.md:{ln} time_since_last_sleep fields missing as written: {missing}]")
    run_block(f"variables.md:{ln} time_since_last_sleep as written", decls=[frags[0]], steps=3, check=lambda e: reg(e, "time_since_last_sleep").tolist())
    frag.update({k: v for k, v in {"type": "scalar", "semantic_type": "custom", "readable_by": ["engine", "agent"], "writable_by": ["engine"], "exposed_to": []}.items() if k not in frag})
    run_block(f"variables.md:{ln} time_since_last_sleep (completed)", decls=[frag], steps=3, check=lambda e: reg(e, "time_since_last_sleep").tolist())

    ln, c = find("declarations.md", "period_of")
    run_block(f"declarations.md:{ln} period_of on L3", curriculum=lambda cur: cur.update(c["curriculum"]), level="L3_temporal_mechanics", check=lambda e: e.day_length)

    ln, tr = find("transition_rules.md", "seen_stealing")
    run_block(f"transition_rules.md:{ln} seen_stealing (illustrative names declared)", decls=ILLUSTRATIVE, rules=tr["transition_rules"], check=lambda e: reg(e, "public_reputation").tolist())

    for needle in ('id: "stamina"', 'id: "need_pressure"', 'id: "true_health"', 'id: "N_042"'):
        ln, d = find("VFS.md", needle)
        d = d if isinstance(d, list) else [d]
        run_block(f"VFS.md:{ln} declarations {needle}", decls=d, check=lambda e, d=d: {x["id"]: reg(e, x["id"]).tolist() for x in d})

    ln, frags = find("VFS.md", "# Engine-mutable, agent-observable")
    full = []
    for f in frags:
        x = decl(f["id"], scope="global", initial_value=0.5, readable=tuple(f["readable_by"]), writable=tuple(f["writable_by"]), exposed=tuple(f["exposed_to"]))
        if f["exposed_to"]:
            x["normalization"] = MINMAX01
        full.append(x)
    run_block(f"VFS.md:{ln} access fragments (completed, global)", decls=full)

    # §9.1 / §9.2 normalization examples: previously refused at the DTO; now as complete declarations
    for needle in ('id: "obs_energy"', 'id: "hour_of_day"'):
        ln, d = find("VFS.md", needle)
        d = d if isinstance(d, list) else [d]
        run_block(f"VFS.md:{ln} normalization block {needle}", decls=d, steps=3, check=lambda e, d=d: {x["id"]: reg(e, x["id"]).tolist() for x in d})

    ln, w = find("VFS.md", 'variable_id: "bar.energy"\n    expression: "-0.005"')
    run_block(f"VFS.md:{ln} writes fragment on a custom action", actions=lambda a: add_action(a, "MOVE_COST_PROBE", w["writes"]), act=["MOVE_COST_PROBE", "WAIT"], check=lambda e: meter(e, "energy").tolist())

    ln, ca = find("VFS.md", "REST_IN_BED")
    run_block(f"VFS.md:{ln} REST_IN_BED (comfort declared)", decls=[decl("comfort", initial_value=0.5)], actions=lambda a: a["custom_actions"].extend(ca["custom_actions"]), act=["REST_IN_BED", "WAIT"], check=lambda e: (meter(e, "energy").tolist(), meter(e, "mood").tolist()))

    # A1: rules on meters (were KeyError at step 1). Compare against the same pack with no rule.
    base_env = run_block("baseline: no rules (meters after 2 WAIT)", check=lambda e: {m: meter(e, m).tolist() for m in ("energy", "satiation", "mood", "health")})
    for needle, label_m in (("energy_base_depletion", "energy"), ("low_satiation_hits_energy", "energy")):
        ln, r = find("VFS.md", needle)
        run_block(f"VFS.md:{ln} rule on meter {needle}", rules=r, check=lambda e: {m: meter(e, m).tolist() for m in ("energy", "satiation")})
    # low_satiation_hits_energy needs satiation < 0.2 to fire: drive it low first
    ln, r = find("VFS.md", "low_satiation_hits_energy")
    p = make_pack("sw_low_sat_driven", rules=r)
    u, err = try_compile(p)
    if err:
        print("REFUSED", err[:300])
    else:
        env = build_env(u, 2)
        env.meters[0, env.meter_name_to_index["satiation"]] = 0.1
        e0 = meter(env, "energy").clone()
        step(env, "WAIT")
        out = f"OK energy delta world0(sat 0.1)={float(meter(env,'energy')[0]-e0[0]):.4f} world1(sat 1.0)={float(meter(env,'energy')[1]-e0[1]):.4f}"
        RESULTS.append((f"VFS.md:{ln} low_satiation_hits_energy driven (sat=0.1 in world 0)", out))
        print(f"--- VFS.md:{ln} low_satiation_hits_energy driven\n    {out}")

    ln, d = find("VFS.md", 'id: "job_is_open"')
    run_block(f"VFS.md:{ln} job_is_open time_in_window", decls=d if isinstance(d, list) else [d], steps=10, check=lambda e: (int(reg(e, "tick")[0]), reg(e, "job_is_open").tolist()))

    ln, ca = find("VFS.md", "CALL_AMBULANCE")
    run_block(
        f"VFS.md:{ln} CALL_AMBULANCE",
        decls=[decl("occupied_by", scope="affordance", type="agent_ref", initial_value=None), decl("ambulance_cost", scope="global", initial_value=10.0, writable=())],
        actions=lambda a: a["custom_actions"].extend(ca["custom_actions"]),
        act=["CALL_AMBULANCE", "WAIT"],
        check=lambda e: (reg(e, "occupied_by")[:, 13].tolist(), meter(e, "money").tolist(), meter(e, "health").tolist()),
    )

    for needle in ("low_health_hits_mood", "seen_stealing_damages_reputation", "ambulance_abuse_social_penalty", "observed_help_raises_reputation", "public_help_increases_reputation"):
        ln, r = find("VFS.md", needle)
        decls_ = [] if needle == "low_health_hits_mood" else ILLUSTRATIVE
        run_block(
            f"VFS.md:{ln} transition_rules {needle}",
            decls=decls_,
            rules=r["transition_rules"],
            check=lambda e: {**{k: reg(e, k).tolist() for k in ("public_reputation",) if k in e.vfs_registry.variables}, "mood": meter(e, "mood").tolist(), "health": meter(e, "health").tolist()},
        )
    # low_health_hits_mood gated on health: drive world 0 health low
    ln, r = find("VFS.md", "low_health_hits_mood")
    print("    [low_health_hits_mood rule]:", r["transition_rules"][0].get("condition"), [w["variable_id"] for w in r["transition_rules"][0]["writes"]])

    p = make_pack("sw_low_health_driven", rules=r["transition_rules"])
    u, err = try_compile(p)
    if err:
        print("REFUSED", err[:300])
    else:
        env = build_env(u, 2)
        env.meters[0, env.meter_name_to_index["health"]] = 0.1
        m0 = meter(env, "mood").clone()
        step(env, "WAIT")
        out = f"OK mood delta world0(health 0.1)={float(meter(env,'mood')[0]-m0[0]):.4f} world1(health 1.0)={float(meter(env,'mood')[1]-m0[1]):.4f}"
        RESULTS.append((f"VFS.md:{ln} low_health_hits_mood driven (health=0.1 in world 0)", out))
        print(f"--- low_health driven\n    {out}")

    ln, d = find("VFS.md", 'id: "trust"')
    run_block(f"VFS.md:{ln} design-era pair/group block (marked design intent)", decls=d["variables"])

    ln, d = find("VFS.md", "# Good: integer coordinates")
    run_block(f"VFS.md:{ln} grid_position fragments as written", decls=d)
    run_block(f"VFS.md:{ln} vec2i/vecNf grid_position (completed)", decls=[decl("grid_position", type="vec2i", initial_value=[0, 0]), decl("grid_position_f", type="vecNf", dims=2, initial_value=[0.0, 0.0])])

    ln, d = find("expressions.md", "is_critical")
    run_block(f"expressions.md:{ln} is_critical as written (whole variables declaration)", extra={"variables.yaml": d}, check=lambda e: reg(e, "is_critical").tolist())
    run_block(f"expressions.md:{ln} is_critical decls spliced", decls=d["variables"]["declarations"], check=lambda e: reg(e, "is_critical").tolist())

    ln, eff = find("expressions.md", "max_active_effects")
    print(f"    [expressions.md:{ln} effects block top keys: {list(eff)}]")
    run_block(f"expressions.md:{ln} effects block as effects.yaml", extra={"effects.yaml": eff})
    ln, sp = find("expressions.md", 'item_type: "apple"')
    print(f"    [expressions.md:{ln} spawn block top keys: {list(sp)}]")
    ism = WT / "configs/test/items_smoke"
    lv = "L0_smoke"
    import shutil as _sh
    for f in (ism / "levels" / lv).iterdir():
        print("    [items_smoke level file]", f.name)
    p = make_pack("sw_items_app", base=ism, level=lv, variables=lambda v: v["declarations"].append(decl("is_winter", scope="global", type="bool", initial_value=False)))
    # replace the level's items_appearance declaration with the doc block
    for f in (p / "levels" / lv).iterdir():
        if "items_appearance" in f.read_text() or (f.name.startswith("items") and "item_type" in f.read_text()):
            print("    [replacing]", f.name); f.unlink()
    dump_yaml(p / "levels" / lv / "items.yaml", sp)
    u, err = try_compile(p, lv)
    if err:
        out = "REFUSED " + short(err.split(" - ", 1)[-1], 300)
    else:
        env = build_env(u, 2, lv)
        for _ in range(2):
            env.step(torch.zeros(2, dtype=torch.long))
        out = "OK items_appearance rules=" + str([(r.item_type, r.spawn_count) for r in u.get_level(lv).items_appearance.items])
    RESULTS.append((f"expressions.md:{ln} items_appearance block on items_smoke (is_winter declared)", out))
    print(f"--- expressions.md:{ln} items_appearance on items_smoke\n    {out}")

    ln, d = find("expressions.md", "# Global derived state - night detection")
    run_block(f"expressions.md:{ln} computed vars as written", decls=d, steps=3, check=lambda e, d=d: {x["id"]: reg(e, x["id"]).tolist() for x in d})

    # old :912 name-keyed entries: re-located by content
    for needle in ("energy_crisis", "# Bad\n- id: x"):
        try:
            ln, d = find("expressions.md", needle)
            print(f"    [expressions.md:{ln} block containing {needle!r}: {str(d)[:200]}]")
        except KeyError:
            print(f"    [no expressions.md block contains {needle!r} any more]")


# ---------------------------------------------------------------- (b)
MARKERS = re.compile(r"design intent|design-era|not authorable|historical|does not compile|will not compile|refused|# Bad|illustrat", re.I)


def classify_block(body):
    try:
        data = yaml.safe_load(body)
    except yaml.YAMLError as exc:
        return "yaml_error", str(exc)
    if isinstance(data, dict) and "transition_rules" in data:
        return "rules", data
    if isinstance(data, list) and data and all(isinstance(x, dict) and "writes" in x for x in data):
        return "rules", {"version": "1.0", "transition_rules": data}
    if isinstance(data, dict) and "variables" in data:
        inner = data["variables"]
        if isinstance(inner, dict) and "declarations" in inner:
            return "whole_vars", data
        if isinstance(inner, list):
            return "decl_list", inner
    if isinstance(data, list) and data and all(isinstance(x, dict) and "id" in x for x in data):
        return "decl_list", data
    if isinstance(data, dict) and "id" in data and ("scope" in data or "type" in data):
        return "decl_list", [data]
    return None, None


def part_b():
    print("\n######## (b) generic sweep ########")
    for doc in DOCS:
        for line, body, ctx in blocks(doc):
            kind, data = classify_block(body)
            if kind is None:
                continue
            marks = sorted({m.group(0).lower() for m in MARKERS.finditer(ctx + "\n" + body[:200])})
            tag = f"{doc}:{line} [{kind}]" + (f" markers={marks}" if marks else "")
            if kind == "yaml_error":
                RESULTS.append((tag, f"YAML ERROR {data[:200]}"))
                print(f"--- {tag}\n    YAML ERROR")
                continue
            if kind == "rules":
                illustrative = "illustrat" in (ctx + body).lower()
                run_block(tag + " (as written)", rules=data["transition_rules"])
                run_block(tag + " (illustrative names declared)", decls=ILLUSTRATIVE, rules=data["transition_rules"])
                _ = illustrative
            elif kind == "whole_vars":
                run_block(tag + " (as whole variables.yaml)", extra={"variables.yaml": data})
                run_block(tag + " (declarations spliced)", decls=data["variables"]["declarations"])
            elif kind == "decl_list":
                run_block(tag + " (spliced)", decls=data)


if __name__ == "__main__":
    which = sys.argv[1:] or ["a", "b"]
    if "a" in which:
        part_a()
    if "b" in which:
        part_b()
    print("\n######## SUMMARY ########")
    for label, out in RESULTS:
        print(f"{label}\n    {short(out, 260)}")
