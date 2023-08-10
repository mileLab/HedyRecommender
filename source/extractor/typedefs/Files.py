from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass


class FileConfig:
    extra = "forbid"
    smart_union = True


class SupportedFiles(str, Enum):
    """
    A list of supported file extensions
    """
    EAGLE_BOARD = "brd"
    PACKAGE_MAPPING = "csv"
    STEP = "step"
    STL = "stl"


@dataclass(config=FileConfig)
class File:
    """
    Representation of a single file
    """
    type: SupportedFiles = Field(description="File extension (without .), e.g. brd, stl")
    encoding: str = Field(description="File encoding, e.g. binary, utf-8,...")
    content: str = Field(description="File content as base64 encoded string")


@dataclass(config=FileConfig)
class StepFile(File):
    """
    Representation of STEP File
    """
    axis_aligned: bool = Field(description="False if axis are not aligned with coordinate system")


@dataclass(config=FileConfig)
class StlFile(File):
    """
    Representation of STL File
    """
    # unit used in the STL file
    unit: str = Field(description="Unit used in the STL file e.g., mm, cm, m, in, ...")
    axis_aligned: bool = Field(description="False if axis are not aligned with coordinate system")
