from typing import Union

from pydantic import Field
from pydantic.dataclasses import dataclass

from extractor.typedefs.Files import File, StlFile, StepFile
from extractor.typedefs.parameters import GenericParameters, PCBParameters
from extractor.typedefs.typedef import Failures, AdditionalParameterInfo, ProductionMethod

ParameterSets = Union[PCBParameters, GenericParameters, None]
SupportedFileTypes = Union[File, StlFile, StepFile]


@dataclass
class ComponentParameters:
    """
    Collection of parameters and failures for a single component
    """
    name: str = Field(description="Name of the component")
    # the least specific type must be at the right
    parameters: ParameterSets = Field(description="List of all extracted parameters with value")
    failures: Failures = Field(description="Datastructure of all occurred failures")
    additional_info: AdditionalParameterInfo = Field(description="Additional hints and warnings")


@dataclass
class Component:
    """
    A production component
    """
    name: str = Field(description="Name of the component")
    method: ProductionMethod = Field(description="Type of production method")
    files: list[SupportedFileTypes] = Field(description="List of corresponding files", default_factory=list)


# input for the extractor
@dataclass
class Input:
    components: list[Component] = Field(description="List of all components", default_factory=list)


# Output of the extractor
@dataclass
class Output:
    # List of all extracted parameters for each component
    components: list[ComponentParameters] = Field(description="List of all extracted parameters for each component",
                                                  default_factory=list)
