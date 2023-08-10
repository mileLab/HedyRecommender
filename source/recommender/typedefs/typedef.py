from enum import Enum
from typing import Optional, Literal, Protocol, Dict

from pydantic import Field
from pydantic.dataclasses import dataclass


class RecommenderSevereError(RuntimeError):
    pass


class IsDataclass(Protocol):
    # checking for this attribute is currently the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: Dict


@dataclass
class ValidityResult:
    valid: bool = Field(description="Score of the demand/supplier match (between 0 and 1)")
    error: Optional[str] = Field(default=None, description="Occurred error, if any")


class ComparisonType(str, Enum):
    """
    All different possibilities how parameters can be compared
    """
    EXACT_MATCH = "exact"  # d == s
    INCLUSIVE = "inclusive"  # s == True or d == s
    INV_INCLUSIVE = "inv_inclusive"  # s == False or d == s
    LESS = "less"  # d < s
    GREATER = "greater"  # d > s
    LESS_EQU = "less_equ"  # d <= s
    GREATER_EQU = "greater_equ"  # d >= s
    IS_IN = "is_in"  # s in d: "abc" in [...] or Range_d in Range_s
    IS_SUPERSET = "is_superset"  # d in s:


BoolComparisons = Literal[ComparisonType.INCLUSIVE, ComparisonType.INV_INCLUSIVE, ComparisonType.EXACT_MATCH]


@dataclass
class ComparisonErrors:
    failures: dict[str, str] = Field(default_factory=dict, description="Maps the identifier to the occurred error")
    skipped: dict[str, str] = Field(default_factory=dict,
                                    description="Maps the identifier to a string, why the identifier was skipped")


ParameterErrors = dict[str, ComparisonErrors]
PreferenceErrors = dict[str, ComparisonErrors]


@dataclass
class ScoreErrors:
    preferences: PreferenceErrors = Field(default=PreferenceErrors(),
                                          description="Errors occurred during evaluation of preferences. Maps a "
                                                      "category name to the corresponding error datastructure")
    parameters: ParameterErrors = Field(default_factory=dict,
                                        description="Errors occurred during evaluation of parameters. Maps a "
                                                    "category name to the corresponding error datastructure")


class DominantParent(str, Enum):
    DEMAND = "Demand"
    SUPPLIER = "Supplier"
    BOTH = "Both"


NO_CATEGORY: str = "NO CATEGORY"