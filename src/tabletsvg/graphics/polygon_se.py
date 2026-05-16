""" polygon_se.py -- Polygon Shape Element """

# System
import logging
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from tabletsvg.layer import Layer

# Tablet
import tabletsvg.element as element
from tabletsvg.geometry_types import Position
from tabletsvg.graphics.line_segment import LineSegment

_logger = logging.getLogger(__name__)


class PolygonSE:
    """
    Manage the rendering of Polygon Shape Elements which are Closed Shapes.

    Additionally, a contiguous sequence of Line Segments are managed here as an
    open polygon shape. There is no concept of an open polygon in the class models so
    add_open delegates to LineSegment rather than maintaining a separate element list.

    Subclass of Closed Shape on class model (R22)

    - ID {I} -- Element ID, unique within a Layer, implemented as object reference
    - Layer {I, R22} -- Element drawn on this Layer
    """

    @classmethod
    def add_open(cls, layer: 'Layer', asset: str, vertices: List[Position]):
        """
        Add a stroked open polyline by decomposing the vertex sequence into line segments.

        Args:
            layer: Draw on this layer.
            asset: Used to determine line style.
            vertices: Ordered vertex positions in tablet coordinates (minimum 2).
        """
        assert len(vertices) > 1, "Open polygon requires at least two vertices"
        for v1, v2 in zip(vertices, vertices[1:]):
            LineSegment.add(layer=layer, asset=asset, from_here=v1, to_there=v2)

    @classmethod
    def render(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Build SVG <polygon> elements for all closed polygons on this layer.

        Args:
            layer: Draw on this layer.

        Returns:
            List of SVG <polygon> elements.
        """
        elements = []
        for poly in layer.Polygons:
            points_str = ' '.join(f'{v.x},{v.y}' for v in poly.vertices)
            _logger.info(f"> Polygon with {len(poly.vertices)} vertices")
            elements.append(ET.Element('polygon', {
                'points': points_str,
                'fill': poly.fill or 'none',
            }))
        return elements
