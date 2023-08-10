import math
from collections.abc import Sequence

import numpy
from shapely.geometry import Point


def discretize_arc(c: float, p1: Point, p2: Point) -> numpy.ndarray:
    center = convert_curve_to_center(p1, p2, c)
    angle = math.radians(c)
    start_angle = math.atan2(p2.y - center.y, p2.x - center.x)
    r = math.sqrt((center.x - p1.x) ** 2 + (center.y - p1.y) ** 2)
    # have at least points. put every 5 degrees a point
    seg_count = max(int(abs(c) / 5), 2) + 1
    # angle = start_angle - end_angle => end_angle = start_angle - angle
    theta = numpy.linspace(start_angle - angle, start_angle, seg_count)
    x = center.x + r * numpy.cos(theta)
    y = center.y + r * numpy.sin(theta)
    # safty to ensure that begin and endpoint match
    x[0] = p1.x
    x[-1] = p2.x
    y[0] = p1.y
    y[-1] = p2.y
    points = numpy.column_stack([x, y])
    return points


def find_min_max_coeffs(p1: Point, p2: Point) -> tuple[float, float, float, float]:
    return min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y)


def compute_min_max(input: Sequence, empty_value: float = 0.0) -> list[float]:
    return [min(input, default=empty_value), max(input, default=empty_value)]


def convert_curve_to_center(p1: Point, p2: Point, angle: float) -> Point:
    if angle == 0.0:
        raise RuntimeError("The angle of the circle is not allowed to be 0.0")
    dx, dy = p2.x - p1.x, p2.y - p1.y
    m = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
    length = p1.distance(p2)
    if length == 0.0:
        raise RuntimeError("The two points of the curve are identical")
    dist = length / (2 * math.tan(math.radians(angle) / 2))

    # center
    return Point(m.x - dist * (dy / length), m.y + dist * (dx / length))


def clamp(value: float, smallest: float, largest: float) -> float:
    return max(smallest, min(value, largest))


def test_and_compute_eagle_clearance(input_mask_clearance: float, stop_limit: list[float, float], size: list[float],
                                     mask_percentage: float) -> float:
    if stop_limit[0] <= input_mask_clearance <= stop_limit[1]:
        return input_mask_clearance
    else:
        return compute_eagle_clearance(mask_percentage, stop_limit, min(size))


def compute_eagle_clearance(mask_percentage: float, stop_limit: list[float, float], size: float) -> float:
    return clamp(size * mask_percentage, stop_limit[0], stop_limit[1])
