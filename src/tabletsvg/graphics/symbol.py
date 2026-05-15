""" symbol.py - Draw a predefined symbol """

# System
import logging
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Callable, Dict

if TYPE_CHECKING:
    from tabletsvg.layer import Layer

# Modelint
from mi_config.config import Config

# Tablet
from tabletsvg.styledb import StyleDB
from tabletsvg.geometry_types import Position
from tabletsvg.graphics.crayon_box import CrayonBox
from tabletsvg.tablet_config import TabletConfig
from tabletsvg.exceptions import BadConfigData

_logger = logging.getLogger(__name__)


def _fill_attr(fill_name) -> str:
    """Return an SVG fill value for a StyleDB color name, or 'none' if unspecified."""
    if not fill_name:
        return 'none'
    color = StyleDB.color.get(fill_name)
    if color:
        return f'rgb({color.r},{color.g},{color.b})'
    return fill_name  # pass through (e.g. 'none')


class Symbol:
    """
    A composite group of shapes that can be rotated and placed anywhere on the Tablet.

    Each instance builds an SVG <g> element containing all component shapes,
    optionally wrapped in a rotation transform, and appends it to the layer's Symbols list.
    """
    symbol_defs = None

    def __init__(self, layer: 'Layer', name: str, pin: Position, angle: int = 0):
        """
        Creates a Symbol from data in symbols.yaml and adds it to the layer's Symbols list.

        Args:
            layer: Layer where the symbol will be drawn.
            name: Symbol name (e.g. 'M mult', 'final pseudo state').
            pin: Bottom-center anchor point in tablet coordinates.
            angle: Degrees clockwise (0=up, 90=right, 180=down, 270=left).
        """
        self.logger = logging.getLogger(__name__)
        self.layer = layer
        self.name = name
        self.pin = pin
        self.angle = angle

        try:
            symbol_def = self.symbol_defs[layer.Drawing_type][name]
        except KeyError:
            self.logger.error(f"No symbol [{name}] defined for drawing type [{layer.Drawing_type}]")
            raise BadConfigData
        except TypeError:
            self.logger.error("Symbol definitions not loaded — ensure Symbol.load_symbol_defs() was called")
            raise

        self.component_methods: Dict[str, Callable] = {
            'polygon':  self.add_polygon,
            'polyline': self.add_polyline,
            'circle':   self.add_circle,
        }

        # Convert pin to device coordinates (used as rotation origin)
        self.device_pin = layer.Tablet.to_dc(pin)

        # Build an SVG group to hold all component elements
        self.svg_group = ET.Element('g')
        if angle:
            self.svg_group.set('transform',
                               f'rotate({angle},{self.device_pin.x},{self.device_pin.y})')

        for component_name, cdef in symbol_def.items():
            component_type = list(cdef.keys())[0]
            try:
                method = self.component_methods[component_type]
            except KeyError:
                self.logger.error(f"Component type [{component_type}] for symbol [{name}] not supported")
                raise BadConfigData
            method(component_name, cdef[component_type])

        layer.Symbols.append(self.svg_group)

    @classmethod
    def load_symbol_defs(cls):
        """Load all symbol definitions from symbols.yaml."""
        raw = Config(app_name=TabletConfig.app_name, lib_config_dir=TabletConfig.config_path,
                     fspec={'symbols': None})
        cls.symbol_defs = raw.loaded_data['symbols']

    def _component_style(self, component_name: str) -> dict:
        """Look up the presentation style dict for a named component of this symbol."""
        try:
            return self.layer.Presentation.Symbol_presentation[self.name][component_name]
        except KeyError:
            self.logger.error(f"No style for component [{component_name}] in symbol [{self.name}]")
            raise BadConfigData

    def add_polygon(self, component_name: str, shape_def):
        """
        Add a filled closed polygon component to the symbol group.

        Args:
            component_name: Component identifier used for style lookup.
            shape_def: List of [x, y] vertex offsets from the pin (tablet coordinates).
        """
        canvas_verts = [Position(v[0] + self.pin.x, v[1] + self.pin.y) for v in shape_def]
        verts_dc = [self.layer.Tablet.to_dc(v) for v in canvas_verts]

        style = self._component_style(component_name)
        attrs = CrayonBox.stroke_style(style['line style'])
        attrs['fill'] = _fill_attr(style.get('fill'))
        attrs['points'] = ' '.join(f'{v.x},{v.y}' for v in verts_dc)

        self.svg_group.append(ET.Element('polygon', attrs))
        self.logger.info(f"> Symbol polygon [{component_name}] at pin {self.pin}")

    def add_polyline(self, component_name: str, shape_def):
        """
        Add an open polyline component to the symbol group.

        Args:
            component_name: Component identifier used for style lookup.
            shape_def: List of [x, y] vertex offsets from the pin (tablet coordinates).
        """
        canvas_verts = [Position(v[0] + self.pin.x, v[1] + self.pin.y) for v in shape_def]
        verts_dc = [self.layer.Tablet.to_dc(v) for v in canvas_verts]

        style = self._component_style(component_name)
        attrs = CrayonBox.stroke_style(style['line style'])
        attrs['fill'] = 'none'
        attrs['points'] = ' '.join(f'{v.x},{v.y}' for v in verts_dc)

        self.svg_group.append(ET.Element('polyline', attrs))
        self.logger.info(f"> Symbol polyline [{component_name}] at pin {self.pin}")

    def add_circle(self, component_name: str, shape_def):
        """
        Add a circle component to the symbol group.

        Args:
            component_name: Component identifier used for style lookup.
            shape_def: Dict with 'center' ([x, y] offsets from pin) and 'radius' keys.
        """
        center_tablet = Position(self.pin.x + shape_def['center'][0],
                                 self.pin.y + shape_def['center'][1])
        center_dc = self.layer.Tablet.to_dc(center_tablet)
        radius = shape_def['radius']

        style = self._component_style(component_name)
        attrs = CrayonBox.stroke_style(style['line style'])
        attrs['fill'] = _fill_attr(style.get('fill'))
        attrs['cx'] = str(center_dc.x)
        attrs['cy'] = str(center_dc.y)
        attrs['r'] = str(radius)

        self.svg_group.append(ET.Element('circle', attrs))
        self.logger.info(f"> Symbol circle [{component_name}] center={center_dc} r={radius}")

    @classmethod
    def render(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Return all symbol group elements for this layer.

        Args:
            layer: Draw on this layer.

        Returns:
            List of SVG <g> elements.
        """
        return list(layer.Symbols)
