import os.path

from recommender import RECOMMENDER_ROOT_DIR
from recommender.importer.output import output_import_errors
from recommender.importer.preprocessor import preprocess_parsed_data
from recommender.importer.reader import read_csv
from recommender.importer.typedef import ImportErrors
from recommender.importer.validator import validation_read_data

if __name__ == "__main__":
    path = os.path.join(RECOMMENDER_ROOT_DIR, "Meta_Fields_Recommender.csv")
    raw_data, parsing_errors = read_csv(path, ',')

    processed_data, processing_errors = preprocess_parsed_data(raw_data)
    invalid_names, validation_errors = validation_read_data(processed_data)

    errors: ImportErrors = {"parsing": parsing_errors, "processing": processing_errors, "validation": validation_errors}

    print(output_import_errors(errors, invalid_names))
