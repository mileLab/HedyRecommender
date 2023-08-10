from collections.abc import Callable
from typing import TypeVar, overload

from common.typedef import Range
from recommender.parameters.parameterTypes import ParameterTypes, NumberTypes
from recommender.typedefs.typedef import ComparisonType
from recommender.typedefs.typedef import ValidityResult

T = TypeVar('T')


def exact_match(d: ParameterTypes, s: ParameterTypes) -> ValidityResult:
    if d == s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand parameter {d} does not exactly match supplier parameter {s}")


def inclusive(d: bool, s: bool) -> ValidityResult:
    if s or d == s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand requirement {d} is not supported by supplier ({s})")


def exclusive(d: bool, s: bool) -> ValidityResult:
    if not s or d == s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand {d} cannot accept suppliers requirement {s}")


def less(d: NumberTypes, s: NumberTypes) -> ValidityResult:
    if d < s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand value {d} is larger than or equal supplier value {s}")


def greater(d: NumberTypes, s: NumberTypes) -> ValidityResult:
    if d > s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand value {d} is smaller than or equal supplier value {s}")


def less_equ(d: NumberTypes, s: NumberTypes) -> ValidityResult:
    if d <= s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand value {d} is larger than supplier value {s}")


def greater_equ(d: NumberTypes, s: NumberTypes) -> ValidityResult:
    if d >= s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand value {d} is smaller than supplier value {s}")


@overload
def is_in(d: T, s: list[T]) -> ValidityResult:
    ...


@overload
def is_in(d: Range[T], s: Range[T]) -> ValidityResult:
    ...


@overload
def is_in(d: T, s: Range[T]) -> ValidityResult:
    ...


def is_in(d, s) -> ValidityResult:
    if isinstance(s, Range):
        if isinstance(d, Range):
            return is_in_range_range(d, s)
        else:
            return is_in_value_range(d, s)
    if isinstance(s, list):
        if isinstance(d, Range):
            raise TypeError(f"Wrong combination of Arguments, got Range and List: {d} and {s}")
        return is_in_single_list(d, s)
    raise TypeError(f"Got some other argument, got {type(d).__name__} and {type(s).__name__}: {d} and {s}")


def is_in_value_range(d: T, s: Range[T]) -> ValidityResult:
    if not isinstance(d, (float, int)):
        raise TypeError(f"Expected first parameter to be int or float, got {type(d).__name__}.")
    if not isinstance(s, Range):
        raise TypeError(f"Expected second parameter to be Range[int] or Range[float], got {type(s).__name__}.")

    if s.min <= d <= s.max:
        return ValidityResult(valid=True)
    elif d < s.min:
        return ValidityResult(valid=False,
                              error=f"Demand value {d} is smaller than lower bound of supplier range [{s.min},{s.max}]")
    elif d > s.max:
        return ValidityResult(valid=False,
                              error=f"Demand value {d} is larger than upper bound of supplier range [{s.min},{s.max}]")


def is_in_range_range(d: Range[T], s: Range[T]) -> ValidityResult:
    if not isinstance(d, Range):
        raise TypeError(f"Expected first parameter to be of type Range, got {type(d).__name__}.")
    if not isinstance(s, Range):
        raise TypeError(f"Expected second parameter to be of type Range, got {type(s).__name__}.")

    if d.min >= s.min and d.max <= s.max:
        return ValidityResult(valid=True)
    else:
        if d.min < s.min <= d.max <= s.max:
            return ValidityResult(valid=False,
                                  error=f"Lower bound of demand range [{d.min},{d.max}] is outside of supplier"
                                        f" range [{s.min},{s.max}]")
        elif d.max > s.max >= d.min >= s.min:
            return ValidityResult(valid=False,
                                  error=f"Upper bound of demand range [{d.min},{d.max}] is outside of supplier"
                                        f" range [{s.min},{s.max}]")
        else:
            return ValidityResult(valid=False, error=f"Demand range [{d.min},{d.max}] is outside of supplier range"
                                                     f" [{s.min},{s.max}]")


def is_in_single_list(d: T, s: list[T]) -> ValidityResult:
    if not isinstance(d, (float, int, str)) or isinstance(d, bool):
        raise TypeError(f"Expected first parameter to be of type float, int or str, got {type(d).__name__}.")
    if not isinstance(s, list):
        raise TypeError(f"Expected second parameter to be of type List, got {type(s).__name__}.")

    if d in s:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Demand value {d} not in supplier list {s}")


@overload
def is_superset(d: list[T], s: T) -> ValidityResult:
    ...


@overload
def is_superset(d: Range[T], s: Range[T]) -> ValidityResult:
    ...


@overload
def is_superset(d: Range[T], s: T) -> ValidityResult:
    ...


def is_superset(d, s) -> ValidityResult:
    if isinstance(d, Range):
        if isinstance(s, Range):
            return is_superset_range_range(d, s)
        else:
            return is_superset_range_value(d, s)
    if isinstance(d, list):
        if isinstance(s, Range):
            raise TypeError(f"Wrong combination of Arguments, got List and Range: {d} and {s}")
        return is_around_list_single(d, s)
    raise TypeError(f"Got some other argument, got {type(d).__name__} and {type(s).__name__}: {d} and {s}")


def is_superset_range_value(d: Range[T], s: T) -> ValidityResult:
    if not isinstance(s, (float, int)):
        raise TypeError(f"Expected second parameter to be int or float, got {type(s).__name__}.")
    if not isinstance(d, Range):
        raise TypeError(f"Expected first parameter to be Range[int] or Range[float], got {type(d).__name__}.")

    if d.min <= s <= d.max:
        return ValidityResult(valid=True)
    elif s < d.min:
        return ValidityResult(valid=False,
                              error=f"Supplier value {s} is smaller than lower bound of demand range [{d.min},{d.max}]")
    elif s > d.max:
        return ValidityResult(valid=False,
                              error=f"Supplier value {s} is larger than upper bound of demand range [{d.min},{d.max}]")


def is_superset_range_range(d: Range[T], s: Range[T]) -> ValidityResult:
    if not isinstance(d, Range):
        raise TypeError(f"Expected first parameter to be of type Range, got {type(d).__name__}.")
    if not isinstance(s, Range):
        raise TypeError(f"Expected second parameter to be of type Range, got {type(s).__name__}.")

    if s.min >= d.min and s.max <= d.max:
        return ValidityResult(valid=True)
    else:
        if s.min < d.min <= s.max <= d.max:
            return ValidityResult(valid=False,
                                  error=f"Lower bound of supplier range [{s.min},{s.max}] is outside of demand"
                                        f" range [{d.min},{d.max}]")
        elif s.max > d.max >= s.min >= d.min:
            return ValidityResult(valid=False,
                                  error=f"Upper bound of supplier range [{s.min},{s.max}] is outside of demand"
                                        f" range [{d.min},{d.max}]")
        else:
            return ValidityResult(valid=False, error=f"Supplier range [{s.min},{s.max}] is outside of demand range"
                                                     f" [{d.min},{d.max}]")


def is_around_list_single(d: list[T], s: T) -> ValidityResult:
    if not isinstance(s, (float, int, str)) or isinstance(s, bool):
        raise TypeError(f"Expected second parameter to be of type float, int or str, got {type(s).__name__}.")
    if not isinstance(d, list):
        raise TypeError(f"Expected first parameter to be of type List, got {type(d).__name__}.")

    if s in d:
        return ValidityResult(valid=True)
    else:
        return ValidityResult(valid=False, error=f"Supplier value {s} not in supplier list {d}")


# collect all comparisons
compare_map: dict[ComparisonType, Callable[[ParameterTypes, ParameterTypes], ValidityResult]] = {
    ComparisonType.EXACT_MATCH: exact_match,
    ComparisonType.INCLUSIVE: inclusive,
    ComparisonType.INV_INCLUSIVE: exclusive,
    ComparisonType.LESS: less,
    ComparisonType.LESS_EQU: less_equ,
    ComparisonType.GREATER: greater,
    ComparisonType.GREATER_EQU: greater_equ,
    ComparisonType.IS_IN: is_in,
    ComparisonType.IS_SUPERSET: is_superset
}
