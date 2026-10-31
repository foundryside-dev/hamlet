import sys; sys.path.insert(0, sys.argv[1])
from hashlib_common import *
from pathlib import Path
work = Path(sys.argv[2])
TR = '''version: "1.0"
transition_rules:
  - id: drift
    phase: apply_transition_rules
    condition: "public_state < 3.0"
    writes:
      - variable_id: public_state
        expression: "0.1"
        composition: additive_delta
        condition: null
        clamp: [0.0, 4.0]
        effect: null
'''
def prep(d):
    (d/"transition_rules.yaml").write_text(TR)
V = "variables.yaml"
def split_vars(d):
    t = (d/V).read_text()
    i = t.index("  - id: hidden_score")
    j = t.index("  - id: immutable_scale")
    frag = t[i:j]
    (d/V).write_text(t[:i] + t[j:])
    (d/"zz_more").mkdir(); (d/"zz_more"/"extra.yml").write_text("variables:\n  declarations:\n" + frag)
def move_vars_to_aa(d):
    t = (d/V).read_text()
    i = t.index("  - id: scaled_public")
    frag = t[i:]
    (d/V).write_text(t[:i])
    (d/"aa.yaml").write_text("variables:\n  declarations:\n" + frag)
def move_drive(d):
    (d/"levels/L0_simple/mechanics").mkdir()
    (d/"levels/L0_simple/drive.yaml").rename(d/"levels/L0_simple/mechanics/rewards.yml")
def multidoc(d):
    a = (d/"experiment.yaml").read_text(); b = (d/"actions.yaml").read_text()
    (d/"experiment.yaml").unlink(); (d/"actions.yaml").unlink()
    (d/"core.yaml").write_text(a + "\n---\n" + b)
edits = [
 ("comment in variables.yaml", "null", lambda d: sub(d/V, "variables:", "# hi\nvariables:  # trailing")),
 ("reorder keys inside a variable decl", "null", lambda d: sub(d/V, "  - id: hidden_score\n    scope: agent\n    type: scalar", "  - id: hidden_score\n    type: scalar\n    scope: agent")),
 ("initial_value 2.0 -> 2", "null", lambda d: sub(d/V, "initial_value: 2.0", "initial_value: 2")),
 ("normalization max 4.0 -> 4", "null", lambda d: sub(d/V, "max: 4.0", "max: 4")),
 ("flow-style readable_by", "null", lambda d: sub(d/V, "    readable_by:\n    - engine\n    writable_by:\n    - engine\n    exposed_to: []\n    initial_value: 2.0", "    readable_by: [engine]\n    writable_by: [engine]\n    exposed_to: []\n    initial_value: 2.0")),
 ("readable_by order swapped", "null", lambda d: sub(d/V, "    readable_by:\n    - engine\n    - agent\n    writable_by:\n    - engine\n    exposed_to:\n    - agent", "    readable_by:\n    - agent\n    - engine\n    writable_by:\n    - engine\n    exposed_to:\n    - agent")),
 ("expression respaced", "null", lambda d: sub(d/V, "public_state * immutable_scale", "public_state*immutable_scale")),
 ("expression redundant parens", "null", lambda d: sub(d/V, "public_state * immutable_scale", "(public_state) * (immutable_scale)")),
 ("expression commuted a*b -> b*a", "sem?", lambda d: sub(d/V, "public_state * immutable_scale", "immutable_scale * public_state")),
 ("split variable fragment to zz_more/extra.yml", "null", split_vars),
 ("move last variable to aa.yaml (reorders)", "null", move_vars_to_aa),
 ("rename drive.yaml -> mechanics/rewards.yml", "null", move_drive),
 ("experiment+actions into one multi-doc", "null", multidoc),
 ("description edit on a variable", "doc", lambda d: sub(d/V, "  - id: hidden_score\n", "  - id: hidden_score\n    description: changed text\n")),
 ("transition rule condition respaced", "null", lambda d: sub(d/"transition_rules.yaml", '"public_state < 3.0"', '"public_state<3.0"')),
 ("transition rule clamp [0.0,4.0]->[0,4]", "null", lambda d: sub(d/"transition_rules.yaml", "clamp: [0.0, 4.0]", "clamp: [0, 4]")),
 ("transition rule expression 0.1 -> 0.2", "sem", lambda d: sub(d/"transition_rules.yaml", 'expression: "0.1"', 'expression: "0.2"')),
 ("transition rule id rename", "sem?", lambda d: sub(d/"transition_rules.yaml", "id: drift", "id: drift2")),
 ("expression semantic * -> +", "sem", lambda d: sub(d/V, "public_state * immutable_scale", "public_state + immutable_scale")),
 ("initial_value 2.0 -> 3.0 (hidden)", "sem", lambda d: sub(d/V, "initial_value: 2.0", "initial_value: 3.0")),
 ("persistent global initial 0.5 -> 0.6", "sem", lambda d: sub(d/V, "initial_value: 0.5", "initial_value: 0.6")),
 ("boundary clamp -> wrap", "sem", lambda d: sub(d/"stratum.yaml", "boundary: clamp", "boundary: wrap")),
 ("affordance cost 0.05 -> 0.06", "sem", lambda d: sub(d/"levels/L0_simple/affordances.yaml", "money: 0.05", "money: 0.06")),
 ("affordance on_start value respaced", "null", lambda d: sub(d/"levels/L0_simple/affordances.yaml", "value: bar.energy + 0.8", "value: bar.energy+0.8")),
 ("affordance costs mapping reordered", "null", lambda d: sub(d/"levels/L0_simple/affordances.yaml", "        energy: 0.15\n        money: 0.03", "        money: 0.03\n        energy: 0.15")),
 ("affordance on_start 0.8 -> 0.9", "sem", lambda d: sub(d/"levels/L0_simple/affordances.yaml", "value: bar.energy + 0.8", "value: bar.energy + 0.9")),
]
run_matrix(Path("configs/static_epistemic_access"), "L0_simple", edits, work, prep)
