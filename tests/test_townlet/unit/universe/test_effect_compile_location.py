"""An effect that fails to compile is located at its own declaration, under an effects code.

Stage 6 used to wrap every effect compile error as ``[VFS-PROFILE-COMPILE]
<pack>/variables.yaml:1`` — the wrong file and the wrong code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_townlet.unit.effects.test_bare_vfs_write import BARE_INCREMENT, LEVEL, _effect, _pack
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def test_effect_compile_error_names_the_effect_declaration(tmp_path: Path) -> None:
    pack = _pack(tmp_path, effects=[_effect("agent", BARE_INCREMENT), _effect("global", BARE_INCREMENT)])
    effects_text = (pack / "effects.yaml").read_text().splitlines()
    failing_line = next(i for i, line in enumerate(effects_text, start=1) if "id: global_probe" in line)

    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)

    (message,) = refusal.value.issues
    assert message.code == "EFFECT-COMPILE"
    assert "Effect 'global_probe' failed to compile" in message.message
    assert message.location is not None
    path, line = message.location.rsplit(":", 1)
    assert Path(path).name == "effects.yaml"
    assert int(line) == failing_line
    assert "variables.yaml" not in str(refusal.value)
