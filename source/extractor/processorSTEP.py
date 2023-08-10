import traceback
from typing import Tuple

import OCC.Core.Interface as OCC_Interface
import pint
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity, IFSelect_CountByItem, IFSelect_ListByItem
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import TopoDS_Shape

from extractor import Q_
from extractor.extractBoundingBox import extract_bounding_box_dimensions
from extractor.typedefs.Files import StepFile
from extractor.typedefs.parameters import GenericParameters
from extractor.typedefs.typedef import Failures, ExtractorSevereError, AdditionalParameterInfo, SingleError, \
    ProductionMethod
from extractor.utils import create_temp_file, destroy_temp_file


def process_generic_step(file: StepFile) -> tuple[GenericParameters, Failures, AdditionalParameterInfo]:
    # http://www.scientificlib.com/en/ComputationalGeometry/MinimumBoundingBox.html

    alignment = file.axis_aligned
    failures = Failures()
    additional_data = {}
    parameter_warnings = []

    # create "persistent" tempfile, otherwise, it cannot be opened
    try:
        tempfile = create_temp_file(file.content, file.type, file.encoding)
    except RuntimeError as e:
        raise ExtractorSevereError("Creation of temporary file failed") from e

    try:
        try:
            # extract data from file
            shape,info = read_step_file(tempfile.name)

            # handle warning from reading
            if info != "":
                parameter_warnings.append(info)
        except RuntimeError as e:
            raise ExtractorSevereError("Could not read STEP file") from e

        # compute mesh
        try:
            # if the accuracy is not sufficient, tune this parameter:
            # e.g. via max(AABB) * 0.001 (0.1% of the maximum extent)
            BRepMesh_IncrementalMesh(shape, 0.1)

            # compute bounding box dimensions
            dimensions = extract_bounding_box_dimensions(shape, alignment=alignment, sort=True)
        except RuntimeError as e:
            raise ExtractorSevereError("Could not extract dimension from STEP file") from e

    finally:
        # cleanup tempfile
        destroy_temp_file(tempfile)

    try:
        unit = OCC_Interface.Interface_Static_CVal("xstep.cascade.unit").lower()
    except RuntimeError as e:
        failures.parsing.append(
            SingleError(f"Could not retrieve unit from OpenCascade internal representation, defaulting to "
                        f"'mm'. Error: {e}", traceback.format_exc()))
        unit = "mm"

    # convert units
    try:
        extent = Q_(dimensions, unit)
        extent_mm = extent.to('millimeter').magnitude
    except (pint.UndefinedUnitError, RuntimeError) as e:
        # for p in ["length", "width", "height"]:
        #     failures.extracting[p] = processing_error(param=p,inp="geometry extent")
        raise ExtractorSevereError("Conversion of Opencascade Unit to 'mm' failed") from e

    return GenericParameters(production_method=ProductionMethod.GENERIC, length=extent_mm[0], width=extent_mm[1],
                             height=extent_mm[2]), failures, AdditionalParameterInfo(info_parameter=additional_data,
                                                                                     warnings=parameter_warnings)


def read_step_file(filename: str) -> Tuple[TopoDS_Shape,str]:
    step_reader = STEPControl_Reader()
    info = ""
    try:
        status = step_reader.ReadFile(filename)
    except (RuntimeError, FileNotFoundError, AssertionError) as e:
        raise RuntimeError("Cannot read STEP File with error: {e}") from e

    if status == IFSelect_RetDone:  # check status
        fails_only = True
        step_reader.PrintCheckLoad(fails_only, IFSelect_ItemsByEntity)
        step_reader.PrintCheckLoad(fails_only, IFSelect_CountByItem)
        step_reader.PrintCheckLoad(fails_only, IFSelect_ListByItem)
        step_reader.PrintCheckTransfer(fails_only, IFSelect_ItemsByEntity)

        step_reader.TransferRoot()
        _nbs = step_reader.NbShapes()
        if _nbs > 1:
            info="Several shapes in STEP file found, selecting only the first one."
        shape = step_reader.Shape()

    else:
        raise RuntimeError("Cannot read STEP File")
    return shape, info
