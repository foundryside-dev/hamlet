"""Tests for the universe-compiler error-code registry."""

from __future__ import annotations

import re
from pathlib import Path

import townlet.universe as universe_pkg
from townlet.universe.error_codes import ErrorCode


def test_error_code_values_are_unique() -> None:
    values = [code.value for code in ErrorCode]
    assert len(values) == len(set(values))


def test_error_codes_format_as_their_value() -> None:
    assert f"{ErrorCode.DAC_REF_UNDEFINED_MODIFIER_BAR}" == "DAC-REF-001"
    assert f"{ErrorCode.YAML_SYNTAX_ERROR}" == "YAML_SYNTAX_ERROR"


def test_no_stray_code_literals_in_the_compiler_package() -> None:
    """Every diagnostic code must come from the registry, not a string literal."""
    package_root = Path(universe_pkg.__file__).parent
    offenders: list[str] = []
    for path in sorted(package_root.rglob("*.py")):
        if path.name == "error_codes.py":
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if re.search(r'code="', line):
                offenders.append(f"{path.relative_to(package_root)}:{lineno}")
    assert not offenders, f"string-literal diagnostic codes outside the registry: {offenders}"


def test_no_diagnostic_cites_the_ghost_drive_filename() -> None:
    """drive_as_code.yaml exists in no pack; diagnostics must cite levels/<level>/drive.yaml."""
    package_root = Path(universe_pkg.__file__).parent
    offenders = [
        str(path.relative_to(package_root)) for path in sorted(package_root.rglob("*.py")) if "drive_as_code.yaml" in path.read_text()
    ]
    assert not offenders, f"diagnostics still cite the nonexistent drive_as_code.yaml: {offenders}"
