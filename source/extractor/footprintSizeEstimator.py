import shapely.ops
from shapely import affinity
from shapely.geometry import Polygon, LineString, Point, box, LinearRing

from extractor.eagleFileUtils import discretize_arc, find_min_max_coeffs
from extractor.typedefs.BoardTypes import Footprint, Segment, Rectangle, Circle, Arc, Poly, ContactItem

try:
    import extractor.plotting.generatePlots as generatePlots

    can_plot = True
except ImportError:
    can_plot = False
    generatePlots = None


def estimate_footprint_size(fp: Footprint) -> list[float]:
    generate_plot = False
    # convert the input to shapely objects and assign to the right class.
    closed_geometries, geometric_objects_initial = convert_to_shapely_geometries(fp)

    # remove duplicates
    geometric_objects = [v1 for i, v1 in enumerate(geometric_objects_initial) if
                         not any(v1 == v2 for v2 in geometric_objects_initial[:i])]

    # identify closed geometries by merging the open ones
    open_geometries = categorize_geometries(closed_geometries, geometric_objects)

    # assign rectangles to pads
    closed_assignment_map, unassigned_pads = assign_closed_geometries_to_pads(closed_geometries, fp)

    # remove some closed geometries, cause they may not contribute to the size of the package
    removed_rectangles, cleaned_closed_geometries = cleanup_closed_geometries(closed_assignment_map, closed_geometries,
                                                                              open_geometries)

    final_shape, obb_all, size = find_package_boundary(cleaned_closed_geometries, open_geometries)

    if generate_plot and can_plot:
        final_shape_with_pads, obb_all_with_pads, size_with_pads = find_package_boundary(closed_geometries,
                                                                                         open_geometries)
        generatePlots.generate_plots(cleaned_closed_geometries, closed_assignment_map, closed_geometries, final_shape,
                                     final_shape_with_pads, fp, geometric_objects_initial, obb_all, obb_all_with_pads,
                                     open_geometries, removed_rectangles, unassigned_pads)

    return size


def convert_to_shapely_geometries(fp: Footprint) -> tuple[dict[str, list[Polygon]], list[LineString]]:
    geometric_objects: list[LineString] = []
    closed_geometries: dict[str, list[Polygon]] = {"circles": [], "rectangles": [], "polygons": []}
    for drawing in fp.drawings:
        if isinstance(drawing, Segment):
            geometric_objects.append(LineString([drawing.start, drawing.end]))
        elif isinstance(drawing, Rectangle):
            p1p2 = find_min_max_coeffs(Point(drawing.start), Point(drawing.end))
            closed_geometries["rectangles"].append(box(*p1p2))
        elif isinstance(drawing, Circle):
            c = Point(drawing.center).buffer(drawing.radius)
            closed_geometries["circles"].append(c)
        elif isinstance(drawing, Arc):
            points = discretize_arc(drawing.angle, Point(drawing.start), Point(drawing.end))
            geometric_objects.append(LineString(points))
        elif isinstance(drawing, Poly):
            p = Polygon(drawing.points)
            if abs(p.area - p.minimum_rotated_rectangle.area) / p.area < 0.01:
                closed_geometries["rectangles"].append(p)
            else:
                closed_geometries["polygons"].append(p)
    return closed_geometries, geometric_objects


def categorize_geometries(closed_geometries: dict[str, list[Polygon]], uncategorized_geometries: list[LineString]) -> \
        list[LineString]:
    open_geometries: list[LineString] = []
    progress = True
    trying_sanitizing = False
    while progress:
        open_geometries, rect, poly = categorize_open_closed(uncategorized_geometries)
        closed_geometries["rectangles"] += rect
        closed_geometries["polygons"] += poly

        # if there are no or only one open geometries left, break
        if len(open_geometries) < 2:
            break
        # try to merge them to
        union = shapely.ops.unary_union(open_geometries)
        if isinstance(union, LineString):
            uncategorized_geometries = [union]
        else:
            uncategorized_geometries = list(union.geoms)

        progress = len(uncategorized_geometries) < len(open_geometries)
        if not progress:
            if not trying_sanitizing:
                # sanitize line strings for once
                sanitize_linestrings(uncategorized_geometries)
                trying_sanitizing = True
                progress = True
    return open_geometries


def cleanup_closed_geometries(closed_assignment_map: dict[(int, str), Polygon],
                              closed_geometries: dict[str, list[Polygon]], open_geometries: list[LineString], pads=True,
                              circles=True) -> tuple[list[Polygon], dict[str, list[Polygon]]]:
    removed_closed_geoms = []

    # first create copy and then remove the already assigned closed geometries
    cleaned_closed_geometries: dict[str, list[Polygon]] = {t: [geom for geom in sublist] for t, sublist in
                                                           closed_geometries.items()}
    # removed pads from the potential package, larger index first is more efficient
    for i, t in reversed(closed_assignment_map.keys()):
        removed_closed_geoms.append(cleaned_closed_geometries[t][i])
        del cleaned_closed_geometries[t][i]

    union_open_geoms = shapely.ops.unary_union(open_geometries)
    conv_hull = union_open_geoms.convex_hull

    for i, cl in enumerate(closed_geometries["circles"]):
        other_union = shapely.ops.unary_union(
            [geom for sublist in closed_geometries.values() for j, geom in enumerate(sublist) if geom != cl])
        other_union = other_union.union(conv_hull)
        if other_union.is_empty:
            break

        d = other_union.distance(cl)
        if d != 0.0 and not other_union.intersects(cl):
            removed_closed_geoms.append(cl)
            del cleaned_closed_geometries["circles"][i]

    return removed_closed_geoms, cleaned_closed_geometries


def assign_closed_geometries_to_pads(closed_geometries: dict[str, list[Polygon]], fp) -> tuple[
    dict[(int, str), Polygon], list[Polygon]]:
    pad_assignments = [[generate_rectangle_from_pad(p), False] for p in fp.contacts]
    closed_assignment_map: dict[(int, str), Polygon] = {}
    # a pad is sometimes also indicated as circle, use those as well
    for t in closed_geometries.keys():
        for i, rectangle in enumerate(closed_geometries[t]):
            pad_assignments.sort(key=lambda x: rectangle.centroid.distance(x[0].minimum_rotated_rectangle.centroid),
                                 reverse=False)
            # rectangle_obb = rectangle.minimum_rotated_rectangle
            candidates = []
            for j, p in enumerate(pad_assignments):
                pad: Polygon = p[0]
                assigned: bool = p[1]
                if assigned:
                    continue
                if not pad.intersects(rectangle):
                    break
                overlap_area = rectangle.intersection(pad).area

                # at least 90% overlap of the area for rectangle and Pad
                if overlap_area / rectangle.area > 0.9 and overlap_area / pad.area > 0.9:
                    candidates.append((j, 0.5 * (overlap_area / rectangle.area + overlap_area / pad.area)))
                    continue
                # if overlap_area / rectangle.area > 0.95 and overlap_area / pad.area > 0.30:
                #     continue
                # at least 95% overlap of the rectangle, but a sufficiently large percentage of the pad is also covered
                if overlap_area / rectangle.area > 0.97 and overlap_area / pad.area > 0.25:
                    candidates.append((j, 0.5 * (overlap_area / rectangle.area + overlap_area / pad.area)))
                    continue

            if len(candidates) > 0:
                candidates.sort(key=lambda x: x[1], reverse=True)
                best_candidate = candidates[0]
                index = best_candidate[0]
                pad_assignments[index][1] = True

                closed_assignment_map[(i, t)] = pad_assignments[index][0]

    unassigned_pads = [p[0] for p in pad_assignments if not p[1]]
    return closed_assignment_map, unassigned_pads


def find_package_boundary(closed_geoms: dict[str, list[Polygon]], open_geometries: list[LineString]):
    # deciding, what defines the package size:
    # using bounding box of footprint as reference
    # if no closed geoms exists or they are not sufficiency large, use overall bounding box
    # otherwise, dimensions of largest closed box

    closed_geoms = [geom for sublist in closed_geoms.values() for geom in sublist]
    union_all_objects = shapely.ops.unary_union([g.boundary for g in closed_geoms] + open_geometries)
    obb_all = union_all_objects.minimum_rotated_rectangle
    if len(closed_geoms) > 0:
        closed_geoms.sort(key=lambda x: x.area, reverse=True)
        maximum_closed_geometry = closed_geoms[0]
        obb_closed = maximum_closed_geometry.minimum_rotated_rectangle

        if obb_closed.area / obb_all.area > 0.8:
            # at least 80% of the area is covered
            size = get_dimension_bounding_box(obb_closed)
            final_shape = obb_closed
        else:
            size = get_dimension_bounding_box(obb_all)
            final_shape = obb_all
    else:
        size = get_dimension_bounding_box(obb_all)
        final_shape = obb_all
    return final_shape, obb_all, size


def categorize_open_closed(geometric_objects: list[LineString]) -> tuple[
    list[LineString], list[Polygon], list[Polygon]]:
    open: list[LineString] = []
    rectangles: list[Polygon] = []
    polygons: list[Polygon] = []

    # try to merge connected lines into line string
    connected_lines = shapely.ops.linemerge(geometric_objects)
    if isinstance(connected_lines, LineString):
        merged_lines: list[LineString] = [connected_lines]
    else:
        merged_lines: list[LineString] = list(connected_lines.geoms)
    # identify closed line strings (rectangle or polygon)
    for linestring in merged_lines:
        # ignore those, which can never be closed
        if len(linestring.coords) < 3:
            open.append(linestring)
            continue

        # check if closing the linestring changes its length => open/closed
        linering = LinearRing(linestring)
        is_closed = False
        if abs(linestring.length - linering.length) / linering.length < 0.01:
            is_closed = True

        # check if area of oriented_bounding box is different from closed polygon => rectangle
        poly = Polygon(linestring)
        if poly.area == 0:
            open.append(linestring)
        elif abs(poly.area - poly.minimum_rotated_rectangle.area) / poly.area < 0.01:
            # sometimes footprints are drawn lazy, ignoring the closing line (its a part of a longer line)
            rectangles.append(poly)
        else:
            if is_closed:
                polygons.append(poly)
            else:
                open.append(linestring)

    return open, rectangles, polygons


def get_dimension_bounding_box(box: Polygon) -> list[float, float]:
    # get coordinates of polygon vertices
    x, y = box.exterior.coords.xy
    # get length of bounding box edges
    edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
    # get length of polygon as the longest edge of the bounding box
    length = max(edge_length)
    # get width of polygon as the shortest edge of the bounding box
    width = min(edge_length)
    return [length, width]


def sanitize_linestrings(linestrings: list[LineString]):
    linestrings.sort(key=lambda x: x.length, reverse=True)
    visited = [False] * len(linestrings)

    for i in range(0, len(linestrings)):
        visited[i] = True
        ls = linestrings[i]
        for j in range(0, len(linestrings)):
            if visited[j]:
                continue
            ls_other = linestrings[j]
            # forward, backward = shapely.ops.shared_paths(ls,ls_other)
            difference = ls_other.difference(ls)

            if not difference.is_empty and difference != ls_other:
                linestrings[j] = difference

    visited = [False] * len(linestrings)
    for i in range(0, len(linestrings)):
        ls = linestrings[i]
        x, y = ls.coords.xy
        visited[i] = True
        for j in range(0, len(linestrings)):
            if visited[j]:
                continue
            ls_other = linestrings[j]
            x_other, y_other = ls_other.coords.xy
            if (x[-1] == x_other[-1] and y[-1] == y_other[-1]) or (x[1] == x_other[1] and y[1] == y_other[1]):
                linestrings[j] = shapely.ops.transform(_reverse, ls_other)
                visited[j] = True


def _reverse(x, y):
    return x[::-1], y[::-1]


def generate_rectangle_from_pad(pad: ContactItem) -> Polygon:
    geom = box(pad.center[0] - pad.size[0] * 0.5, pad.center[1] - pad.size[1] * 0.5, pad.center[0] + pad.size[0] * 0.5,
               pad.center[1] + pad.size[1] * 0.5)
    geom = affinity.rotate(geom, pad.orientation, tuple(pad.center))
    return geom
