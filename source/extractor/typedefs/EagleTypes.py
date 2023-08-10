from dataclasses import dataclass
from enum import Enum
from typing import Optional

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from extractor.typedefs.typedef import ParsingError


class Isolate(Enum):
    CORE = "c"
    PREPREG = "p"


CopperThickness = dict[int, float]
IsolateThickness = dict[tuple[int, int], float]
Stackup = dict[tuple[int, int], Isolate]


@dataclass
class MinimalDistances:
    mdWireWire: Optional[float] = None
    mdWirePad: Optional[float] = None
    mdWireVia: Optional[float] = None
    mdPadPad: Optional[float] = None
    mdPadVia: Optional[float] = None
    mdViaVia: Optional[float] = None


@dataclass
class StopMaskLimits:
    stop_limit: list[float, float]
    stop_perc: float
    via_stop_limit: float


@dataclass
class Rules:
    min_distances: MinimalDistances
    stop_mask_limits: StopMaskLimits


@dataclass
class Topology:
    outer_boundary: Polygon
    closed_objects: list[BaseGeometry]
    open_objects: list[BaseGeometry]
    millings: list[BaseGeometry]


@dataclass
class EagleBoardData:
    failures: ParsingError
    warnings: list[str]

    stackup: Optional[Stackup] = None
    copper_thickness: Optional[CopperThickness] = None
    isolate_thickness: Optional[IsolateThickness] = None
    rules: Optional[Rules] = None
    topology: Optional[Topology] = None
