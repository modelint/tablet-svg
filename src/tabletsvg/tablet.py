"""
tablet.py – A multi-layered drawing surface that renders to SVG
"""
# System
import logging
import xml.etree.ElementTree as ET
from datetime import datetime  # For initial log entry
from pathlib import Path
from typing import Optional


# Qt
# from PyQt6.QtWidgets import QApplication

# Tablet
from tabletsvg.exceptions import *
from tabletsvg.geometry_types import Rect_Size, Position
from tabletsvg.styledb import StyleDB
# from tabletqt.graphics.text_element import TextElement
from tabletsvg.layer import Layer
# from tabletqt.scene_view import MainWindow
# from tabletqt.graphics.image import ImageDE
from tabletsvg.configuration.styles import FloatRGB
from tabletsvg.graphics.symbol import Symbol
from tabletsvg.graphics.text_element import TextElement
from tabletsvg.graphics.image import ImageDE
from tabletsvg.resource_library import ResourceLibrary

default_background = FloatRGB(255, 255, 255)  # White

# gui_app = QApplication([]) # Declare it here so it is not garbage collected on repeated instantiation of Tablet
# We create a Qt App instance just once on the import and then keep using the same one

class Tablet:
    """
    The Tablet class is part of the Drawing domain which provides a service to an application
    with simple 2D diagramming needs such as the Flatland model diagram generator.

    Most importantly, the Drawing domain and hence the Tablet abstract away the details of
    graphics library interaction from the fundamental diagramming application.

    The original implementation of Tablet supported the Cairo graphics library while the current
    implementation is built on the Qt Gui framework. No changes are necessary in any client diagramming
    applications that draw on a Tablet.

    For example, when a Flatland node compartment wants to draw itself, it doesn't worry about line
    widths, dash patterns and colors. It also doesn't worry about flipping to whatever coordinate
    system the graphics library uses. A compartment would just say "add_shape( asset, size, pin )" and
    the Tablet will take care of the rest. Here the asset is the name of the model entity 'compartment',
    the size in points (or whatever units the Flatland app wants to use) and pin expressed in Flatland
    Canvas coordinates.

    When a Tablet is created, it is initialized with a single populated Layer where Assets can be drawn.
    For example, Flatland might start with a predefined 'diagram' Layer using a Drawing Type such as
    'state machine diagram' and a Presentation such as 'default' or 'formal' or 'corporate'.

    The Diagram Type determines what kinds of things might be drawn, Assets such as 'connector',
    'compartment', 'class name', etc., while the Presentation establishes the Text and Line Styles to
    be used when drawing those Assets. All of this information is stored in yaml files which the Tablet
    loads upon creation.

    Each time the application wants something drawn, it will ask Tablet to add the appropriate Asset
    to one of its render lists. A separate list is maintained for all the rectangles, line segments and
    text lines to be rendered. When the application is finished populating these lists, the Tablet can
    render everything using its graphic library (Qt in this implementation) using whatever coordinate
    system the library supplies, making any necessary conversions from the application coordinate system.

        Attributes and relationships defined on the class model

        - ID {I} -- Unique id, implemented as a reference to a Tablet object, no attribute needed
        - Size -- The height and width of the drawing surface (attribute)
        - Output_file -- A filename or output stream object to be output as a drawing (attribute)
        - Background_color -- The color of the Tablet (visible through all non-opaque layer elements)
    """

    def __init__(self, size: Rect_Size, output_file: Path, drawing_type: str, presentation: str,
                 layer: str, show_window: bool = False, background_color: Optional[str] = 'white',
                 pdf: bool = False):
        """
        Constructs a new Tablet instance with a single initial predefined Layer.

        Args:
            size: Vertical and horizontal span of the entire draw surface in points.
            output_file: Name of the drawing file to be generated.
            drawing_type: Initial layer Drawing Type so we know what kinds text and graphics Assets can be drawn.
            presentation: Initial layer's Presentation so we know what graphic styles to use for our Assets.
            layer: The name of the predefined initial Layer to be created on this Tablet (typically 'diagram').
            background_color: Name of background color defined in colors.yaml.
            pdf: If True, also write a PDF alongside the SVG file.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Tablet init: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.app_name = "tablet"

        # Load all of the common font, color, etc. styles used by all Presentations from yaml files
        StyleDB.load_config_files()

        # Ensure the user has an image library
        ResourceLibrary.init_user_images()

        # Load symbols, stickers, and build image paths for all assets and drawing types
        Symbol.load_symbol_defs()
        ImageDE.build_paths()
        TextElement.load_stickers()

        # Establish a system default layer ordering. Not all of them will be used in any given
        # View, but this is the draw order from bottom-most layer upward
        # It can (should be) customizable by the user, but this should work for most diagrams
        self.show_window = show_window
        self.pdf = pdf
        try:
            self.background_color = StyleDB.color[background_color]  # This is referenced when filling text underlay rects
        except KeyError:
            self.logger.error(f'Background color [{background_color} not defined in colors.yaml file')
            raise MissingConfigData
        self.layer_order = ['sheet', 'grid', 'frame', 'diagram', 'scenario', 'annotation']
        self.Presentations = {}  # Presentations loaded from the Flatland database, updated by Layer class
        # self.App = gui_app  # QT Application (must be created before any QT widgets)
        # self.Window = MainWindow(title=self.app_name, size=size, background=self.background_color)  # QT widget for drawing 2D elements
        # self.View = self.Window.graphics_view

        if layer not in self.layer_order:
            raise NonSystemInitialLayer
        self.layers = {layer: Layer(name=layer, tablet=self, presentation=presentation, drawing_type=drawing_type)}
        # Initialize the first layer at the indicated position. If the position is not in the system layer order
        # list, it will be placed as the topmost layer. Usually, though, the initial layer should be diagram

        # self.Drawing_type = drawing_type  # class diagram, state diagram, etc
        self.Size = size
        self.Output_file = output_file

    def add_layer(self, name: str, presentation: str, drawing_type: str) -> Optional[Layer]:
        """
        Populate a new layer by name and return it. If a layer of the same name has already been
        populated, no layer is returned.

        All drawing takes place on a designated layer, such as 'diagram' or 'sheet'.

        A defined layer is simply a known layer name within a predefined rendering order.
        You can think of each position in the order as a z coordinate with 0 corresponding to the first
        rendered layer. For example, the 'sheet' layer is at the bottom (0) with 'diagram' somewhere
        above it.

        A layer, predefined or custom, must be populated before anything can be drawn on it.
        The client application is responsible for populating any layers that it needs. There is not automatic
        population.

        If a layer name is supplied that does not correspond to any of the predefined layers, it will be stacked
        after the last predefined layer and, thus, rendered last.

        Args:
            name: One of the standard layer stickers or a custom layer name.
            presentation: The Presentation name associated with this Layer.
            drawing_type: The Drawing Type defining this Presentation.

        Returns:
            A reference to the newly created layer.
        """
        if not self.layers.get(name):
            if name not in self.layer_order:
                self.layer_order.append(name)
            self.layers[name] = Layer(name=name, tablet=self, presentation=presentation, drawing_type=drawing_type)
            return self.layers[name]
        else:
            self.logger.warning(f"Layer: [{name}] already exists")
            return None

    def render(self):
        """
        Renders each populated layer of the Tablet moving up the z axis and writes an SVG file.
        Any unpopulated layers are skipped.
        """
        w, h = self.Size.width, self.Size.height
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(w),
            'height': str(h),
            'viewBox': f'0 0 {w} {h}',
        })

        bg = self.background_color
        ET.SubElement(svg, 'rect', {
            'width': str(w),
            'height': str(h),
            'fill': f'rgb({bg.r},{bg.g},{bg.b})',
        })

        for name in self.layer_order:
            if self.layers.get(name):
                for el in self.layers[name].render():
                    svg.append(el)

        self.Output_file.parent.mkdir(parents=True, exist_ok=True)
        tree = ET.ElementTree(svg)
        ET.indent(tree, space='  ')
        tree.write(str(self.Output_file), encoding='unicode', xml_declaration=False)
        self.logger.info(f"SVG written to {self.Output_file}")

        if self.pdf:
            import cairosvg
            pdf_path = self.Output_file.with_suffix('.pdf')
            cairosvg.svg2pdf(url=str(self.Output_file), write_to=str(pdf_path))
            self.logger.info(f"PDF written to {pdf_path}")

    def to_dc(self, tablet_coord: Position) -> Position:
        """
        Convert from tabletqt coordinates (tc) used by the client application to device
        coordinates (dc).

        Tablet coordinates are upper right quadrant cartesian with the origin (0,0) in the
        lower left corner of the tabletqt. This is what client application (user) specifies
        when drawing.

        Device coordinates depend on the graphics library. Here we are using Qt, so we have
        a standard display coordinate system with the origin in the upper left corner with
        y values ascending toward the bottom of the display.

        An exception is thrown if the supplied position is outside of the tabletqt boundary.

        Note: This may seem like overkill for a simple computation and check, but less
        error prone than having this pattern sprinked throughout the code.

        Args:
            tablet_coord: Position in table coordinates.

        Returns:
            Position in device coordinates.
        """
        if tablet_coord.y > self.Size.height:
            raise TabletBoundsExceeded("Tablet height exceeded", height=tablet_coord.y - self.Size.height, width=0)
        assert tablet_coord.x >= 0, "Negative x value"
        assert tablet_coord.y >= 0, "Negative y value"
        return Position(x=tablet_coord.x, y=self.Size.height - tablet_coord.y)

    def __repr__(self):
        return f'Size: {self.Size},  Output: {self.Output_file}'
