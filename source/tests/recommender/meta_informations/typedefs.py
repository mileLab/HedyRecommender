from enum import Enum
from typing import Union

from common.typedef import Range
from recommender.parameters.parameterMetadata import ParameterMetadata
from recommender.typedefs.typedef import ComparisonType


class ProductionMethod(str, Enum):
    """
    Enumeration of all production methods
    """
    PCB_ASSEMBLY = "PCB_ASSEMBLY"
    MACHINING_GEOM_CUT = "MACHINING_GEOM_CUT"
    MOULDING_PLASTIC = "MOULDING_PLASTIC"
    GENERIC = "GENERIC"


ParameterValues = Union[bool, int, float, Range[int], Range[float], str]

all_methods = [ProductionMethod(e).value for e in ProductionMethod]


def bool_exact_all(category="") -> ParameterMetadata:
    return ParameterMetadata(production_method=all_methods, comparison=ComparisonType.EXACT_MATCH, demand_type=bool,
                             supplier_type=bool, category=category)


def bool_inclusive_all(category="") -> ParameterMetadata:
    return ParameterMetadata(production_method=all_methods, comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                             supplier_type=bool, category=category)


def bool_exclusive_all(category="") -> ParameterMetadata:
    return ParameterMetadata(production_method=all_methods, comparison=ComparisonType.INV_INCLUSIVE, demand_type=bool,
                             supplier_type=bool, category=category)


def value_to_range(t: Union[type[int], type[float]], category="") -> ParameterMetadata:
    return ParameterMetadata(production_method=all_methods, comparison=ComparisonType.IS_IN, demand_type=t,
                             supplier_type=Range[t], category=category)


def range_to_value(t: Union[type[int], type[float]], category="") -> ParameterMetadata:
    return ParameterMetadata(production_method=all_methods, comparison=ComparisonType.IS_SUPERSET, demand_type=Range[t],
                             supplier_type=t, category=category)
