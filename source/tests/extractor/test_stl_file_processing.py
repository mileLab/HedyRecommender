import os
from pathlib import Path

import pytest
from pytest import approx

from extractor.processorSTL import process_generic_stl
from extractor.typedefs.Files import StlFile, SupportedFiles


@pytest.fixture
def generate_stl_file_content():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'data')
    with open(os.path.join(path, "test_stl_encoded_file.txt"), mode='br') as f:
        return f.read()


def test_stl_file_processing(generate_stl_file_content):
    file = StlFile(type=SupportedFiles.STL, encoding="binary", content=generate_stl_file_content, unit="meter")

    params, failures, additional_info = process_generic_stl(file)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length > params.width > params.height

    assert params.height == approx(15000.0, abs=0.01)
    assert params.length == approx(51751.16, abs=0.01)
    assert params.width == approx(21400.0, abs=0.01)


def test_stl_file_processing_non_align(generate_stl_file_content):
    file = StlFile(type=SupportedFiles.STL, encoding="binary", content=generate_stl_file_content, unit="meter",
                   axis_aligned=False)

    params, failures, additional_info = process_generic_stl(file)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length > params.width > params.height

    assert params.height == approx(15000.0, abs=0.01)
    assert params.length == approx(51751.16, abs=0.01)
    assert params.width == approx(21400.0, abs=0.01)


def test_stl_file_processing_units(generate_stl_file_content):
    file_m = StlFile(type=SupportedFiles.STL, encoding="binary", content=generate_stl_file_content, unit="m")
    file_cm = StlFile(type=SupportedFiles.STL, encoding="binary", content=generate_stl_file_content, unit="cm")
    file_mm = StlFile(type=SupportedFiles.STL, encoding="binary", content=generate_stl_file_content, unit="mm")
    file_in = StlFile(type=SupportedFiles.STL, encoding="binary", content=generate_stl_file_content, unit="in")

    params_m, _, _ = process_generic_stl(file_m)
    params_cm, _, _ = process_generic_stl(file_cm)
    params_mm, _, _ = process_generic_stl(file_mm)
    params_in, _, _ = process_generic_stl(file_in)

    # result is always in MM
    assert params_m.height == approx(100 * params_cm.height)
    assert params_m.length == approx(100 * params_cm.length)
    assert params_m.width == approx(100 * params_cm.width)

    assert params_cm.height == approx(10 * params_mm.height)
    assert params_cm.length == approx(10 * params_mm.length)
    assert params_cm.width == approx(10 * params_mm.width)

    assert params_m.height == approx(39.3701 * params_in.height)
    assert params_m.length == approx(39.3701 * params_in.length)
    assert params_m.width == approx(39.3701 * params_in.width)
