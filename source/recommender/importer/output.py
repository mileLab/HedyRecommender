import re

from texttable import Texttable

from recommender.importer.typedef import ImportErrors, ImporterStageError


def has_errors(import_errors: ImportErrors):
    for s in ["parsing", "processing", "validation"]:
        if any([len(errors) > 0 for errors in import_errors[s].values()]):
            return True
    return False


def output_import_errors(errors: ImportErrors, invalid: list[str]) -> str:
    output_string = ""

    output_string += "PARSING ERRORS\n"
    t_parsing = __generate_error_table(errors["parsing"])
    output_string += t_parsing.draw() + "\n\n"

    output_string += "PROCESSING ERRORS\n"
    t_processing = __generate_error_table(errors["processing"])
    output_string += t_processing.draw() + "\n\n"

    output_string += "VALIDATION ERRORS\n"
    t_validation = __generate_error_table(errors["validation"], invalid)
    output_string += t_validation.draw() + "\n\n"

    return output_string


def __generate_error_table(err: ImporterStageError, invalid=None):
    table = Texttable(max_width=2000)
    rows = []

    if invalid is None:
        header = ['Name', 'Errors']
    else:
        header = ['Name', 'Invalid', 'Errors']

    for p, e in err.items():
        if len(e) != 0:
            e_updated = ["** " + ee for ee in e]  # add ** to each error
            e_updated = [re.sub("(.{128})", "\\1\n   ", ee, 0, re.DOTALL) for ee in
                         e_updated]  # linebreak after 128 chars
            combined_errors = "\n\n".join(e_updated)  # join to single string with empty line
            if invalid is None:
                rows.append([p, combined_errors])
            else:
                inv = '*' if p in invalid else ''
                rows.append([p, inv, combined_errors])

    table.add_rows([header] + rows)

    return table
