"""Presentation configuration — how an observer SHOWS a universe, declared by the pack.

`presentation.yaml` is an **observer-only** surface (PDR-0025): the live-inference server reads
it and forwards it to the frontend; the universe compiler never opens it and nothing here enters
a compiled hash. Its absence is the honest default — every meter renders from its declared
bounds, uniformly, and no site may infer presentation from a variable's name.

A pack that opts in (a "locked" showcase, PDR-0025) declares presentation per meter and per
affordance. Everything present is explicit: a declared entry declares all of its fields, and a
`currency` format is the only one that carries a symbol.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "PlainFormat",
    "PercentFormat",
    "CurrencyFormat",
    "MeterFormat",
    "MeterPresentation",
    "AffordancePresentation",
    "PresentationConfig",
]


class PlainFormat(BaseModel):
    """Render the raw value with a fixed number of decimals."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["plain"] = Field(description="Format kind")
    decimals: int = Field(ge=0, description="Decimal places shown")


class PercentFormat(BaseModel):
    """Render the value as a percentage of the meter's declared range."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["percent"] = Field(description="Format kind")
    decimals: int = Field(ge=0, description="Decimal places shown")


class CurrencyFormat(BaseModel):
    """Render the raw value prefixed with a currency symbol (showcase packs only)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["currency"] = Field(description="Format kind")
    symbol: str = Field(min_length=1, description="Currency symbol shown before the value")
    decimals: int = Field(ge=0, description="Decimal places shown")


MeterFormat = Annotated[PlainFormat | PercentFormat | CurrencyFormat, Field(discriminator="kind")]


class MeterPresentation(BaseModel):
    """How one meter is shown. Keyed by meter name in `PresentationConfig.meters`."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, description="Display label")
    format: MeterFormat = Field(description="Value format")
    color: str = Field(min_length=1, description="CSS colour for the meter's bar")


class AffordancePresentation(BaseModel):
    """How one affordance is shown. Keyed by affordance name in `PresentationConfig.affordances`."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, description="Display label")
    icon: str = Field(min_length=1, description="Glyph rendered for the affordance")


class PresentationConfig(BaseModel):
    """`presentation.yaml` — pack-level, observer-only, opt-in."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(description="Config version")
    meters: dict[str, MeterPresentation] = Field(description="Per-meter presentation, keyed by meter name")
    affordances: dict[str, AffordancePresentation] = Field(description="Per-affordance presentation, keyed by affordance name")
