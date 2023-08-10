import dataclasses
import itertools
import json
import os
import subprocess
import traceback
import xml.etree.ElementTree as ET
from operator import attrgetter
from pathlib import Path
from typing import Optional, Union, Any

from common.typedef import Range
from extractor.eagleFileParsing import check_eagle_version, parse_eagle_stackup, parse_eagle_packaging, \
    parse_eagle_rules, parse_eagle_topology
from extractor.eagleFileUtils import compute_min_max, test_and_compute_eagle_clearance, compute_eagle_clearance
from extractor.footprintSizeEstimator import estimate_footprint_size
from extractor.typedefs.BoardTypes import SimplifiedBoard, DrillType, Layer, FullDrill
from extractor.typedefs.EagleTypes import CopperThickness, Isolate, EagleBoardData
from extractor.typedefs.Files import File
from extractor.typedefs.parameters import PCBParameters
from extractor.typedefs.typedef import Failures, ExtractorSevereError, ExtractionError, \
    ParsingError, PackageInformation, SingleError, AdditionalParameterInfo, PackagingInfo, \
    ParameterInfo, PackageSize, PackageFailuresInformation, PackageMapping, PackagingType, ProductionMethod
from extractor.utils import create_temp_file, destroy_temp_file, OutOfProcess


def process_board_file(file: File, package_mapping: Optional[PackageMapping]) -> tuple[
    PCBParameters, Failures, AdditionalParameterInfo]:
    failures_parsing: ParsingError = []

    # create "persistent" tempfile, otherwise, it cannot be opened by another process
    try:
        tempfile = create_temp_file(file.content, file.type, file.encoding)
    except RuntimeError as e:
        raise ExtractorSevereError("Creation of temporary file failed") from e

    # get path to sbf converter
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'SBFConverter', 'sbf_converter.py')
    try:
        kicad = os.environ['KICAD_PYTHON_EXEC']
    except ValueError as e:
        raise ExtractorSevereError("KICAD_PYTHON_EXEC environment variable not set, could not start process")
    proc = OutOfProcess(kicad, [path])
    # print(f"[INFO]: Calling {os.path.join(source_dir, 'SBFConverter', 'sbf_converter.py')}  with python to parse {tempfile.name}")

    try:
        try:
            rc, out, err = proc.start(tempfile.name)
        except (RuntimeError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            raise ExtractorSevereError("Could not spawn conversion script") from e
        finally:
            proc.kill()

        # handle return code
        if rc == 0:

            try:
                # convert to json
                json_out = json.loads(out)
            except json.JSONDecodeError as e:
                raise ExtractorSevereError("Corrupted return data from external script, not a valid JSON") from e

            # convert to internal Board structure
            board_data = SimplifiedBoard(**json_out)
            failures_parsing = failures_parsing + board_data.failures

            packaging_mapping, failures_packaging, failures_package_mapping = parse_eagle_packaging(board=board_data,
                                                                                                    package_mapping=package_mapping)
            failures_parsing = failures_parsing + failures_packaging

        else:
            if rc == 1:
                raise ExtractorSevereError(f"Dependency error of converter: {err}")
            elif rc == 2:
                raise ExtractorSevereError(f"Could not open brd file: {err}")
            elif rc == 3:
                raise ExtractorSevereError(f"Severe internal script error: {err}")
            else:
                raise ExtractorSevereError(f"Unknown conversion error: {err}")

        # parse Eagle file for additional data
        eagle_data = parse_eagle_board_file(tempfile.name)
        failures_parsing = failures_parsing + eagle_data.failures

        # postprocessing of parsed data
        processed_packaging = processing_extracted_data(eagle=eagle_data, board=board_data,
                                                        packaging_mapping=packaging_mapping)

        # process obtained data
        param, failures_extraction, infos_parameter = extract_relevant_parameters(eagle=eagle_data, board=board_data,
                                                                                  package_mapping=processed_packaging)

        info_packaging = PackagingInfo(failures={
            p: PackageFailuresInformation(failure=failures_package_mapping[p], size=processed_packaging[p].size) for p
            in failures_package_mapping.keys()},
            success={p: pi for p, pi in processed_packaging.items() if
                     isinstance(pi, PackageInformation)})

        return param, Failures(extracting=failures_extraction, parsing=failures_parsing), AdditionalParameterInfo(
            warnings=eagle_data.warnings, info_parameter=infos_parameter, info_packaging=info_packaging)
    finally:
        # cleanup tempfile
        destroy_temp_file(tempfile)


def processing_extracted_data(eagle: EagleBoardData, board: SimplifiedBoard,
                              packaging_mapping: Optional[dict[str, Optional[PackageInformation]]]) -> Optional[
    dict[str, Union[PackageInformation, PackageSize]]]:
    if packaging_mapping is None:
        return None

    processed_packaging: dict[str, Union[PackageInformation, PackageSize]] = {}

    footprints = [f for f in board.footprints if f.package != "" and len(f.contacts) > 0]
    # remove none type and add sizing information
    for fp in footprints:
        if packaging_mapping[fp.package] is None:
            processed_packaging[fp.package] = PackageSize([0.0, 0.0])
        else:
            processed_packaging[fp.package] = packaging_mapping[fp.package]

        # estimate footprint size, if none is available
        if processed_packaging[fp.package].size == [0.0, 0.0]:
            size_without_pads = estimate_footprint_size(fp)
            processed_packaging[fp.package].size = size_without_pads

    return processed_packaging


def extract_relevant_parameters(eagle: EagleBoardData, board: SimplifiedBoard,
                                package_mapping: Optional[dict[str, Union[PackageInformation, PackageSize]]]) -> tuple[
    PCBParameters, ExtractionError, ParameterInfo]:
    stackup = eagle.stackup
    copper = eagle.copper_thickness
    iso = eagle.isolate_thickness
    rules = eagle.rules
    topo = eagle.topology

    failures_processing: ExtractionError = {}
    additional_information: ParameterInfo = {}

    min_max_emtpy = 0.0

    ### Layers
    p_n_layers = outer_layers = None
    if dependency_check(param="n_layers", inp={"layers": board.layers}, failures=failures_processing):
        p_n_layers = sum([layer.is_cu for layer in board.layers])
        outer_layers = [lay.id for lay in board.layers if (lay.is_cu and not lay.is_internal_Cu)]
        if copper is not None and p_n_layers != len(copper.keys()):
            raise RuntimeError("Critical Error in SBF conversion [different number of layers]")

    p_copper_thickness = None
    if dependency_check(param="copper_thickness", inp={"copper_thicknesses": copper}, failures=failures_processing):
        p_copper_thickness = Range.from_list(compute_min_max(list(copper.values()), min_max_emtpy))

    p_prepreg_thickness = p_core_thickness = None
    if dependency_check(param=["prepreg_thickness", "core_thickness"], inp={"layer_stackup": stackup},
                        failures=failures_processing):
        list_prepreg = [iso[l12] for l12 in stackup.keys() if stackup[l12] == Isolate.PREPREG]
        p_prepreg_thickness = Range.from_list(compute_min_max(list_prepreg, min_max_emtpy))

        list_core = [iso[l12] for l12 in stackup.keys() if stackup[l12] == Isolate.CORE]
        p_core_thickness = Range.from_list(compute_min_max(list_core, min_max_emtpy))

    ### Board
    p_width = p_height = None
    if dependency_check(param=["width", "height"], inp={"board_dimensions": board.board}, failures=failures_processing):
        p_width = board.board.width
        p_height = board.board.height
        # width is always the longest side!
        if p_width < p_height: p_height, p_width = p_width, p_height

    p_thickness = None
    if dependency_check(param="thickness", inp={"copper_thicknesses": copper, "isolate_thicknesses": iso},
                        failures=failures_processing):
        p_thickness = sum(copper.values()) + sum(iso.values())

    ### Drills and Vias
    drill_parameter_list = ["n_via", "n_buried_via", "n_blind_via", "n_through_via", "n_PTH", "n_NPTH",
                            "drill_size_PTH", "drill_size_NPTH", "drill_size_VIA", "p_drill_size"]
    p_drill_size_PTH = p_drill_size_NPTH = p_drill_size_VIA = p_drill_size = None
    n_buried = n_via = n_blind = n_through = n_PTH = n_NPTH = None
    if dependency_check(param=drill_parameter_list, inp={"drills": board.drills}, failures=failures_processing):
        sizes = {}
        counts = {}
        for drill_type in DrillType:
            if drill_type in [DrillType.PTH, DrillType.NPTH]:
                # Those drills can be oval as well, take its max and its min
                sizes[drill_type] = [min([min(d.diameter) for d in board.drills if d.type == drill_type]),
                                     max([max(d.diameter) for d in board.drills if d.type == drill_type])]
                counts[drill_type] = len([d for d in board.drills if d.type == drill_type])
            else:
                d_sizes = [d.diameter for d in board.drills if d.type == drill_type]
                sizes[drill_type] = compute_min_max(d_sizes, min_max_emtpy)
                counts[drill_type] = len(d_sizes)

        via_set = [DrillType.VIA_THROUGH, DrillType.VIA_MICROVIA, DrillType.VIA_BLIND_BURIED]

        if dependency_check(param=["n_buried_via", "n_blind_via"], inp={"layers": board.layers},
                            failures=failures_processing):
            n_buried = len([d for d in board.drills if (
                    d.type == DrillType.VIA_BLIND_BURIED and (
                    d.layers[0] in outer_layers or d.layers[1] in outer_layers))])
            n_blind = counts[DrillType.VIA_BLIND_BURIED] - n_buried

        n_via = sum([counts[via_t] for via_t in via_set])

        n_through = counts[DrillType.VIA_THROUGH]
        n_PTH = counts[DrillType.PTH]
        n_NPTH = counts[DrillType.NPTH]

        p_drill_size_PTH = Range.from_list(sizes[DrillType.PTH])
        p_drill_size_NPTH = Range.from_list(sizes[DrillType.NPTH])
        p_drill_size_VIA = Range.from_list([min([sizes[i][0] for i in via_set if counts[i] > 0], default=min_max_emtpy),
                                            max([sizes[i][1] for i in via_set if counts[i] > 0],
                                                default=min_max_emtpy)])
        p_drill_size = Range.from_list([min([sizes[i][0] for i in DrillType if counts[i] > 0], default=min_max_emtpy),
                                        max([sizes[i][1] for i in DrillType if counts[i] > 0], default=min_max_emtpy)])

    ### Tracks
    p_trace_width = None
    if dependency_check(param="trace_width", inp={"tracks": board.tracks}, failures=failures_processing):
        t_width = [t.width for t in board.tracks]
        p_trace_width = Range.from_list(compute_min_max(t_width, min_max_emtpy))

    ### Clearance
    p_trace_clearance = None
    if dependency_check(param="trace_clearance", inp={"design_rules": rules}, failures=failures_processing):
        p_trace_clearance = min([v for v in dataclasses.asdict(rules.min_distances).values() if v is not None])

    p_solder_mask_clearance = None
    if dependency_check(param="solder_mask_clearance", inp={"desgn_rules": rules}, failures=failures_processing):
        stop_limit = rules.stop_mask_limits.stop_limit
        stop_percent = rules.stop_mask_limits.stop_perc
        via_stop_limit = rules.stop_mask_limits.via_stop_limit
        p_solder_mask_clearance = compute_solder_mask_clearance(board, failures_processing, stop_limit, stop_percent,
                                                                via_stop_limit)

    ### Components

    # use set-comprehension {} here to get rid of duplicate values
    p_assembly_sides = None
    if dependency_check(param="assembly_sides", inp={"footprints": board.footprints, "layers": board.layers},
                        failures=failures_processing):
        p_assembly_sides = len({fp.layer for fp in board.footprints if fp.layer in outer_layers})

    footprints = []
    p_n_components = p_components_per_type = None
    if dependency_check(param=["n_components", "components_per_type"], inp={"footprints": board.footprints},
                        failures=failures_processing):
        # collect all relevant footprints
        footprints = [f for f in board.footprints if f.package != "" and len(f.contacts) > 0]
        # there might be components, which don't have pads or no package type (some artificially one for visualization)
        p_n_components = len([fp for fp in footprints if len(fp.contacts) > 0])

        get_attr = attrgetter('package')
        p_components_per_type = {p: len([fp for fp in list(g)])
                                 for p, g in itertools.groupby(sorted(footprints, key=get_attr), get_attr)}
        if p_n_components != sum(p_components_per_type.values()):
            raise RuntimeError("Inconsistent packaging counts")

    ### Topology
    p_inner_milling = None
    if dependency_check(param="inner_milling", inp={"board_topology": topo}, failures=failures_processing):
        boundary = topo.outer_boundary
        p_inner_milling = False
        additional_information["inner_milling"] = []
        # as it seems, the milling layer does not give information about inner millings, it is used for description of
        # so called slots.
        for inner in topo.open_objects + topo.closed_objects:
            if boundary.contains(inner):
                p_inner_milling = True

                # additional information
                if inner in topo.open_objects:
                    reason = "from open objects set"
                elif inner in topo.closed_objects:
                    reason = "from closed objects set"
                else:
                    # unused now
                    reason = "from the milling layer"
                additional_information["inner_milling"].append(
                    f"Inner millings detected due to object {inner} {reason} found inside outer boundary {boundary}.")
                # collect all detected inner millings for debugging purposes

    ### PackagingType
    p_packaging_count = p_n_different_packaging_types = None
    if dependency_check(param=["packaging_count", "n_different_packaging_types"],
                        inp={"footprints": board.footprints, "package_mapping": package_mapping},
                        failures=failures_processing):

        p_packaging_count = {pt: 0 for pt in PackagingType}
        for f in footprints:
            info = package_mapping[f.package]
            if isinstance(info, PackageInformation):
                p_packaging_count[info.packaging_type] += 1
        p_n_different_packaging_types = sum([p > 0 for p in p_packaging_count.values()])

    ### Packaging Size
    p_component_size_length = p_component_size_width = None
    if dependency_check(param=["component_size_length,component_size_width"],
                        inp={"footprints": board.footprints, "package_mapping": package_mapping},
                        failures=failures_processing):

        package_sizes: list[list[float]] = [[], []]
        for f in footprints:
            info = package_mapping[f.package]
            if isinstance(info, PackageSize):
                package_sizes[0].append(info.size[0])  # length
                package_sizes[1].append(info.size[1])  # width

        p_component_size_length = compute_min_max(package_sizes[0])
        p_component_size_width = compute_min_max(package_sizes[1])

    #### Put parameters together
    return PCBParameters(production_method=ProductionMethod.PCB_ASSEMBLY,
                         length=p_width,
                         width=p_height,
                         height=p_thickness,
                         assembly_sides=p_assembly_sides,
                         n_layers=p_n_layers,
                         inner_milling=p_inner_milling,
                         drill_size=p_drill_size,
                         drill_size_PTH=p_drill_size_PTH,
                         drill_size_NPTH=p_drill_size_NPTH,
                         drill_size_via=p_drill_size_VIA,
                         packaging_count={p.value: c for p, c in p_packaging_count.items()},
                         n_components=p_n_components,
                         n_components_per_package=p_components_per_type,
                         component_size_length=p_component_size_length,
                         component_size_width=p_component_size_width,
                         n_different_packaging_types=p_n_different_packaging_types,
                         copper_thickness=p_copper_thickness,
                         trace_width=p_trace_width,
                         prepreg_thickness=p_prepreg_thickness,
                         trace_clearance=p_trace_clearance,
                         solder_mask_clearance=p_solder_mask_clearance,
                         core_thickness=p_core_thickness,
                         n_via=n_via,
                         n_blind_via=n_blind,
                         n_buried_via=n_buried,
                         n_through_hole_via=n_through,
                         n_PTH=n_PTH,
                         n_NPTH=n_NPTH,
                         ), failures_processing, additional_information


def compute_solder_mask_clearance(board: SimplifiedBoard, failures_processing: ExtractionError, stop_limit: list[float],
                                  stop_percent: float,
                                  via_stop_limit: float) -> Optional[list[float]]:
    if stop_limit[0] == stop_limit[1]:
        # if upper bound equals lower bound, then the clearance equals those bounds
        return stop_limit
    else:
        if dependency_check(param="solder_mask_clearance", inp={"footprints": board.footprints, "drills": board.drills},
                            failures=failures_processing):
            mask_clearances: list[float] = []

            # first all the board footprints
            for fp in board.footprints:
                for c in fp.contacts:
                    if c.solder_mask_clearance is not None:  # if solder mask is not disabled for contact
                        mask_clearances.append(
                            test_and_compute_eagle_clearance(c.solder_mask_clearance, stop_limit, c.size, stop_percent))

            # second all the drills and vias (need not be part of footprint)
            for d in board.drills:
                if isinstance(d, FullDrill):
                    mask_clearances.append(
                        test_and_compute_eagle_clearance(d.solder_mask_margin, stop_limit, d.diameter, stop_percent))
                else:
                    # only consider vias with diameter larger than via_stop_limit
                    if d.diameter > via_stop_limit:
                        mask_clearances.append(compute_eagle_clearance(mask_percentage=stop_percent, size=d.diameter,
                                                                       stop_limit=stop_limit))

            # compute min max
            return compute_min_max(mask_clearances) if len(mask_clearances) > 0 else None


def parse_eagle_board_file(filename: str) -> EagleBoardData:
    failures: ParsingError = []
    warnings: list[str] = []
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
    except ET.ParseError as e:
        failures.append(SingleError(f"Critical error when parsing {filename}: {e}", traceback.format_exc()))
        return EagleBoardData(failures=failures, warnings=warnings)

    try:
        check_eagle_version(root, warnings)
    except RuntimeError as e:
        warnings.append("Could not read Eagle file format version")

    try:
        stackup, cu_thick, iso_thick, parsing_failure = parse_eagle_stackup(root)
    except RuntimeError as e:
        failures.append(SingleError(f"Critical error in parsing whole stackup: {e}", traceback.format_exc()))
        stackup, cu_thick, iso_thick = None, None, None
    else:
        failures = failures + parsing_failure

    try:
        rules = parse_eagle_rules(root)
    except (RuntimeError, TypeError, KeyError) as e:
        failures.append(SingleError(f"Critical error in parsing rules: {e}", traceback.format_exc()))
        rules = None

    try:
        topo = parse_eagle_topology(root, failures)
    except RuntimeError as e:
        failures.append(SingleError(f"Critical error in parsing topology: {e}", traceback.format_exc()))
        topo = None

    if stackup is None:
        failures.append(SingleError("Critical error in stackup extraction, could not process stackup"))
    if cu_thick is None:
        failures.append(
            SingleError("Critical error in copper thickness extraction, could not process copper thickness"))
    if iso_thick is None:
        failures.append(
            SingleError("Critical error in isolate thickness extraction, could not process isolate thickness"))
    if rules is None:
        failures.append(SingleError("Critical error in rules extraction, could not process rules"))
    if topo is None:
        failures.append(SingleError("Critical error in topology extraction, could not process topology"))

    return EagleBoardData(stackup=stackup, copper_thickness=cu_thick, isolate_thickness=iso_thick, rules=rules,
                          topology=topo, failures=failures, warnings=warnings)


def compute_layer_id_map(copper: CopperThickness, layers: list[Layer]) -> tuple[dict[int, int], dict[int, int]]:
    back_id, front_id = None, None
    cu_layers = []
    for layer in layers:
        if layer.is_cu:
            if layer.is_front:
                front_id = layer.id
            if layer.is_back:
                back_id = layer.id
            cu_layers.append(layer.id)
    if back_id is None or front_id is None:
        raise RuntimeError("Critical Error in SBF conversion [No front or back layer found]")
    reverse = front_id > back_id

    E2K = {}
    K2E = {}

    keys = list(copper.keys())
    keys.sort(reverse=False)
    for idx, id in enumerate(keys):
        if reverse:
            E2K[id] = cu_layers[-idx - 1]
            K2E[cu_layers[-idx - 1]] = id
        else:
            E2K[id] = cu_layers[idx]
            K2E[cu_layers[idx]] = id
    return E2K, K2E


def dependency_check(param: Union[str, list[str]], inp: dict[str, Any], failures: ExtractionError) -> bool:
    missing: Union[str, list[str]] = []
    for k in inp.keys():
        if inp[k] is None:
            missing.append(k)

    if len(missing) == 0:
        return True
    if len(missing) == 1:
        missing = missing[0]

    if isinstance(param, str):
        param = [param]

    for p in param:
        if p not in failures.keys():
            failures[p] = []
        failures[p].append(processing_error(p, missing))
    return False


def processing_error(param: str, inp: Union[str, list[str]]) -> SingleError:
    was_were = "were" if isinstance(inp, list) else "was"
    return SingleError(
        error=f"Cannot process parameter {param}, because {inp} {was_were} not calculated appropriately.")
