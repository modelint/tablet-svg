""" line_segment.py -- Line Segment """

# System
import logging
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tabletsvg.layer import Layer

# Tablet
import tabletsvg.element as element
from tabletsvg.geometry_types import Position
from tabletsvg.graphics.crayon_box import CrayonBox
from tabletsvg.exceptions import MissingConfigData

_logger = logging.getLogger(__name__)


class LineSegment:
    """
    Manage the rendering of Line Segments

    Attributes and relationships defined on the class model

    Subclass of Shape Element on class model (R12)

    - ID {I} -- Element ID, unique within a Layer, implemented as object reference
    - Layer {I, R12} -- Element drawn on this Layer via R12/R15/Element/R19/Layer
    - From -- Draw from here in tablet coordinates
    - To -- To here in tablet coordinates
    """

    @classmethod
    def add(cls, layer: 'Layer', asset: str, from_here: Position, to_there: Position):
        """
        Convert line segment coordinates to device coordinates and combine with the Line Style defined
        for the Asset in the selected Presentation Style.

        Args:
            layer: Draw on this layer.
            asset: Used to determine draw style.
            from_here: In tablet coordinates.
            to_there: In tablet coordinates.
        """
        try:
            line_style = layer.Presentation.Line_presentation[asset]['line style']
        except KeyError:
            _logger.exception(f"No line style specified in line presentation for asset: [{asset}]")
            raise MissingConfigData

        layer.Line_segments.append(
            element.Line_Segment(
                from_here=layer.Tablet.to_dc(from_here),
                to_there=layer.Tablet.to_dc(to_there),
                style=line_style,
            )
        )

    @classmethod
    def render(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Build SVG line elements for all line segments on this layer.

        Args:
            layer: Draw on this layer.

        Returns:
            List of SVG <line> elements.
        """
        elements = []
        for ls in layer.Line_segments:
            _logger.info(f"> Line {ls.from_here}, {ls.to_there}")
            attrs = CrayonBox.stroke_style(ls.style)
            attrs['x1'] = str(ls.from_here.x)
            attrs['y1'] = str(ls.from_here.y)
            attrs['x2'] = str(ls.to_there.x)
            attrs['y2'] = str(ls.to_there.y)
            elements.append(ET.Element('line', attrs))
        return elements