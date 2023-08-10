import re
from dataclasses import make_dataclass, field, Field
from typing import Union

from recommender.importer.typedef import ParameterData, PreferenceData
from recommender.parameters.parameterMetadata import ParameterMetadata
from recommender.preferences.preferenceBase import PreferenceBase
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.preferences.preferenceTypes import PreferenceTypesList, preference_factory


def extract_global_data(data: list[Union[ParameterData, PreferenceData]]):
    categories: list[str] = []
    production_methods: list[str] = []

    for d in data:
        # if isinstance(d, PreferenceData):
        categories.append(d.category)

        production_methods += d.production_method

    categories = list(set(categories))

    production_methods = list(set(production_methods))
    if "ALL" in production_methods: production_methods.remove("ALL")
    if "GENERIC" in production_methods: production_methods.remove("GENERIC")

    return categories, production_methods


# def generate_preference_categories(categories: list[str]):
#     # creating class dynamically
#     content = {__fix_input_name(c): c for c in categories}
#     e = enum.Enum(value='PreferenceCategory', names=content, type=str)
#     return e
#
#
# def generate_production_method(production_methods: list[str]):
#     # creating class dynamically
#     content = {__fix_input_name(pm): pm for pm in production_methods if pm != 'ALL'}
#     e = enum.Enum(value='ProductionMethod', names=content, type=str)
#     return e


def generate_input_metadata_types(data: list[Union[ParameterData, PreferenceData]], production_methods: list[str]):
    data_parameters, data_preferences = _extract_input_types_from_data(data, production_methods)
    parameter_metadata = _generate_input_types_parameters(data_parameters)
    preference_metadata = _generate_input_types_preferences(data_preferences)

    return parameter_metadata, preference_metadata


def _generate_input_types_parameters(data_parameters: list[ParameterData]):
    members = []
    for d in data_parameters:
        name = d.name
        t = ParameterMetadata
        param_meta_instance = ParameterMetadata(production_method=d.production_method, comparison=d.comparison_type,
                                                supplier_type=d.type_supplier, demand_type=d.type_demand,
                                                category=d.category)
        f: Field = field(default=param_meta_instance)
        members.append((name, t, f))

    parameter_types = make_dataclass(cls_name="InputParameters", fields=members)
    return parameter_types


def _generate_input_types_preferences(data_preferences: list[PreferenceData]):
    members = []
    for d in data_preferences:
        name = d.name
        t = PreferenceMetadata
        pref_type = next(pt for pt in PreferenceTypesList if pt.__name__ == d.preference_type)
        pref_type_instance = preference_factory[pref_type.__name__](d)
        pref_meta_instance = PreferenceMetadata(production_method=d.production_method,
                                                preference_type=pref_type_instance,
                                                depends_on=d.depends_on, dominant_side=d.dominant_parent,
                                                category=d.category)
        f: Field = field(default=pref_meta_instance)
        members.append((name, t, f))

    parameter_types = make_dataclass(cls_name="Preferences", fields=members, bases=(PreferenceBase,))
    return parameter_types


def __fix_input_name(s: str):
    return re.sub('\W|^(?=\d)', '_', s)


def _extract_input_types_from_data(data: list[Union[ParameterData, PreferenceData]], production_methods: list[str]):
    parameter_data: list[ParameterData] = []
    preference_data: list[PreferenceData] = []
    for d in data:
        selected_methods = d.production_method
        # if "ALL" is specified, use all available production_methods
        if "ALL" in selected_methods:
            d.production_method = production_methods

        # group by production method
        # for pm in selected_methods:
        if isinstance(d, ParameterData):
            parameter_data.append(d)
        else:
            preference_data.append(d)

    return parameter_data, preference_data
