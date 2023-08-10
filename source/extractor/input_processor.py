import traceback

from extractor.processPackaging import process_package_mapping
from extractor.processorBRD import process_board_file
from extractor.processorSTEP import process_generic_step
from extractor.processorSTL import process_generic_stl
from extractor.typedefs.Files import SupportedFiles, StepFile, StlFile, File
from extractor.typedefs.io_types import Input, Output, ComponentParameters, Component
from extractor.typedefs.parameters import PCBParameters, GenericParameters
from extractor.typedefs.typedef import Failures, ExtractorSevereError, AdditionalParameterInfo, SingleError, \
    ProductionMethod


def process_input(inp: Input) -> Output:
    output = Output()
    for component in inp.components:
        failures = Failures()
        try:
            if component.method == ProductionMethod.PCB_ASSEMBLY:
                parameters, failures, additional_info = process_pcb_assembly(component)
            elif component.method == ProductionMethod.MACHINING_GEOM_CUT:
                parameters, failures, additional_info = process_generic(component)
                parameters.production_method = ProductionMethod.MACHINING_GEOM_CUT
            elif component.method == ProductionMethod.MOULDING_PLASTIC:
                parameters, failures, additional_info = process_generic(component)
                parameters.production_method = ProductionMethod.MOULDING_PLASTIC
            elif component.method == ProductionMethod.GENERIC:
                parameters, failures, additional_info = process_generic(component)
            else:
                parameters, failures, additional_info = process_generic(component)
                additional_info.warnings.append(f"Unknown method {component.method} for component {component.name}, "
                                                f"defaulting to extraction of bounding box")

        except ExtractorSevereError as e:
            failures.parsing.append(
                SingleError(f"Critical error processing {component.name} of type {component.method}."
                            f" Occurred Error: {e}", traceback.format_exc()))
            component_parameters = ComponentParameters(name=component.name, parameters=None, failures=failures,
                                                       additional_info=AdditionalParameterInfo(info_parameter={},
                                                                                               warnings=[]))
        else:
            component_parameters = ComponentParameters(name=component.name, parameters=parameters, failures=failures,
                                                       additional_info=additional_info)
        output.components.append(component_parameters)
    return output


def process_pcb_assembly(component: Component) -> tuple[PCBParameters, Failures, AdditionalParameterInfo]:
    name = component.name

    # first search for the package_mapping csv file
    packaging_file = next((file for file in component.files if file.type == SupportedFiles.PACKAGE_MAPPING), None)
    try:
        package_mapping, package_failures = process_package_mapping(packaging_file)
    except (RuntimeError, ExtractorSevereError) as e:
        package_mapping = None
        package_failures = [
            SingleError(error=f"Critical error in reading package mapping: {e}", traceback=traceback.format_exc())]

    # second for all other files, currently only the .brd file
    for file in component.files:
        if file.type == SupportedFiles.EAGLE_BOARD:
            if isinstance(file, File):
                params, failures, additonal_info = process_board_file(file, package_mapping)
                failures.parsing += package_failures
                return params, failures, additonal_info
            else:
                raise ExtractorSevereError(f"Input file for {name} is not of type eagle, got {type(file)}. ")
        elif file.type == SupportedFiles.PACKAGE_MAPPING:
            continue  # handled before
        else:
            raise ExtractorSevereError("Currently only EAGLE .brd files are supported for component {name}")


def process_generic(component: Component) -> tuple[GenericParameters, Failures, AdditionalParameterInfo]:
    n_files = len(component.files)
    # only one file per component allowed
    if n_files > 1:
        raise ExtractorSevereError(f"Only a single file is expected, got {n_files}")

    file = component.files[0]
    if file.type == SupportedFiles.STEP:
        if not isinstance(file, StepFile):
            raise ExtractorSevereError(
                f"Input file description for component {component.name} does not match expected StepFile.")
        return process_generic_step(file)
    elif file.type == SupportedFiles.STL:
        if not isinstance(file, StlFile):
            raise ExtractorSevereError(
                f"Input file description for component {component.name} does not match expected StlFile.")
        return process_generic_stl(file)
    else:
        raise ExtractorSevereError(
            f"Generic processing for component {component.name} is not supported for {file.type}. Currently supported "
            f"files are STEP and STL.")
