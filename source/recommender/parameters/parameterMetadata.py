from typing import Union

from recommender.parameters.parameterComparison import compare_map
from recommender.parameters.parameterTypes import ParameterTypeTypes, ParameterTypeList
from recommender.typedefs.typedef import ComparisonType, NO_CATEGORY


class ParameterMetadata:

    def __init__(self, production_method: Union[str, list[str]], comparison: ComparisonType, category: str,
                 demand_type: ParameterTypeTypes, supplier_type: ParameterTypeTypes, demand_description: str = "",
                 supplier_description: str = ""):
        if not isinstance(production_method, list):
            self.production_method = [production_method]
        else:
            self.production_method = production_method

        self.comparison = comparison
        try:
            self.cmp_fnc = compare_map[self.comparison]
        except LookupError as e:
            raise RuntimeError(f"Could not find comparison function for {self.comparison.value}") from e

        if demand_type not in ParameterTypeList:
            raise RuntimeError(f"Input demand type {demand_type} is not a valid type from: {ParameterTypeList}")
        self.demand_type = demand_type

        if demand_type not in ParameterTypeList:
            raise RuntimeError(f"Input demand type {demand_type} is not a valid type from: {ParameterTypeList}")
        self.supplier_type = supplier_type

        self.demand_description = demand_description if demand_description != "" else None
        self.supplier_description = supplier_description if supplier_description != "" else None

        self.category = category if category != "" else NO_CATEGORY
