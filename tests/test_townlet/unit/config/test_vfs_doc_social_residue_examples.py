"""docs/architecture/vfs.md social-residue examples must compile as written.

Every fenced yaml block in vfs.md whose top-level mapping carries a
``social_residue`` key is treated as a complete transition_rules.yaml document
and must pass the DTO gate and the VTC social-residue compiler. This keeps the
doc the shipped grammar instead of a decaying proposal.
"""

import re
from pathlib import Path

import yaml

from townlet.config.transition_rules_config import TransitionRulesConfig
from townlet.vfs import compile_vtc_social_residue_rules

VFS_DOC = Path("docs/architecture/vfs.md")


def _social_residue_blocks() -> list[str]:
    text = VFS_DOC.read_text()
    blocks = re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    matching = []
    for block in blocks:
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "social_residue" in data:
            matching.append(block)
    return matching


def test_doc_social_residue_examples_compile_as_written() -> None:
    blocks = _social_residue_blocks()
    assert len(blocks) >= 3, (
        f"Expected the vfs.md §14.3/§16.4 social-residue examples as complete "
        f"transition_rules.yaml documents; found {len(blocks)} yaml block(s) "
        f"with a top-level social_residue key"
    )
    for block in blocks:
        config = TransitionRulesConfig(**yaml.safe_load(block))
        program = compile_vtc_social_residue_rules(config.social_residue_sources())
        assert len(program.rules) >= 1
