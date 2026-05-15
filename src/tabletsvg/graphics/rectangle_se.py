""" rectangle_se.py -- Rectangle Shape Element """

# System
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tabletsvg.layer import Layer

# Tablet
import xml.etree.ElementTree as ET
import tabletsvg.element as element
from tabletsvg.geometry_types import Rect_Size, Position
from tabletsvg.styledb import StyleDB
from tabletsvg.graphics.crayon_box import CrayonBox
from tabletsvg.exceptions import MissingConfigData

_logger = logging.getLogger(__name__)


def _rounded_rect_path(x: float, y: float, w: float, h: float,
                       top_r: int, bottom_r: int) -> str:
    """
    Build an SVG path string for a rectangle with independently rounded top and/or bottom corners.

    Args:
        x: Upper-left x in device coordinates.
        y: Upper-left y in device coordinates.
        w: Width.
        h: Height.
        top_r: Corner radius for top corners (0 = square).
        bottom_r: Corner radius for bottom corners (0 = square).

    Returns:
        SVG path data string.
    """
    r_t = top_r
    r_b = bottom_r

    if r_t and r_b:
        # All corners rounded — use a single SVG rect with rx/ry instead (caller may use <rect>)
        # Build as path anyway for consistency
        return (
            f"M {x+r_t},{y} "
            f"L {x+w-r_t},{y} "
            f"A {r_t},{r_t} 0 0 1 {x+w},{y+r_t} "
            f"L {x+w},{y+h-r_b} "
            f"A {r_b},{r_b} 0 0 1 {x+w-r_b},{y+h} "
            f"L {x+r_b},{y+h} "
            f"A {r_b},{r_b} 0 0 1 {x},{y+h-r_b} "
            f"L {x},{y+r_t} "
            f"A {r_t},{r_t} 0 0 1 {x+r_t},{y} Z"
        )
    elif r_t and not r_b:
        # Top corners rounded, bottom square
        return (
            f"M {x+r_t},{y} "
            f"L {x+w-r_t},{y} "
            f"A {r_t},{r_t} 0 0 1 {x+w},{y+r_t} "
            f"L {x+w},{y+h} "
            f"L {x},{y+h} "
            f"L {x},{y+r_t} "
            f"A {r_t},{r_t} 0 0 1 {x+r_t},{y} Z"
        )
    else:
        # Bottom corners rounded, top square
        return (
            f"M {x},{y} "
            f"L {x+w},{y} "
            f"L {x+w},{y+h-r_b} "
            f"A {r_b},{r_b} 0 0 1 {x+w-r_b},{y+h} "
            f"L {x+r_b},{y+h} "
            f"A {r_b},{r_b} 0 0 1 {x},{y+h-r_b} "
            f"L {x},{y} Z"
        )


class RectangleSE:
    """
    Manage the rendering of Rectangle Shape Elements.

    Attributes and relationships defined on the class model

    Subclass of Closed Shape on class model (R22)

    - ID {I} -- Element ID, unique within a Layer, implemented as object reference
    - Layer {I, R22} -- Element drawn on this Layer
    - Size -- Rectangle height and width
    - Lower left -- Position of corner in tablet coordinates
    """

    @classmethod
    def add(cls, layer: 'Layer', asset: str, lower_left: Position, size: Rect_Size,
            color_usage: Optional[str] = None):
        """
        Adds a rectangle to the Layer with position converted to device coordinates.

        Args:
            layer: Draw on this Layer.
            asset: Used to determine draw style.
            lower_left: Lower left corner position in tablet coordinates.
            size: The size of the rectangle in points.
            color_usage: If supplied, overrides the presentation fill color.
        """
        ll_dc = layer.Tablet.to_dc(lower_left)
        ul = Position(x=ll_dc.x, y=ll_dc.y - size.height)

        rect_style = layer.Presentation.Rectangle_presentation[asset]
        fill = rect_style.get('fill')

        try:
            border = rect_style['line style']
        except KeyError:
            _logger.exception(f"No line style in rectangle presentation for asset: [{asset}]")
            raise MissingConfigData

        if color_usage:
            try:
                fill = StyleDB.color_usage[color_usage]
            except KeyError:
                _logger.warning(f'No color defined for usage [{color_usage}]')

        cspec = rect_style.get('corner spec')
        try:
            radius, top, bottom = (0, False, False) if not cspec else (cspec['radius'], cspec['top'], cspec['bottom'])
        except KeyError:
            _logger.exception(f"Missing data in rectangle corner spec for asset: [{asset}]")
            raise MissingConfigData

        layer.Rectangles.append(element.Rectangle(
            upper_left=ul, size=size, border_style=border, fill=fill,
            radius=radius, top=top, bottom=bottom,
        ))

    @classmethod
    def render(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Build SVG elements for all rectangles on this layer.

        Args:
            layer: Draw on this layer.

        Returns:
            List of SVG elements.
        """
        elements = []
        for r in layer.Rectangles:
            x, y = r.upper_left.x, r.upper_left.y
            w, h = r.size.width, r.size.height

            stroke_attrs = CrayonBox.stroke_style(r.border_style)

            # Resolve fill
            if r.fill:
                color = StyleDB.color.get(r.fill)
                fill_val = f'rgb({color.r},{color.g},{color.b})' if color else r.fill
            else:
                fill_val = 'none'

            top_r = r.radius if r.top else 0
            bottom_r = r.radius if r.bottom else 0

            if top_r or bottom_r:
                # Partial or full corner rounding requires a path
                attrs = dict(stroke_attrs)
                attrs['fill'] = fill_val
                attrs['d'] = _rounded_rect_path(x, y, w, h, top_r, bottom_r)
                el = ET.Element('path', attrs)
            else:
                attrs = dict(stroke_attrs)
                attrs['fill'] = fill_val
                attrs['x'] = str(x)
                attrs['y'] = str(y)
                attrs['width'] = str(w)
                attrs['height'] = str(h)
                el = ET.Element('rect', attrs)

            _logger.info(f"> Rectangle at: {r.upper_left}, size: {r.size}")
            elements.append(el)
        return elements

    @classmethod
    def render_fillrect(cls, layer: 'Layer', frect: element.FillRect) -> list[ET.Element]:
        """
        Render a single filled, borderless rectangle (used for text underlays).

        Args:
            layer: Draw on this layer.
            frect: The fill rectangle element.

        Returns:
            List containing one SVG rect element.
        """
        c = frect.color
        el = ET.Element('rect', {
            'x': str(frect.upper_left.x), 'y': str(frect.upper_left.y),
            'width': str(frect.size.width), 'height': str(frect.size.height),
            'fill': f'rgb({c.r},{c.g},{c.b})',
            'stroke': 'none',
        })
        _logger.info(f"> Filled rect at: {frect.upper_left}, size: {frect.size}")
        return [el]
