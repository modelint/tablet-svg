"""
layer.py - Layer of content drawn on a Tablet
"""
# System
import logging
from typing import TYPE_CHECKING, List

# Qt
# from PyQt6.QtWidgets import (QGraphicsRectItem, QGraphicsLineItem, QGraphicsPolygonItem,
#                              QGraphicsItemGroup)

# Tablet
import tabletsvg.element as element
from tabletsvg.presentation import Presentation
# from tabletqt.graphics.circle_se import CircleSE
# from tabletqt.graphics.polygon_se import PolygonSE
from tabletsvg.graphics.line_segment import LineSegment
from tabletsvg.graphics.diagnostic_marker import DiagnosticMarker
from tabletsvg.graphics.text_element import TextElement
from tabletsvg.graphics.symbol import Symbol
from tabletsvg.graphics.rectangle_se import RectangleSE
from tabletsvg.graphics.image import ImageDE


if TYPE_CHECKING:
    from tabletsvg.tablet import Tablet

class Layer:
    """
    A common feature of many drawing and image editing applications is the ability to stack layers of
    content along a z axis toward the user’s viewpoint. Similarly, the Tablet renders each layer working
    from the lowest value on the z axis toward the highest. Thus, content on the higher layers may overlap
    content underneath.

        Attributes and relationships defined on the class model

        - Name {I} -- A name that is unique among other Layers on this Tablet (attribute)
        - Z coord {I2, OR20} -- Rendering order, also unique on this Tablet (implement as Tablet list)
        - Presentation {R2} -- Defines styling of text and graphics (attribute)
        - Drawing type {R?} -- Determines assets that can be drawn (attribute)
        - Tablet {R13} -- Layer is managed on this Tablet (attribute)
    """

    def __init__(self, name: str, tablet: 'Tablet', presentation: str, drawing_type: str):
        """
        Constructor.

        Args:
            name: A predefined or custom Layer name.
            tablet: Layer is created on this Tablet object.
            presentation: Name of Presentation styling the text and graphics on this Layer.
            drawing_type: Name of Drawing Type to determine assets that may be drawn on this Layer.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"creating layer: [{name}] ")
        self.Name = name
        self.Tablet = tablet
        # self.Scene = tablet.View.scene  # This is what we actually draw on
        self.Drawing_type = drawing_type

        # Stuff we will draw on the Layer
        self.Line_segments: List[element.Line_Segment] = []
        self.Symbols: list = []
        self.RawRectangles: List[element.Raw_Rectangle] = []
        self.RawLines: List[element.Raw_Line] = []
        self.TextUnderlayRects: List[element.FillRect] = []
        self.Text: List[element.Text_line] = []
        # self.Circles: List[element.Circle] = []
        # self.Polygons: List[...] = []
        self.Rectangles: List[element.Rectangle] = []
        self.Images: List[element.Image] = []

        # Load this Layer's presentation assets if they haven't been already
        # Unique ID (see Tablet Subsystem class diagram) of a Presentation is both
        # its name and its View Type name.  So we combine them to form the index
        pres_index = ':'.join([self.Drawing_type, presentation])
        self.Presentation = self.Tablet.Presentations.get(pres_index)
        if not self.Presentation:
            # It hasn't been loaded from the Flatland DB yet
            self.Presentation = Presentation(name=presentation, drawing_type=self.Drawing_type)
            self.Tablet.Presentations[pres_index] = self.Presentation


    def render(self) -> list:
        """Renders all Elements on this Layer, returning a list of SVG elements."""

        self.logger.info(f'Rendering layer: {self.Name}')

        # Rendering order determines what can potentially overlap on this Layer, so order matters
        elements = []
        elements.extend(LineSegment.render(self))
        elements.extend(Symbol.render(self))
        # CircleSE.render(self)
        elements.extend(RectangleSE.render(self))
        # PolygonSE.render(self)
        elements.extend(TextElement.render_underlays(self))
        elements.extend(TextElement.render(self))
        elements.extend(ImageDE.render(self))

        # Diagnostic elements with explicit styling that bypass StyleDB lookup
        # Not intended for use by any client applications
        elements.extend(DiagnosticMarker.render(self))
        return elements
