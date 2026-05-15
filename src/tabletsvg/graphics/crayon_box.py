""" crayon_box.py - Returns SVG stroke attributes derived from the StyleDB """

import logging
from tabletsvg.styledb import StyleDB

_logger = logging.getLogger(__name__)


class CrayonBox:
    """
    Get your SVG stroke attributes here.
    """

    @classmethod
    def stroke_style(cls, border_style: str) -> dict:
        """
        Returns a dict of SVG stroke attributes for a named line style.

        Args:
            border_style: Name of the line style key in the StyleDB.

        Returns:
            Dict of SVG presentation attributes (stroke, stroke-width, stroke-dasharray).
        """
        ls = StyleDB.line_style[border_style]
        color = StyleDB.color[ls.color]
        attrs = {
            'stroke': f'rgb({color.r},{color.g},{color.b})',
            'stroke-width': str(ls.width),
        }
        if ls.pattern != 'no dash':
            dp = StyleDB.dash_pattern[ls.pattern]
            attrs['stroke-dasharray'] = f'{dp.solid} {dp.blank}'
        _logger.info(f"Stroke: color={ls.color}, width={ls.width}, pattern={ls.pattern}")
        return attrs