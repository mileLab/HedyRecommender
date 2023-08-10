import os
import sys
from typing import Literal

from recommender import RECOMMENDER_ROOT_DIR
from recommender.importer.output import output_import_errors, has_errors
from recommender.importer.preprocessor import preprocess_parsed_data
from recommender.importer.processor import extract_global_data, generate_input_metadata_types
from recommender.importer.reader import read_csv
from recommender.importer.typedef import ImportErrors
from recommender.importer.validator import validation_read_data
from recommender.parameters.parameterGeneration import generate_demand_supplier_dataclass
from recommender.parameters.parameterMetadata import ParameterMetadata
from recommender.parameters.parameterTypeRegistry import ParameterTypeRegistry
from recommender.preferences.preferenceGeneration import generate_preference_dataclass
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.preferences.preferenceTypeRegistry import PreferenceTypeRegistry
from recommender.typedefs.typedef import NO_CATEGORY


def __generate() -> tuple[list[str], list[str], type, type]:
    # 1. Read in csv file
    sep = ";"
    filename = os.environ['RECOMMENDER_TYPE_DEFINITION']
    path = os.path.join(RECOMMENDER_ROOT_DIR, filename)
    raw_data, parsing_errors = read_csv(path, sep)

    # 2. Perform preprocessing
    processed_data, processing_errors = preprocess_parsed_data(raw_data)

    # 3. Validate processed data
    invalid_names, validation_errors = validation_read_data(processed_data)

    # 4. Error handling
    errors: ImportErrors = {"parsing": parsing_errors, "processing": processing_errors, "validation": validation_errors}
    if has_errors(errors):
        error_table = output_import_errors(errors, invalid_names)
        print("Fatal error in generating input types. The following error(s) occurred: \n" + error_table,
              file=sys.stderr, flush=True)
        raise RuntimeError(
            f"An fatal error appeared during reading and processing of input fields of {filename}, the following fieldnames are invalid {invalid_names}. Stopping startup of recommender.")

    # 5. Generate "categories" and "production_methods"
    categories, production_methods = extract_global_data(processed_data)
    categories.append(NO_CATEGORY)

    # 6. Generate Metadataclass for parameters and preferences
    parameter_metadata, preference_metadata = generate_input_metadata_types(data=processed_data,
                                                                            production_methods=production_methods)

    # 7. generate the preference input types for all production methods
    preference_input_types = generate_preference_dataclass(preference_metadata, production_methods)

    # 8. Register each preference input type in the type registry = dict: production_method => Type
    for pm in production_methods:
        t = preference_input_types[pm]
        PreferenceTypeRegistry.register(pm, t)

    # 9. generate the preference input types for all production methods
    parameter_input_types_demand, parameter_input_types_supplier = generate_demand_supplier_dataclass(
        parameter_metadata, production_methods=production_methods)

    # 10. register each preference input type in the type registry = dict: production_method,'demand/supplier' => Type
    for pm in production_methods:
        ParameterTypeRegistry.register(pm, 'Demand', parameter_input_types_demand[pm])
        ParameterTypeRegistry.register(pm, 'Supplier', parameter_input_types_supplier[pm])

    return categories, production_methods, parameter_metadata, preference_metadata


all_categories, all_production_methods, Parameters, Preferences = __generate()
ProductionMethods = Literal[tuple(all_production_methods)]

# create union type for FastAPI interface
InputPreferences = PreferenceTypeRegistry.get_input_type()

# create union type for FastAPI interface
InputParametersDemand = ParameterTypeRegistry.get_input_type('Demand')
InputParametersSupplier = ParameterTypeRegistry.get_input_type('Supplier')


def get_parameter_metadata(name: str, ParamMetadata: type = Parameters) -> ParameterMetadata:
    return getattr(ParamMetadata, name)


def get_preference_metadata(name: str, PrefMetadata: type = Preferences) -> PreferenceMetadata:
    return getattr(PrefMetadata, name)
