""" diagnostic_marker.py -- Diagnostic marking """

# System
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tabletsvg.layer import Layer

# Tablet
import tabletsvg.element as element
from tabletsvg.geometry_types import Position, Rect_Size


class DiagnosticMarker:
    """
    Manage the rendering of diagnostic markers such as crosshairs and rectangles
    drawn with explicitly specified styles.

    (The StyleDB is not consulted for any of these)
    """
    ch_radius = 3  # Cross hair radius

    @classmethod
    def add_cross_hair(cls, layer: 'Layer', location: Position, color: str = 'purple'):
        """
        Place a diagnostic cross hair at the requested point.

        Args:
            layer: Draw on this layer.
            location: Where to place the crosshair in tablet coordinates.
            color: CSS color name for the crosshair lines.
        """
        dc = layer.Tablet.to_dc(location)
        r = cls.ch_radius
        layer.RawLines.append(element.Raw_Line(
            from_here=Position(dc.x - r, dc.y), to_there=Position(dc.x + r, dc.y), color=color))
        layer.RawLines.append(element.Raw_Line(
            from_here=Position(dc.x, dc.y - r), to_there=Position(dc.x, dc.y + r), color=color))

    @classmethod
    def add_raw_rectangle(cls, layer: 'Layer', upper_left: Position, size: Rect_Size):
        """
        Add an unfilled rectangle for diagnostic purposes. Dimensions are supplied
        directly without consulting the StyleDB.

        Args:
            layer: Draw on this layer.
            upper_left: Upper-left corner in tablet coordinates.
            size: Width and height of the rectangle.
        """
        uldc = layer.Tablet.to_dc(upper_left)
        layer.RawRectangles.append(element.Raw_Rectangle(upper_left=uldc, size=size))

    @classmethod
    def render(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Build SVG elements for all diagnostic markers on this layer.

        Args:
            layer: Draw on this layer.

        Returns:
            List of SVG elements.
        """
        elements = []

        for rl in layer.RawLines:
            elements.append(ET.Element('line', {
                'x1': str(rl.from_here.x), 'y1': str(rl.from_here.y),
                'x2': str(rl.to_there.x),  'y2': str(rl.to_there.y),
                'stroke': rl.color, 'stroke-width': '1',
            }))

        for rr in layer.RawRectangles:
            elements.append(ET.Element('rect', {
                'x': str(rr.upper_left.x), 'y': str(rr.upper_left.y),
                'width': str(rr.size.width), 'height': str(rr.size.height),
                'fill': 'none', 'stroke': 'black', 'stroke-width': '1',
            }))

        return elements
