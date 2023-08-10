import pint
from OCC.Extend.DataExchange import read_stl_file

from extractor import Q_
from extractor.extractBoundingBox import extract_bounding_box_dimensions
from extractor.typedefs.Files import StlFile
from extractor.typedefs.parameters import GenericParameters
from extractor.typedefs.typedef import Failures, ExtractorSevereError, AdditionalParameterInfo, ProductionMethod
from extractor.utils import create_temp_file, destroy_temp_file


def process_generic_stl(file: StlFile) -> tuple[GenericParameters, Failures, AdditionalParameterInfo]:
    alignment = file.axis_aligned
    failures = Failures()
    additional_data = {}
    warnings = []

    # create "persistent" tempfile, otherwise, it cannot be opened
    try:
        tempfile = create_temp_file(file.content, file.type, file.encoding)
    except RuntimeError as e:
        raise ExtractorSevereError("Creation of temporary file failed") from e

    try:
        try:
            # read stl file
            shape = read_stl_file(tempfile.name)
        except (RuntimeError, FileNotFoundError, AssertionError) as e:
            raise ExtractorSevereError("Could not read STL file") from e

        try:
            # compute bounding box dimensions from shape
            dimensions = extract_bounding_box_dimensions(shape, alignment=alignment, sort=True)
        except RuntimeError as e:
            raise ExtractorSevereError("Could not extract dimension from STL file") from e
    finally:
        # cleanup tempfile
        destroy_temp_file(tempfile)

    # convert units
    extent = None
    try:
        extent = Q_(dimensions, file.unit)
        extent_mm = extent.to('millimeter').magnitude
    except pint.UndefinedUnitError as e:
        raise ExtractorSevereError(f"Unknown input unit {file.unit}.") from e
    except pint.DimensionalityError as e:
        long_unit_name = "unknown" if extent is None else extent.units
        raise ExtractorSevereError(f"Conversion of unit {file.unit} ({long_unit_name}) to 'mm' failed") from e

    return GenericParameters(length=extent_mm[0], width=extent_mm[1],
                             height=extent_mm[2], production_method=ProductionMethod.GENERIC), failures, AdditionalParameterInfo(
        info_parameter=additional_data,
        warnings=warnings)
