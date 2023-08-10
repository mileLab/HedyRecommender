import pytest

from common.typedef import Range
from recommender.parameters.parameterComparison import exact_match, inclusive, exclusive, less, less_equ, greater, \
    greater_equ, \
    is_in, is_superset, compare_map
from recommender.typedefs.typedef import ComparisonType


def test_exact_match():
    assert exact_match(True, True).valid == True
    assert exact_match(False, True).valid == False
    assert len(exact_match(False, True).error) > 0

    assert exact_match(2, 2).valid == True
    assert exact_match(1, 2).valid == False
    assert len(exact_match(1, 2).error) > 0

    assert exact_match(2.0, 2.0).valid == True
    assert exact_match(1.0, 2.0).valid == False
    assert len(exact_match(1.0, 2.0).error) > 0

    assert exact_match("abc", "abc").valid == True
    assert exact_match("abc", "abcd").valid == False
    assert len(exact_match("abc", "abcd").error) > 0

    assert exact_match([1, 2, 3], [1, 2, 3]).valid == True
    assert exact_match([1, 2, 3], [1, 2, 3, 4]).valid == False
    assert len(exact_match([1, 2, 3], [1, 2, 3, 4]).error) > 0

    assert exact_match(Range(0.2, 0.4), Range(0.2, 0.4)).valid == True
    assert exact_match(Range(0.3, 0.4), Range(0.2, 0.4)).valid == False
    assert len(exact_match(Range(0.23, 0.4), Range(0.2, 0.4)).error) > 0


def test_inclusive():
    assert inclusive(True, True).valid == True
    assert inclusive(False, False).valid == True
    assert inclusive(False, True).valid == True
    assert inclusive(True, False).valid == False
    assert len(inclusive(True, False).error) > 0


def test_exclusive():
    assert exclusive(True, True).valid == True
    assert exclusive(False, False).valid == True
    assert exclusive(False, True).valid == False
    assert exclusive(True, False).valid == True
    assert len(exclusive(False, True).error) > 0


def test_less():
    assert less(1, 2).valid == True
    assert less(2, 2).valid == False
    assert less(3, 2).valid == False
    assert len(less(2, 2).error) > 0

    assert less(2.0, 2.1).valid == True
    assert less(2.0, 2.0).valid == False
    assert less(2.1, 2.0).valid == False
    assert len(less(2.0, 2.0).error) > 0


def test_less_equ():
    assert less_equ(1, 2).valid == True
    assert less_equ(2, 2).valid == True
    assert less_equ(3, 2).valid == False
    assert len(less_equ(3, 2).error) > 0

    assert less_equ(2.0, 2.1).valid == True
    assert less_equ(2.0, 2.0).valid == True
    assert less_equ(2.1, 2.0).valid == False
    assert len(less_equ(3.0, 2.0).error) > 0


def test_greater():
    assert greater(1, 2).valid == False
    assert greater(2, 2).valid == False
    assert greater(3, 2).valid == True
    assert len(greater(2, 2).error) > 0

    assert greater(2.0, 2.1).valid == False
    assert greater(2.0, 2.0).valid == False
    assert greater(2.1, 2.0).valid == True
    assert len(greater(2.0, 2.0).error) > 0


def test_greater_equ():
    assert greater_equ(1, 2).valid == False
    assert greater_equ(2, 2).valid == True
    assert greater_equ(3, 2).valid == True
    assert len(greater_equ(2, 3).error) > 0

    assert greater_equ(2.0, 2.1).valid == False
    assert greater_equ(2.0, 2.0).valid == True
    assert greater_equ(2.1, 2.0).valid == True
    assert len(greater_equ(2.0, 3.0).error) > 0


def test_is_in():
    assert is_in(1, [1, 2]).valid == True
    assert is_in(3, [1, 2]).valid == False
    assert len(is_in(3, [1, 2]).error) > 0

    assert is_in(1, Range(0.2, 1.0)).valid == True
    assert is_in(3, Range(0.2, 1.0)).valid == False
    assert is_in(0, Range(0.2, 1.0)).valid == False
    assert is_in(0, Range(max=1.0)).valid == True
    assert is_in(3, Range(min=0.2)).valid == True
    assert len(is_in(3, Range(0.2, 1.0)).error) > 0

    assert is_in(Range(0.2, 0.7), Range(0.2, 1.0)).valid == True
    assert is_in(Range(0.2, 1.7), Range(0.2, 1.0)).valid == False
    assert is_in(Range(0.0, 1.7), Range(0.2, 1.0)).valid == False
    assert is_in(Range(0.0, 0.1), Range(0.2, 1.0)).valid == False
    assert is_in(Range(0.0, 0.3), Range(0.2, 1.0)).valid == False
    assert len(is_in(Range(0.2, 1.7), Range(0.2, 1.0)).error) > 0
    assert len(is_in(Range(0.0, 1.7), Range(0.2, 1.0)).error) > 0
    assert len(is_in(Range(0.0, 0.1), Range(0.2, 1.0)).error) > 0


def test_is_in_throw():
    with pytest.raises(TypeError):
        is_in([1, 2], Range(0.2, 1.0))
    with pytest.raises(TypeError):
        is_in(Range(0.2, 1.0), [1, 2])
    with pytest.raises(TypeError):
        is_in(1, 1)
    with pytest.raises(TypeError):
        is_in(True, [True, False])


def test_is_around():
    assert is_superset([1, 2], 1).valid == True
    assert is_superset([1, 2], 3).valid == False
    assert len(is_superset([1, 2], 3).error) > 0

    assert is_superset(Range(0.2, 1.0), 1).valid == True
    assert is_superset(Range(0.2, 1.0), 3).valid == False
    assert is_superset(Range(0.2, 1.0), 0).valid == False
    assert is_superset(Range(max=1.0), 0).valid == True
    assert is_superset(Range(min=0.2), 1).valid == True
    assert len(is_superset(Range(0.2, 1.0), 3).error) > 0

    assert is_superset(Range(0.2, 1.0), Range(0.2, 0.7)).valid == True
    assert is_superset(Range(0.2, 1.0), Range(0.2, 1.7)).valid == False
    assert is_superset(Range(0.2, 1.0), Range(0.0, 1.7)).valid == False
    assert is_superset(Range(0.2, 1.0), Range(0.0, 0.1)).valid == False
    assert is_superset(Range(0.2, 1.0), Range(0.0, 0.3)).valid == False
    assert len(is_superset(Range(0.2, 1.0), Range(0.2, 1.7)).error) > 0
    assert len(is_superset(Range(0.2, 1.0), Range(0.0, 1.7)).error) > 0
    assert len(is_superset(Range(0.2, 1.0), Range(0.0, 0.1)).error) > 0


def test_is_around_throw():
    with pytest.raises(TypeError):
        is_superset(Range(0.2, 1.0), [1, 2])
    with pytest.raises(TypeError):
        is_superset([1, 2], Range(0.2, 1.0))
    with pytest.raises(TypeError):
        is_superset(1, 1)
    with pytest.raises(TypeError):
        is_superset([True, False], True)


def test_comparison_mapping():
    assert compare_map[ComparisonType.EXACT_MATCH](False, True) == exact_match(False, True)
    assert compare_map[ComparisonType.INCLUSIVE](False, True) == inclusive(False, True)
    assert compare_map[ComparisonType.INV_INCLUSIVE](False, True) == exclusive(False, True)
    assert compare_map[ComparisonType.LESS](1.1, 1.0) == less(1.1, 1.0)
    assert compare_map[ComparisonType.LESS_EQU](1.1, 1.0) == less_equ(1.1, 1.0)
    assert compare_map[ComparisonType.GREATER](1.0, 1.1) == greater(1.0, 1.1)
    assert compare_map[ComparisonType.GREATER_EQU](1.0, 1.1) == greater_equ(1.0, 1.1)
    assert compare_map[ComparisonType.IS_IN](3, Range(0.2, 1.0)) == is_in(3, Range(0.2, 1.0))
    assert compare_map[ComparisonType.IS_SUPERSET](Range(0.2, 1.0), 3) == is_superset(Range(0.2, 1.0), 3)
