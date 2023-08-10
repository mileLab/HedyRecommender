import traceback
from dataclasses import dataclass, fields, field
from enum import Enum
from typing import Union, Optional, Tuple

from extractor.typedefs.typedef import ParsingError, SingleError


class DrillType(Enum):
    VIA_MICROVIA = "via_micro"
    VIA_THROUGH = "via_through"
    VIA_BLIND_BURIED = "via_blind_buried"
    NPTH = "NPTH"
    PTH = "PTH"


class TrackType(Enum):
    LINE = "line"
    ARC = "arc"


@dataclass
class Drill:
    position: list[float]  # x,y
    width: float
    type: DrillType  # enum
    net: str

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = DrillType(self.type)


@dataclass
class ViaDrill(Drill):
    layers: list[int]  # min,max
    diameter: float


@dataclass
class FullDrill(Drill):
    solder_mask_margin: float
    trace_clearance: list[float]
    diameter: list[float]


@dataclass
class Track:
    start: list[float]
    end: list[float]
    width: float
    type: str  # enum
    layer: int
    net: str


@dataclass
class Layer:
    is_cu: bool
    is_internal_Cu: bool
    is_board_tech: bool
    is_tech: bool
    is_front_assembly: bool
    is_back_assembly: bool
    is_front: bool
    is_back: bool
    is_user: bool
    is_user_defined: bool
    is_physical: bool
    id: int
    name: str
    name_def: str
    visible: bool


@dataclass
class BoardInformation:
    width: float
    height: float


class ContactType(Enum):
    SMD = "SMD"
    PTH = "PTH"
    NPTH = "NPTH"


@dataclass
class ContactItem:
    type: ContactType
    center: list[float]
    size: list[float]
    orientation: float
    solder_mask_clearance: Optional[float]  # if none, then solder_mask is disabled for this item


@dataclass
class Segment:
    start: list[float]
    end: list[float]


@dataclass
class Arc:
    start: list[float]
    end: list[float]
    # center: list[float]
    angle: float


@dataclass
class Circle:
    center: list[float]
    radius: float


@dataclass
class Rectangle:
    start: list[float]
    end: list[float]


@dataclass
class Poly:
    points: list[list[float]]


GeometricalObjects = Union[Segment, Arc, Circle, Rectangle, Poly]


@dataclass
class Footprint:
    package: str
    nets: list[str]
    orientation: float
    position: list[float]
    layer: int
    dimensions: list[float]
    reference_name: str
    value_name: str
    # nPads: int
    drawings: list[GeometricalObjects]
    contacts: list[ContactItem]

    def __post_init__(self):

        drawings: list[GeometricalObjects] = []
        if isinstance(self.drawings, list):
            for d in self.drawings:
                if isinstance(d, dict):
                    drawing_type = str(d["type"])
                    d.pop("type")
                    if drawing_type == "segment":
                        drawings.append(Segment(**d))
                    elif drawing_type == "rect":
                        drawings.append(Rectangle(**d))
                    elif drawing_type == "arc":
                        drawings.append(Arc(**d))
                    elif drawing_type == "circle":
                        drawings.append(Circle(**d))
                    elif drawing_type == "polygon":
                        drawings.append(Poly(**d))
                    else:
                        raise RuntimeError(f"Unknown type of geometrical object {drawing_type}")
        self.drawings = drawings
        if isinstance(self.contacts, list):
            self.contacts = [ContactItem(**c) for c in self.contacts if isinstance(c, dict)]


@dataclass
class SimplifiedBoard:
    drills: Optional[list[Union[FullDrill, ViaDrill]]]
    tracks: Optional[list[Track]]
    layers: Optional[list[Layer]]
    board: Optional[BoardInformation]
    footprints: Optional[list[Footprint]]

    failures: ParsingError = field(init=False)

    # required, so all the child dataclasses are filled recursively
    def __post_init__(self):
        self.failures = []
        errors: dict[str, Tuple[str, str]] = {}
        if isinstance(self.drills, list):
            try:
                self.drills = [ViaDrill(**d) if "layers" in d else FullDrill(**d) for d in self.drills if
                               isinstance(d, dict)]
            except TypeError as e:
                self.drills = None
                errors["drills"] = str(e), traceback.format_exc()

        if isinstance(self.tracks, list):
            try:
                self.tracks = [Track(**t) for t in self.tracks if isinstance(t, dict)]
            except TypeError as e:
                self.tracks = None
                errors["tracks"] = str(e), traceback.format_exc()

        if isinstance(self.layers, list):
            try:
                self.layers = [Layer(**l) for l in self.layers if isinstance(l, dict)]
            except TypeError as e:
                self.layers = None
                errors["layers"] = str(e), traceback.format_exc()

        if isinstance(self.board, dict):
            try:
                self.board = BoardInformation(**self.board)
            except TypeError as e:
                self.board = None
                errors["board"] = str(e), traceback.format_exc()

        if isinstance(self.footprints, list):
            try:
                self.footprints = [Footprint(**fp) for fp in self.footprints if isinstance(fp, dict)]
            except TypeError as e:
                self.footprints = None
                errors["footprints"] = str(e), traceback.format_exc()

        # set some error information
        for f in fields(self):
            if getattr(self, f.name) is None:
                self.failures.append(SingleError(
                    f"Could not process data to build SimplifiedBoard for field {f.name}. Error: {errors[f.name][0]}",
                    errors[f.name][1]))

        # if we have not received content, set the corresponding field to None
        for f in fields(self):
            if f.name == "failures":
                continue
            if isinstance(getattr(self, f.name), list) and len(getattr(self, f.name)) == 0:
                setattr(self, f.name, None)
                self.failures.append(SingleError(f"Got no data to build SimplifiedBoard for field {f.name}.", ""))
