from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass


class ProductionMethod(str, Enum):
    """
    Enumeration of all production methods
    """
    PCB_ASSEMBLY = "PCB_ASSEMBLY"
    MACHINING_GEOM_CUT = "MACHINING_GEOM_CUT"
    MOULDING_PLASTIC = "MOULDING_PLASTIC"
    GENERIC = "GENERIC"


class PackagingType(str, Enum):
    """
    Enumeration of all available PCB packaging types
    """
    TWO_TERMINAL = "Two-terminal packages"
    THROUGH_HOLE = "Through-hole packages"
    SURFACE_MOUNT = "Surface mount"
    CHIP_CARRIER = "Chip carrier"
    PIN_GRID_ARRAY = "Pin grid arrays"
    FLAT_PACKAGE = "Flat packages"
    SMALL_OUTLINE_IC = "Small outline packages"
    CHIP_SCALE = "Chip-scale packages"
    BALL_GRID_ARRAY = "Ball grid array"
    TRAN_DIO_SMALL_PIN_IC = "Transistor, diode, small-pin-count IC packages"
    MULTI_CHIP = "Multi-chip packages"
    T_CAPACITOR = "Tantalum capacitors"
    A_CAPACITOR = "Aluminum capacitors"
    NON_PACKAGED = "Non-packaged devices"
    OTHERS = "Others"


@dataclass
class SingleError:
    error: str = Field(description="Short description of error or string representation of exception")
    traceback: Optional[str] = Field(default=None, description="Full traceback of exception")


ExtractionError = dict[str, list[SingleError]]
ParsingError = list[SingleError]


class ExtractorSevereError(RuntimeError):
    pass


@dataclass
class Failures:
    parsing: ParsingError = Field(description="Datastructure for occurred parsing errors", default_factory=list)
    extracting: ExtractionError = Field(
        description="Datastructure for parameter extraction errors. Maps the name of the output parameter to the occurred error.",
        default_factory=dict)


@dataclass
class PackageSize:
    size: list[float] = Field(description="Size of the packaging, first entry corresponds to longest side")


@dataclass
class PackageFailureInformation(PackageSize):
    failure: str = Field(description="Reason, why the package could not be matched")


ParameterInfo = dict[str, list[str]]
PackageFailures = dict[str, str]
ParameterWarnings = list[str]
PackageFailuresInformation = dict[str, PackageFailureInformation]


@dataclass
class MatchingInformation:
    score: float = Field(description="Score of the package matching")
    matching_type: str = Field(description="Description how the matching was performed")


@dataclass
class PackageInformation(PackageSize):
    packaging_type: PackagingType = Field(description="Type of the package")
    name: str = Field(description="Name of the footprint in the given file")
    matched_package: str = Field(description="Name of the matched footprint from database")
    matching_information: MatchingInformation = Field(description="Additional information of the matching process")


@dataclass
class PackagingInfo:
    failures: PackageFailuresInformation = Field(description="Packages, which could not be matched")
    success: dict[str, PackageInformation] = Field(
        description="Successfully matched packages with additional information")


@dataclass
class AdditionalParameterInfo:
    info_parameter: ParameterInfo = Field(description="Additional information about the parameter extraction process")
    warnings: ParameterWarnings = Field(description="Warnings occurred during the parameter extraction process")
    info_packaging: Optional[PackagingInfo] = Field(default=None,
                                                    description="Additional information about the package matching process (only for PCB)")


@dataclass
class PackageMappingContent:
    p_type: PackagingType
    length: float
    width: float


PackageMapping = dict[str, PackageMappingContent]


@dataclass
class PackageMappingCSVData:
    names: list[str]
    packaging: str
    length: float
    width: float
