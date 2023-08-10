from _csv import reader
from io import StringIO

import pytest

from common.typedef import Range
from recommender.importer.preprocessor import preprocess_parsed_data
from recommender.importer.reader import _extract_data_from_row, extract_data_from_reader
from recommender.importer.typedef import CsvIdx, RawParameterData, RawPreferenceData, PreferenceData, ParameterData, \
    __POSSIBLE_PREF_TYPE_TYPES
from recommender.importer.validator import validation_read_data
from recommender.parameters.parameterTypes import supported_parameter_type_combinations
from recommender.preferences.preferenceTypes import supported_preference_type_combinations
from recommender.typedefs.typedef import ComparisonType, DominantParent
from recommender.utils import convert_type_to_input_str


def generate_csv_row(full_name="", name="", comp_type="", production_method="", category="", depends_on="",
                     dominant_parent="", type_demand="", type_supplier="", data_type=""):
    n = max([i.value for i in CsvIdx]) + 1
    row = [""] * n
    row[CsvIdx.full_name] = full_name
    row[CsvIdx.field_name] = name
    row[CsvIdx.comparison_type] = comp_type
    row[CsvIdx.production_method] = production_method
    row[CsvIdx.category] = category
    row[CsvIdx.depends_on] = depends_on
    row[CsvIdx.dominant_parent] = dominant_parent
    row[CsvIdx.data_type_demand] = type_demand
    row[CsvIdx.data_type_supplier] = type_supplier
    row[CsvIdx.type] = data_type
    return row


@pytest.mark.parametrize('td', ['int', 'float', 'str', 'list', 'bool', 'range'])
def test_importer_extract_row_parameter(td):
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           depends_on="other_name", dominant_parent="Both", type_demand=td, type_supplier="list , str",
                           data_type="Parameter")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 0

    assert data.name == "short"
    assert data.full_name == "Long name"
    assert data.production_method == ["ALL"]
    assert data.comparison_type == ComparisonType.IS_IN
    assert data.type_demand == [td]
    assert data.type_supplier == ["list", "str"]


def test_importer_extract_row_no_type():
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           depends_on="other_name", dominant_parent="Both", type_demand="int", type_supplier="int",
                           data_type='NoType')
    data, errors = _extract_data_from_row(row)

    assert data is None
    assert len(errors) == 0


@pytest.mark.parametrize('td', ['int', 'float', 'list', 'bool', 'range'])
def test_importer_extract_row_preference(td):
    row = generate_csv_row(full_name="Long name ", name="short ", comp_type=" IS_IN", production_method=" ALL",
                           depends_on="other_name ", dominant_parent="Both", type_demand=td,
                           type_supplier="list , bool ",
                           data_type=" SingleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    assert data.name == "short"
    assert data.full_name == "Long name"
    assert data.production_method == ["ALL"]
    assert data.comparison_type == ComparisonType.IS_IN
    assert data.type_demand == [td]
    assert data.type_supplier == ["list", "bool"]
    assert data.dominant_parent == DominantParent.BOTH
    assert data.preference_type == "SingleChoicePreference"
    assert data.category == "cat"
    assert data.depends_on == "other_name"


@pytest.mark.parametrize('data_type', __POSSIBLE_PREF_TYPE_TYPES)
def test_importer_extract_row_preference_dt(data_type):
    row = generate_csv_row(full_name="Long name ", name="short ", comp_type=" IS_IN", production_method=" ALL",
                           depends_on="other_name ", dominant_parent="Both", type_demand="bool",
                           type_supplier="list , bool ",
                           data_type=data_type, category="cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    assert data.name == "short"
    assert data.full_name == "Long name"
    assert data.production_method == ["ALL"]
    assert data.comparison_type == ComparisonType.IS_IN
    assert data.type_demand == ["bool"]
    assert data.type_supplier == ["list", "bool"]
    assert data.dominant_parent == DominantParent.BOTH
    assert data.preference_type == data_type
    assert data.category == "cat"
    assert data.depends_on == "other_name"


def test_importer_extract_dominant_parent_none():
    row = generate_csv_row(full_name="Long name ", name="short ", comp_type=" IS_IN", production_method=" ALL",
                           depends_on="other_name ", dominant_parent="", type_demand="bool",
                           type_supplier="list , bool ",
                           data_type=" SingleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0
    assert data.dominant_parent is None


def test_importer_extract_comp_type_none():
    row = generate_csv_row(full_name="Long name ", name="short ", comp_type="", production_method=" ALL",
                           depends_on="other_name ", dominant_parent="Supplier", type_demand="bool",
                           type_supplier="list , bool ",
                           data_type=" SingleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0
    assert data.comparison_type is None


def test_importer_extract_production_method():
    row = generate_csv_row(full_name="Long name ", name="short ", comp_type="",
                           production_method="Some,Some_other  ,more ",
                           depends_on="other_name ", dominant_parent="Supplier", type_demand="bool",
                           type_supplier="list , bool ",
                           data_type=" SingleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0
    assert len(data.production_method) == 3
    assert data.production_method == ["Some", "Some_other", "more"]


@pytest.mark.parametrize('invalid_name', ['1name', 'def', 'na me', 'id!', "in", "for", "name*name"])
def test_importer_extract_row_error_name(invalid_name):
    row = generate_csv_row(full_name="Long name", name=invalid_name, comp_type="IS_IN", production_method="ALL",
                           depends_on="other_name", dominant_parent="Both", type_demand="str", type_supplier="str",
                           data_type="Parameter")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 1
    assert invalid_name in errors[0]


def test_importer_extract_row_error_comp_type():
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_OUT", production_method="ALL",
                           depends_on="other_name", dominant_parent="Both", type_demand="str", type_supplier="str",
                           data_type="Parameter")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 1
    assert "Unknown comparison_type" in errors[0]
    assert "is_out" in errors[0]


def test_importer_extract_row_error_dominant_parent():
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           depends_on="other_name", dominant_parent="Some", type_demand="str", type_supplier="str",
                           data_type="Parameter")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 1
    assert "Unknown dominant_parent" in errors[0]
    assert "Some" in errors[0]


@pytest.mark.parametrize('invalid_type', ['long', 'list[str]', 'Range', 'range[int]', "double", "str", "list[int]"])
def test_importer_extract_row_error_preference_type(invalid_type):
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           depends_on="other_name", dominant_parent="Both", type_demand=invalid_type,
                           type_supplier="int",
                           data_type="RangePreference")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 1
    assert "Unsupported demand datatype" in errors[0]
    assert invalid_type in errors[0]


@pytest.mark.parametrize('invalid_type', ['long', 'list[str]', 'Range', 'range[int]', "double", "list[int]"])
def test_importer_extract_row_error_parameter_type(invalid_type):
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           depends_on="other_name", dominant_parent="Both", type_demand=invalid_type,
                           type_supplier="int",
                           data_type="RangePreference")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 1
    assert "Unsupported demand datatype" in errors[0]
    assert invalid_type in errors[0]


@pytest.mark.parametrize('invalid_type', ['Preference', 'NewType', "SingleChoicePreferencesOrdered"])
def test_importer_extract_row_error_data_type(invalid_type):
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           depends_on="other_name", dominant_parent="Both", type_demand="int", type_supplier="int",
                           data_type=invalid_type)
    data, errors = _extract_data_from_row(row)

    assert data is None
    assert len(errors) == 1
    assert "Recommender type" in errors[0]
    assert "short" in errors[0]


def test_import_csv_data():
    in_mem_csv = StringIO("""\
Frontend Supply,"Fertigungsmethode, für relevant",classes,Sub classes (#),Feldname [EN],ComparisonType,Datentyp Python Demand,Datentyp Python Supply,Recommender Typ,Abhängigkeiten zu anderen Preferences,Dominant Parent
...?,ALL,class SustanabilityProfile,TECHNOLOGY,environmental_tech,IS_IN,"list,bool","list,bool",SingleChoicePreferenceOrdered,-,-
Garantierte Standzeit/Zyklen,CUTTING,class ToolConstructionInjectionMolding,TOOLING_MOLDING_GENERELL,guaranteed_service,IS_IN,int,"int,range",Parameter,-,-
min. max. Bauteilhöhe [mm],ALL,class GeneralOrderParameters,GENRELL_PRODUCT_PARAMETER,width,IS_IN,float,"range,float",Parameter,-,-""")

    r = reader(in_mem_csv, delimiter=',')

    data, errors = extract_data_from_reader(r)

    assert errors["environmental_tech"] == []
    assert errors["guaranteed_service"] == []
    assert errors["width"] == []
    assert len(data) == 3


def test_import_csv_data_error_unique_name():
    in_mem_csv = StringIO("""\
Frontend Supply,"Fertigungsmethode, für relevant",classes,Sub classes (#),Feldname [EN],ComparisonType,Datentyp Python Demand,Datentyp Python Supply,Recommender Typ,Abhängigkeiten zu anderen Preferences,Dominant Parent
...?,ALL,class SustanabilityProfile,TECHNOLOGY,environmental_tech,IS_IN,"list,bool","list,bool",SingleChoicePreferenceOrdered,-,-
Garantierte Standzeit/Zyklen,CUTTING,class ToolConstructionInjectionMolding,TOOLING_MOLDING_GENERELL,guaranteed_service,IS_IN,int,"int,range",Parameter,-,-
min. max. Bauteilhöhe [mm],ALL,class GeneralOrderParameters,GENRELL_PRODUCT_PARAMETER,guaranteed_service,IS_IN,float,"range,float",Parameter,-,-""")

    r = reader(in_mem_csv, delimiter=',')

    data, errors = extract_data_from_reader(r)

    assert len(errors['guaranteed_service']) == 1
    assert "is already used" in errors['guaranteed_service'][0]
    assert 'guaranteed_service' in errors['guaranteed_service'][0]
    assert len(data) == 2


@pytest.mark.parametrize('demand_t,expected',
                         [('str', str), ('bool', bool), ('int', int), ('float', float), ('range,int', Range[int]),
                          ('range,float', Range[float]), ('float,range', Range[float]), ('list,str', list[str]),
                          ('bool,list', list[bool])])
def test_importer_preprocess_types(demand_t, expected):
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           type_demand=demand_t, type_supplier="int", data_type="Parameter")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], ParameterData)
    assert len(processing_errors['short']) == 0

    assert processed_data[0].type_demand == expected


@pytest.mark.parametrize('demand_t,err_str',
                         [('str,str', "cannot be base types"), ('range,list', "cannot be container types"),
                          ('list', "additional base type"), ('range', "additional base type"),
                          ('str,str,str', "maximum is 2")])
def test_importer_preprocess_types_failures(demand_t, err_str):
    row = generate_csv_row(full_name="Long name", name="short", comp_type="IS_IN", production_method="ALL",
                           type_demand=demand_t, type_supplier="int", data_type="Parameter")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert len(processed_data) == 0
    assert len(processing_errors['short']) == 1
    assert "Demand type:" in processing_errors['short'][0]
    assert err_str in processing_errors['short'][0]


@pytest.mark.parametrize('expected,t',
                         [('str', str), ('bool', bool), ('int', int), ('float', float), ('range,int', Range[int]),
                          ('range,float', Range[float]), ('range,float', Range[float]), ('list,str', list[str]),
                          ('list,bool', list[bool])])
def test_importer_test_type_conversion(expected, t):
    result = convert_type_to_input_str(t)
    assert result == expected


@pytest.mark.parametrize('demand_t,supplier_t,comp_t',
                         [('str', "list,str", "IS_IN"), ('float', 'range,float', 'IS_IN'), ('bool', 'bool', 'EXACT')])
def test_importer_validation_parameters(demand_t, supplier_t, comp_t):
    row = generate_csv_row(full_name="Long name", name="short", comp_type=comp_t, production_method="ALL",
                           type_demand=demand_t, type_supplier=supplier_t, data_type="Parameter", category="ABC")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], ParameterData)
    assert len(processing_errors['short']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['short']) == 0
    assert len(invalid_data) == 0


__POSSIBLE_PARAMETER_COMBINATIONS = [(convert_type_to_input_str(tc.demand_type),
                                      convert_type_to_input_str(tc.supplier_type),
                                      tc.comparison_type.value) for tc in supported_parameter_type_combinations]


@pytest.mark.parametrize('demand_t,supplier_t,comp_t', __POSSIBLE_PARAMETER_COMBINATIONS)
def test_importer_validation_parameters_all(demand_t, supplier_t, comp_t):
    row = generate_csv_row(full_name="Long name", name="short", comp_type=comp_t, production_method="ALL",
                           type_demand=demand_t, type_supplier=supplier_t, data_type="Parameter", category="ABC")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], ParameterData)
    assert len(processing_errors['short']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['short']) == 0
    assert len(invalid_data) == 0


@pytest.mark.parametrize('demand_t,supplier_t,comp_t,pref_type',
                         [('float', "float", "", "RangePreference"),
                          ('list,bool', 'list,bool', 'EXACT', 'MultipleChoicePreference'),
                          ('int', 'range,int', 'EXACT', 'ZonePreference'),
                          ('list, bool', 'list, bool', '', 'SingleChoicePreferenceOrdered')])
def test_importer_validation_preferences(demand_t, supplier_t, comp_t, pref_type):
    row = generate_csv_row(full_name="Long name", name="short", comp_type=comp_t, production_method="ALL",
                           type_demand=demand_t, type_supplier=supplier_t, data_type=pref_type, category="cat",
                           depends_on="")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['short']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['short']) == 0
    assert len(invalid_data) == 0


__POSSIBLE_PREFERENCE_COMBINATIONS = [(convert_type_to_input_str(tc.demand_type),
                                       convert_type_to_input_str(tc.supplier_type),
                                       "" if (tc.comparison_type is None) else tc.comparison_type.value,
                                       tc.preference_type) for tc in supported_preference_type_combinations]


@pytest.mark.parametrize('demand_t,supplier_t,comp_t,pref_type', __POSSIBLE_PREFERENCE_COMBINATIONS)
def test_importer_validation_preferences_all(demand_t, supplier_t, comp_t, pref_type):
    row = generate_csv_row(full_name="Long name", name="short", comp_type=comp_t, production_method="ALL",
                           type_demand=demand_t, type_supplier=supplier_t, data_type=pref_type, category="my_cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['short']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['short']) == 0
    assert len(invalid_data) == 0


def test_importer_validation_preferences_ordered():
    row = generate_csv_row(full_name="Long name", name="short", comp_type="", production_method="ALL",
                           type_demand="list,bool", type_supplier="list,bool",
                           data_type="SingleChoicePreferenceOrdered", category="my_cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['short']) == 0
    assert processed_data[0].preference_type == "SingleChoicePreference"
    assert processed_data[0].ordered == True

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['short']) == 0
    assert len(invalid_data) == 0


def test_importer_validation_error_self_ref():
    row = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method=" ALL",
                           depends_on="name1 ", dominant_parent="Supplier", type_demand="list, bool",
                           type_supplier="list , bool ",
                           data_type=" SingleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(invalid_data) == 1
    assert len(validation_errors['name1']) == 1
    assert 'depends on itself' in validation_errors['name1'][0]


def test_importer_validation_error_depend_param():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method=" ALL",
                            depends_on="name2 ", dominant_parent="Supplier", type_demand="list,bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="cat")
    row2 = generate_csv_row(full_name="Long name ", name="name2 ", comp_type="EXACT", production_method=" ALL",
                            dominant_parent="Supplier", type_demand="bool", type_supplier="bool ",
                            data_type=" Parameter", category="ABC")
    data1, errors = _extract_data_from_row(row1)
    assert isinstance(data1, RawPreferenceData)
    assert len(errors) == 0

    data2, errors = _extract_data_from_row(row2)
    assert isinstance(data2, RawParameterData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data1, data2])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert 'depends on parameter' in validation_errors['name1'][0]


def test_importer_validation_error_empty_cat():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method=" ALL",
                            depends_on="", dominant_parent="Supplier", type_demand="list, bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="")
    data, errors = _extract_data_from_row(row1)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert 'is not defined' in validation_errors['name1'][0]


def test_importer_validation_error_empty_production_method():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method="  ",
                            depends_on="", dominant_parent="Supplier", type_demand="list, bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row1)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert 'is not defined' in validation_errors['name1'][0]


def test_importer_validation_error_not_existent_parent():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method=" ALL ",
                            depends_on="some_other", dominant_parent="Supplier", type_demand="list, bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row1)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert 'does not exist' in validation_errors['name1'][0]


def test_importer_validation_error_depend_param_production():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method="B,C",
                            type_demand="list,bool", type_supplier="list , bool ", data_type=" SingleChoicePreference",
                            category="cat")
    row2 = generate_csv_row(full_name="Long name ", name="name2 ", comp_type="EXACT", production_method="A",
                            dominant_parent="Supplier", type_demand="float", type_supplier="float ",
                            data_type=" RangePreference", category="ABC", depends_on="name1")
    row3 = generate_csv_row(full_name="Long name ", name="name3 ", comp_type="EXACT", production_method="A,B",
                            depends_on="name1", dominant_parent="Supplier", type_demand="float", type_supplier="float ",
                            data_type=" RangePreference", category="ABC")
    data1, errors = _extract_data_from_row(row1)
    assert isinstance(data1, RawPreferenceData)
    assert len(errors) == 0

    data2, errors = _extract_data_from_row(row2)
    assert isinstance(data2, RawPreferenceData)
    assert len(errors) == 0

    data3, errors = _extract_data_from_row(row3)
    assert isinstance(data3, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data1, data2, data3])

    assert len(processing_errors['name1']) == 0
    assert len(processing_errors['name2']) == 0
    assert len(processing_errors['name3']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 0
    assert len(validation_errors['name2']) == 1
    assert len(validation_errors['name3']) == 1
    assert len(invalid_data) == 2
    assert 'production method' in validation_errors['name2'][0]
    assert 'production method' in validation_errors['name3'][0]


def test_importer_validation_error_cycle():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method=" ALL",
                            depends_on="name2 ", dominant_parent="Supplier", type_demand="list, bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="cat")
    row2 = generate_csv_row(full_name="Long name ", name="name2 ", comp_type="", production_method=" ALL",
                            depends_on="name3 ", dominant_parent="Supplier", type_demand="list , bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="cat")
    row3 = generate_csv_row(full_name="Long name ", name="name3 ", comp_type="", production_method=" ALL",
                            depends_on="name4 ", dominant_parent="Supplier", type_demand="list , bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="cat")
    row4 = generate_csv_row(full_name="Long name ", name="name4 ", comp_type="", production_method=" ALL",
                            depends_on="name2 ", dominant_parent="Supplier", type_demand="list , bool",
                            type_supplier="list , bool ",
                            data_type=" SingleChoicePreference", category="cat")

    data = []
    for r in [row1, row2, row3, row4]:
        d, e = _extract_data_from_row(r)
        assert len(e) == 0
        data.append(d)

    processed_data, processing_errors = preprocess_parsed_data(data)
    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 0
    assert len(validation_errors['name2']) == 1
    assert len(validation_errors['name3']) == 1
    assert len(validation_errors['name4']) == 1
    assert 'Detected depends_on cycle' in validation_errors['name2'][0]
    assert 'Detected depends_on cycle' in validation_errors['name3'][0]
    assert 'Detected depends_on cycle' in validation_errors['name4'][0]
    assert len(invalid_data) == 3


def test_importer_validation_error_parameter_comp_type():
    row = generate_csv_row(full_name="Long name ", name="short ", comp_type="something", production_method=" Method ",
                           type_demand="bool",
                           type_supplier="bool ", data_type=" Parameter", category="cat")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['short']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['short']) == 1
    assert len(invalid_data) == 1
    assert 'not have a comparison_type' in validation_errors['short'][0]


@pytest.mark.parametrize('demand_t,supplier_t,comp_t,expected_err',
                         [('str', "str", "IS_IN", "is not supported by comparison_type"),
                          ('float', 'str', 'IS_IN', "missmatch and/or are not supported by"),
                          ('list,bool', 'bool', 'EXACT', "Choose a different comparison type"),
                          ('range,float', 'float', 'EXACT', "Choose a different comparison type"),
                          ('list,bool', 'float', 'EXACT', "need to be based"),
                          ('list,float', 'range,float', 'EXACT',
                           "Demand type 'list,float' and Supplier type 'range,float' missmatch.")])
def test_importer_validation_error_parameter_comp_type(demand_t, supplier_t, comp_t, expected_err):
    row = generate_csv_row(full_name="Long name ", name="short ", comp_type=comp_t, production_method=" Method ",
                           type_demand=demand_t,
                           type_supplier=supplier_t, data_type=" Parameter", category="ABC")
    data, errors = _extract_data_from_row(row)

    assert isinstance(data, RawParameterData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], ParameterData)
    assert len(processing_errors['short']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['short']) == 1
    assert len(invalid_data) == 1
    assert expected_err in validation_errors['short'][0]


def test_importer_validation_error_preference_comparison_type():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="", production_method=" ALL "
                            , dominant_parent="Supplier", type_demand="list, bool",
                            type_supplier="list , bool ",
                            data_type=" MultipleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row1)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert "Preference type 'MultipleChoicePreference' requires a comparison_type, none supplied." in \
           validation_errors['name1'][0]


def test_importer_validation_error_preference_other():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="IS_IN", production_method=" ALL "
                            , dominant_parent="Supplier", type_demand="list, bool",
                            type_supplier="list , bool ",
                            data_type=" MultipleChoicePreference", category="cat")
    data, errors = _extract_data_from_row(row1)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert "comparison type 'is_in' for preference type 'MultipleChoicePreference'" in validation_errors['name1'][0]


def test_importer_validation_error_preference_wrong_combination():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="INCLUSIVE", production_method=" ALL "
                            , dominant_parent="Supplier", type_demand="list, bool",
                            type_supplier="bool ",
                            data_type=" MultipleChoicePreference", category="cat")

    data, errors = _extract_data_from_row(row1)

    assert isinstance(data, RawPreferenceData)
    assert len(errors) == 0

    processed_data, processing_errors = preprocess_parsed_data([data])

    assert isinstance(processed_data[0], PreferenceData)
    assert len(processing_errors['name1']) == 0

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert "'('list,bool', 'bool')' is not supported for preference type 'MultipleChoicePreference'" in \
           validation_errors['name1'][0]


def test_importer_validation_error_preference_depends_on():
    row1 = generate_csv_row(full_name="Long name ", name="name1 ", comp_type="INCLUSIVE", production_method=" ALL ",
                            type_demand="list, bool", depends_on="other", type_supplier="list, bool ",
                            data_type=" MultipleChoicePreference", category="cat")

    row2 = generate_csv_row(full_name="Long name ", name="other ", comp_type="INCLUSIVE", production_method=" ALL ",
                            type_demand="list, bool", type_supplier="list, bool ",
                            data_type=" MultipleChoicePreference",
                            category="cat")

    data1, errors = _extract_data_from_row(row1)
    data2, errors = _extract_data_from_row(row2)

    processed_data, processing_errors = preprocess_parsed_data([data1, data2])

    invalid_data, validation_errors = validation_read_data(processed_data)

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert "Preference 'name1' has a dependency on preference 'other'" in validation_errors['name1'][0]


@pytest.mark.parametrize('pref_type', ['RangePreference', 'SingleChoicePreference', 'ZonePreference'])
def test_importer_validation_error_no_comp_type(pref_type):
    data = PreferenceData(full_name='full', name='name1',
                          production_method=['ALL'], category='QUALITY_AWARENESS', depends_on=None,
                          dominant_parent=None, type_supplier=int, type_demand=int, comparison_type=None,
                          preference_type=pref_type)

    invalid_data, validation_errors = validation_read_data([data])

    assert len(validation_errors['name1']) == 1
    assert len(invalid_data) == 1
    assert "specified demand-supplier type combination" in validation_errors['name1'][0]


@pytest.mark.parametrize('pref_type', ['ValueMagnitudePreference'])
def test_importer_validation_no_comp_type(pref_type):
    data = PreferenceData(full_name='full', name='name1',
                          production_method=['ALL'], category='QUALITY_AWARENESS', depends_on=None,
                          dominant_parent=None, type_supplier=int, type_demand=int, comparison_type=None,
                          preference_type=pref_type)

    invalid_data, validation_errors = validation_read_data([data])

    assert len(validation_errors['name1']) == 0
    assert len(invalid_data) == 0
