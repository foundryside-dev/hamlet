"""Doc examples: splice each authorable YAML block from the docs into a scratch copy of default_curriculum,
compile, and step. Blocks that are deliberately design-era/historical are compiled anyway to record the refusal."""

from harness import *  # noqa: F403

import re
import yaml

DOCS = {
    "VFS.md": WT / "docs/architecture/VFS.md",
    "variables.md": WT / "docs/config-schemas/variables.md",
    "declarations.md": WT / "docs/config-schemas/declarations.md",
    "transition_rules.md": WT / "docs/config-schemas/transition_rules.md",
    "expressions.md": WT / "docs/config-schemas/expressions.md",
}


def blocks(path):
    text = path.read_text()
    for m in re.finditer(r"```yaml\n(.*?)```", text, flags=re.DOTALL):
        line = text[: m.start()].count("\n") + 1
        yield line, m.group(1)


def doc_block(doc, line):
    for ln, body in blocks(DOCS[doc]):
        if ln + 1 == line or ln == line:
            return yaml.safe_load(body)
    raise KeyError((doc, line))


def run_block(label, *, decls=(), rules=None, actions=None, affordances=None, curriculum=None, level=LEVEL, steps=2, extra=None, check=None, act=None):
    print(f"\n--- {label}")
    kw = {}
    if decls:
        kw["variables"] = lambda v: v["declarations"].extend(list(decls))
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
    p = make_pack("doc_" + re.sub(r"\W+", "_", label)[:40], **kw)
    u, err = try_compile(p, level)
    if err:
        print("REFUSED:", short(err.split(" - ", 1)[-1].replace("\n", " "), 400))
        return None
    try:
        env = build_env(u, 2, level)
        for _ in range(steps):
            step(env, act or "WAIT")
        print("compiled + stepped OK", check(env) if check else "")
        return env
    except Exception as exc:  # noqa: BLE001
        print("STEP CRASH:", type(exc).__name__, short(str(exc), 300))
        return None


def main():
    # variables.md:8 day_phase block (the shipped one) -- compile as the pack's whole variables declaration
    v = doc_block("variables.md", 9)
    run_block("variables.md:8 day_phase as whole declaration", extra={"variables.yaml": v}, check=lambda e: reg(e, "day_phase").tolist())

    # variables.md:313 time_since_last_sleep (fragment; complete the required fields)
    frag = doc_block("variables.md", 314)[0]
    frag.update({"type": "scalar", "semantic_type": "custom", "readable_by": ["engine", "agent"], "writable_by": ["engine"], "exposed_to": []})
    run_block("variables.md:313 time_since_last_sleep (completed)", decls=[frag], steps=3, check=lambda e: reg(e, "time_since_last_sleep").tolist())

    # declarations.md:96 clock reference on L3
    c = doc_block("declarations.md", 97)
    run_block("declarations.md:96 period_of on L3", curriculum=lambda cur: cur.update(c["curriculum"]), level="L3_temporal_mechanics", check=lambda e: e.day_length)

    # transition_rules.md:46 example (declare the illustrative names)
    tr = doc_block("transition_rules.md", 47)
    run_block(
        "transition_rules.md:46 seen_stealing (names declared)",
        decls=[decl("public_reputation", initial_value=0.5), decl("was_observed", type="bool", initial_value=True), decl("chosen_action", initial_value=1.0), decl("STEAL", scope="global", initial_value=1.0, writable=())],
        rules=tr["transition_rules"],
        check=lambda e: reg(e, "public_reputation").tolist(),
    )

    # VFS.md:290 stamina, :343 need_pressure, :531 three decls, :1780 N_042
    for line in (291, 344, 532, 1781):
        d = doc_block("VFS.md", line)
        d = d if isinstance(d, list) else [d]
        run_block(f"VFS.md:{line-1} declarations", decls=d, check=lambda e, d=d: {x["id"]: reg(e, x["id"]).tolist() for x in d})

    # VFS.md:677 access block (fragments: complete them)
    frags = doc_block("VFS.md", 678)
    full = []
    for f in frags:
        x = decl(f["id"], scope="global", initial_value=0.5, readable=tuple(f["readable_by"]), writable=tuple(f["writable_by"]), exposed=tuple(f["exposed_to"]))
        if f["exposed_to"]:
            x["normalization"] = MINMAX01
        full.append(x)
    run_block("VFS.md:677 access fragments (completed, global)", decls=full)

    # VFS.md:927 / :960 normalization fragments -- historical shapes; record refusal
    for line in (928, 961):
        d = doc_block("VFS.md", line)
        d = d if isinstance(d, list) else [d]
        try:
            from townlet.config.variables_config import VariableDeclaration

            for x in d:
                VariableDeclaration(**x)
            print(f"\n--- VFS.md:{line-1} normalization fragment: PARSED (unexpected)")
        except Exception as exc:  # noqa: BLE001
            print(f"\n--- VFS.md:{line-1} normalization fragment: refused at DTO: {short(str(exc), 160)}")

    # VFS.md:1052 writes fragment (movement cost) -> as a custom action
    w = doc_block("VFS.md", 1053)["writes"]
    run_block("VFS.md:1052 writes fragment on a custom action", actions=lambda a: add_action(a, "MOVE_COST_PROBE", w), act=["MOVE_COST_PROBE", "WAIT"], check=lambda e: meter(e, "energy").tolist())

    # VFS.md:1274 REST_IN_BED (needs comfort)
    ca = doc_block("VFS.md", 1275)["custom_actions"]
    run_block("VFS.md:1274 REST_IN_BED (comfort declared)", decls=[decl("comfort", initial_value=0.5)], actions=lambda a: a["custom_actions"].extend(ca), act=["REST_IN_BED", "WAIT"], check=lambda e: (meter(e, "energy").tolist(), meter(e, "mood").tolist()))

    # VFS.md:1441 and :1456 rules (meter targets)
    for line in (1442, 1457):
        r = doc_block("VFS.md", line)
        run_block(f"VFS.md:{line-1} rule on meter", rules=r, check=lambda e: meter(e, "energy").tolist())

    # VFS.md:1473 job_is_open
    d = doc_block("VFS.md", 1474)
    run_block("VFS.md:1473 job_is_open time_in_window", decls=[d], steps=10, check=lambda e: (int(reg(e, "tick")[0]), reg(e, "job_is_open").tolist()))

    # VFS.md:1592 CALL_AMBULANCE (occupied_by affordance agent_ref, ambulance_cost global)
    ca = doc_block("VFS.md", 1593)["custom_actions"]
    run_block(
        "VFS.md:1592 CALL_AMBULANCE",
        decls=[decl("occupied_by", scope="affordance", type="agent_ref", initial_value=None), decl("ambulance_cost", scope="global", initial_value=10.0, writable=())],
        actions=lambda a: a["custom_actions"].extend(ca),
        act=["CALL_AMBULANCE", "WAIT"],
        check=lambda e: (reg(e, "occupied_by").tolist(), meter(e, "money").tolist(), meter(e, "health").tolist()),
    )

    # VFS.md:1691, :1712, :1730, :2002, :2525 transition_rules documents
    for line, decls_ in (
        (1692, []),
        (1713, [decl("public_reputation", initial_value=0.5), decl("was_observed", type="bool", initial_value=True), decl("chosen_action", initial_value=1.0), decl("STEAL", scope="global", initial_value=1.0, writable=())]),
        (1731, [decl("public_reputation", initial_value=0.5), decl("chosen_action", initial_value=1.0), decl("CALL_AMBULANCE", scope="global", initial_value=1.0, writable=())]),
        (2003, [decl("public_reputation", initial_value=0.5), decl("was_observed", type="bool", initial_value=True), decl("chosen_action", initial_value=1.0), decl("HELP", scope="global", initial_value=1.0, writable=())]),
        (2526, [decl("public_reputation", initial_value=0.5), decl("was_observed", type="bool", initial_value=True)]),
    ):
        r = doc_block("VFS.md", line)
        run_block(f"VFS.md:{line-1} transition_rules doc", decls=decls_, rules=r["transition_rules"], check=lambda e: {k: reg(e, k).tolist() for k in ("public_reputation",) if k in e.vfs_registry.variables})

    # VFS.md:1911 design-era variables block (pair/group) -> expect refusal
    d = doc_block("VFS.md", 1912)["variables"]
    run_block("VFS.md:1911 design-era pair/group block", decls=d)

    # VFS.md:2454 grid_position fragments (completed)
    run_block("VFS.md:2454 vec2i/vecNf grid_position (completed)", decls=[decl("grid_position", type="vec2i", initial_value=[0, 0]), decl("grid_position_f", type="vecNf", dims=2, initial_value=[0.0, 0.0])])

    # expressions.md:189 is_critical (missing readable_by/writable_by: expect DTO refusal, then completed)
    d = doc_block("expressions.md", 190)["variables"]["declarations"][0]
    run_block("expressions.md:189 is_critical as written", decls=[d])
    d2 = dict(d, readable_by=["engine", "agent"], writable_by=["engine"])
    run_block("expressions.md:189 is_critical completed", decls=[d2], check=lambda e: reg(e, "is_critical").tolist())
    # expressions.md:206 effects_catalog (old grammar) and :222 spawn_rules (old grammar): as extra top-level docs
    run_block("expressions.md:206 effects_catalog old grammar as a pack file", extra={"effects_catalog.yaml": doc_block("expressions.md", 207)})
    run_block("expressions.md:222 spawn_rules old grammar as a pack file", extra={"spawn_rules.yaml": doc_block("expressions.md", 223)})
    # expressions.md:647 three computed variables (is_night, is_crisis, motivation) -- missing readable_by/writable_by
    d = doc_block("expressions.md", 648)
    run_block("expressions.md:647 computed vars as written", decls=d)
    d2 = [dict(x, readable_by=["engine", "agent"], writable_by=["engine"]) for x in d]
    run_block("expressions.md:647 computed vars completed", decls=d2, steps=3, check=lambda e: {x["id"]: reg(e, x["id"]).tolist() for x in d2})
    # expressions.md:912 `name:` keyed entries (best practice 5)
    run_block("expressions.md:912 name-keyed entries", decls=[{"name": "energy_crisis", "type": "bool", "expression": "bar.energy < 0.2"}])


if __name__ == "__main__":
    main()
