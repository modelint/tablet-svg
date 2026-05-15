""" test_state_symbols.py - Draw all state machine symbols for different presentations """

import inspect
from pathlib import Path
from tabletsvg.tablet import Tablet
from tabletsvg.geometry_types import Rect_Size, Position
from tabletsvg.graphics.symbol import Symbol

points_in_mm = 2.83465
A4 = Rect_Size(round(210 * points_in_mm), round(297 * points_in_mm))
OUTPUT = Path(__file__).parent / "output"


def test_state_symbols():
    dtype = "xUML state machine diagram"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="default", layer="diagram", show_window=False, background_color='autumn')
    dlayer = test_tablet.layers['diagram']

    Symbol(layer=dlayer, name='target state',        pin=Position(100, 200), angle=0)
    Symbol(layer=dlayer, name='initial pseudo state', pin=Position(200, 200), angle=0)
    Symbol(layer=dlayer, name='final pseudo state',   pin=Position(300, 200), angle=0)

    Symbol(layer=dlayer, name='target state',        pin=Position(100, 400), angle=90)
    Symbol(layer=dlayer, name='initial pseudo state', pin=Position(200, 400), angle=180)
    Symbol(layer=dlayer, name='final pseudo state',   pin=Position(300, 400), angle=270)

    test_tablet.render()
    assert True


def test_bp_state_symbols():
    dtype = "xUML state machine diagram"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="blueprint", layer="diagram", show_window=False, background_color='blueprint')
    dlayer = test_tablet.layers['diagram']

    Symbol(layer=dlayer, name='target state',        pin=Position(100, 200), angle=0)
    Symbol(layer=dlayer, name='initial pseudo state', pin=Position(200, 200), angle=0)
    Symbol(layer=dlayer, name='final pseudo state',   pin=Position(300, 200), angle=0)

    Symbol(layer=dlayer, name='target state',        pin=Position(100, 400), angle=90)
    Symbol(layer=dlayer, name='initial pseudo state', pin=Position(200, 400), angle=180)
    Symbol(layer=dlayer, name='final pseudo state',   pin=Position(300, 400), angle=270)

    test_tablet.render()
    assert True
