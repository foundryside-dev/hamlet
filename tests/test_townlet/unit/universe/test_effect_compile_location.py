"""An effect that fails to compile is located at its own declaration, under an effects code.

Stage 6 used to wrap every effect compile error as ``[VFS-PROFILE-COMPILE]
<pack>/variables.yaml:1`` — the wrong file and the wrong code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_townlet._fixtures.command_namespace import command_symbols
from tests.test_townlet.unit.effects.test_bare_vfs_write import BARE_INCREMENT, LEVEL, _effect, _pack
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

OLD_SPELLING = [{"modify": "vfs.public_state", "value": "1.0"}]


def test_effect_compile_error_names_the_refused_command(tmp_path: Path) -> None:
    pack = _pack(tmp_path, effects=[_effect("agent", BARE_INCREMENT), _effect("global", OLD_SPELLING)])
    effects_text = (pack / "effects.yaml").read_text().splitlines()
    failing_line = next(i for i, line in enumerate(effects_text, start=1) if "modify: vfs.public_state" in line)

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


def test_catalog_compile_error_carries_the_effect_id() -> None:
    """The catalog names the failing effect on the exception; stage 6 reads it instead of
    recompiling each definition alone to find it."""
    from tests.test_townlet.unit.effects.test_bare_vfs_write import SCHEMA
    from townlet.config.effects_config import EffectsConfig
    from townlet.effects.catalog import EffectCatalog, EffectCompileError
    from townlet.world.expression.type_checker import TypeCheckError

    config = EffectsConfig(
        version="1.0",
        max_active_effects={"global": 1, "agent": 1, "item": 1, "affordance": 1},
        effect_definitions=[_effect("agent", BARE_INCREMENT), _effect("global", OLD_SPELLING)],
    )
    schema = {**SCHEMA, "public_state": "float"}

    with pytest.raises(EffectCompileError) as refusal:
        EffectCatalog.from_config(config, command_symbols(schema))

    assert refusal.value.effect_id == "global_probe"
    assert "Effect 'global_probe' failed to compile" in str(refusal.value)
    assert isinstance(refusal.value.__cause__, TypeCheckError)
