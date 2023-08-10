import os
from pathlib import Path

import pytest

from extractor.processPackaging import process_package, parse_packaging_definition_file, \
    process_packaging_definition_file, process_package_mapping
from extractor.typedefs.Files import File, SupportedFiles
from extractor.typedefs.typedef import PackageMapping, PackageMappingContent, PackagingType


@pytest.fixture
def generate_csv_file_content():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'data')
    with open(os.path.join(path, "encoded_csv_PackageMapping.txt"), mode='br') as f:
        return f.read()


def generate_package_mapping() -> PackageMapping:
    package_mapping = {
        "201": (PackagingType.TWO_TERMINAL, 0.1, 0.03),
        "0201": (PackagingType.TWO_TERMINAL, 0.1, 0.03),
        "805": (PackagingType.TWO_TERMINAL, 0.0, 0.0),
        "SOP": (PackagingType.SMALL_OUTLINE_IC, 0.0, 0.0),
        "TSOP": (PackagingType.SMALL_OUTLINE_IC, 0.0, 0.0),
        "SOT-416": (PackagingType.TRAN_DIO_SMALL_PIN_IC, 1.0, 0.0),
        "TO-220": (PackagingType.TRAN_DIO_SMALL_PIN_IC, 1.1, 0.6),
        "NRF_BL": (PackagingType.OTHERS, 0.0, 0.0)
    }
    return {k: PackageMappingContent(*v) for k, v in package_mapping.items()}


def test_process_package():
    pm = generate_package_mapping()

    pi = process_package("201", pm)
    assert pi.matched_package == "201"
    assert "exact" in pi.matching_information.matching_type
    assert pi.size[0] == pm["201"].length
    assert pi.size[1] == pm["201"].width

    assert process_package("C201", pm).matched_package == "201"
    assert process_package("C0201", pm).matched_package == "0201"
    pi = process_package("7201", pm)
    assert pi.matched_package == "201"
    assert "best matching substring" in pi.matching_information.matching_type
    assert pi.matching_information.score < 1.0
    assert pi.size[0] == pm["201"].length
    assert pi.size[1] == pm["201"].width

    assert process_package("SOT416", pm).matched_package == "SOT-416"
    assert process_package("SOT_416", pm).matched_package == "SOT-416"
    assert process_package("SOT-41_6", pm).matched_package == "SOT-416"
    assert process_package("SOT-41_6", pm).size[0] == pm["SOT-416"].length
    assert process_package("SOT-41_6", pm).size[1] == pm["SOT-416"].width
    assert process_package("QSOP14", pm).matched_package == "SOP"
    assert process_package("QTSOP", pm).matched_package == "TSOP"
    assert process_package("SO1.0X2.0", pm) is None
    assert process_package("7805 TO220", pm).matched_package == "TO-220"
    assert process_package("NRF52840_BL654", pm).matched_package == "NRF_BL"


def test_load_internal_csv():
    defs = parse_packaging_definition_file(path_to_file=None)
    mapping, errors = process_packaging_definition_file(defs)

    assert len(errors) == 0

    assert mapping["201"].p_type == PackagingType.TWO_TERMINAL
    assert mapping["0201"].p_type == mapping["201"].p_type
    assert mapping["0201"].length == mapping["201"].length
    assert mapping["0201"].width == mapping["201"].width


def test_load_external_csv(generate_csv_file_content):
    file = File(type=SupportedFiles.PACKAGE_MAPPING, encoding="utf-8", content=generate_csv_file_content)
    mapping, errors = process_package_mapping(file)

    assert len(errors) == 0

    assert mapping["201"].p_type == PackagingType.TWO_TERMINAL
    assert mapping["0201"].p_type == mapping["201"].p_type
    assert mapping["0201"].length == mapping["201"].length
    assert mapping["0201"].width == mapping["201"].width
