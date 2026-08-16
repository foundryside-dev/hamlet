"""Presentation is declared, not inferred: the `presentation.yaml` DTO.

Observer-only surface (PDR-0025): a pack MAY declare how a meter or affordance is shown. The
compiler never reads it and it enters no compiled hash. Everything present is explicit — an
entry that is declared declares all of its fields.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from townlet.config.presentation_config import (
    AffordancePresentation,
    MeterPresentation,
    PresentationConfig,
)


def _minimal(**overrides):
    data = {
        "version": "1.0",
        "meters": {
            "money": {
                "label": "Money",
                "format": {"kind": "currency", "symbol": "$", "decimals": 0},
                "color": "#fbbf24",
            }
        },
        "affordances": {"EAT": {"label": "Eat", "icon": "\U0001f37d️"}},
    }
    data.update(overrides)
    return data


def test_minimal_showcase_declaration_parses() -> None:
    cfg = PresentationConfig.model_validate(_minimal())
    assert isinstance(cfg.meters["money"], MeterPresentation)
    assert cfg.meters["money"].format.kind == "currency"
    assert cfg.meters["money"].format.symbol == "$"
    assert isinstance(cfg.affordances["EAT"], AffordancePresentation)


def test_empty_sections_are_legal() -> None:
    """A pack may declare only affordance icons, or only meter formats."""
    cfg = PresentationConfig.model_validate({"version": "1.0", "meters": {}, "affordances": {}})
    assert cfg.meters == {}
    assert cfg.affordances == {}


@pytest.mark.parametrize(
    "fmt",
    [
        {"kind": "plain", "decimals": 2},
        {"kind": "percent", "decimals": 0},
        {"kind": "currency", "symbol": "€", "decimals": 2},
    ],
)
def test_the_three_format_kinds(fmt: dict) -> None:
    cfg = PresentationConfig.model_validate(_minimal(meters={"m": {"label": "M", "format": fmt, "color": "#000000"}}))
    assert cfg.meters["m"].format.kind == fmt["kind"]


def test_currency_requires_symbol_and_plain_forbids_it() -> None:
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(
            _minimal(meters={"m": {"label": "M", "format": {"kind": "currency", "decimals": 0}, "color": "#000"}})
        )
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(
            _minimal(meters={"m": {"label": "M", "format": {"kind": "plain", "symbol": "$", "decimals": 0}, "color": "#000"}})
        )


def test_unknown_format_kind_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(
            _minimal(meters={"m": {"label": "M", "format": {"kind": "dollars", "decimals": 0}, "color": "#000"}})
        )


@pytest.mark.parametrize("missing", ["label", "format", "color"])
def test_a_declared_meter_entry_declares_every_field(missing: str) -> None:
    entry = {"label": "M", "format": {"kind": "plain", "decimals": 1}, "color": "#000000"}
    del entry[missing]
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(_minimal(meters={"m": entry}))


@pytest.mark.parametrize("missing", ["label", "icon"])
def test_a_declared_affordance_entry_declares_every_field(missing: str) -> None:
    entry = {"label": "Eat", "icon": "x"}
    del entry[missing]
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(_minimal(affordances={"EAT": entry}))


def test_stray_keys_fail_at_parse_time() -> None:
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(_minimal(theme="dark"))
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(
            _minimal(meters={"m": {"label": "M", "format": {"kind": "plain", "decimals": 1}, "color": "#000", "icon": "x"}})
        )


def test_version_is_required_and_pinned() -> None:
    data = _minimal()
    del data["version"]
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(data)
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(_minimal(version="2.0"))


def test_negative_decimals_rejected() -> None:
    with pytest.raises(ValidationError):
        PresentationConfig.model_validate(
            _minimal(meters={"m": {"label": "M", "format": {"kind": "plain", "decimals": -1}, "color": "#000"}})
        )
