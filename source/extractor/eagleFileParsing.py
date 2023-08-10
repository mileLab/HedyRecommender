import re
import traceback
from dataclasses import fields
from typing import Optional, Union
from xml.etree import ElementTree as ET

import shapely.ops
from packaging import version
from shapely.geometry import Point, LineString, Polygon, box
from shapely.geometry.base import BaseGeometry

from extractor.eagleFileUtils import discretize_arc, find_min_max_coeffs
from extractor.processPackaging import process_packaging
from extractor.typedefs.BoardTypes import SimplifiedBoard
from extractor.typedefs.EagleTypes import Stackup, CopperThickness, IsolateThickness, Rules, MinimalDistances, Topology, \
    Isolate, StopMaskLimits
from extractor.typedefs.typedef import SingleError, PackageInformation, ParsingError, PackageFailures, PackageMapping


def check_eagle_version(root: ET.Element, warnings: list[str]):
    v_str = parse_basic_str(root, 'version')
    v = version.parse(v_str)
    if v < version.parse("9.0.0"):
        warnings.append("The version of the eagle brd file seems to be old and can lead to several error. Please try "
                        "to reopen the project in a newer Eagle and save the brd file again.")


def parse_eagle_stackup(root: ET.Element) -> tuple[
    Stackup, Optional[CopperThickness], Optional[IsolateThickness], list[SingleError]]:
    layer_setup = ""
    copper_thicknesses = ""
    isolate_thicknesses = ""
    failures: list[SingleError] = []

    for rules in root.iter('designrules'):
        for param in rules.iter('param'):
            name = parse_basic_str(param, 'name', '')
            if name == 'layerSetup':
                layer_setup = parse_basic_str(param, 'value', '')
            elif name == 'mtCopper':
                copper_thicknesses = parse_basic_str(param, 'value', '')
            elif name == 'mtIsolate':
                isolate_thicknesses = parse_basic_str(param, 'value', '')

    if not layer_setup or layer_setup == "":
        raise RuntimeError("Could not find layer setup")
    try:
        stackup = parse_eagle_layer_stackup(layer_setup)
    except (RuntimeError, LookupError) as err:
        raise RuntimeError("Could not process layer setup") from err

    cu_thick = None
    if copper_thicknesses and copper_thicknesses != "":
        try:
            cu_thick_tokens = parse_copper_layers(copper_thicknesses)
            cu_thick = cleanup_copper_layers(copper=cu_thick_tokens, stackup=stackup)
        except (RuntimeError, LookupError) as e:
            cu_thick = None
            failures.append(SingleError(f"Could not parse copper layer. Error: {e}", traceback.format_exc()))

    iso_thick = None
    if isolate_thicknesses and isolate_thicknesses != "":
        try:
            iso_thick_tokens = parse_isolate_layers(isolate_thicknesses)
            iso_thick = merge_isolated_layers(iso=iso_thick_tokens, stackup=stackup)
        except (RuntimeError, LookupError) as e:
            iso_thick = None
            failures.append(SingleError(f"Could not parse isolate layer. Error: {e}", traceback.format_exc()))

    return stackup, cu_thick, iso_thick, failures


def parse_eagle_packaging(board: SimplifiedBoard, package_mapping: Optional[PackageMapping]) -> tuple[
    dict[str, Optional[PackageInformation]], ParsingError, PackageFailures]:
    failures: ParsingError = []
    failures_packaging: PackageFailures = {}

    if board.footprints is None:
        failures.append(SingleError("Could not parse packaging, because boards footprints could not be parsed."))
        return {}, failures, failures_packaging

    if package_mapping is None:
        failures.append(
            SingleError("Could not parse packaging, due to an critical error in parsing the package mapping."))
        return {}, failures, failures_packaging

    footprints = [f for f in board.footprints if f.package != "" and len(f.contacts) > 0]
    try:
        packaging_mapping = process_packaging(footprints, failures=failures_packaging, packaging_info=package_mapping)
    except (RuntimeError, LookupError, TypeError) as e:
        failures.append(SingleError(f"Critical error in parsing packaging. Error: {e}", traceback.format_exc()))
        packaging_mapping = {f.package: None for f in footprints}

    return packaging_mapping, failures, failures_packaging


def parse_eagle_rules(root: ET.Element) -> Rules:
    min_dist: dict[str, float] = {}
    min_dist_names = [f.name for f in fields(MinimalDistances)]

    stop_limit: list[float, float] = [0.0, 0.0]

    design_rules: dict[str, str] = {}
    for rules in root.iter('designrules'):
        for param in rules.iter('param'):
            name = parse_basic_str(param, 'name', '')
            value = parse_basic_str(param, 'value')

            design_rules[name] = value

    # minimal distances rules
    for name in min_dist_names:
        min_dist[name] = parse_eagle_value(design_rules[name])

    # clearance rules
    stop_perc = parse_eagle_value(design_rules["mvStopFrame"], unitless=True)
    stop_limit[0] = parse_eagle_value(design_rules["mlMinStopFrame"])
    stop_limit[1] = parse_eagle_value(design_rules["mlMaxStopFrame"])
    via_stop_limit = parse_eagle_value(design_rules["mlViaStopLimit"])

    return Rules(min_distances=MinimalDistances(**min_dist),
                 stop_mask_limits=StopMaskLimits(stop_limit=stop_limit, stop_perc=stop_perc,
                                                 via_stop_limit=via_stop_limit))


def parse_eagle_topology(root: ET.Element, failures: ParsingError) -> Topology:
    closed_objects = []
    possible_outer_bound: list[LineString] = []

    # find dimension layer
    for plain in root.iter('plain'):
        for element in plain.iter():
            tag = element.tag
            if tag not in ["wire", "rectangle", "circle", "polygon", "spline"]:
                continue
            layer = parse_basic_str(element, 'layer')
            if layer == "20":  # dimension layer
                try:
                    if tag == "wire":
                        possible_outer_bound.append(parse_wire(element, no_width=True))
                    elif tag == "rectangle":
                        closed_objects.append(parse_rectangle(element))
                    elif tag == "circle":
                        closed_objects.append(parse_circle(element))
                    elif tag == "polygon":
                        closed_objects.append(parse_polygon(element, no_width=True))
                    elif tag == "spline":
                        possible_outer_bound.append(parse_spline(element, no_width=True))
                except RuntimeError as e:
                    failures.append(
                        SingleError(f"Parse of geometric object {tag} failed with error: {e}", traceback.format_exc()))
                    continue

    millings = []
    # find milling layer
    for package in root.iter('packages'):
        for element in package.iter():
            tag = element.tag
            if tag not in ["wire", "rectangle", "circle", "polygon", "spline"]:
                continue
            layer = parse_basic_str(element, 'layer')
            if layer == "46":  # milling layer
                try:
                    if tag == "wire":
                        millings.append(parse_wire(element))
                    elif tag == "rectangle":
                        millings.append(parse_rectangle(element))
                    elif tag == "circle":
                        millings.append(parse_circle(element))
                    elif tag == "polygon":
                        millings.append(parse_polygon(element))
                    elif tag == "spline":
                        millings.append(parse_spline(element))
                except RuntimeError as e:
                    failures.append(
                        SingleError(f"Parse of geometric object {tag} failed with error: {e}", traceback.format_exc()))
                    continue

    if len(possible_outer_bound) == 0:
        raise RuntimeError(f"Critical error at parsing outer boundary, nothing found.")

    # Merge dimension objects into closed curves if possible
    try:
        linmerge = shapely.ops.linemerge(possible_outer_bound)
        if isinstance(linmerge, LineString):
            merged_lines: list[BaseGeometry] = [linmerge]
        else:
            merged_lines: list[BaseGeometry] = list(linmerge.geoms)
    except (RuntimeError, TypeError) as e:
        raise RuntimeError("Could not merge individual geometries from outer boundary") from e

    # identify open and closed polygons
    closed_polygons = [Polygon(line) for line in merged_lines if line.is_closed]
    open_lines = [line for line in merged_lines if not line.is_closed]
    closed_polygons.sort(key=lambda x: x.area, reverse=True)

    if len(closed_polygons) == 0:
        raise RuntimeError("Could not identify the outer boundary, no closed polygon in dimension layer found")
    outer_boundary = closed_polygons[0]

    return Topology(outer_boundary=outer_boundary, closed_objects=closed_polygons[1:] + closed_objects,
                    open_objects=open_lines, millings=millings)


def parse_two_points(elem: ET.Element) -> tuple[Point, Point]:
    p1 = Point(parse_basic_float(elem, 'x1'), parse_basic_float(elem, 'y1'))
    p2 = Point(parse_basic_float(elem, 'x2'), parse_basic_float(elem, 'y2'))
    return p1, p2


def parse_one_point(elem: ET.Element) -> Point:
    return Point(parse_basic_float(elem, 'x'), parse_basic_float(elem, 'y'))


def parse_unit(input: str) -> tuple[float, str]:
    unit = re.findall(r'[a-z,A-Z]+', input)
    if len(unit) != 1:
        raise RuntimeError(f"unexpected unit {unit}, parsing of value failed")
    unit = unit[0]

    value = input.replace(unit, "")
    value = float(value)

    return value, unit


def convert_to_mm(value: float, unit: str) -> float:
    # First convert to nano meter:
    unit_normalized = unit.lower()

    if "mil" in unit_normalized:
        nm = int(value * 25.4 * 10 ** 3)
    elif "in" in unit_normalized:
        nm = int(value * 25.4 * 10 ** 6)
    elif "mm" in unit_normalized:
        nm = int(value * 10 ** 6)
    elif "nm" in unit_normalized:
        nm = int(value)
    else:
        raise RuntimeError("Unkown unit {unit}, available are 'mil','in','mm','nm'")

    # Nanometer to mm
    return float(nm) / 10 ** 6


def parse_eagle_value(input: str, unitless: bool = False) -> float:
    if unitless:
        return float(input)
    value, unit = parse_unit(input)
    return convert_to_mm(value, unit)


def parse_basic_float(elem: ET.Element, id: str, default: Optional[float] = None) -> float:
    value = elem.get(id)
    if value is None:
        return get_default(default, elem.attrib)
    else:
        return float(value)


def parse_basic_int(elem: ET.Element, id: str, default: Optional[int] = None) -> int:
    value = elem.get(id)
    if value is None:
        return get_default(default, elem.attrib)
    else:
        return int(value)


def parse_basic_str(elem: ET.Element, id: str, default: Optional[str] = None) -> str:
    value = elem.get(id)
    if value is None:
        return get_default(default, elem.attrib)
    else:
        return str(value)


def get_default(default: Union[str, float, int, None], attribute: dict[str, str]) -> Union[str, float, int]:
    if default is not None:
        return default
    else:
        raise RuntimeError(f"Could not find {id} in xml element {attribute}")


def split_delimiter(input: str, delim: str) -> list[str]:
    list_parts = input.split(delim)
    result = []
    for e in list_parts:
        result.append(e)
        result.append(delim)
    result.pop()
    return result


def extract_number(input: str) -> int:
    if ':' in input:
        sides = input.split(':')
        if '[' in input:
            side = sides[1]
        else:
            side = sides[0]
        result = re.findall(r'\d+', side)
    else:
        result = re.findall(r'\d+', input)

    if len(result) != 1:
        print(f"Error in extracting number from {input}, got {result}")

    return int(result[0])


def parse_eagle_layer_stackup(stackup: str) -> Stackup:
    split_plus = split_delimiter(stackup, '+')
    split = []
    for s in split_plus:
        s_times = split_delimiter(s, '*')
        split.extend(s_times)

    stackup = {}
    for i, s in enumerate(split):
        if s != '+' and s != '*':
            continue
        s1 = extract_number(split[i - 1])
        s2 = extract_number(split[i + 1])
        # error handling
        if s1 > s2:
            print("Parser Warning: layers seem to be switched, reordering automatically ")
            s2, s1 = s1, s2
        if s1 == s2:
            raise RuntimeError("Parsing of layer stackup failed, identical layer values")

        # get right material
        if s == '+':
            stackup[(s1, s2)] = Isolate.PREPREG
        elif s == '*':
            stackup[(s1, s2)] = Isolate.CORE
    return stackup


def parse_copper_layers(copper_thicknesses: str) -> CopperThickness:
    thicknesses = parse_layer_thicknesses(copper_thicknesses)
    return {i + 1: thicknesses[i] for i in range(0, len(thicknesses))}  # 1 based


def parse_isolate_layers(isolate_thicknesses: str) -> IsolateThickness:
    thicknesses = parse_layer_thicknesses(isolate_thicknesses)
    return {(i + 1, i + 2): thicknesses[i] for i in range(0, len(thicknesses))}  # 1 based


def merge_isolated_layers(iso: IsolateThickness, stackup: Stackup) -> IsolateThickness:
    result = {}
    for s in stackup.keys():
        if s[0] == s[1] + 1:
            result[s] = iso[s]
        else:
            result[s] = iso[(s[0], s[0] + 1)]
    return result


def cleanup_copper_layers(copper: CopperThickness, stackup: Stackup) -> CopperThickness:
    result = {}
    for s in stackup.keys():
        result[s[0]] = copper[s[0]]
        result[s[1]] = copper[s[1]]  # duplicate entries will be overwritten anyway
    return result


def parse_layer_thicknesses(input: str) -> list[float]:
    thicknesses = input.split(sep=" ")
    result = []
    for thickness in thicknesses:
        result.append(parse_eagle_value(thickness))
    return result


def parse_wire(wire: ET.Element, no_width=False) -> LineString:
    p1, p2 = parse_two_points(wire)
    w = parse_basic_float(wire, "width", 0.0)
    c = parse_basic_float(wire, "curve", 0.0)

    if c != 0.0:
        points = discretize_arc(c, p1, p2)
    else:
        points = [p1, p2]

    if w == 0 or no_width:
        return LineString(points)
    else:
        return LineString(points).buffer(w)


def parse_rectangle(rect: ET.Element) -> box:
    p1, p2 = parse_two_points(rect)
    p1p2 = find_min_max_coeffs(p1, p2)
    return box(*p1p2)


def parse_circle(circ: ET.Element) -> Point:
    m = parse_one_point(circ)
    r = parse_basic_float(circ, 'radius')
    return m.buffer(r)


def parse_spline(spline: ET.Element, no_width=False) -> LineString:
    points = []
    for v in spline.iter('vertex'):
        points.append(parse_one_point(v))
    if len(points) == 0:
        raise RuntimeError('Could not parse vertices of spline')
    w = parse_basic_float(spline, 'width', 0.0)
    if w == 0.0 or no_width:
        return LineString(points)
    else:
        return LineString(points).buffer(w)


def parse_polygon(poly: ET.Element, no_width=False) -> Polygon:
    points = []
    for v in poly.iter('vertex'):
        points.append(parse_one_point(v))
    if len(points) == 0:
        raise RuntimeError('Could not parse vertices of polygon')

    w = parse_basic_float(poly, 'width', 0.0)
    if w == 0 or no_width:
        return Polygon(points)
    else:
        return Polygon(points).buffer(w)
