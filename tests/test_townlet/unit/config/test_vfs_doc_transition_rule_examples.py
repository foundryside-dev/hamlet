"""docs/architecture/VFS.md transition-rule examples must compile as written.

Every fenced yaml block in VFS.md whose top-level mapping carries a
``transition_rules`` key is treated as a complete transition-rules declaration
and must pass the DTO gate and the VTC transition-rule compiler. This keeps the
doc the shipped grammar instead of a decaying proposal.
"""

import re
from pathlib import Path

import yaml

from townlet.config.transition_rules_config import TransitionRulesConfig
from townlet.vfs import VTCWriteTarget, compile_vtc_transition_rules
from townlet.vfs.schema import VariableScope

VFS_DOC = Path("docs/architecture/VFS.md")


def _target(scope: VariableScope, var_type: str = "scalar", *, meter: bool = False) -> VTCWriteTarget:
    return VTCWriteTarget(scope, var_type, meter=meter, expression=None)


#: Declared scope and type of every state the examples write or read: the agent-scope
#: target, the action-index globals the conditions compare against, the per-agent
#: mask, and the two meters. There is no pair scope (VFS WP15), so no example relates
#: two agents.
DOC_TARGET_SCOPES = {
    "public_reputation": _target(VariableScope.AGENT),
    "chosen_action": _target(VariableScope.AGENT),
    "STEAL": _target(VariableScope.GLOBAL),
    "CALL_AMBULANCE": _target(VariableScope.GLOBAL),
    "HELP": _target(VariableScope.GLOBAL),
    "was_observed": _target(VariableScope.AGENT, "bool"),
    "health": _target(VariableScope.AGENT, meter=True),
    "mood": _target(VariableScope.AGENT, meter=True),
}


def _transition_rule_blocks() -> list[str]:
    text = VFS_DOC.read_text()
    blocks = re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    matching = []
    for block in blocks:
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "transition_rules" in data:
            matching.append(block)
    return matching


def test_doc_transition_rule_examples_compile_as_written() -> None:
    blocks = _transition_rule_blocks()
    assert len(blocks) >= 3, (
        f"Expected the VFS.md §14.3/§16.4 transition-rule examples as complete "
        f"transition-rules declarations; found {len(blocks)} yaml block(s) "
        f"with a top-level transition_rules key"
    )
    for block in blocks:
        config = TransitionRulesConfig(**yaml.safe_load(block))
        program = compile_vtc_transition_rules(config.rule_sources(), DOC_TARGET_SCOPES)
        assert len(program.rules) >= 1
        for rule in program.rules:
            # Derived reads are real declared state, never the authored illustrative list.
            assert set(rule.reads) <= set(DOC_TARGET_SCOPES)


def test_doc_carries_no_old_family_examples() -> None:
    """A ``social_residue:`` document in the doc would be the deleted grammar."""
    text = VFS_DOC.read_text()
    for block in re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        assert not (isinstance(data, dict) and "social_residue" in data), block
