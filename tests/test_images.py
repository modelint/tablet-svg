""" test_images.py - Draw image elements """

import inspect
from pathlib import Path
from tabletsvg.tablet import Tablet
from tabletsvg.geometry_types import Rect_Size, Position
from tabletsvg.graphics.image import ImageDE

points_in_mm = 2.83465
A4 = Rect_Size(round(210 * points_in_mm), round(297 * points_in_mm))
OUTPUT = Path(__file__).parent / "output"


def test_images():
    dtype = "Starr class diagram"
    output_path = OUTPUT / f"{inspect.currentframe().f_code.co_name}.svg"

    test_tablet = Tablet(size=A4, output_file=output_path, drawing_type=dtype,
                         presentation="default", layer="diagram", show_window=False, background_color='blue steel')
    dlayer = test_tablet.layers['diagram']

    ImageDE.add(layer=dlayer, name="mint-small",  lower_left=Position(100, 50),  size=Rect_Size(180, 24))
    ImageDE.add(layer=dlayer, name="mint-large",  lower_left=Position(100, 150), size=Rect_Size(191, 25))
    ImageDE.add(layer=dlayer, name="MIT-small",   lower_left=Position(100, 350), size=Rect_Size(180, 24))

    test_tablet.render()
    assert True
