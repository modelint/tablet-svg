""" test_rectangles.py - Draw rectangle shapes for different presentations """

import inspect
from pathlib import Path
from tabletsvg.tablet import Tablet
from tabletsvg.geometry_types import Rect_Size, Position
from tabletsvg.graphics.rectangle_se import RectangleSE

points_in_mm = 2.83465
A4 = Rect_Size(round(210 * points_in_mm), round(297 * points_in_mm))
OUTPUT = Path(__file__).parent / "output"


def test_grid_boundary():
    dtype = "Grid Diagnostic"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="default", layer="grid", show_window=False, background_color='white')
    glayer = test_tablet.layers['grid']

    RectangleSE.add(layer=glayer, asset="grid border", lower_left=Position(10, 10),
                    size=Rect_Size(height=400, width=400))
    test_tablet.render()
    assert True


def test_class_compartment():
    dtype = "Starr class diagram"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="default", layer="diagram", show_window=False, background_color='blue steel')
    dlayer = test_tablet.layers['diagram']

    RectangleSE.add(layer=dlayer, asset="class name compartment", lower_left=Position(100, 100),
                    size=Rect_Size(height=27, width=253))
    test_tablet.render()
    assert True


def test_bp_class_compartment():
    dtype = "Starr class diagram"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="blueprint", layer="diagram", show_window=False, background_color='blueprint')
    dlayer = test_tablet.layers['diagram']

    RectangleSE.add(layer=dlayer, asset="imported class attribute compartment", lower_left=Position(100, 100),
                    size=Rect_Size(height=27, width=253))
    test_tablet.render()
    assert True


def test_state_compartment():
    dtype = "xUML state machine diagram"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="default", layer="diagram", show_window=False, background_color='autumn')
    dlayer = test_tablet.layers['diagram']

    RectangleSE.add(layer=dlayer, asset="state name only name compartment", lower_left=Position(100, 100),
                    size=Rect_Size(height=27, width=253))
    test_tablet.render()
    assert True


def test_bp_state_compartment():
    dtype = "xUML state machine diagram"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="blueprint", layer="diagram", show_window=False, background_color='blueprint')
    dlayer = test_tablet.layers['diagram']

    RectangleSE.add(layer=dlayer, asset="state name only compartment", lower_left=Position(100, 100),
                    size=Rect_Size(height=27, width=253))
    test_tablet.render()
    assert True
