import csv
import os
from keyword import iskeyword
from pathlib import Path
from typing import Optional, Union

from recommender.importer.typedef import __POSSIBLE_PARAM_TYPES, __POSSIBLE_PREF_TYPES, __POSSIBLE_PREF_TYPE_TYPES, \
    __PARAMETER_TYPE_TAG, __OTHER_TYPE_TAG, __POSSIBLE_DOMINANT_PARENT_VALUES, __POSSIBLE_COMPARISON_TYPE_VALUES, \
    CsvIdx, RawPreferenceData, RawParameterData, REQIRED_CSV_COLUMNS
from recommender.typedefs.typedef import ComparisonType, DominantParent


def read_csv(path: Optional[str] = None, sep: str = ",") -> tuple[
    list[Union[RawParameterData, RawPreferenceData]], dict[str, list[str]]]:
    # if no path is given, use the default file
    if path is None:
        source_path = Path(__file__).resolve()
        source_dir = source_path.parent
        source_name = "RecommenderTypes.csv"
        path = os.path.join(source_dir, source_name)

    # open csv file
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=sep)

        data, errors = extract_data_from_reader(reader)

    return data, errors


def extract_data_from_reader(reader) -> tuple[list[Union[RawParameterData, RawPreferenceData]], dict[str, list[str]]]:
    errors: dict[str, list[str]] = {}
    data: list[Union[RawParameterData, RawPreferenceData]] = []

    # ignore header
    header = next(reader)
    if len(header) < REQIRED_CSV_COLUMNS:
        raise RuntimeError(f"Severe CSV error, got {len(header)} columns, but {REQIRED_CSV_COLUMNS} are required.")

    for row in reader:
        single_data, error = _extract_data_from_row(row)

        # if it's a no_type, skip. If an sever error occurred, then report it and then skip
        if single_data is None:
            if len(error) != 0:
                errors[row[CsvIdx.field_name]] = error
            continue

        name = single_data.name

        # if name was already used, add an error and skip this entry
        if name in errors.keys():
            errors[name].append(f"Fieldname [EN] '{name}' is already used, select a different name.")
            continue

        error = [e for e in error]

        errors[name] = error
        if len(error) == 0:
            data.append(single_data)

    return data, errors


def _extract_data_from_row(row: list[str]) -> tuple[Union[RawPreferenceData, RawParameterData, None], list[str]]:
    errors = []
    full_name = read_entity(row[CsvIdx.full_name])
    name = read_entity(row[CsvIdx.field_name])
    comp_type_str = read_entity(row[CsvIdx.comparison_type]).lower()
    production_method = read_entity(row[CsvIdx.production_method])
    category = read_entity(row[CsvIdx.category])
    depends_on = read_entity(row[CsvIdx.depends_on])
    dominant_parent_str = read_entity(row[CsvIdx.dominant_parent])
    type_supplier = read_entity(row[CsvIdx.data_type_supplier])
    type_demand = read_entity(row[CsvIdx.data_type_demand])
    data_type = read_entity(row[CsvIdx.type])

    is_pref = data_type in __POSSIBLE_PREF_TYPE_TYPES
    is_param = data_type == __PARAMETER_TYPE_TAG
    is_other = data_type == __OTHER_TYPE_TAG

    if not is_pref and not is_param and not is_other:
        errors.append(
            f"Recommender type '{data_type}' 'for fieldname [EN] '{name}' is whether a preference ({__POSSIBLE_PREF_TYPE_TYPES}), parameter ({[__PARAMETER_TYPE_TAG]}) or 'no type' ({[__OTHER_TYPE_TAG]}).")
        return None, errors

    # is its a no_type, then ignore it
    if is_other:
        return None, []

    if not name.isidentifier() or iskeyword(name):
        errors.append(f"Fieldname [EN] '{name}' is not a valid python identifier. Choose a different name.")

    if dominant_parent_str not in __POSSIBLE_DOMINANT_PARENT_VALUES:
        errors.append(
            f"Unknown dominant_parent value '{dominant_parent_str}', expected one of {__POSSIBLE_DOMINANT_PARENT_VALUES}.")
        dominant_parent_str = ""

    if comp_type_str not in __POSSIBLE_COMPARISON_TYPE_VALUES:
        errors.append(
            f"Unknown comparison_type value '{comp_type_str}', expected one of {__POSSIBLE_COMPARISON_TYPE_VALUES}.")
        comp_type_str = ""

    type_set = __POSSIBLE_PREF_TYPES if is_pref else __POSSIBLE_PARAM_TYPES

    type_demand = [t.strip() for t in type_demand.split(",")]
    type_supplier = [t.strip() for t in type_supplier.split(",")]
    for ds, types in zip(("demand", "supplier"), (type_demand, type_supplier)):
        for t in types:
            if t == "":
                errors.append(f"No {ds} datatype given, expected one of {type_set}.")
            elif t not in type_set:
                errors.append(f"Unsupported {ds} datatype '{t}', expected one of {type_set}.")

    comp_type = None if comp_type_str == "" else ComparisonType(comp_type_str)

    production_method = [pm.strip() for pm in production_method.split(",")]

    if is_pref:
        dominant_parent = None if dominant_parent_str == "" else DominantParent(dominant_parent_str)

        return RawPreferenceData(full_name=full_name, name=name, production_method=production_method,
                                 category=category, depends_on=depends_on, dominant_parent=dominant_parent,
                                 type_supplier=type_supplier, type_demand=type_demand,
                                 comparison_type=comp_type, preference_type=data_type), errors
    if is_param:
        return RawParameterData(full_name=full_name, name=name, production_method=production_method,
                                type_supplier=type_supplier, type_demand=type_demand,
                                comparison_type=comp_type, category=category), errors


def read_entity(input_string: str) -> str:
    raw_input = input_string.strip()
    if raw_input == "-":
        return ""
    return raw_input
