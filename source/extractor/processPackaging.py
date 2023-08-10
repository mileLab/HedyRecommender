import csv
import os.path
import re
from pathlib import Path
from typing import Any, Optional

import numpy

from extractor.typedefs.BoardTypes import Footprint
from extractor.typedefs.Files import File
from extractor.typedefs.typedef import PackageInformation, MatchingInformation, PackageFailures, PackageMapping, \
    ExtractorSevereError, PackageMappingCSVData, PackageMappingContent, SingleError, PackagingType
from extractor.utils import create_temp_file


def process_package_mapping(file: Optional[File]) -> tuple[PackageMapping, list[SingleError]]:
    # open specified package mapping file
    path = None
    if file is not None:
        # create "persistent" tempfile, otherwise, it cannot be opened
        try:
            tempfile = create_temp_file(file.content, file.type, file.encoding)
            path = tempfile.name
        except RuntimeError as e:
            raise ExtractorSevereError("Creation of temporary file failed") from e

    # parse package definition file
    definition = parse_packaging_definition_file(path)

    # post processing and cleanup (delete duplicates, verification)
    return process_packaging_definition_file(definition)


def process_packaging(footprints: list[Footprint], packaging_info: PackageMapping, failures: PackageFailures,
                      threshold_score=0.75) -> dict[str, Optional[PackageInformation]]:
    # This functions tries to identify a suitable package name from the package mapping obtained from the database (PackageMapping.csv),
    # representing the footprints from the file. This function first tries to use the package-name to find a suitable package from
    # the database and if this fails it uses the package-value. In rare cases the package-value might contain useful information.
    # e.g: package-name="SOT23-5" package-value="MCP73832T-2ACI/OT"; package-name="LITTLEFUSE" package-value="MF-RX250/72"

    packaging_mapping: dict[str, Optional[PackageInformation]] = {}
    for f in footprints:
        if f.package not in packaging_mapping.keys():

            # first attempt using package name (f.package)
            package_info = process_package(f.package, packaging_info)

            if package_info is None:
                # if not found
                packaging_mapping[f.package] = None
                failures[f.package] = f"Could not find a corresponding matching package for {f.package}"
            elif package_info.matching_information.score < threshold_score:
                # if quality too bad
                packaging_mapping[f.package] = None
                failures[f.package] = f"Found a possible match {package_info.matched_package} for {f.package}, however" \
                                      f" matching score was not large enough {package_info.matching_information.score:.3} " \
                                      f"(<{threshold_score:.3})"
            else:
                # everything fine
                packaging_mapping[f.package] = package_info

            # second attempt with using package value (f.value_name)
            if packaging_mapping[f.package] is None:
                package_info = process_package(f.value_name, packaging_info)
                if package_info is not None and package_info.matching_information.score > threshold_score:
                    # found a suitable packaging type
                    package_info.matching_information.matching_type += f" - Done for the package value {f.value_name}."
                    packaging_mapping[f.package] = package_info

                    # cleanup failure
                    del failures[f.package]

    return packaging_mapping


def parse_packaging_definition_file(path_to_file: Optional[str]) -> list[PackageMappingCSVData]:
    data = []

    # if no path is given, use the default file
    if path_to_file is None:
        source_path = Path(__file__).resolve()
        source_dir = source_path.parent
        source_name = "PackageMapping.csv"
        path_to_file = os.path.join(source_dir, source_name)

    # open csv file and extract database
    with open(path_to_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        header = next(reader)
        if len(header) < 8:
            raise RuntimeError(
                f"Inapropriate file format of PackagingMapping CSV file. 8 Columns are required, got {len(header)}.")
        for row in reader:
            name = [x.strip() for x in row[0].split(',') if x.strip() != '']
            alt_name = [x.strip() for x in row[2].split(',') if x.strip() != '']
            names = name + alt_name
            p_type_str = row[4].strip()

            length = width = 0.0
            if row[6].strip() != '':
                length = float(row[6].strip())
            if row[7].strip() != '':
                width = float(row[7].strip())

            length, width = max(length, width), min(length, width)
            data.append(
                PackageMappingCSVData(names=[n for n in names], packaging=p_type_str, length=length, width=width))

    return data


def process_packaging_definition_file(data: list[PackageMappingCSVData]) -> tuple[PackageMapping, list[SingleError]]:
    result: dict[str, PackageMappingContent] = {}
    failures: list[SingleError] = []

    for d in data:

        for n in d.names:
            if n not in result.keys():
                try:
                    p_type = PackagingType(d.packaging)
                except ValueError:
                    failures.append(SingleError(
                        error=f"Warning: could not find {d.packaging} in PackagingType for {n}. Skipping entry."))
                    continue

                result[n] = PackageMappingContent(p_type=p_type, length=d.length, width=d.width)
            else:
                entry = result[n]

                try:
                    p_type = PackagingType(d.packaging)
                except ValueError:
                    failures.append(SingleError(
                        error=f"Warning: could not find {d.packaging} in PackagingType for {n}. Skipping entry"))
                    continue
                if p_type != entry.p_type:
                    failures.append(
                        SingleError(error=f"Conflicting entry: {n} :  {entry.p_type} vs {p_type}. Keeping first one."))
                    continue

                if entry.length is None:
                    entry.length = d.length
                if entry.width is None:
                    entry.width = d.width

    return result, failures


def process_package(package: str, packaging_info: PackageMapping) -> Optional[PackageInformation]:
    # 1) search for immediate match
    if package in packaging_info.keys():
        pi = packaging_info[package]
        return PackageInformation(packaging_type=pi.p_type, name=package, matched_package=package,
                                  matching_information=MatchingInformation(score=1.0, matching_type="exact match"),
                                  size=[pi.length, pi.width])

    # 2) search for substrings
    candidates = []
    for name in packaging_info.keys():
        if name in package:
            # the pure digit packages like 803 (or 0803) are special, they should not match to a 7803,
            # but only to a possible R803, a 0 in front however is allowed
            if name.isdigit():
                idx = package.index(name)
                if idx > 0 and package[idx - 1].isdigit() and package[idx - 1] != "0":
                    continue
            candidates.append(name)

    # if match found
    if len(candidates) > 1:
        # sort the string by length => most letters of package mapped
        candidates.sort(key=lambda x: len(x), reverse=True)
        pi = packaging_info[candidates[0]]
        return PackageInformation(packaging_type=pi.p_type, name=package, matched_package=candidates[0],
                                  matching_information=MatchingInformation(score=1.0,
                                                                           matching_type="the longest matching substring"),
                                  size=[pi.length, pi.width])
    if len(candidates) == 1:
        pi = packaging_info[candidates[0]]
        return PackageInformation(packaging_type=pi.p_type, name=package, matched_package=candidates[0],
                                  matching_information=MatchingInformation(score=1.0,
                                                                           matching_type="the only matching substring"),
                                  size=[pi.length, pi.width])

    # 3) search for substrings when removing all _,- or whitespaces
    candidates = []
    normalized_package = re.sub('_|-|\s', "", package)
    for name in packaging_info.keys():
        normalized_name = re.sub('_|-|\s', "", name)
        if normalized_name in normalized_package:
            # the pure digit packages like 803 (or 0803) are special, they should not match to a 7803,
            # but only to a possible R803, a 0 in front however is allowed
            if normalized_package.isdigit():
                idx = normalized_package.index(normalized_name)
                if idx > 0 and normalized_package[idx - 1].isdigit() and normalized_package[idx - 1] != "0":
                    continue
            candidates.append(name)

    # if match found
    if len(candidates) > 1:
        # sort the string by length => most letters of package mapped
        candidates.sort(key=lambda x: len(re.sub('_|-|\s', "", x)), reverse=True)
        pi = packaging_info[candidates[0]]
        return PackageInformation(packaging_type=pi.p_type, name=package, matched_package=candidates[0],
                                  matching_information=MatchingInformation(score=1.0,
                                                                           matching_type="the longest matching normalized substring"),
                                  size=[pi.length, pi.width])
    if len(candidates) == 1:
        pi = packaging_info[candidates[0]]
        return PackageInformation(packaging_type=pi.p_type, name=package, matched_package=candidates[0],
                                  matching_information=MatchingInformation(score=1.0,
                                                                           matching_type="the only matching normalized substring"),
                                  size=[pi.length, pi.width])

    # 4) remove common building blocks:
    # e.g.: size: 1.1X1.2
    cleaned_package = re.sub('(\d+\.)?\d+[Xx]\d+(\.\d+)?', "", package)
    if len(cleaned_package) < 3:
        return None
    # print("cleaned package: ", cleaned_package)

    weight_l = 0.75
    weight_d = 0.15
    weight_r = 0.1

    # 5) split package by "," and _ and try to match each individual part in the best possible way
    scores: dict[str, float] = {}
    debug = {}
    splitted_package, pack_l, pack_d, pack_r = split_and_partition_name(cleaned_package)

    for name in packaging_info.keys():
        split_name, name_l, name_d, name_r = split_and_partition_name(name)

        l_score = find_overlap(pack_l, name_l)
        d_score = find_overlap(pack_d, name_d)
        r_score = find_overlap(pack_r, name_r)
        score = numpy.array([l_score, d_score, r_score])
        weight = numpy.array(
            [weight_l * float(l_score >= 0), weight_d * float(d_score >= 0), weight_r * float(r_score >= 0)])

        normalization = weight.sum()

        if normalization > 0:
            final_score = score.dot(weight)
            if final_score > 0:
                scores[name] = final_score / normalization
                debug[name] = {"l_score": l_score, "d_score": d_score, "r_score": r_score, "l_part": name_l,
                               "d_part": name_d, "r_part": name_r}

    # nothing found
    if len(scores.keys()) == 0:
        # print(f"NOT FOUND: {package}")
        return None

    # sort the results after score (decending) and select the ones with the highest score
    kv: list[tuple[str, float]] = list(scores.items())
    kv.sort(key=lambda x: x[1], reverse=True)
    max_pair = [pairs for pairs in kv if pairs[1] == kv[0][1]]

    # extract the one with the smallest length, because that one can already explain package_name the best way.
    max_pair.sort(key=lambda x: len(x[0]))
    best_package, best_score = max_pair[0]

    pi = packaging_info[best_package]
    return PackageInformation(packaging_type=pi.p_type, name=package, matched_package=best_package,
                              matching_information=MatchingInformation(score=best_score,
                                                                       matching_type="the best matching substrings"),
                              size=[pi.length, pi.width])


# returns how many percent of the package, can be described by db_name
def find_overlap(package: list[str], db_name: list[str]) -> float:
    n_chars = sum([len(p) for p in package])
    if n_chars == 0:
        return -1

    # sort by length
    db_name.sort(key=lambda x: len(x), reverse=True)

    # generate a map of all possible assignments
    mapping = {"remainder": package} # setting initial value, recursive call of generate_mapping
    generate_mapping(mapping, package, db_name)

    # find the best match
    matched_chars = 0
    if len(mapping.keys()) > 1:
        sub_list, length_remainder = find_best_substitution(mapping)
        matched_chars = n_chars - length_remainder

    return matched_chars / n_chars

    # matches_words = [n for p in package for n in db_name if n in p]
    # matched_chars = sum([len(w) for w in matches_words])
    # return matched_chars / n_chars


def split_and_partition_name(s: str) -> tuple[list[str], list[str], list[str], list[str]]:
    # splitting the input string into pure letters and digits substrings and the mixed substrings
    # splitting is performed by "-" and "_"
    parts = separate_number_chars(s)
    letters = [p for p in parts if p.isalpha()]
    digits = [p for p in parts if p.isdigit()]
    remainder = [p for p in parts if (p not in letters and p not in digits)]
    return parts, letters, digits, remainder


def separate_number_chars(s: str) -> list[str]:
    # splitting by whitespace leads to bad matching behavior due to "SomeName A" in the db.
    res = re.split('-|_|(\d+)', s)
    return [r.strip() for r in res if r is not None and r.strip() != ""]


# finds all possible combinations how the tokens from db_name can be assigned to the tokens in package
# returns {(n1, p1) => {remainder = "asdaat"; (n12,p12) => {remainder = "asd", (n13,p13) => { ... }}}
def generate_mapping(mapping: dict, package: list[str], db_name: list[str]):
    for n in db_name:
        for p in package:
            if n in p:
                # non matched part of string
                r = p.replace(n, "").strip()

                # child mapping
                mapping[(n, p)] = {}

                # new set of package tokens
                new_package = list(package)
                new_package.remove(p)
                if r != "":
                    new_package.append(r)

                # new set of db_name tokens (avoid permutation of order, hence remove already used ones)
                new_db_name = list(db_name)
                new_db_name = new_db_name[new_db_name.index(n) + 1:]

                # update mapping
                mapping[(n, p)]["remainder"] = new_package

                # recursive call
                generate_mapping(mapping[(n, p)], new_package, new_db_name)


def find_best_substitution(mapping: dict[str, Any]) -> tuple[list[tuple[str, str]], int]:
    if len(mapping.keys()) > 1:
        max_len = sum([len(r) for r in mapping['remainder']])
        best_list: list[tuple[str, str]] = []
        for k in mapping.keys():
            if k != "remainder":
                l, new_len = find_best_substitution(mapping[k])
                if new_len <= max_len:
                    max_len = new_len
                    best_list = l

        return best_list, max_len

    else:
        return [], sum([len(r) for r in mapping['remainder']])
