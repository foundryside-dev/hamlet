"""Fields deleted as dead config refuse at parse, naming the authored file and line.

Compiler WP3 (docs/remediation/compiler.md; findings_compiler F4, F5). Each of these
was once required by the no-defaults DTOs while no code read it, so authors wrote dead
config that was never validated (a cue on a meter that does not exist, a bogus
affordance category, an unread checkpoint retention count). They are deleted; an old
pack that still declares one fails as an extra field at the line that declares it.
``RecordingConfig`` used to be ``extra="allow"``, so a typo'd recording key entered
``training_hash``; it now refuses like every neighbour.

Built from ``configs/test/model_config_4meter`` (the ``dead_fields`` scratch pack of the
2026-10-24 review, rebuilt against the current branch).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from townlet.universe.errors import CompilationError
from townlet.universe.raw_configs_v21 import RawConfigsV21

SOURCE_PACK = Path("configs/test/model_config_4meter")
LEVEL = "L0_4meter"
TRAINING = f"levels/{LEVEL}/training.yaml"


@dataclass(frozen=True)
class DeadField:
    """Insert ``lines`` directly after the first line equal to ``anchor`` in ``file``."""

    file: str
    anchor: str
    lines: tuple[str, ...]
    field_path: str


DEAD_FIELDS = {
    "experiment.metadata.author": DeadField("experiment.yaml", "  metadata:", ('    author: "someone"',), "metadata.author"),
    "experiment.metadata.created": DeadField("experiment.yaml", "  metadata:", ('    created: "2025-11-15"',), "metadata.created"),
    "experiment.metadata.tags": DeadField("experiment.yaml", "  metadata:", ("    tags: [a, b]",), "metadata.tags"),
    "experiment.curriculum_levels": DeadField(
        "experiment.yaml", "experiment:", ("  curriculum_levels:", "    - BOGUS_LEVEL"), "curriculum_levels"
    ),
    "environment.affordances.category": DeadField(
        "environment.yaml", "    - name: EAT", ("      category: NOT_A_CATEGORY",), "affordances[0].category"
    ),
    "environment.affordances.description": DeadField(
        "environment.yaml", "    - name: EAT", ('      description: "Eat food"',), "affordances[0].description"
    ),
    "environment.cues": DeadField(
        "environment.yaml",
        "environment:",
        ("  cues:", "    - name: x", "      trigger: {bar: NO_SUCH_METER, threshold: 0.1, direction: below}"),
        "cues",
    ),
    "training.training_loop.evaluation": DeadField(
        TRAINING, "  training_loop:", ("    evaluation:", "      interval: 999999", "      num_episodes: 1"), "training_loop.evaluation"
    ),
    "training.training_loop.checkpointing.keep_last": DeadField(
        TRAINING, "    checkpointing:", ("      keep_last: 999999",), "training_loop.checkpointing.keep_last"
    ),
    "recording.typo_key": DeadField(TRAINING, "run_metadata:", (), "recording.typo_key_that_should_refuse"),
}


def _inject(pack: Path, dead: DeadField) -> range:
    """Insert the dead field; return the 1-based lines the inserted text occupies."""
    path = pack / dead.file
    lines = path.read_text().split("\n")
    anchor_index = lines.index(dead.anchor)
    lines[anchor_index + 1 : anchor_index + 1] = list(dead.lines)
    path.write_text("\n".join(lines))
    return range(anchor_index + 2, anchor_index + 2 + len(dead.lines))


def _append_recording_typo(pack: Path) -> range:
    path = pack / TRAINING
    lines = path.read_text().rstrip("\n").split("\n")
    lines += ["recording:", "  enabled: false", "  typo_key_that_should_refuse: 1"]
    path.write_text("\n".join(lines) + "\n")
    return range(len(lines), len(lines) + 1)


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    target = tmp_path / "pack"
    shutil.copytree(SOURCE_PACK, target, ignore=shutil.ignore_patterns(".compiled"))
    return target


def test_unmodified_source_pack_parses(pack: Path) -> None:
    raw = RawConfigsV21.from_experiment_dir(pack)
    assert list(raw.levels) == [LEVEL]


@pytest.mark.parametrize("name", sorted(DEAD_FIELDS))
def test_deleted_field_refuses_at_parse_with_file_and_line(pack: Path, name: str) -> None:
    dead = DEAD_FIELDS[name]
    inserted = _append_recording_typo(pack) if name == "recording.typo_key" else _inject(pack, dead)

    with pytest.raises(CompilationError) as raised:
        RawConfigsV21.from_experiment_dir(pack)

    matching = [issue for issue in raised.value.issues if f"({dead.field_path})" in issue.message]
    assert matching, [issue.message for issue in raised.value.issues]
    assert len(raised.value.issues) == 1, [str(issue) for issue in raised.value.issues]
    issue = matching[0]
    assert "Extra inputs are not permitted" in issue.message
    # The location names the authored file and a line inside the dead declaration (a
    # block mapping value is located at its first child line, a scalar at its own line).
    assert issue.location is not None
    file_part, _, line_part = issue.location.rpartition(":")
    assert file_part == str(pack / dead.file)
    assert int(line_part) in inserted, (issue.location, list(inserted))
