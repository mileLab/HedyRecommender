import math

from common.typedef import Range
from recommender.preferences.preferenceTypes import BoolPreference, ChoicePreference, RangePreference, \
    SingleChoicePreference, MultipleChoicePreference, ValueMagnitudePreference, ZonePreference, CustomTypeInstance
from recommender.typedefs.typedef import ComparisonType


def distance_preference(d: CustomTypeInstance, s: CustomTypeInstance) -> float:
    """
    Main dispatch function for preference comparison
    :param d: Value for demand, wrapped in a SpecificTypeInstance
    :param s: Value for supplier, wrapped in a SpecificTypeInstance
    :return: The normalized distance of the demand and supplier value
    """
    if isinstance(d, CustomTypeInstance) and isinstance(s, CustomTypeInstance):
        if isinstance(d.base_type, BoolPreference) and isinstance(s.base_type, BoolPreference):
            return distance_bool_preferences(d.value, s.value, d.base_type)
        if isinstance(d.base_type, ChoicePreference) and isinstance(s.base_type, ChoicePreference):
            if d.base_type != s.base_type:
                raise RuntimeError(
                    f"Mixed up subclasses of ChoicePreference, got {type(d).__name__} and {type(s).__name__}.")
            return distance_list_preferences(d.value, s.value, d.base_type)
        if isinstance(d.base_type, RangePreference) and isinstance(s.base_type, RangePreference):
            return distance_range_preferences(d.value, s.value, d.base_type)
        if isinstance(d.base_type, ValueMagnitudePreference) and isinstance(s.base_type, ValueMagnitudePreference):
            return distance_value_magnitude_preference(d.value, s.value, d.base_type)
        if isinstance(d.base_type, ZonePreference) and isinstance(s.base_type, ZonePreference):
            return distance_zone_preference(d.value, s.value, d.base_type)
        raise RuntimeError(
            f"Mixed up subclasses of CustomTypeInstances to preference comparison, got {type(d).__name__} and {type(s).__name__}.")
    raise RuntimeError(
        f"Unexpected or mixed up input type to preference comparison, got {type(d).__name__} and {type(s).__name__}.")


def distance_range_preferences(d: RangePreference.type, s: RangePreference.type, base_type: RangePreference) -> float:
    dist = abs(d - s)
    weighted_distance = base_type.importance * dist
    return weighted_distance


def distance_bool_preferences(d: BoolPreference.type, s: BoolPreference.type, base_type: BoolPreference) -> float:
    if not isinstance(d, bool) or not isinstance(s, bool):
        raise RuntimeError(
            f"Preference values do have the expected type {base_type.type.__name__}, got {type(d).__name__} and {type(s).__name__}")

    if base_type.comparison_type == ComparisonType.EXACT_MATCH:
        dist = 1 - float(d == s)
    elif base_type.comparison_type == ComparisonType.INCLUSIVE:
        dist = 1 - float(s or d == s)
    elif base_type.comparison_type == ComparisonType.INV_INCLUSIVE:
        dist = 1 - float(not s or d == s)
    else:
        raise RuntimeError(f"Unsupported comparison of base_type, got {base_type.comparison_type}.")

    weighted_distance = dist - dist * (1 - base_type.importance) ** 2

    return weighted_distance


# Note, this is not a metric in the mathematical sense, cause is non-symmetric
def distance_list_preferences(d: ChoicePreference.type, s: ChoicePreference.type, base_type: ChoicePreference) -> float:
    if not isinstance(d, list) or not isinstance(s, list):
        raise RuntimeError(
            f"Preference values do have the expected type {base_type.type}, got {type(d).__name__} and {type(s).__name__}")
    if not all([isinstance(v, bool) for v in d]) or not all([isinstance(v, bool) for v in s]):
        raise RuntimeError(f"Not all values of input values are list of bool, got {d} and {s}")

    if len(d) != len(s):
        raise RuntimeError(
            f"Size of value of input preferences do not match, got length demand {len(d)} and length supplier {len(s)}")

    if isinstance(base_type, MultipleChoicePreference):
        # multiple choice
        return distance_multiple_choice(d, s, base_type)

    elif isinstance(base_type, SingleChoicePreference):
        # single choice
        return distance_single_choice(d, s, base_type)
    else:
        raise RuntimeError(f"Unknown base type '{type(base_type).__name__}'")


def distance_single_choice(d: SingleChoicePreference.type, s: SingleChoicePreference.type,
                           base_type: SingleChoicePreference) -> float:
    if d.count(True) != 1 or s.count(True) != 1:
        raise RuntimeError(
            f"Input value is supposed to be a single choice value, got not exactly one True entry. Got {d} and {s}")

    if base_type.ordered:
        # find each first index and calculate the difference (range: 0 -- (len -1))
        # no distinction if demand or supplier is left or right of each other
        distance = abs(d.index(True) - s.index(True))
        if len(d) == 1:
            normalized_distance = 0.0
        else:
            normalized_distance = float(distance / (len(d) - 1))  # range 0--1
        weighted_distance = base_type.importance * normalized_distance

    else:
        # all entries must be equal, distance is 0 if all are equal, otherwise 1
        distance = 1 - float(all([d_val == s_val for (d_val, s_val) in zip(d, s)]))
        weighted_distance = distance - distance * (1 - base_type.importance) ** 2
    return weighted_distance


def distance_multiple_choice(d: MultipleChoicePreference.type, s: MultipleChoicePreference.type,
                             base_type: MultipleChoicePreference) -> float:
    count_overlap = sum([int(d_val and s_val) for (d_val, s_val) in zip(d, s)])
    # count the number of overlapping d/s preferences wrt total, d or s preferences
    if base_type.comparison_type == ComparisonType.EXACT_MATCH:
        count_positive_ds = sum([int(d_val | s_val) for (d_val, s_val) in zip(d, s)])
        dist = 1 - float(count_overlap) / count_positive_ds if count_positive_ds > 0 else 0.0
    elif base_type.comparison_type == ComparisonType.INCLUSIVE:
        count_positive_d = sum([int(v) for v in d])
        dist = 1 - float(count_overlap / count_positive_d) if count_positive_d > 0 else 0.0
    elif base_type.comparison_type == ComparisonType.INV_INCLUSIVE:
        count_positive_s = sum([int(v) for v in s])
        dist = 1 - float(count_overlap / count_positive_s) if count_positive_s > 0 else 0.0
    else:
        raise RuntimeError(f"Unsupported comparison of base_type, got {base_type.comparison_type}.")

    weighted_distance = base_type.importance * dist
    return weighted_distance


def distance_value_magnitude_preference(d: ValueMagnitudePreference.type, s: ValueMagnitudePreference.type,
                                        base_type: ValueMagnitudePreference) -> float:
    e = 1 + base_type.importance
    dval, sval = math.log(abs(d) + 1), math.log(abs(s) + 1)

    # dval == sval == 0, then we have a division by 0
    if dval == sval:
        score = 1
    else:
        score = 2 * min(dval ** e, sval ** e) / (dval ** e + sval ** e)
    weighted_distance = 1 - score
    return weighted_distance


def distance_zone_preference(d: ZonePreference.type, s: ZonePreference.type, base_type: ZonePreference) -> float:
    if not isinstance(d, (float, int)):
        raise RuntimeError(f"ZonePreference requires a float or int as demand value, got '{type(d).__name__}'.")

    s_unified = s
    if isinstance(s, (int, float)):
        s_unified = Range(min=s, max=s)

    if s_unified.min <= d <= s_unified.max:
        weighted_distance = 0.0
    else:
        distance, boundary = (abs(s_unified.min - d), s_unified.min) if d <= s_unified.min else (
        abs(s_unified.max - d), s_unified.max)
        relative_distance = float(distance) / boundary if boundary != 0 else float(distance)
        e = 1 + base_type.importance
        weighted_distance = 1 - 1.0 / ((1 + relative_distance) ** e)

    return weighted_distance
