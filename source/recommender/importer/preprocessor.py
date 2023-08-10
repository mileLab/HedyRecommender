from types import GenericAlias
from typing import Union, Optional, Type

from common.typedef import Range
from recommender.importer.typedef import RawParameterData, RawPreferenceData, PreferenceData, ParameterData

__container_types = ['list', 'range']
__primitive_types = ['int', 'float', 'bool', 'str']

__primitive_str_to_type: dict[str, Type] = {'int': int, 'float': float, 'bool': bool, 'str': str}
__container_str_to_type: dict[str, Type] = {'list': list, 'range': Range}


def preprocess_parsed_data(data: list[Union[RawParameterData, RawPreferenceData]]) -> tuple[
    list[Union[ParameterData, PreferenceData]], dict[str, list[str]]]:
    errors: dict[str, list[str]] = {}
    processed_data: list[Union[ParameterData, PreferenceData]] = []
    for d in data:

        errors[d.name] = []
        # clean up production method
        if "" in d.production_method:
            d.production_method.remove("")

        # transform strings to types
        type_demand, error = combine_string_types(d.type_demand)
        errors[d.name] += ["Demand type: " + e for e in error]
        type_supplier, error = combine_string_types(d.type_supplier)
        errors[d.name] += ["Supplier type: " + e for e in error]

        # if failure
        if type_demand is None or type_supplier is None:
            continue

        # generate processed data
        if isinstance(d, RawParameterData):
            processed_data.append(
                ParameterData(full_name=d.full_name, name=d.name, production_method=d.production_method,
                              type_supplier=type_supplier, type_demand=type_demand, comparison_type=d.comparison_type,
                              category=d.category))
        else:

            # set depends on to None instead to empty string
            depends_on = d.depends_on if d.depends_on != "" else None

            # deal with SingleChoicePreferenceOrdered
            preference_type = d.preference_type
            ordered = False
            if "Ordered" in d.preference_type:
                preference_type = d.preference_type.replace("Ordered", "")
                ordered = True

            # append data
            processed_data.append(
                PreferenceData(full_name=d.full_name, name=d.name, production_method=d.production_method,
                               type_supplier=type_supplier, type_demand=type_demand, comparison_type=d.comparison_type,
                               category=d.category, depends_on=depends_on, preference_type=preference_type,
                               dominant_parent=d.dominant_parent, ordered=ordered))

    return processed_data, errors


def combine_string_types(types: list[str]) -> tuple[Optional[Union[Type, GenericAlias]], list[str]]:
    errors: list[str] = []
    if len(types) == 0:
        errors.append("No type specified")
        return None, errors
    if len(types) > 2:
        errors.append(f"Too many types specified ({len(types)}), maximum is 2.")
        return None, errors

    if len(types) == 1:
        t = types[0]
        if t in __container_types:
            errors.append(
                f"Only the container type '{t}' is specified, an additional base type is required. One of {__primitive_types}")
            return None, errors
        return _generate_base_type_from_string(t), errors

    if len(types) == 2:
        t1, t2 = types[0], types[1]

        if t1 in __container_types and t2 in __container_types:
            errors.append(
                f"Both specified types '{t1}' and '{t2}' cannot be container types. One of them must be in {__primitive_types}")
            return None, errors

        if t1 in __primitive_types and t2 in __primitive_types:
            errors.append(
                f"Both specified types '{t1}' and '{t2}' cannot be base types. One of them must be in {__container_types}")
            return None, errors

        container = list(set(types) & set(__container_types))
        if len(container) == 0:
            errors.append(
                f"At least one of the specified types '{t1}' and '{t2}' must be a container type. One of {__container_types}")
            return None, errors
        container = container[0]

        base = list(set(types) & set(__primitive_types))
        if len(base) == 0:
            errors.append(
                f"At least one of the specified types '{t1}' and '{t2}' must be a base type. One of {__primitive_types}")
            return None, errors

        base = base[0]

        # f"{container}[{base}]"

        return _generate_container_type_from_strings(base, container), errors


def _generate_container_type_from_strings(base: str, container: str) -> GenericAlias:
    base_type = __primitive_str_to_type[base]
    container_type = __container_str_to_type[container]

    return container_type[base_type]


def _generate_base_type_from_string(base: str) -> Type:
    return __primitive_str_to_type[base]
