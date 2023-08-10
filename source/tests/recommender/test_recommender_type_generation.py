from dataclasses import fields
from typing import Union

import pytest

from recommender.importer.processor import extract_global_data, _extract_input_types_from_data, \
    _generate_input_types_parameters, _generate_input_types_preferences
from recommender.importer.typedef import ParameterData, PreferenceData
from recommender.preferences.preferenceTypes import RangePreference
from recommender.typedefs.typedef import ComparisonType


@pytest.fixture
def _generate_input_data():
    return [
        ParameterData(production_method=["A"], category="ABC", full_name="long", name="param_1", type_demand=bool,
                      type_supplier=bool,
                      comparison_type=ComparisonType.EXACT_MATCH),
        ParameterData(production_method=["B"], category="HIJ", full_name="long", name="param_2", type_demand=int,
                      type_supplier=list[int],
                      comparison_type=ComparisonType.IS_IN),
        ParameterData(production_method=["B", "C"], category="ABC", full_name="long", name="param_3",
                      type_demand=list[int], type_supplier=list[int],
                      comparison_type=ComparisonType.EXACT_MATCH),
        ParameterData(production_method=["A", "C"], category="ABC", full_name="long", name="param_4", type_demand=bool,
                      type_supplier=bool,
                      comparison_type=ComparisonType.INCLUSIVE),
        ParameterData(production_method=["ALL"], category="ABC", full_name="long", name="param_5", type_demand=bool,
                      type_supplier=bool, comparison_type=ComparisonType.INCLUSIVE),
        PreferenceData(production_method=["A", "D"], category="ABC", full_name="long", name="pref_1",
                       preference_type="RangePreference",
                       type_supplier=float, type_demand=float, comparison_type=None, depends_on=None,
                       dominant_parent=None),
        PreferenceData(production_method=["A", "D"], category="XYZ", full_name="long", name="pref_2",
                       preference_type="RangePreference",
                       type_supplier=float, type_demand=float, comparison_type=None, depends_on=None,
                       dominant_parent=None),
        PreferenceData(production_method=["A", "F"], category="XYZ", full_name="long", name="pref_3",
                       preference_type="RangePreference",
                       type_supplier=float, type_demand=float, comparison_type=None, depends_on=None,
                       dominant_parent=None),
        PreferenceData(production_method=["F", "D"], category="ABC", full_name="long", name="pref_4",
                       preference_type="RangePreference",
                       type_supplier=float, type_demand=float, comparison_type=None, depends_on=None,
                       dominant_parent=None),
        PreferenceData(production_method=["A", "D", "F"], category="EFG", full_name="long", name="pref_5",
                       preference_type="RangePreference",
                       type_supplier=float, type_demand=float, comparison_type=None, depends_on=None,
                       dominant_parent=None)
    ]


@pytest.fixture
def _generate_preference_data(_generate_input_data):
    _, production_methods = extract_global_data(_generate_input_data)
    _, preference_data = _extract_input_types_from_data(_generate_input_data, production_methods)
    return preference_data


@pytest.fixture
def _generate_parameter_data(_generate_input_data):
    _, production_methods = extract_global_data(_generate_input_data)
    parameter_data, _ = _extract_input_types_from_data(_generate_input_data, production_methods)
    return parameter_data


def __pd_for_pm(pd: Union[list[ParameterData], list[PreferenceData]], pm: str):
    return [p for p in pd if pm in p.production_method]


def __pmd_for_pm(pmd, pm: str):
    return [p for p in fields(pmd) if pm in getattr(pmd, p.name).production_method]


def test_importer_processor_generate_production_type(_generate_input_data):
    _, production_methods = extract_global_data(_generate_input_data)

    assert "A" in production_methods
    assert "B" in production_methods
    assert "C" in production_methods
    assert "D" in production_methods
    assert "F" in production_methods
    assert "ALL" not in production_methods
    assert "GENERIC" not in production_methods


def test_importer_processor_generate_categories(_generate_input_data):
    categories, _ = extract_global_data(_generate_input_data)

    assert "ABC" in categories
    assert "XYZ" in categories
    assert "EFG" in categories
    assert "HIJ" in categories


def test_importer_processor_extract_input_types(_generate_input_data):
    _, production_methods = extract_global_data(_generate_input_data)

    parameter_data, preference_data = _extract_input_types_from_data(_generate_input_data, production_methods)

    assert len(parameter_data) + len(preference_data) == len(_generate_input_data)
    assert len(__pd_for_pm(parameter_data, "A")) == 3
    assert len(__pd_for_pm(parameter_data, "B")) == 3
    assert len(__pd_for_pm(parameter_data, "C")) == 3
    assert len(__pd_for_pm(parameter_data, "F")) == 1
    assert len(__pd_for_pm(parameter_data, "D")) == 1

    assert len(__pd_for_pm(preference_data, "A")) == 4
    assert len(__pd_for_pm(preference_data, "B")) == 0
    assert len(__pd_for_pm(preference_data, "D")) == 4
    assert len(__pd_for_pm(preference_data, "F")) == 3


def test_importer_processor_generate_parameter_metadata(_generate_parameter_data):
    param_metadata = _generate_input_types_parameters(_generate_parameter_data)

    assert len(__pmd_for_pm(param_metadata, "A")) == 3
    assert len(__pmd_for_pm(param_metadata, "B")) == 3
    assert len(__pmd_for_pm(param_metadata, "C")) == 3
    assert len(__pmd_for_pm(param_metadata, "F")) == 1
    assert len(__pmd_for_pm(param_metadata, "D")) == 1

    assert getattr(param_metadata, "param_2").demand_type == int
    assert getattr(param_metadata, "param_2").supplier_type == list[int]
    assert getattr(param_metadata, "param_2").comparison == ComparisonType.IS_IN


def test_importer_processor_generate_preference_metadata(_generate_preference_data):
    pref_metadata = _generate_input_types_preferences(_generate_preference_data)

    assert len(__pmd_for_pm(pref_metadata, "A")) == 4
    assert len(__pmd_for_pm(pref_metadata, "B")) == 0
    assert len(__pmd_for_pm(pref_metadata, "D")) == 4
    assert len(__pmd_for_pm(pref_metadata, "F")) == 3

    assert isinstance(getattr(pref_metadata, "pref_2").preference_type, RangePreference)
