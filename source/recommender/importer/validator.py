from typing import Union, get_origin, get_args

from recommender.importer.typedef import ParameterData, PreferenceData
from recommender.parameters.parameterTypes import GenericTypes, supported_parameter_type_combinations_cmp_type
from recommender.preferences.preferenceTypes import supported_preference_type_combinations_pref_type, \
    PreferenceTypeCombination
from recommender.utils import convert_type_to_input_str as to_str


def validation_read_data(data: list[Union[ParameterData, PreferenceData]]):
    invalid_entries, errors = _global_validation_read_data(data)

    for d in data:
        if isinstance(d, ParameterData):
            valid, error = _validation_read_parameter_data(d)
        else:
            valid, error = _validation_read_preference_data(d)

        if d.name in errors.keys():
            errors[d.name] += error
        else:
            errors[d.name] = error

        if not valid:
            invalid_entries.append(d.name)

    return list(set(invalid_entries)), errors


def _global_validation_read_data(data: list[Union[ParameterData, PreferenceData]]) -> tuple[
    list[str], dict[str, list[str]]]:
    invalid: list[str] = []
    cycle_ignore_list: list[str] = []
    data_dict: dict[str, Union[ParameterData, PreferenceData]] = {d.name: d for d in data}
    preference_dict: dict[str, PreferenceData] = {d.name: d for d in data if isinstance(d, PreferenceData)}
    parameter_dict: dict[str, PreferenceData] = {d.name: d for d in data if isinstance(d, ParameterData)}
    errors: dict[str, list[str]] = {n: [] for n in data_dict.keys()}

    for name, d in data_dict.items():
        # check valid production method
        if len(d.production_method) == 0:
            errors[name].append(f"Production method for preference/parameter '{name}' is not defined.")

        # check valid category for parameter and preferences
        if d.category == "":
            errors[name].append(f"Category for preference/parameter '{name}' is not defined.")

    for name, d in preference_dict.items():
        # check valid depends_on
        if d.depends_on is not None:
            if d.depends_on == name:
                errors[name].append(f"Preference '{name}' depends on itself.")
            elif d.depends_on in parameter_dict.keys():
                errors[name].append(f"Preference '{name}' depends on parameter '{d.depends_on}', select a preference.")
            elif len(d.depends_on.split(',')) > 1:
                errors[name].append(
                    f"Preference '{name}' depends on several preferences ({d.depends_on.split(',')}), only a single prefernce is allowed.")
            elif d.depends_on not in data_dict.keys():
                errors[name].append(f"Preference '{name}' refers to '{d.depends_on}', which does not exist.")
            elif d.depends_on in preference_dict.keys() and not set(d.production_method).issubset(
                    set(preference_dict[d.depends_on].production_method)):
                errors[name].append(
                    f"Production methods {d.production_method} are not contained in production methods {preference_dict[d.depends_on].production_method} of parent constraint {d.depends_on}")

            # don't consider this name for cycle dependence because is anyway invalid
            if len(errors[name]) > 0:
                cycle_ignore_list.append(name)

    # detect cycles
    invalid += _detect_cycles(data_dict, preference_dict, cycle_ignore_list, errors)

    # update invalid entries
    for name in errors.keys():
        if len(errors[name]) > 0:
            invalid.append(name)

    # remove duplicates
    return list(set(invalid)), errors


def _detect_cycles(data_dict: dict[str, Union[ParameterData, PreferenceData]],
                   preference_dict: dict[str, PreferenceData], cycle_ignore_list: list[str],
                   errors: dict[str, list[str]]) -> list[str]:
    visited: dict[str, bool] = {name: False for name in preference_dict.keys()}
    invalid: list[str] = []
    for name, d in preference_dict.items():
        current = name
        current_data = d
        cycle = []
        if visited[current] or name in cycle_ignore_list:
            continue

        while True:

            # cycle detected, the current element has already appeared
            if current in cycle:
                first_appearance = cycle.index(current)
                s_cycle = cycle[first_appearance:]
                for n in s_cycle:
                    errors[n].append(
                        f"Detected depends_on cycle for preference '{n}' with dependency chain '{cycle}'. Smallest cycle is: '{s_cycle + [current]}'.")
                    invalid.append(n)
                break

            # update visited elements
            cycle.append(current)
            visited[current] = True

            # base case, element does not have a parent element. Root of the tree
            if current_data.depends_on is None:
                break

            # update current data
            current = current_data.depends_on
            current_data = data_dict.get(current)

            # if we hit an item, which should be ignored stop.
            if current in cycle_ignore_list:
                break

    return invalid


def _validation_read_parameter_data(d: ParameterData) -> tuple[bool, list[str]]:
    error: list[str] = []

    if d.comparison_type is None:
        error.append(f"Parameter '{d.name}' does not have a comparison_type defined.")
        return False, error

    type_combinations = supported_parameter_type_combinations_cmp_type[d.comparison_type]

    # check of d is contained in type_combinations
    tc_comparison = [tc.demand_type == d.type_demand and tc.supplier_type == d.type_supplier for tc in
                     type_combinations]
    if sum(tc_comparison) > 1:
        multiple_elements = [tc for b, tc in zip(tc_comparison, type_combinations) if b]
        error.append(f"Multiple types for '{d.name}' combination with type_combinations '{multiple_elements}'.")
    found = any(tc_comparison)

    if not found:
        # error handling
        if d.type_supplier == d.type_demand:
            error.append(
                f"Demand and supplier type '{to_str(d.type_demand)}' is not supported by comparison_type '{d.comparison_type}'.")
        else:
            base_d, origin_d = __extract_origin_base(d.type_demand)
            base_s, origin_s = __extract_origin_base(d.type_supplier)

            if base_d != base_s:
                solution = "Demand and supplier type need to be based on the same type."
            else:
                solution = f"Choose a different comparison type or select appropriate types."

            if origin_s is None and origin_d is None:
                error.append(
                    f"Demand base type '{to_str(base_d)}' and Supplier base type '{to_str(base_s)}' missmatch and/or are not supported by '{d.comparison_type}'. " + solution)
            elif origin_s is None or origin_d is None:
                error.append(
                    f"Combination of Demand type '{to_str(d.type_demand)}' and Supplier type '{to_str(d.type_supplier)}' is not supported by '{d.comparison_type}'. " + solution)
            else:
                error.append(
                    f"Demand type '{to_str(d.type_demand)}' and Supplier type '{to_str(d.type_supplier)}' missmatch. " + solution)

    return len(error) == 0, error


def __extract_origin_base(t):
    if any([get_origin(t) == g for g in GenericTypes]):
        origin = get_origin(t)
        base = get_args(t)[0]
    else:
        base = t
        origin = None
    return base, origin


def _validation_read_preference_data(d: PreferenceData) -> tuple[bool, list[str]]:
    error: list[str] = []

    # check if depends_on and dominant_parent is set
    if d.depends_on is not None and d.dominant_parent is None:
        error.append(
            f"Preference '{d.name}' has a dependency on preference '{d.depends_on}' but no dominant_parent is defined.")

    type_combinations: list[PreferenceTypeCombination] = supported_preference_type_combinations_pref_type[
        d.preference_type]
    # check of d is contained in type_combinations
    tc_comparison = [tc.demand_type == d.type_demand and tc.supplier_type == d.type_supplier and (
                tc.comparison_type is None or tc.comparison_type == d.comparison_type) for tc in type_combinations]
    if sum(tc_comparison) > 1:
        multiple_elements = [tc for b, tc in zip(tc_comparison, type_combinations) if b]
        error.append(f"Multiple types for {d.name} combination with type_combinations {multiple_elements}.")
    found = any(tc_comparison)

    if not found:
        # check if comparison_type fit to preference_type
        cts = set([tc.get_comp_type_value() for tc in type_combinations])
        if d.comparison_type is None and all([ct is not None for ct in cts]):
            error.append(
                f"Preference type '{d.print_pref_type()}' requires a comparison_type, none supplied. Must be one of {cts}. ")

        if d.comparison_type is not None and all([ct != d.comparison_type.value for ct in cts]):
            error.append(
                f"Missmatch of specified comparison type '{d.comparison_type.value}' for preference type '{d.print_pref_type()}', must be one of {cts}.")

        # check if types fit to preference_type
        possible_type_combinations = set([(tc.demand_type, tc.supplier_type) for tc in type_combinations])

        if (d.type_demand, d.type_supplier) not in possible_type_combinations:
            error.append(
                f"The specified demand-supplier type combination '{(to_str(d.type_demand), to_str(d.type_supplier))}' is not supported for preference type '{d.print_pref_type()}'. Possible combinations are {set((to_str(t1), to_str(t2)) for t1, t2 in possible_type_combinations)}.")

    return len(error) == 0, error
