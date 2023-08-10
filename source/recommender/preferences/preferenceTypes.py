import dataclasses
from abc import ABC
from types import GenericAlias
from typing import Union, Type, Any, Optional

from pydantic import confloat

from common.typedef import Range
from recommender.typedefs.typedef import BoolComparisons, ComparisonType


class CustomType(ABC):
    type: Union[Type, GenericAlias]


class BoolPreference(CustomType):
    type = bool

    def __init__(self, comparison_type: BoolComparisons = ComparisonType.EXACT_MATCH,
                 importance: confloat(ge=0, le=1) = 1):
        self.comparison_type: BoolComparisons = comparison_type
        self.importance = importance

    def deduce_importance(self, value) -> float:
        return float(value)


class ChoicePreference(CustomType):
    type = list[bool]


class RangePreference(CustomType):
    type = confloat(ge=0.0, le=1.0)

    def __init__(self, importance: confloat(ge=0, le=1) = 1):
        self.importance = importance

    def deduce_importance(self, value) -> float:
        return float(value)


class SingleChoicePreference(ChoicePreference):
    def __init__(self, ordered: bool = False, importance: confloat(ge=0, le=1) = 1):
        self.ordered: bool = ordered
        self.importance = importance


class MultipleChoicePreference(ChoicePreference):
    def __init__(self, comparison_type: BoolComparisons = ComparisonType.EXACT_MATCH,
                 importance: confloat(ge=0, le=1) = 1):
        self.comparison_type: BoolComparisons = comparison_type
        self.importance = importance


class ValueMagnitudePreference(CustomType):
    type = Union[int, float]

    def __init__(self, importance: confloat(ge=0, le=1) = 1):
        self.importance = importance


class ZonePreference(CustomType):
    type = Union[int, float, Range[int], Range[float]]

    def __init__(self, importance: confloat(ge=0, le=1) = 1):
        self.importance = importance


@dataclasses.dataclass
class CustomTypeInstance:
    base_type: CustomType
    value: Any


PreferenceTypes = Union[CustomTypeInstance]
PreferenceTypesList = [RangePreference, BoolPreference, SingleChoicePreference, MultipleChoicePreference,
                       ValueMagnitudePreference, ZonePreference]
PreferenceTypesTypes = Union[tuple(PreferenceTypesList)]
PreferenceTypesTypesLiterals: list[str] = [t.__name__ for t in PreferenceTypesList]

PreferenceValueTypes = [int, float, Range[int], Range[float], bool, list[bool]]
PreferenceValueTypesTypes = Union[tuple({Type[t] for t in PreferenceValueTypes})]

preference_factory = {
    RangePreference.__name__: lambda data: RangePreference(),
    BoolPreference.__name__: lambda data: BoolPreference(comparison_type=data.comparison_type),
    SingleChoicePreference.__name__: lambda data: SingleChoicePreference(ordered=data.ordered),
    MultipleChoicePreference.__name__: lambda data: MultipleChoicePreference(comparison_type=data.comparison_type),
    ValueMagnitudePreference.__name__: lambda data: ValueMagnitudePreference(),
    ZonePreference.__name__: lambda data: ZonePreference()
}


@dataclasses.dataclass
class PreferenceTypeCombination:
    demand_type: PreferenceValueTypes
    supplier_type: PreferenceValueTypes
    comparison_type: Optional[ComparisonType]
    preference_type: PreferenceTypesTypesLiterals

    def get_comp_type_value(self) -> Optional[str]:
        if self.comparison_type is None:
            return None
        else:
            return self.comparison_type.value


__range = [PreferenceTypeCombination(float, float, None, RangePreference.__name__)]
__bool = [PreferenceTypeCombination(bool, bool, ct, BoolPreference.__name__) for ct in
          [ComparisonType.INCLUSIVE, ComparisonType.INV_INCLUSIVE, ComparisonType.EXACT_MATCH]]
__single_choice = [PreferenceTypeCombination(list[bool], list[bool], None, SingleChoicePreference.__name__)]
__multiple_choice = [PreferenceTypeCombination(list[bool], list[bool], ct, MultipleChoicePreference.__name__) for ct in
                     [ComparisonType.INCLUSIVE, ComparisonType.INV_INCLUSIVE, ComparisonType.EXACT_MATCH]]
__magnitude = [PreferenceTypeCombination(t, t, None, ValueMagnitudePreference.__name__) for t in [int, float]]
__zone = [PreferenceTypeCombination(t, Range[t], None, ZonePreference.__name__) for t in [int, float]]

supported_preference_type_combinations: list[PreferenceTypeCombination] = \
    __range + __bool + __single_choice + __multiple_choice + __magnitude + __zone

supported_preference_type_combinations_pref_type: dict[str, list[PreferenceTypeCombination]] = {
    pt: [tc for tc in supported_preference_type_combinations if tc.preference_type == pt] for
    pt in PreferenceTypesTypesLiterals}
