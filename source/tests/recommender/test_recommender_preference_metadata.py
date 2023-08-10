import dataclasses
from typing import Optional

import pytest

from recommender.preferences.preferenceBase import PreferenceBase
from recommender.preferences.preferenceGeneration import generate_preference_dataclass, \
    convert_generic_types_to_concrete
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.preferences.preferenceTypes import BoolPreference, RangePreference, SingleChoicePreference, \
    MultipleChoicePreference, ValueMagnitudePreference, ZonePreference
from recommender.typedefs.typedef import ComparisonType, DominantParent


@dataclasses.dataclass
class TestPreferencesMetadata(PreferenceBase):
    quality1: PreferenceMetadata = PreferenceMetadata("ABC", "QUALITY_AWARENESS",
                                                      BoolPreference(comparison_type=ComparisonType.INCLUSIVE),
                                                      depends_on="low_price", dominant_side=DominantParent.DEMAND)
    quality2: PreferenceMetadata = PreferenceMetadata("ABC", "QUALITY_AWARENESS", MultipleChoicePreference(
        comparison_type=ComparisonType.INCLUSIVE), depends_on="low_price", dominant_side=DominantParent.DEMAND)
    quality3: PreferenceMetadata = PreferenceMetadata("ABC", "QUALITY_AWARENESS", ZonePreference())
    quality4: PreferenceMetadata = PreferenceMetadata("ABC", "QUALITY_AWARENESS", ValueMagnitudePreference())
    quality5: PreferenceMetadata = PreferenceMetadata("ABC", "QUALITY_AWARENESS", SingleChoicePreference())
    low_price: PreferenceMetadata = PreferenceMetadata("ABC", "PRICE", RangePreference(), depends_on="sdg",
                                                       dominant_side=DominantParent.DEMAND)
    sdg: PreferenceMetadata = PreferenceMetadata("ABC", "SUSTAINABILITY_PROFILE",
                                                 BoolPreference(comparison_type=ComparisonType.EXACT_MATCH))


@dataclasses.dataclass
class TestPreferencesMetadataFailure(PreferenceBase):
    quality: PreferenceMetadata = PreferenceMetadata("ABC", "QUALITY_AWARENESS", RangePreference(),
                                                     depends_on="other_name", dominant_side=DominantParent.DEMAND)
    low_price: PreferenceMetadata = PreferenceMetadata("ABC", "PRICE",

                                                       BoolPreference(comparison_type=ComparisonType.EXACT_MATCH))


def test_recommender_complete_dependencies():
    metadata = TestPreferencesMetadata()
    assert len(metadata.sdg.children) == 1
    assert metadata.sdg.children[0].name == "low_price"
    assert metadata.sdg.parent is None

    assert metadata.low_price.parent.name == "sdg"
    assert len(metadata.low_price.children) == 2
    assert metadata.low_price.children[0].name == "quality1"
    assert metadata.low_price.children[1].name == "quality2"

    assert metadata.quality1.parent.name == "low_price"
    assert len(metadata.quality1.children) == 0
    assert metadata.quality2.parent.name == "low_price"
    assert len(metadata.quality2.children) == 0


def test_recommender_complete_dependencies_fail():
    with pytest.raises(RuntimeError, match=r"other_name.*quality"):
        TestPreferencesMetadataFailure()


def test_recommender_metadata_definition_fail():
    with pytest.raises(ValueError):
        PreferenceMetadata("ABC", "QUALITY_AWARENESS", RangePreference(),
                           depends_on="low_price")


def test_recommender_test_generate_input_type():
    metadata = TestPreferencesMetadata()
    TestPreferences = generate_preference_dataclass(TestPreferencesMetadata, ["ABC"])["ABC"]

    assert (dataclasses.is_dataclass(TestPreferences()))

    test_preferences_inst: TestPreferences = TestPreferences()

    assert metadata.keys() == dataclasses.asdict(test_preferences_inst).keys()
    for f in dataclasses.fields(test_preferences_inst):
        name = f.name
        preference_metadata: PreferenceMetadata = getattr(metadata, name)
        assert Optional[convert_generic_types_to_concrete(preference_metadata.preference_type.type)] == f.type
