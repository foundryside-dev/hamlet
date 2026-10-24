"""R8: which semantic edits to the variables declaration move no checkpoint-gated hash."""
from harness import *  # noqa
from townlet.training.checkpoint_utils import attach_universe_metadata


def stamp(pack):
    u = compile_pack(pack)
    ck = {}
    attach_universe_metadata(ck, u)
    return ck


def variant(label, mutate_vars):
    pack = make_pack(f"r8_{label}", variables=mutate_vars)
    return stamp(pack)


def set_field(var_id, **fields):
    def f(v):
        for d in v["declarations"]:
            if d["id"] == var_id:
                d.update(fields)
    return f


@probe("R8 checkpoint hash coverage of variable semantics")
def main():
    base = variant("base", lambda v: None)
    edits = {
        # scaled_public is a hidden agent expression on the witness: public_state * immutable_scale
        "hidden_expression_text": set_field("scaled_public", expression="public_state * 10.0"),
        "hidden_semantic_type": set_field("hidden_score", semantic_type="temporal"),
        "hidden_initial_value": set_field("hidden_score", initial_value=3.0),
        "exposed_norm_kind_minmax_to_log": set_field("public_state", normalization={"kind": "log_scaled", "min": 0.0, "max": 4.0, "clip": True}),
    }
    for label, fn in edits.items():
        ck = variant(label, fn)
        moved = sorted(k for k in base if base[k] != ck.get(k))
        print(f"{label:34s} moved: {moved if moved else 'NOTHING (checkpoint resumes silently)'}")

    # Behavioural consequence: an exposed, rewarded expression variable whose expression changes.
    MM = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}

    def rewarded(expr):
        def f(v):
            v["declarations"].append(decl("bonus", exposed=("agent",), normalization=MM, expression=expr))
        return f

    def drive(dest):
        edit_yaml(dest / "levels/L0_simple/drive.yaml",
                  lambda p: p["drive"]["extrinsic"].update({"variable_bonuses": [{"variable": "bonus", "weight": 1.0}]}))

    outs = {}
    for label, expr in (("bonus_a", "public_state * 1.0"), ("bonus_b", "public_state * 3.0")):
        pack = make_pack(f"r8_{label}", variables=rewarded(expr))
        drive(pack)
        u = compile_pack(pack)
        ck = {}
        attach_universe_metadata(ck, u)
        env = build_env(u, num_agents=1)
        step(env, "ADVANCE")
        _, r, _, _ = step(env, "ADVANCE")
        outs[label] = (ck, r.tolist(), reg(env, "bonus").tolist())
    moved = sorted(k for k in outs["bonus_a"][0] if outs["bonus_a"][0][k] != outs["bonus_b"][0].get(k))
    print(f"exposed+rewarded expression x1 -> x3: hashes moved: {moved if moved else 'NOTHING'}; "
          f"reward after 2x ADVANCE: {outs['bonus_a'][1]} vs {outs['bonus_b'][1]}; bonus {outs['bonus_a'][2]} vs {outs['bonus_b'][2]}")


main()
