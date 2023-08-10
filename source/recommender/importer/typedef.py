from dataclasses import dataclass
from enum import Enum
from types import GenericAlias
from typing import Literal, get_args, Optional, Type, Union

from recommender.preferences.preferenceTypes import PreferenceTypesTypesLiterals
from recommender.typedefs.typedef import DominantParent, ComparisonType

ImportStages = Literal["parsing", "processing", "validation"]
ImporterStageError = dict[str, list[str]]
ImportErrors = dict[ImportStages, ImporterStageError]

PARAM_TYPES = Literal['bool', 'float', 'int', 'range', 'list', 'str']
__POSSIBLE_PARAM_TYPES: list[PARAM_TYPES] = list(get_args(PARAM_TYPES))
PREF_TYPES = Literal['bool', 'float', 'int', 'range', 'list']
__POSSIBLE_PREF_TYPES: list[PREF_TYPES] = list(get_args(PREF_TYPES))
__POSSIBLE_PREF_TYPE_TYPES = [t for t in PreferenceTypesTypesLiterals] + ['SingleChoicePreferenceOrdered']
__PARAMETER_TYPE_TAG = "Parameter"
__OTHER_TYPE_TAG = "NoType"
__POSSIBLE_DOMINANT_PARENT_VALUES = set([item.value for item in DominantParent] + [""])
__POSSIBLE_COMPARISON_TYPE_VALUES = set([item.value for item in ComparisonType] + [""])


class CsvIdx(int, Enum):
    full_name = 0
    production_method = 1
    class_name = 2
    category = 3
    field_name = 4
    comparison_type = 5
    data_type_demand = 6
    data_type_supplier = 7
    type = 8
    depends_on = 9
    dominant_parent = 10


REQIRED_CSV_COLUMNS: int = max([i.value for i in CsvIdx]) + 1


@dataclass
class RawPreferenceData:
    full_name: str
    name: str
    production_method: list[str]
    category: str
    depends_on: str
    dominant_parent: Optional[DominantParent]

    type_supplier: list[PREF_TYPES]
    type_demand: list[PREF_TYPES]
    comparison_type: Optional[ComparisonType]
    preference_type: str


@dataclass
class RawParameterData:
    full_name: str
    name: str
    production_method: list[str]
    category: str

    type_supplier: list[PARAM_TYPES]
    type_demand: list[PARAM_TYPES]
    comparison_type: Optional[ComparisonType]


@dataclass
class PreferenceData:
    full_name: str
    name: str
    production_method: list[str]
    category: str
    depends_on: Optional[str]
    dominant_parent: Optional[DominantParent]

    type_supplier: Union[Type, GenericAlias]
    type_demand: Union[Type, GenericAlias]
    comparison_type: Optional[ComparisonType]
    preference_type: str
    ordered: bool = False

    def print_pref_type(self):
        return self.preference_type if not self.ordered else self.preference_type + "Ordered"


@dataclass
class ParameterData:
    full_name: str
    name: str
    production_method: list[str]
    category: str

    type_supplier: Union[Type, GenericAlias]
    type_demand: Union[Type, GenericAlias]
    comparison_type: Optional[ComparisonType]
