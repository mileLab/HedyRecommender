import dataclasses
from dataclasses import is_dataclass
from typing import Type, Optional, ClassVar, get_origin, Union, get_args

import pydantic

from common.typedef import Range
from recommender.parameters.parameterGeneration import generic_range_to_concrete
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.preferences.preferenceTypes import CustomType
from recommender.typedefs.typedef import IsDataclass


def complete_preference_namings(preferences: IsDataclass):
    # fills in the PreferenceMetadata its associated name
    if not is_dataclass(preferences):
        raise RuntimeError(f"Input class {preferences.__class__.__name__} needs to be a dataclass")

    for f in dataclasses.fields(preferences):
        name = f.name
        metadata: PreferenceMetadata = getattr(preferences, name)
        metadata.name = name


def complete_preference_dependencies(preferences: IsDataclass):
    # defines connects the parent and child relationships
    if not is_dataclass(preferences):
        raise RuntimeError(f"Input class {preferences.__class__.__name__} needs to be a dataclass")

    for f in dataclasses.fields(preferences):
        name = f.name
        metadata: PreferenceMetadata = getattr(preferences, name)

        if metadata.depends_on is not None:
            parent_metadata: PreferenceMetadata = getattr(preferences, metadata.depends_on, None)

            if parent_metadata is None:
                raise RuntimeError(
                    f"Parent preference {metadata.depends_on} from {name} does not exist in list of preferences.")

            metadata.parent = parent_metadata
            parent_metadata.children.append(metadata)


def generate_preference_dataclass(Metadata: IsDataclass, production_methods: list[str]) -> dict[
    str, Type['pydantic.dataclasses.Dataclass']]:
    if not is_dataclass(Metadata):
        raise RuntimeError(f"Input class {Metadata.__class__.__name__} needs to be a dataclass")

    derived_from_tuple = ("derived_from", ClassVar[Type], dataclasses.field(default=Metadata))
    pairs_fields: dict[str, list[tuple[str, type, pydantic.Field]]] = {pm: [derived_from_tuple] for pm in
                                                                       production_methods}
    base_name = Metadata.__name__
    for f in dataclasses.fields(Metadata):
        p_name = f.name
        p_type = getattr(Metadata, p_name)
        if not isinstance(p_type, PreferenceMetadata):
            raise RuntimeError(f"Metadata Type needs to be of PreferenceMetadata, got {type(p_type)}.")

        if isinstance(p_type.preference_type, CustomType):
            # convert Range[int], Range[float] to RangeInt, RangeFloat
            t = convert_generic_types_to_concrete(p_type.preference_type.type)

            # Add optional to type
            preference_type: Type = Optional[t]
        else:
            raise RuntimeError(f"Preference needs to be derived from CustomType")

        # add to dataclass
        for pm in p_type.production_method:
            pairs_fields[pm].append(
                (p_name, preference_type, pydantic.Field(default=None, description=p_type.description)))

    data_class = {pm: pydantic.dataclasses.dataclass(dataclasses.make_dataclass("Input" + base_name + pm, fields))
                  for pm, fields in pairs_fields.items()}

    return data_class


def convert_generic_types_to_concrete(t: type) -> Type:
    if get_origin(t) == Union:
        args = get_args(t)
        args = list(map(lambda x: generic_range_to_concrete(x) if x in [Range[int], Range[float]] else x, args))
        return Union[tuple(args)]
    elif t in [Range[int], Range[float]]:
        return generic_range_to_concrete(t)
    return t
