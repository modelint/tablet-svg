""" text_element.py -- Text Element """

# System
import logging
import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from tabletsvg.layer import Layer
    from tabletsvg.presentation import Presentation

# Modelint
from mi_config.config import Config

# Tablet
import tabletsvg.element as element
from tabletsvg.geometry_types import Position, Rect_Size, HorizAlign
from tabletsvg.styledb import StyleDB
from tabletsvg.exceptions import TabletBoundsExceeded
from tabletsvg.tablet_config import TabletConfig

logger = logging.getLogger(__name__)

# Margin added around text for underlay rectangles
underlay_margin_h = 5
underlay_margin_v = 5

underlay_offset_x = 2  # Lower-left corner offsets from text anchor for underlay positioning
underlay_offset_y = 3


class TextBlockCorner(Enum):
    """ Text Block corners """
    UL = "upper left"
    UR = "upper right"
    LL = "lower left"
    LR = "lower right"


class TextElement:
    """
    Manage the definition and rendering of Text Elements (blocks of text)

    Attributes and relationships defined on the class model

    Subclass of Element on class model (R15)

    - ID {I} -- Element ID, unique within a Layer, implemented as object reference
    - Layer {I, R22} -- Element drawn on this Layer via R22/R12/R15/Element/R19/Layer
    - Content -- One or more lines of text, implemented here as a list of strings
    - Lower left -- Position in tablet coordinates of the entire text block
    - Text style {R16} -- Typeface, color, and other display properties to be applied
    """

    stickers = None

    @classmethod
    def load_stickers(cls):
        """Load all predefined sticker text from the stickers.yaml file."""
        sticker_data = Config(app_name=TabletConfig.app_name, lib_config_dir=TabletConfig.config_path,
                              fspec={'stickers': None})
        cls.stickers = sticker_data.loaded_data['stickers']

    @classmethod
    def line_size(cls, presentation: 'Presentation', asset: str, text_line: str) -> Rect_Size:
        """
        Returns the approximate size of a line of text when rendered with the asset's text style.

        Uses font size as the cap height and estimates width at 0.6× font size per character,
        which is a reasonable average for the proportional fonts used in this project.

        Args:
            presentation: The Presentation.
            asset: Determines text display style.
            text_line: Line of text.

        Returns:
            Approximate size of the text line.
        """
        style_name = presentation.Text_presentation[asset]
        style = StyleDB.text_style[style_name['text style']]
        height = style.size
        width = int(style.size * 0.6 * len(text_line))
        return Rect_Size(height=height, width=width)

    @classmethod
    def text_block_size(cls, presentation: 'Presentation', asset: str, text_block: List[str]) -> Rect_Size:
        """
        Determines the approximate dimensions of a rectangle bounding the text to be drawn.

        Args:
            presentation: The Presentation.
            asset: Name of the text asset to get display style properties.
            text_block: A list of text lines to be displayed.

        Returns:
            The approximate display size of the text block.
        """
        style_name = presentation.Text_presentation[asset]
        style = StyleDB.text_style[style_name['text style']]
        font_height = style.size
        spacing = font_height * style.spacing
        inter_line_spacing = spacing - font_height

        num_lines = len(text_block)
        assert num_lines > 0, "Text block size requested for empty text block"
        widths = [cls.line_size(presentation=presentation, asset=asset, text_line=line).width for line in text_block]
        block_width = max(widths)
        block_height = num_lines * spacing - inter_line_spacing

        return Rect_Size(width=block_width, height=block_height)

    @classmethod
    def lower_left_pin(cls, presentation: 'Presentation', asset: str, text_block: List[str], pin: Position,
                       corner: TextBlockCorner) -> Position:
        """
        Given a text block and the position of one of its corners, return the position of its lower left corner.

        Args:
            presentation: The target layer's Presentation.
            asset: Name of asset that defines the style properties for rendering the text.
            text_block: Lines of text in the block.
            pin: Location of some corner in Tablet coordinates.
            corner: The corner to be pinned (upper left, lower right, ...).

        Returns:
            The position of the lower left corner in Tablet coordinates.
        """
        if corner == TextBlockCorner.LL:
            return pin

        tblock_size = cls.text_block_size(presentation=presentation, asset=asset, text_block=text_block)

        if corner == TextBlockCorner.UL:
            return Position(pin.x, pin.y - tblock_size.height)
        if corner == TextBlockCorner.LR:
            return Position(pin.x - tblock_size.width, pin.y)
        if corner == TextBlockCorner.UR:
            return Position(pin.x - tblock_size.width, pin.y - tblock_size.height)

    @classmethod
    def add_sticker(cls, layer: 'Layer', asset: str, name: str, pin: Position, corner: TextBlockCorner):
        """
        Place a Sticker at the requested location.

        A sticker is always a single line of text, so alignment is not specified.

        Args:
            layer: Place sticker on this layer.
            asset: Defines the style properties for rendering the text.
            name: Name of the sticker to be applied.
            pin: Location of some corner (like a thumbtack pin).
            corner: The corner to be pinned.
        """
        drawing_type = cls.stickers[layer.Drawing_type]
        try:
            sticker_text = drawing_type[asset][name]
        except KeyError:
            return

        ll_corner = cls.lower_left_pin(presentation=layer.Presentation, asset=asset, text_block=[sticker_text],
                                       pin=pin, corner=corner)
        cls.add_line(layer=layer, asset=asset, lower_left=ll_corner, text=sticker_text)

    @classmethod
    def add_underlay(cls, layer: 'Layer', lower_left: Position, size: Rect_Size):
        """
        Add a filled rectangle matching the background color to sit beneath text.

        Args:
            layer: Draw on this layer.
            lower_left: Lower left corner position in tablet coordinates.
            size: The size of the underlay rectangle in points.
        """
        ll_dc = layer.Tablet.to_dc(lower_left)
        ul = Position(x=ll_dc.x, y=ll_dc.y - size.height)
        layer.TextUnderlayRects.append(element.FillRect(
            upper_left=ul, size=size, color=layer.Tablet.background_color))

    @classmethod
    def add_line(cls, layer: 'Layer', asset: str, lower_left: Position, text: str):
        """
        Add a line of text to the Layer at the specified lower left corner.

        For SVG output the stored position is the device-coordinate baseline anchor —
        the x,y from which the SVG renderer draws the text upward.

        Args:
            layer: Draw on this layer.
            asset: Used to determine text style.
            lower_left: Lower left corner position of text line in tablet coordinates.
            text: The text string to render.
        """
        ll_dc = layer.Tablet.to_dc(lower_left)

        if asset in layer.Presentation.Underlays:
            tl_size = cls.line_size(presentation=layer.Presentation, asset=asset, text_line=text)
            underlay_size = Rect_Size(height=tl_size.height + underlay_margin_v,
                                     width=tl_size.width + underlay_margin_h)
            underlay_pos = Position(lower_left.x - underlay_offset_x, lower_left.y - underlay_offset_y)
            cls.add_underlay(layer=layer, lower_left=underlay_pos, size=underlay_size)

        try:
            layer.Text.append(
                element.Text_line(
                    upper_left=ll_dc,  # SVG baseline anchor in device coordinates
                    text=text,
                    style=layer.Presentation.Text_presentation[asset],
                )
            )
        except TabletBoundsExceeded:
            logger.warning(f"Asset: [{asset}] Text: [{text}] outside of tablet draw area")

    @classmethod
    def pin_block(cls, layer: 'Layer', asset: str, text: List[str], pin: Position,
                  corner: TextBlockCorner, align: HorizAlign = HorizAlign.LEFT):
        """
        Pin a text block to a Layer specifying any of the four block corners.

        Args:
            layer: Add text to this layer.
            asset: Determines text style.
            text: One or more lines of text.
            pin: Location of the pinned corner in tablet coordinates.
            corner: Which corner is pinned.
            align: Horizontal alignment within the block.
        """
        ll_corner = cls.lower_left_pin(presentation=layer.Presentation, asset=asset, text_block=text,
                                       pin=pin, corner=corner)
        cls.add_block(layer=layer, asset=asset, lower_left=ll_corner, text=text, align=align)

    @classmethod
    def add_block(cls, layer: 'Layer', asset: str, lower_left: Position, text: List[str],
                  align: HorizAlign = HorizAlign.LEFT):
        """
        Add all lines in a text block to the Layer, positioned from the bottom up.

        Args:
            layer: Add text to this Layer.
            asset: Determines text style.
            lower_left: Lower left corner of the text block on the Tablet.
            text: One or more lines of text.
            align: Horizontal alignment (left, right, or center).
        """
        style_name = layer.Presentation.Text_presentation[asset]
        style = StyleDB.text_style[style_name['text style']]
        spacing = style.size * style.spacing

        xpos, ypos = lower_left
        block_width = None
        if align != HorizAlign.LEFT:
            longest_line = max(text, key=len)
            block_width = cls.line_size(presentation=layer.Presentation, asset=asset, text_line=longest_line).width

        for line in text[::-1]:  # Bottom to top
            x_indent = 0
            if align == HorizAlign.RIGHT:
                assert block_width is not None
                line_width = cls.line_size(presentation=layer.Presentation, asset=asset, text_line=line).width
                x_indent = block_width - line_width
            if align == HorizAlign.CENTER:
                line_width = cls.line_size(presentation=layer.Presentation, asset=asset, text_line=line).width
                x_indent = (block_width - line_width) / 2
            cls.add_line(layer=layer, asset=asset, lower_left=Position(xpos + x_indent, ypos), text=line)
            ypos += spacing

    @classmethod
    def render_underlays(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Render all text underlays as filled, borderless rectangles.

        Args:
            layer: Draw on this layer.

        Returns:
            List of SVG rect elements.
        """
        elements = []
        for u in layer.TextUnderlayRects:
            c = u.color
            elements.append(ET.Element('rect', {
                'x': str(u.upper_left.x), 'y': str(u.upper_left.y),
                'width': str(u.size.width), 'height': str(u.size.height),
                'fill': f'rgb({c.r},{c.g},{c.b})',
                'stroke': 'none',
            }))
        return elements

    @classmethod
    def render(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Render all lines of text on this layer as SVG text elements.

        The stored position is the SVG baseline anchor (device coordinates).
        Font properties are mapped directly to SVG presentation attributes.

        Args:
            layer: Draw on this Layer.

        Returns:
            List of SVG text elements.
        """
        elements = []
        for t in layer.Text:
            style = StyleDB.text_style[t.style['text style']]
            color = StyleDB.color[style.color]
            font_family = StyleDB.typeface[style.typeface]

            attrs = {
                'x': str(t.upper_left.x),
                'y': str(t.upper_left.y),
                'font-family': font_family,
                'font-size': str(style.size),
                'fill': f'rgb({color.r},{color.g},{color.b})',
            }
            if style.weight == 'bold':
                attrs['font-weight'] = 'bold'
            if style.slant == 'italic':
                attrs['font-style'] = 'italic'

            logger.info(f'> Text [{t.text}] at {t.upper_left}, style={style}')
            el = ET.Element('text', attrs)
            el.text = t.text
            elements.append(el)
        return elements
