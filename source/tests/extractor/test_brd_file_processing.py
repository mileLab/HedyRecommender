import os
from pathlib import Path

import pytest
from pytest import approx

from common.typedef import Range
from extractor.processPackaging import process_package_mapping
from extractor.processorBRD import process_board_file
from extractor.typedefs.Files import SupportedFiles, File


@pytest.fixture
def generate_brd_file_content_trackbar():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'data')
    with open(os.path.join(path, "test_brd_trackbar_basic_v1_hole.txt"), mode='br') as f:
        return f.read()


@pytest.fixture
def generate_brd_file_content_booster():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'data')
    with open(os.path.join(path, "test_brd_dcc_booster_03_new.txt"), mode='br') as f:
        return f.read()


@pytest.fixture
def generate_brd_file_content_booster2():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'data')
    with open(os.path.join(path, "encoded_brd_dcc_booster_03_2.txt"), mode='br') as f:
        return f.read()


@pytest.fixture
def generate_brd_file_content_blinkenrocket():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'data')
    with open(os.path.join(path, "test_brd_blinkenrocket_v2e.txt"), mode='br') as f:
        return f.read()


def test_brd_file_processing_trackbar(generate_brd_file_content_trackbar):
    file = File(type=SupportedFiles.EAGLE_BOARD, encoding="utf-8", content=generate_brd_file_content_trackbar)
    package_mapping, package_failures = process_package_mapping(file=None)

    params, failures, additional_info = process_board_file(file, package_mapping)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length >= params.width >= params.height

    assert params.height == approx(1.376, abs=0.001)
    assert params.length == approx(47.68, abs=0.1)
    assert params.width == approx(17.61, abs=0.1)
    assert params.core_thickness == Range(min=approx(0.71), max=approx(0.71))
    assert params.copper_thickness == Range(min=approx(0.018), max=approx(0.035))
    assert params.prepreg_thickness == Range(min=approx(0.2), max=approx(0.36))
    assert params.n_layers == 4
    assert params.inner_milling
    assert params.drill_size == Range(min=approx(0.2), max=approx(2))
    assert params.drill_size_PTH == Range(min=approx(1.02), max=approx(1.02))
    assert params.drill_size_NPTH == Range(min=approx(0.7), max=approx(2))
    assert params.drill_size_via == Range(min=approx(0.2), max=approx(0.2))
    assert params.solder_mask_clearance == Range(min=approx(0.03), max=approx(0.03))
    assert params.n_PTH == 2
    assert params.n_NPTH == 3
    assert params.n_via == 132
    assert params.n_blind_via == 0
    assert params.n_buried_via == 0
    assert params.packaging_count == {
        "Two-terminal packages": 49,
        "Through-hole packages": 0,
        "Surface mount": 2,
        "Chip carrier": 0,
        "Pin grid arrays": 0,
        "Flat packages": 3,
        "Small outline packages": 0,
        "Chip-scale packages": 0,
        "Ball grid array": 0,
        "Transistor, diode, small-pin-count IC packages": 11,
        "Multi-chip packages": 0,
        "Tantalum capacitors": 0,
        "Aluminum capacitors": 0,
        "Non-packaged devices": 0,
        "Others": 2
    }
    assert params.n_different_packaging_types == 5
    assert params.n_components == 72
    assert params.n_components_per_package == {
        "0402": 48,
        "0603": 1,
        "4-SMD_0606": 1,
        "LGA-14L-2.5X3": 1,
        "NRF52840_BL654": 1,
        "PINHEADER_1X1_TH": 2,
        "QFN14_3.5X3.5_V2": 1,
        "SOD-923": 1,
        "SOT-323": 1,
        "SOT-523": 4,
        "SOT-563": 2,
        "SOT23-5": 3,
        "SWITCH_EVQP7D": 1,
        "TVS_UDFN-9": 1,
        "UDFN-8_8X6": 1,
        "USB-C_1054500101": 1,
        "VLGA-8": 1,
        "XTAL2_3.2X1.5": 1
    }
    assert sum(params.n_components_per_package.values()) == params.n_components
    assert params.trace_width == Range(min=approx(0.2), max=approx(0.4))
    assert params.trace_clearance == approx(0.15, abs=0.01)

    # assert component_size_width
    # assert component_size_length


def test_brd_file_processing_booster(generate_brd_file_content_booster):
    file = File(type=SupportedFiles.EAGLE_BOARD, encoding="utf-8", content=generate_brd_file_content_booster)
    package_mapping, package_failures = process_package_mapping(file=None)

    params, failures, additional_info = process_board_file(file, package_mapping)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length >= params.width >= params.height

    assert params.height == approx(1.57, abs=0.01)
    assert params.length == approx(100.0, abs=0.1)
    assert params.width == approx(100.0, abs=0.1)
    assert params.core_thickness == Range(min=approx(1.5), max=approx(1.5))
    assert params.copper_thickness == Range(min=approx(0.035), max=approx(0.035))
    assert params.prepreg_thickness == Range(min=approx(0.0), max=approx(0.0))
    assert params.n_layers == 2
    assert not params.inner_milling
    assert params.drill_size == Range(min=approx(0.6), max=approx(3.302))
    assert params.drill_size_PTH == Range(min=approx(0.8128), max=approx(1.3))
    assert params.drill_size_NPTH == Range(min=approx(2.8), max=approx(3.302))
    assert params.drill_size_via == Range(min=approx(0.6), max=approx(0.6))
    assert params.solder_mask_clearance == Range(min=approx(0.1016), max=approx(0.1016))
    assert params.n_PTH == 54
    assert params.n_NPTH == 6
    assert params.n_via == 94
    assert params.n_blind_via == 0
    assert params.n_buried_via == 0
    assert params.packaging_count == {
        "Two-terminal packages": 86,
        "Through-hole packages": 0,
        "Surface mount": 0,
        "Chip carrier": 0,
        "Pin grid arrays": 0,
        "Flat packages": 0,
        "Small outline packages": 4,
        "Chip-scale packages": 0,
        "Ball grid array": 0,
        "Transistor, diode, small-pin-count IC packages": 15,
        "Multi-chip packages": 0,
        "Tantalum capacitors": 0,
        "Aluminum capacitors": 0,
        "Non-packaged devices": 0,
        "Others": 0
    }
    assert params.n_different_packaging_types == 3
    assert params.n_components == 113
    assert params.n_components_per_package == {
        "1X02": 1,
        "78XXL": 1,
        "AC10": 1,
        "C0805": 19,
        "C1206": 9,
        "CHIPLED_0805": 6,
        "E5-10,5": 2,
        "LITTLEFUSE": 2,
        "M617-31": 1,
        "MKDSN1,5_2-5,08": 1,
        "R0805": 41,
        "R1206": 9,
        "R2512W": 2,
        "SMB": 1,
        "SMC": 2,
        "SO08": 1,
        "SO16": 1,
        "SOD80C": 2,
        "SOIC-16": 1,
        "SOIC08": 1,
        "SOT23": 7,
        "TO220BH": 2
    }
    assert sum(params.n_components_per_package.values()) == params.n_components
    assert params.trace_width == Range(min=approx(0.25), max=approx(6.4516))
    assert params.trace_clearance == approx(0.1524, abs=0.0001)

    # assert component_size_width
    # assert component_size_length


def test_brd_file_processing_blinkenrocket(generate_brd_file_content_blinkenrocket):
    file = File(type=SupportedFiles.EAGLE_BOARD, encoding="utf-8", content=generate_brd_file_content_blinkenrocket)
    package_mapping, package_failures = process_package_mapping(file=None)

    params, failures, additional_info = process_board_file(file, package_mapping)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length >= params.width >= params.height

    assert params.height == approx(1.57, abs=0.01)
    assert params.length == approx(96.33, abs=0.01)  # 0.04mm off
    assert params.width == approx(47.05, abs=0.01)  # 0.05mm off
    assert params.core_thickness == Range(min=approx(1.5), max=approx(1.5))
    assert params.copper_thickness == Range(min=approx(0.035), max=approx(0.035))
    assert params.prepreg_thickness == Range(min=approx(0.0), max=approx(0.0))
    assert params.n_layers == 2
    assert not params.inner_milling
    assert params.drill_size == Range(min=approx(0.5), max=approx(5.0))
    assert params.drill_size_PTH == Range(min=approx(1.0), max=approx(1.5))
    assert params.drill_size_NPTH == Range(min=approx(1.2), max=approx(5.0))
    assert params.drill_size_via == Range(min=approx(0.5), max=approx(0.6))
    assert params.solder_mask_clearance == Range(min=approx(0.0508), max=approx(0.0508))
    assert params.n_PTH == 51
    assert params.n_NPTH == 8
    assert params.n_via == 45
    assert params.n_blind_via == 0
    assert params.n_buried_via == 0
    assert params.packaging_count == {
        "Two-terminal packages": 9,
        "Through-hole packages": 0,
        "Surface mount": 0,
        "Chip carrier": 0,
        "Pin grid arrays": 1,
        "Flat packages": 1,
        "Small outline packages": 1,
        "Chip-scale packages": 0,
        "Ball grid array": 0,
        "Transistor, diode, small-pin-count IC packages": 2,
        "Multi-chip packages": 0,
        "Tantalum capacitors": 0,
        "Aluminum capacitors": 0,
        "Non-packaged devices": 0,
        "Others": 0
    }
    assert params.n_different_packaging_types == 5
    assert params.n_components == 23  # CHAOSKNOTEN is not a component
    assert params.n_components_per_package == {
        "1X02": 1,
        "1X04-S": 2,
        "AUDIO-JACK": 1,
        "AVR-ISP-6": 1,
        "B3F-10XX": 2,
        "BAT_20MM_TH": 1,
        "C1206": 3,
        "CR2032PAC_ELECTRODRAGON": 1,
        "R1206": 6,
        "SEGMENT_BL-M12A883": 1,
        "SO08-EIAJ": 1,
        "SOD3718X135N": 2,
        "TQFP32-08": 1
    }
    assert sum(params.n_components_per_package.values()) == params.n_components
    assert params.trace_width == Range(min=approx(0.2540), max=approx(0.3048))
    assert params.trace_clearance == approx(0.1524, abs=0.0001)

    # assert component_size_width
    # assert component_size_length


def test_brd_file_processing_booster2(generate_brd_file_content_booster2):
    file = File(type=SupportedFiles.EAGLE_BOARD, encoding="utf-8", content=generate_brd_file_content_booster2)
    package_mapping, package_failures = process_package_mapping(file=None)

    params, failures, additional_info = process_board_file(file, package_mapping)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length >= params.width >= params.height

    assert params.height == approx(1.57, abs=0.01)
    assert params.length == approx(100.0, abs=0.1)
    assert params.width == approx(100.0, abs=0.1)
    assert params.core_thickness == Range(min=approx(1.5), max=approx(1.5))
    assert params.copper_thickness == Range(min=approx(0.035), max=approx(0.035))
    assert params.prepreg_thickness == Range(min=approx(0.0), max=approx(0.0))
    assert params.n_layers == 2
    assert not params.inner_milling
    assert params.drill_size == Range(min=approx(0.6), max=approx(3.302))
    assert params.drill_size_PTH == Range(min=approx(0.8128), max=approx(1.3))
    assert params.drill_size_NPTH == Range(min=approx(2.8), max=approx(3.302))
    assert params.drill_size_via == Range(min=approx(0.6), max=approx(0.6))
    assert params.solder_mask_clearance == Range(min=approx(0.1016), max=approx(0.1651))
    assert params.n_PTH == 54
    assert params.n_NPTH == 6
    assert params.n_via == 94
    assert params.n_blind_via == 0
    assert params.n_buried_via == 0
    assert params.packaging_count == {
        "Two-terminal packages": 86,
        "Through-hole packages": 0,
        "Surface mount": 0,
        "Chip carrier": 0,
        "Pin grid arrays": 0,
        "Flat packages": 0,
        "Small outline packages": 4,
        "Chip-scale packages": 0,
        "Ball grid array": 0,
        "Transistor, diode, small-pin-count IC packages": 15,
        "Multi-chip packages": 0,
        "Tantalum capacitors": 0,
        "Aluminum capacitors": 0,
        "Non-packaged devices": 0,
        "Others": 0
    }
    assert params.n_different_packaging_types == 3
    assert params.n_components == 113
    assert params.n_components_per_package == {
        "1X02": 1,
        "78XXL": 1,
        "AC10": 1,
        "C0805": 19,
        "C1206": 9,
        "CHIPLED_0805": 6,
        "E5-10,5": 2,
        "LITTLEFUSE": 2,
        "M617-31": 1,
        "MKDSN1,5_2-5,08": 1,
        "R0805": 41,
        "R1206": 9,
        "R2512W": 2,
        "SMB": 1,
        "SMC": 2,
        "SO08": 1,
        "SO16": 1,
        "SOD80C": 2,
        "SOIC-16": 1,
        "SOIC08": 1,
        "SOT23": 7,
        "TO220BH": 2
    }
    assert sum(params.n_components_per_package.values()) == params.n_components
    assert params.trace_width == Range(min=approx(0.25), max=approx(6.4516))
    assert params.trace_clearance == approx(0.1524, abs=0.0001)

    # assert component_size_width
    # assert component_size_length
