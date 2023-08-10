from dataclasses import is_dataclass, field, fields, make_dataclass
from typing import ClassVar, Type, Optional

import pydantic

from common.typedef import Range, RangeFloat, RangeInt
from recommender.parameters.parameterMetadata import ParameterMetadata


def generate_demand_supplier_dataclass(Metadata, production_methods: list[str]) -> tuple[
    dict[str, Type['pydantic.dataclasses.Dataclass']], dict[str, Type['pydantic.dataclasses.Dataclass']]]:
    if not is_dataclass(Metadata):
        raise RuntimeError("Input class needs to be a dataclass")

    # ClassVar is not captured by fields method, hence no special case when iterating over fields
    derived_from_tuple = ("derived_from", ClassVar[Type], field(default=Metadata))
    pairs_demand: dict[str, list[tuple[str, type, pydantic.Field]]] = {pm: [derived_from_tuple] for pm in
                                                                       production_methods}
    pairs_supplier: dict[str, list[tuple[str, type, pydantic.Field]]] = {pm: [derived_from_tuple] for pm in
                                                                         production_methods}

    base_name = Metadata.__name__
    for f in fields(Metadata):
        p_name = f.name
        p_type = getattr(Metadata, p_name)
        if not isinstance(p_type, ParameterMetadata):
            raise RuntimeError(f"Metadata Type needs to be of ParameterMetadata, got {type(p_type)}.")

        # workaround for fastapi bug with generics
        demand_type = p_type.demand_type
        supplier_type = p_type.supplier_type
        if demand_type in [Range[int], Range[float]]:
            demand_type = generic_range_to_concrete(demand_type)
        if supplier_type in [Range[int], Range[float]]:
            supplier_type = generic_range_to_concrete(supplier_type)

        # Add optional
        d_type: Type = Optional[demand_type]
        s_type: Type = Optional[supplier_type]

        for pm in p_type.production_method:
            # add to dataclass
            pairs_demand[pm].append(
                (p_name, d_type, pydantic.Field(default=None, description=p_type.demand_description)))
            pairs_supplier[pm].append(
                (p_name, s_type, pydantic.Field(default=None, description=p_type.supplier_description)))

    class ModelConfig:
        extra = "forbid"

    demand_data_class = {pm: pydantic.dataclasses.dataclass(make_dataclass(base_name + pm + "Demand", f), config=ModelConfig) for pm, f in
                         pairs_demand.items()}
    supplier_data_class = {pm: pydantic.dataclasses.dataclass(make_dataclass(base_name + pm + "Supplier", f), config=ModelConfig) for pm, f
                           in pairs_supplier.items()}

    return demand_data_class, supplier_data_class


def generic_range_to_concrete(range_type: Type) -> Type:
    if range_type == Range[float]:
        return RangeFloat
    if range_type == Range[int]:
        return RangeInt
    return range_type
