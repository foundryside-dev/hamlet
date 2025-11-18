"""Spatial substrate abstractions for UNIVERSE_AS_CODE.

The spatial substrate defines the coordinate system, topology, and distance metric
for agent positioning and navigation. This is an OPTIONAL component - aspatial
universes (pure resource management) are perfectly valid.

Note: SubstrateConfig now lives in townlet.config.stratum_config as substrate
config is nested inside stratum.yaml in v2.1.
"""

from townlet.substrate.aspatial import AspatialSubstrate
from townlet.substrate.base import SpatialSubstrate
from townlet.substrate.continuous import Continuous1DSubstrate, Continuous2DSubstrate, Continuous3DSubstrate
from townlet.substrate.continuousnd import ContinuousNDSubstrate
from townlet.substrate.factory import SubstrateFactory
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate
from townlet.substrate.gridnd import GridNDSubstrate

__all__ = [
    "SpatialSubstrate",
    "Grid2DSubstrate",
    "Grid3DSubstrate",
    "GridNDSubstrate",
    "Continuous1DSubstrate",
    "Continuous2DSubstrate",
    "Continuous3DSubstrate",
    "ContinuousNDSubstrate",
    "AspatialSubstrate",
    "SubstrateFactory",
]
