import pytest
from pytest import approx

from common.typedef import Range
from recommender.preferences.preferenceComparison import distance_bool_preferences, distance_list_preferences, \
    distance_single_choice, distance_multiple_choice, distance_range_preferences, distance_preference, \
    distance_value_magnitude_preference, distance_zone_preference
from recommender.preferences.preferenceTypes import BoolPreference, ChoicePreference, RangePreference, \
    SingleChoicePreference, MultipleChoicePreference, ValueMagnitudePreference, ZonePreference, CustomTypeInstance
from recommender.typedefs.typedef import ComparisonType


def test_distance_bool_preferences():
    input_result_exact = [(True, True, 0.0), (True, False, 1.0), (False, True, 1.0), (False, False, 0.0)]
    input_result_inclusive = [(True, True, 0.0), (True, False, 1.0), (False, True, 0.0), (False, False, 0.0)]
    input_result_exclusive = [(True, True, 0.0), (True, False, 0.0), (False, True, 1.0), (False, False, 0.0)]

    p = BoolPreference(comparison_type=ComparisonType.EXACT_MATCH)
    for (a, b, result) in input_result_exact:
        assert result == distance_bool_preferences(a, b, p)
    p = BoolPreference(comparison_type=ComparisonType.INCLUSIVE)
    for (a, b, result) in input_result_inclusive:
        assert result == distance_bool_preferences(a, b, p)
    p = BoolPreference(comparison_type=ComparisonType.INV_INCLUSIVE)
    for (a, b, result) in input_result_exclusive:
        assert result == distance_bool_preferences(a, b, p)


def test_distance_bool_preferences_importance():
    # importance = 0
    input_result_exact = [(True, True, 0.0), (True, False, 0.0), (False, True, 0.0), (False, False, 0.0)]
    input_result_inclusive = [(True, True, 0.0), (True, False, 0.0), (False, True, 0.0), (False, False, 0.0)]
    input_result_exclusive = [(True, True, 0.0), (True, False, 0.0), (False, True, 0.0), (False, False, 0.0)]

    p = BoolPreference(comparison_type=ComparisonType.EXACT_MATCH, importance=0.0)
    for (a, b, result) in input_result_exact:
        assert result == distance_bool_preferences(a, b, p)
    p = BoolPreference(comparison_type=ComparisonType.INCLUSIVE, importance=0.0)
    for (a, b, result) in input_result_inclusive:
        assert result == distance_bool_preferences(a, b, p)
    p = BoolPreference(comparison_type=ComparisonType.INV_INCLUSIVE, importance=0.0)
    for (a, b, result) in input_result_exclusive:
        assert result == distance_bool_preferences(a, b, p)

    # importance = 0.5
    input_result_exact = [(True, True, 0.0), (True, False, 0.75), (False, True, 0.75), (False, False, 0.0)]
    input_result_inclusive = [(True, True, 0.0), (True, False, 0.75), (False, True, 0.0), (False, False, 0.0)]
    input_result_exclusive = [(True, True, 0.0), (True, False, 0.0), (False, True, 0.75), (False, False, 0.0)]

    p = BoolPreference(comparison_type=ComparisonType.EXACT_MATCH, importance=0.5)
    for (a, b, result) in input_result_exact:
        assert result == distance_bool_preferences(a, b, p)
    p = BoolPreference(comparison_type=ComparisonType.INCLUSIVE, importance=0.5)
    for (a, b, result) in input_result_inclusive:
        assert result == distance_bool_preferences(a, b, p)
    p = BoolPreference(comparison_type=ComparisonType.INV_INCLUSIVE, importance=0.5)
    for (a, b, result) in input_result_exclusive:
        assert result == distance_bool_preferences(a, b, p)


def test_distance_bool_preferences_throws():
    with pytest.raises(RuntimeError, match=r"bool, .* int .* bool.*"):
        distance_bool_preferences(1, True, BoolPreference(comparison_type=ComparisonType.EXACT_MATCH))
    with pytest.raises(RuntimeError, match=r"bool, .* bool .* float.*"):
        distance_bool_preferences(True, 1.0, BoolPreference(comparison_type=ComparisonType.EXACT_MATCH))
    with pytest.raises(RuntimeError, match=r".* is_in.*"):
        distance_bool_preferences(True, True, BoolPreference(comparison_type=ComparisonType.IS_IN))


def test_distance_list_preferences_throws():
    with pytest.raises(RuntimeError, match=r"list\[bool\], .* int .* list.*"):
        distance_list_preferences(1, [True], MultipleChoicePreference())
    with pytest.raises(RuntimeError, match=r"list\[bool\], .* list .* float.*"):
        distance_list_preferences([True], 1.0, SingleChoicePreference())
    with pytest.raises(RuntimeError):
        distance_list_preferences([True, False], [1.0, True], SingleChoicePreference())
    with pytest.raises(RuntimeError):
        distance_list_preferences([1.0, True], [True, True], SingleChoicePreference())
    with pytest.raises(RuntimeError, match=r".* 2 .* 1"):
        distance_list_preferences([False, True], [True], SingleChoicePreference())
    with pytest.raises(RuntimeError, match=r"Unknown"):
        distance_list_preferences([False, True], [True, False], ChoicePreference())


def test_distance_single_choice_preferences():
    with pytest.raises(RuntimeError):
        distance_single_choice([True, True], [True, False], SingleChoicePreference())
    with pytest.raises(RuntimeError):
        distance_single_choice([False, True], [True, True], SingleChoicePreference())
    with pytest.raises(RuntimeError):
        distance_single_choice([False, True], [False, False], SingleChoicePreference())

    ordered = SingleChoicePreference(ordered=True)
    not_ordered = SingleChoicePreference(ordered=False)
    assert 0.0 == distance_single_choice([True, False, False, False], [True, False, False, False], not_ordered)
    assert 1.0 == distance_single_choice([True, False, False, False], [False, False, True, False], not_ordered)

    assert 0.0 == distance_single_choice([True, False, False, False, False], [True, False, False, False, False],
                                         ordered)
    assert 0.75 == distance_single_choice([True, False, False, False, False], [False, False, False, True, False],
                                          ordered)
    assert 0.75 == distance_single_choice([False, False, False, True, False], [True, False, False, False, False],
                                          ordered)
    assert 1.0 == distance_single_choice([False, False, False, False, True], [True, False, False, False, False],
                                         ordered)


def test_distance_single_choice_preferences_importance():
    ordered = SingleChoicePreference(ordered=True, importance=0.0)
    not_ordered = SingleChoicePreference(ordered=False, importance=0.0)
    assert 0.0 == distance_single_choice([True, False, False, False], [True, False, False, False], not_ordered)
    assert 0.0 == distance_single_choice([True, False, False, False], [False, False, True, False], not_ordered)

    assert 0.0 == distance_single_choice([True, False, False, False, False], [True, False, False, False, False],
                                         ordered)
    assert 0.0 == distance_single_choice([True, False, False, False, False], [False, False, False, True, False],
                                         ordered)
    assert 0.0 == distance_single_choice([False, False, False, True, False], [True, False, False, False, False],
                                         ordered)
    assert 0.0 == distance_single_choice([False, False, False, False, True], [True, False, False, False, False],
                                         ordered)

    ordered = SingleChoicePreference(ordered=True, importance=0.5)
    not_ordered = SingleChoicePreference(ordered=False, importance=0.5)

    assert 0.0 == distance_single_choice([True, False, False, False], [True, False, False, False], not_ordered)
    assert 0.75 == distance_single_choice([True, False, False, False], [False, False, True, False], not_ordered)

    assert 0.0 == distance_single_choice([True, False, False, False, False], [True, False, False, False, False],
                                         ordered)
    assert 0.375 == distance_single_choice([True, False, False, False, False], [False, False, False, True, False],
                                           ordered)
    assert 0.375 == distance_single_choice([False, False, False, True, False], [True, False, False, False, False],
                                           ordered)
    assert 0.5 == distance_single_choice([False, False, False, False, True], [True, False, False, False, False],
                                         ordered)


def test_distance_multiple_choice_preferences():
    exact = MultipleChoicePreference(comparison_type=ComparisonType.EXACT_MATCH)
    inclusive = MultipleChoicePreference(comparison_type=ComparisonType.INCLUSIVE)
    exclusive = MultipleChoicePreference(comparison_type=ComparisonType.INV_INCLUSIVE)

    assert approx(0.0) == distance_multiple_choice([False, False, False, False], [False, False, False, False], exact)
    assert approx(0.0) == distance_multiple_choice([True, True, False, False], [True, True, False, False], exact)
    assert approx(2.0 / 3) == distance_multiple_choice([True, True, False, False], [True, False, True, False], exact)
    assert approx(1.0 / 3) == distance_multiple_choice([True, True, True, False], [True, True, False, False], exact)
    assert approx(0.75) == distance_multiple_choice([True, True, False, True], [True, False, True, False], exact)
    assert approx(1.0) == distance_multiple_choice([False, True, True, False], [True, False, False, True], exact)
    assert approx(1.0) == distance_multiple_choice([False, True, False, False], [True, False, False, False], exact)

    assert approx(0.0) == distance_multiple_choice([False, False, False, False], [True, False, False, False], inclusive)
    assert approx(0.0) == distance_multiple_choice([True, True, False, False], [True, True, False, False], inclusive)
    assert approx(0.5) == distance_multiple_choice([True, True, False, False], [True, False, True, False], inclusive)
    assert approx(1.0 / 3) == distance_multiple_choice([True, True, True, False], [True, True, False, False], inclusive)
    assert approx(2.0 / 3) == distance_multiple_choice([True, True, False, True], [True, False, True, False], inclusive)
    assert approx(1.0) == distance_multiple_choice([False, True, True, False], [True, False, False, True], inclusive)
    assert approx(1.0) == distance_multiple_choice([False, True, False, False], [True, False, False, False], inclusive)

    assert approx(0.0) == distance_multiple_choice([True, False, False, False], [False, False, False, False], exclusive)
    assert approx(0.0) == distance_multiple_choice([True, True, False, False], [True, True, False, False], exclusive)
    assert approx(0.5) == distance_multiple_choice([True, True, False, False], [True, False, True, False], exclusive)
    assert approx(0.0) == distance_multiple_choice([True, True, True, False], [True, True, False, False], exclusive)
    assert approx(0.5) == distance_multiple_choice([True, True, False, True], [True, False, True, False], exclusive)
    assert approx(1.0) == distance_multiple_choice([False, True, True, False], [True, False, False, True], exclusive)
    assert approx(1.0) == distance_multiple_choice([False, True, False, False], [True, False, False, False], exclusive)


def test_distance_multiple_choice_preferences_throw():
    with pytest.raises(RuntimeError):
        wrong = MultipleChoicePreference(comparison_type=ComparisonType.IS_IN)
        distance_multiple_choice([True, True, False, False], [True, True, False, False], wrong)


def test_distance_range_preferences():
    b = RangePreference()
    assert approx(0.0) == distance_range_preferences(0.5, 0.5, b)
    assert approx(1.0) == distance_range_preferences(0.0, 1.0, b)
    assert approx(1.0) == distance_range_preferences(1.0, 0.0, b)
    assert approx(0.2) == distance_range_preferences(0.3, 0.5, b)


def test_distance_value_magnitude_preference_0():
    b = ValueMagnitudePreference(importance=0.0)
    assert approx(0.0) == distance_value_magnitude_preference(10, 10, b)
    assert approx(0.0) == distance_value_magnitude_preference(1000, 1000, b)
    assert approx(0.00106625507) == distance_value_magnitude_preference(100, 101, b)
    assert approx(0.19903324216281204) == distance_value_magnitude_preference(100, 1000, b)
    assert approx(0.14279159516167317) == distance_value_magnitude_preference(1000, 10000, b)
    assert approx(0.0) == distance_value_magnitude_preference(0, 0, b)
    # if one value is zero, the behavior is quite extreme
    assert approx(1.0) == distance_value_magnitude_preference(9, 0, b)


def test_distance_value_magnitude_preference_1():
    b = ValueMagnitudePreference(importance=1.0)
    assert approx(0.0) == distance_value_magnitude_preference(10, 10, b)
    assert approx(0.0) == distance_value_magnitude_preference(1000, 1000, b)
    assert approx(0.0021325077334073406) == distance_value_magnitude_preference(100, 101, b)
    assert approx(0.3828982638653363) == distance_value_magnitude_preference(100, 1000, b)
    assert approx(0.279876662014098) == distance_value_magnitude_preference(1000, 10000, b)
    assert approx(0.0) == distance_value_magnitude_preference(0, 0, b)
    # if one value is zero, the behavior is quite extreme
    assert approx(1.0) == distance_value_magnitude_preference(9, 0, b)


def test_distance_zone_preference_0():
    b = ZonePreference(importance=0.0)
    r = Range(min=50, max=100)
    assert approx(0.0) == distance_zone_preference(50, r, b)
    assert approx(0.0) == distance_zone_preference(75, r, b)
    assert approx(0.0) == distance_zone_preference(100, r, b)
    assert approx(0.009900990099) == distance_zone_preference(101, r, b)
    assert approx(0.333333333333) == distance_zone_preference(150, r, b)
    assert approx(0.9) == distance_zone_preference(1000, r, b)
    assert distance_zone_preference(40, r, b) == distance_zone_preference(120, r, b)  # 20% deviation gives same result


def test_distance_zone_preference_1():
    b = ZonePreference(importance=1.0)
    r = Range(min=50, max=100)
    assert approx(0.0) == distance_zone_preference(50, r, b)
    assert approx(0.0) == distance_zone_preference(75, r, b)
    assert approx(0.0) == distance_zone_preference(100, r, b)
    assert approx(0.01970395) == distance_zone_preference(101, r, b)
    assert approx(0.55555555) == distance_zone_preference(150, r, b)
    assert approx(0.99) == distance_zone_preference(1000, r, b)
    assert distance_zone_preference(40, r, b) == distance_zone_preference(120, r, b)  # 20% deviation gives same result


def test_distance_zone_preference_single():
    b = ZonePreference(importance=1.0)
    r = 100
    assert approx(0.01970395) == distance_zone_preference(101, r, b)
    assert approx(0.55555555) == distance_zone_preference(150, r, b)


def test_distance_zone_preference_zero():
    b = ZonePreference(importance=0.0)
    r = 0
    assert approx(0) == distance_zone_preference(0, r, b)
    assert approx(0.8) == distance_zone_preference(4, r, b)
    assert approx(0.9) == distance_zone_preference(9, r, b)


def test_distance_preferences():
    b = RangePreference()
    d = CustomTypeInstance(base_type=RangePreference(), value=0.3)
    s = CustomTypeInstance(base_type=RangePreference(), value=0.5)
    assert distance_range_preferences(0.3, 0.5, b) == approx(distance_preference(d, s))

    base = MultipleChoicePreference(comparison_type=ComparisonType.EXACT_MATCH)
    d = CustomTypeInstance(base_type=base, value=[True, True, False, True])
    s = CustomTypeInstance(base_type=base, value=[True, False, True, False])
    assert distance_multiple_choice(d.value, s.value, base) == approx(distance_preference(d, s))

    base = SingleChoicePreference(ordered=True)
    d = CustomTypeInstance(base_type=base, value=[False, False, False, True, False])
    s = CustomTypeInstance(base_type=base, value=[True, False, False, False, False])
    assert distance_single_choice(d.value, s.value, base) == approx(distance_preference(d, s))

    base = BoolPreference(comparison_type=ComparisonType.EXACT_MATCH)
    d = CustomTypeInstance(base_type=base, value=True)
    s = CustomTypeInstance(base_type=base, value=True)
    assert distance_bool_preferences(d.value, s.value, base) == approx(distance_preference(d, s))


def test_distance_preferences_throw():
    with pytest.raises(RuntimeError):
        base = MultipleChoicePreference(comparison_type=ComparisonType.EXACT_MATCH)
        base2 = SingleChoicePreference(ordered=True)
        d = CustomTypeInstance(base_type=base, value=[True, True, False, True])
        s = CustomTypeInstance(base_type=base2, value=[True, False, False, False])
        distance_preference(d, s)

    with pytest.raises(RuntimeError):
        base = MultipleChoicePreference(comparison_type=ComparisonType.EXACT_MATCH)
        base2 = BoolPreference()
        d = CustomTypeInstance(base_type=base, value=[True, True, False, True])
        s = CustomTypeInstance(base_type=base2, value=True)
        distance_preference(d, s)

    with pytest.raises(RuntimeError):
        base = MultipleChoicePreference(comparison_type=ComparisonType.EXACT_MATCH)
        base2 = BoolPreference()
        d = CustomTypeInstance(base_type=base, value=[True, True, False, True])
        s = 1.0
        distance_preference(d, s)
