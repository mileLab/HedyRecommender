from pytest import approx

from extractor.eagleFileParsing import parse_eagle_layer_stackup, convert_to_mm
from extractor.typedefs.EagleTypes import Isolate


def test_eagle_layer_stackup_parser_1():
    stackup = parse_eagle_layer_stackup("([2:1+2*3])")
    assert stackup[(1, 2)] == Isolate.PREPREG
    assert stackup[(2, 3)] == Isolate.CORE


def test_eagle_layer_stackup_parser_2():
    stackup = parse_eagle_layer_stackup("[2:1+(2*15)+16:15]")
    assert stackup[(1, 2)] == Isolate.PREPREG
    assert stackup[(2, 15)] == Isolate.CORE
    assert stackup[(15, 16)] == Isolate.PREPREG


def test_eagle_layer_stackup_parser_3():
    stackup = parse_eagle_layer_stackup("([2:1+[13:(2+(13*14))]+16:14])")
    assert stackup[(1, 2)] == Isolate.PREPREG
    assert stackup[(2, 13)] == Isolate.PREPREG
    assert stackup[(13, 14)] == Isolate.CORE
    assert stackup[(14, 16)] == Isolate.PREPREG


def test_eagle_layer_stackup_parser_4():
    stackup = parse_eagle_layer_stackup("([([2:1+2*3])+(14*15+16):15])")
    assert stackup[(1, 2)] == Isolate.PREPREG
    assert stackup[(2, 3)] == Isolate.CORE
    assert stackup[(3, 14)] == Isolate.PREPREG
    assert stackup[(14, 15)] == Isolate.CORE
    assert stackup[(15, 16)] == Isolate.PREPREG


def test_eagle_layer_stackup_parser_5():
    stackup = parse_eagle_layer_stackup("([2:1+[3:2+[4:3+[5:4+(5*6+(7*8+9*10)+11*12)+13:12]+14:13]+15:14]+16:15])")
    assert stackup[(1, 2)] == Isolate.PREPREG
    assert stackup[(2, 3)] == Isolate.PREPREG
    assert stackup[(3, 4)] == Isolate.PREPREG
    assert stackup[(4, 5)] == Isolate.PREPREG
    assert stackup[(5, 6)] == Isolate.CORE
    assert stackup[(6, 7)] == Isolate.PREPREG
    assert stackup[(7, 8)] == Isolate.CORE
    assert stackup[(8, 9)] == Isolate.PREPREG
    assert stackup[(9, 10)] == Isolate.CORE
    assert stackup[(10, 11)] == Isolate.PREPREG
    assert stackup[(11, 12)] == Isolate.CORE
    assert stackup[(12, 13)] == Isolate.PREPREG
    assert stackup[(13, 14)] == Isolate.PREPREG
    assert stackup[(14, 15)] == Isolate.PREPREG
    assert stackup[(15, 16)] == Isolate.PREPREG


def test_eagle_unit_parsing():
    assert convert_to_mm(1.0, "mil") == approx(0.0254)
    assert convert_to_mm(1.0, "mm") == approx(1.0)
    assert convert_to_mm(1.0, "nm") == approx(0.000001)
    assert convert_to_mm(1.0, "in") == approx(25.4)
