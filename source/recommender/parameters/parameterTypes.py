import dataclasses
from typing import Union, Type

from common.typedef import Range
from recommender.typedefs.typedef import ComparisonType

ParameterTypeList = [bool, int, float, Range[int], Range[float], str, list[str], list[int], list[float], list[bool]]
ParameterTypeTypes = Union[Type[bool], Type[int], Type[float], Type[Range[int]], Type[Range[float]], Type[str],
                           Type[list[str]], Type[list[bool]]]
ParameterTypes = Union[bool, int, float, str, list, Range]
NumberTypes = Union[int, float]

GenericTypes = [Range, list]


@dataclasses.dataclass
class ParameterTypeCombination:
    demand_type: ParameterTypeTypes
    supplier_type: ParameterTypeTypes
    comparison_type: ComparisonType


__same_exact = [ParameterTypeCombination(t, t, comparison_type=ComparisonType.EXACT_MATCH) for t in ParameterTypeList]
__number_comparison = [ParameterTypeCombination(t, t, c) for t in [int, float] for c in (
    ComparisonType.LESS, ComparisonType.LESS_EQU, ComparisonType.GREATER, ComparisonType.GREATER_EQU)]

__bool_comparisons = [
    ParameterTypeCombination(demand_type=bool, supplier_type=bool, comparison_type=ComparisonType.INCLUSIVE),
    ParameterTypeCombination(demand_type=bool, supplier_type=bool, comparison_type=ComparisonType.INV_INCLUSIVE),
]

__is_in_value_list = [ParameterTypeCombination(t, list[t], comparison_type=ComparisonType.IS_IN) for t in
                      [int, float, str]]
__is_in_range_range = [ParameterTypeCombination(Range[t], Range[t], comparison_type=ComparisonType.IS_IN) for t in
                       [int, float]]
__is_in_value_range = [ParameterTypeCombination(t, Range[t], comparison_type=ComparisonType.IS_IN) for t in
                       [int, float]]

__is_superset_value_list = [ParameterTypeCombination(list[t], t, comparison_type=ComparisonType.IS_SUPERSET) for t in
                            [int, float, str]]
__is_superset_range_range = [ParameterTypeCombination(Range[t], Range[t], comparison_type=ComparisonType.IS_SUPERSET)
                             for t in [int, float]]
__is_superset_value_range = [ParameterTypeCombination(Range[t], t, comparison_type=ComparisonType.IS_SUPERSET) for t in
                             [int, float]]

__is_in = __is_in_value_list + __is_in_range_range + __is_in_value_range
__is_superset = __is_superset_value_list + __is_superset_range_range + __is_superset_value_range

supported_parameter_type_combinations: list[ParameterTypeCombination] = \
    __same_exact + __number_comparison + __bool_comparisons + __is_in + __is_superset

supported_parameter_type_combinations_cmp_type: dict[ComparisonType, list[ParameterTypeCombination]] = {
    c: [tc for tc in supported_parameter_type_combinations if tc.comparison_type == c] for c in ComparisonType}

pass
