from typing import Optional, Literal, get_args

from pydantic import Field
from pydantic.dataclasses import dataclass

from common.typedef import Range
from extractor.typedefs.typedef import PackagingType, ProductionMethod


_SPECIFIC_PM_LITERAL = Literal[ProductionMethod.PCB_ASSEMBLY]
_SPECIFIC_PRODUCTION_METHODS:list[str] = list(get_args(_SPECIFIC_PM_LITERAL))
_GENERIC_PM_LITERAL = Literal[tuple(pm for pm in ProductionMethod if pm not in _SPECIFIC_PRODUCTION_METHODS)]
_GENERIC_PRODUCTION_METHODS:list[str] = [pm for pm in ProductionMethod if pm not in _SPECIFIC_PRODUCTION_METHODS]

@dataclass
class GenericParameters:
    """
    Parameters, which are valid for all production methods
    """

    # this field is required due to some unexpected behavior of the response model when it comes to Union Types
    production_method: _GENERIC_PM_LITERAL
    length: Optional[float] = Field(description="Longest dimension of the object")
    width: Optional[float] = Field(description="Second-longest dimension of the object")
    height: Optional[float] = Field(description="Shortest dimension of the object")


@dataclass
class PCBParameters:
    """
    Parameters specifically for PCB Boards
    """

    # this field is required due to some unexpected behavior of the response model when it comes to Union Types
    production_method: Literal[ProductionMethod.PCB_ASSEMBLY]
    length: Optional[float] = Field(description="Longest dimension of the object")
    width: Optional[float] = Field(description="Second-longest dimension of the object")
    height: Optional[float] = Field(description="Shortest dimension of the object")
    assembly_sides: Optional[int] = Field(description="Number of sides where components are places")
    n_layers: Optional[int] = Field(description="Number of layers of the PCB board", title="Number Layers")
    inner_milling: Optional[bool] = Field(description="Flag if inner milling is present")
    drill_size: Optional[Range[float]] = Field(description="Smallest and largest drill size")
    drill_size_PTH: Optional[Range[float]] = Field(description="Smallest and largest PTH drill size")
    drill_size_NPTH: Optional[Range[float]] = Field(description="Smallest and largest NPTH drill size")
    drill_size_via: Optional[Range[float]] = Field(description="Smallest and largest via drill size")
    packaging_count: Optional[dict[PackagingType, int]] = Field(description="Amount of each packaging type")
    n_different_packaging_types: Optional[int] = Field(description="Number of different packaging types present",
                                                       title="Number Different Packaging Types")
    n_components: Optional[int] = Field(description="Total number of components on the board",
                                        title="Number Components")
    n_components_per_package: Optional[dict[str, int]] = Field(
        description="Number of components per package on the board", title="Number Components per Package")
    component_size_length: Optional[Range[float]] = Field(
        description="Minimal and Maximal length of a component, where length denots the longest side")
    component_size_width: Optional[Range[float]] = Field(
        description="Minimal and Maximal width of a component, where width denots the shortest side")
    copper_thickness: Optional[Range[float]] = Field(description="Minimal and maximal thickness of copper layers")
    trace_width: Optional[Range[float]] = Field(description="Minimal and maximal width of traces")
    prepreg_thickness: Optional[Range[float]] = Field(description="Minimal and maximal thickness of prepreg layers")
    trace_clearance: Optional[float] = Field(description="Minimal distance of conductive parts")
    solder_mask_clearance: Optional[Range[float]] = Field(
        description="Minimal and maximal distance of solder mask to pad, via or drill")
    core_thickness: Optional[Range[float]] = Field(description="Minimal and maximal thickness of core layers")
    n_via: Optional[int] = Field(description="Total number of vias", title="Number Vias")
    n_buried_via: Optional[int] = Field(description="Number of buried vias", title="Number Buried Vias")
    n_blind_via: Optional[int] = Field(description="Number of blind vias", title="Number Blind Vias")
    n_through_hole_via: Optional[int] = Field(description="Number of through hole via",
                                              title="Number Through Hole Vias")
    n_PTH: Optional[int] = Field(description="Number of PTH drills", title="Number PTH")
    n_NPTH: Optional[int] = Field(description="Number of NPTH drills", title="Number NPTH")
