import os
from pathlib import Path

import pytest
from pytest import approx

from extractor.processorSTEP import process_generic_step
from extractor.typedefs.Files import StepFile, SupportedFiles


@pytest.fixture
def generate_step_file_content():
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    path = os.path.join(source_dir, 'data')
    with open(os.path.join(path, "test_step_encoded_file.txt"), mode='br') as f:
        return f.read()


def test_stl_file_processing(generate_step_file_content):
    file = StepFile(type=SupportedFiles.STEP, encoding="utf-8", content=generate_step_file_content)

    params, failures, additional_info = process_generic_step(file)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length > params.width > params.height

    assert params.height == approx(15.2, abs=0.01)
    assert params.length == approx(51.95116, abs=0.01)
    assert params.width == approx(21.6000, abs=0.01)


def test_stl_file_processing_non_aligned(generate_step_file_content):
    file = StepFile(type=SupportedFiles.STEP, encoding="utf-8", content=generate_step_file_content, axis_aligned=False)

    params, failures, additional_info = process_generic_step(file)

    assert len(failures.parsing) == 0
    assert len([e for lst in failures.extracting.values() for e in lst]) == 0
    assert params.length > params.width > params.height

    assert params.height == approx(15.07, abs=0.01)
    assert params.length == approx(51.84, abs=0.01)
    assert params.width == approx(21.42, abs=0.01)
