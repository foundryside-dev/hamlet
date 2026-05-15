"""Tests for the `python -m townlet.universe` CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from scripts import validate_compiler_cli
from townlet.universe import __main__ as compiler_cli


def _copy_experiment(tmp_path: Path) -> Path:
    """Create a temporary copy of a v2.1 experiment pack for CLI tests."""
    source = Path("configs/test/model_config")
    dest = tmp_path / "model_config"
    shutil.copytree(source, dest)
    return dest


def test_cli_compile_creates_cache(tmp_path, capsys) -> None:
    config_dir = _copy_experiment(tmp_path)
    cache_path = config_dir / ".compiled" / "universe.msgpack"

    exit_code = compiler_cli.main(["compile", str(config_dir), "--primary-level", "L0_test"])

    assert exit_code == 0
    assert cache_path.exists()

    out = capsys.readouterr().out
    assert "Compilation succeeded" in out
    assert "Universe" in out


def test_cli_inspect_displays_metadata(tmp_path, capsys) -> None:
    config_dir = _copy_experiment(tmp_path)
    cache_path = config_dir / ".compiled" / "universe.msgpack"
    compiler_cli.main(["compile", str(config_dir), "--primary-level", "L0_test"])
    capsys.readouterr()  # Clear compile output

    exit_code = compiler_cli.main(["inspect", str(cache_path)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Artifact path" in out
    assert "Config Hash" in out


def test_cli_inspect_json_output(tmp_path, capsys) -> None:
    config_dir = _copy_experiment(tmp_path)
    cache_path = config_dir / ".compiled" / "universe.msgpack"
    compiler_cli.main(["compile", str(config_dir), "--primary-level", "L0_test"])
    capsys.readouterr()

    exit_code = compiler_cli.main(["inspect", str(cache_path), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metadata"]["universe_name"] == "Model Config (Test)"


def test_cli_validate_skips_cache(tmp_path, capsys) -> None:
    config_dir = _copy_experiment(tmp_path)

    exit_code = compiler_cli.main(["validate", str(config_dir), "--primary-level", "L0_test"])

    assert exit_code == 0
    # Validate currently emits cache for introspection; tolerate presence but should not grow
    out = capsys.readouterr().out
    assert "Validation succeeded" in out


def test_cli_validate_reports_vfs_domain_errors_without_traceback(tmp_path, capsys) -> None:
    config_dir = _copy_experiment(tmp_path)
    (config_dir / "vfs_profiles.yaml").write_text("""
version: '1.0'
global_profile:
  variables:
    - name: first
      type: int
      expression: second + 1
    - name: second
      type: int
      expression: first + 1
""".lstrip())

    exit_code = compiler_cli.main(["validate", str(config_dir), "--primary-level", "L0_test"])

    captured = capsys.readouterr()
    combined_output = captured.out + captured.err
    assert exit_code == 1
    assert "Compilation failed:" in captured.err
    assert "Circular dependency detected" in captured.err
    assert "Traceback" not in combined_output


def test_validate_compiler_script_passes_primary_level_to_cli(monkeypatch) -> None:
    captured: dict[str, list[str]] = {}

    def fake_run(cmd, cwd):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(validate_compiler_cli.subprocess, "run", fake_run)

    validate_compiler_cli.run_cli_validate(Path("configs/test/model_config"))

    assert captured["cwd"] == validate_compiler_cli.REPO_ROOT
    assert "--primary-level" in captured["cmd"]
    assert captured["cmd"][-1] == "L0_test"
