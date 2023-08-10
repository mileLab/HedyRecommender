import dataclasses
from typing import Union

import pytest
from pytest import approx

from common.typedef import Range, RangeFloat, RangeInt
from recommender.preferences.preferenceBase import PreferenceBase
from recommender.preferences.preferenceComparison import distance_bool_preferences, distance_single_choice, \
    distance_multiple_choice, distance_range_preferences, distance_value_magnitude_preference, distance_zone_preference
from recommender.preferences.preferenceGeneration import generate_preference_dataclass, \
    convert_generic_types_to_concrete
from recommender.preferences.preferenceImportance import instantiate_preferences
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.preferences.preferenceTypes import BoolPreference, MultipleChoicePreference, ZonePreference, \
    ValueMagnitudePreference, SingleChoicePreference, RangePreference
from recommender.typedefs.typedef import ComparisonType, DominantParent


def __generate_test_type_range(dominant: DominantParent):
    @dataclasses.dataclass
    class TestPreferencesMetadata(PreferenceBase):
        pre_bool: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                          BoolPreference(comparison_type=ComparisonType.INCLUSIVE),
                                                          depends_on="parent", dominant_side=dominant)
        pre_multi: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                           MultipleChoicePreference(
                                                               comparison_type=ComparisonType.INCLUSIVE),
                                                           depends_on="parent", dominant_side=dominant)
        pre_zone: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS", ZonePreference(),
                                                          depends_on="parent", dominant_side=dominant)
        pre_mag: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                         ValueMagnitudePreference(), depends_on="parent",
                                                         dominant_side=dominant)
        pre_single: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                            SingleChoicePreference(), depends_on="parent",
                                                            dominant_side=dominant)
        pre_range: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS", RangePreference(),
                                                           depends_on="parent", dominant_side=dominant)
        parent: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS", RangePreference(),
                                                        depends_on="parent", dominant_side=dominant)

    return TestPreferencesMetadata


def __generate_test_type_bool(dominant: DominantParent):
    @dataclasses.dataclass
    class TestPreferencesMetadata(PreferenceBase):
        pre_bool: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                          BoolPreference(comparison_type=ComparisonType.INCLUSIVE),
                                                          depends_on="parent", dominant_side=dominant)
        pre_multi: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                           MultipleChoicePreference(
                                                               comparison_type=ComparisonType.INCLUSIVE),
                                                           depends_on="parent", dominant_side=dominant)
        pre_zone: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS", ZonePreference(),
                                                          depends_on="parent", dominant_side=dominant)
        pre_mag: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                         ValueMagnitudePreference(), depends_on="parent",
                                                         dominant_side=dominant)
        pre_single: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS",
                                                            SingleChoicePreference(), depends_on="parent",
                                                            dominant_side=dominant)
        pre_range: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS", RangePreference(),
                                                           depends_on="parent", dominant_side=dominant)
        parent: PreferenceMetadata = PreferenceMetadata(["ABC"], "QUALITY_AWARENESS", BoolPreference(),
                                                        depends_on="parent", dominant_side=dominant)

    return TestPreferencesMetadata


def get_preference_metadata(name: str, PrefMetadata: type) -> PreferenceMetadata:
    return getattr(PrefMetadata, name)


def get_preference_metadata_type(name: str, schema):
    return schema["properties"][name]


@pytest.mark.parametrize('inp_type,expected',
                         [(Range[int], RangeInt),
                          (Range[float], RangeFloat),
                          (int, int),
                          (list[float], list[float]),
                          (str, str),
                          (Union[Range[int], Range[float]], Union[RangeInt, RangeFloat])
                          ])
def test_generic_type_conversion(inp_type, expected):
    result = convert_generic_types_to_concrete(inp_type)
    assert expected == result


def test_importance_generation_types_bool():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]
    schema = TestPreferences.__pydantic_model__.schema()
    assert get_preference_metadata_type("pre_bool", schema)["type"] == "boolean"


def test_importance_generation_types_multi():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]
    schema = TestPreferences.__pydantic_model__.schema()
    assert 'items' in get_preference_metadata_type("pre_multi", schema).keys()
    assert get_preference_metadata_type("pre_multi", schema)['items']["type"] == "boolean"


def test_importance_generation_types_zone():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]
    schema = TestPreferences.__pydantic_model__.schema()
    assert 'anyOf' in get_preference_metadata_type("pre_zone", schema).keys()

    values = set(
        [t["type"] for t in get_preference_metadata_type("pre_zone", schema)["anyOf"] if "type" in t.keys()] + [
            t["$ref"] for t in get_preference_metadata_type("pre_zone", schema)["anyOf"] if "$ref" in t.keys()])
    for i in ["number", "integer", "RangeInt", "RangeFloat"]:
        assert any([i in v for v in values])


def test_importance_generation_types_mag():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]
    schema = TestPreferences.__pydantic_model__.schema()

    values = set([t["type"] for t in get_preference_metadata_type("pre_mag", schema)["anyOf"] if "type" in t.keys()])
    for i in ["number", "integer"]:
        assert any([i in v for v in values])


def test_importance_generation_types_single():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]
    schema = TestPreferences.__pydantic_model__.schema()
    assert 'items' in get_preference_metadata_type("pre_single", schema).keys()
    assert get_preference_metadata_type("pre_single", schema)['items']["type"] == "boolean"


def test_importance_generation_types_range():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]
    schema = TestPreferences.__pydantic_model__.schema()
    assert get_preference_metadata_type("pre_range", schema)["type"] == "number"


def test_importance_generation_demand_range():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=1.0)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=0.0)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(1.0) == preference_metadata_instance.pre_bool.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_multi.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_zone.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_mag.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_single.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_range.preference_type.importance


def test_importance_generation_supplier_range():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.SUPPLIER)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=1.0)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=0.0)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(0.0) == preference_metadata_instance.pre_bool.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_multi.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_zone.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_mag.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_single.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_range.preference_type.importance


def test_importance_generation_demand_bool():
    TestPreferencesMetadata = __generate_test_type_bool(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=True)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=False)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(1.0) == preference_metadata_instance.pre_bool.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_multi.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_zone.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_mag.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_single.preference_type.importance
    assert approx(1.0) == preference_metadata_instance.pre_range.preference_type.importance


def test_importance_generation_supplier_bool():
    TestPreferencesMetadata = __generate_test_type_bool(DominantParent.SUPPLIER)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=True)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=False)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(0.0) == preference_metadata_instance.pre_bool.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_multi.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_zone.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_mag.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_single.preference_type.importance
    assert approx(0.0) == preference_metadata_instance.pre_range.preference_type.importance


def test_importance_generation_both_bool():
    TestPreferencesMetadata = __generate_test_type_bool(DominantParent.BOTH)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=True)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=False)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(0.5) == preference_metadata_instance.pre_bool.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_multi.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_zone.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_mag.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_single.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_range.preference_type.importance


def test_importance_generation_both_range():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.BOTH)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=1.0)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=0.0)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(0.5) == preference_metadata_instance.pre_bool.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_multi.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_zone.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_mag.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_single.preference_type.importance
    assert approx(0.5) == preference_metadata_instance.pre_range.preference_type.importance


def test_recommender_preference_importance_range_1():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=1.0)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=1.0)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(1.0) == distance_bool_preferences(demand.pre_bool, supplier.pre_bool,
                                                    preference_metadata_instance.pre_bool.preference_type)
    assert approx(1.0) == distance_range_preferences(demand.pre_range, supplier.pre_range,
                                                     preference_metadata_instance.pre_range.preference_type)
    assert approx(1.0) == distance_multiple_choice(demand.pre_multi, supplier.pre_multi,
                                                   preference_metadata_instance.pre_multi.preference_type)
    assert approx(1.0) == distance_single_choice(demand.pre_single, supplier.pre_single,
                                                 preference_metadata_instance.pre_single.preference_type)
    assert approx(0.950674205) == distance_value_magnitude_preference(demand.pre_mag, supplier.pre_mag,
                                                                      preference_metadata_instance.pre_mag.preference_type)
    assert approx(0.84) == distance_zone_preference(demand.pre_zone, supplier.pre_zone,
                                                    preference_metadata_instance.pre_zone.preference_type)


def test_recommender_preference_importance_range_0():
    TestPreferencesMetadata = __generate_test_type_range(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=0.0)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=0.0)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(0.0) == distance_bool_preferences(demand.pre_bool, supplier.pre_bool,
                                                    preference_metadata_instance.pre_bool.preference_type)
    assert approx(0.0) == distance_range_preferences(demand.pre_range, supplier.pre_range,
                                                     preference_metadata_instance.pre_range.preference_type)
    assert approx(0.0) == distance_multiple_choice(demand.pre_multi, supplier.pre_multi,
                                                   preference_metadata_instance.pre_multi.preference_type)
    assert approx(0.0) == distance_single_choice(demand.pre_single, supplier.pre_single,
                                                 preference_metadata_instance.pre_single.preference_type)
    assert approx(0.725599618616011) == distance_value_magnitude_preference(demand.pre_mag, supplier.pre_mag,
                                                                            preference_metadata_instance.pre_mag.preference_type)
    assert approx(0.6) == distance_zone_preference(demand.pre_zone, supplier.pre_zone,
                                                   preference_metadata_instance.pre_zone.preference_type)


def test_recommender_preference_importance_bool_1():
    TestPreferencesMetadata = __generate_test_type_bool(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=True)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=True)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(1.0) == distance_bool_preferences(demand.pre_bool, supplier.pre_bool,
                                                    preference_metadata_instance.pre_bool.preference_type)
    assert approx(1.0) == distance_range_preferences(demand.pre_range, supplier.pre_range,
                                                     preference_metadata_instance.pre_range.preference_type)
    assert approx(1.0) == distance_multiple_choice(demand.pre_multi, supplier.pre_multi,
                                                   preference_metadata_instance.pre_multi.preference_type)
    assert approx(1.0) == distance_single_choice(demand.pre_single, supplier.pre_single,
                                                 preference_metadata_instance.pre_single.preference_type)
    assert approx(0.9506742053878598) == distance_value_magnitude_preference(demand.pre_mag, supplier.pre_mag,
                                                                             preference_metadata_instance.pre_mag.preference_type)
    assert approx(0.84) == distance_zone_preference(demand.pre_zone, supplier.pre_zone,
                                                    preference_metadata_instance.pre_zone.preference_type)


def test_recommender_preference_importance_bool_0():
    TestPreferencesMetadata = __generate_test_type_bool(DominantParent.DEMAND)
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    demand = TestPreferences(pre_bool=True, pre_multi=[True, False, True], pre_zone=25.0, pre_mag=1000.0,
                             pre_single=[False, True, False], pre_range=1.0, parent=False)
    supplier = TestPreferences(pre_bool=False, pre_multi=[False, True, False], pre_zone=RangeFloat(5.0, 10.0),
                               pre_mag=2.0,
                               pre_single=[False, False, True], pre_range=0.0, parent=False)

    preference_metadata_instance = instantiate_preferences(preference_metadata=TestPreferencesMetadata,
                                                           demand_values=demand,
                                                           supplier_values=supplier, production_method="ABC")

    assert approx(0.0) == distance_bool_preferences(demand.pre_bool, supplier.pre_bool,
                                                    preference_metadata_instance.pre_bool.preference_type)
    assert approx(0.0) == distance_range_preferences(demand.pre_range, supplier.pre_range,
                                                     preference_metadata_instance.pre_range.preference_type)
    assert approx(0.0) == distance_multiple_choice(demand.pre_multi, supplier.pre_multi,
                                                   preference_metadata_instance.pre_multi.preference_type)
    assert approx(0.0) == distance_single_choice(demand.pre_single, supplier.pre_single,
                                                 preference_metadata_instance.pre_single.preference_type)
    assert approx(0.725599618616011) == distance_value_magnitude_preference(demand.pre_mag, supplier.pre_mag,
                                                                            preference_metadata_instance.pre_mag.preference_type)
    assert approx(0.6) == distance_zone_preference(demand.pre_zone, supplier.pre_zone,
                                                   preference_metadata_instance.pre_zone.preference_type)
