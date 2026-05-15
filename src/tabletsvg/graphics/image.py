""" image.py -- Image Display Element """

# System
import base64
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tabletsvg.layer import Layer

# Modelint
from mi_config.config import Config

# Tablet
import tabletsvg.element as element
from tabletsvg.geometry_types import Position, Rect_Size
from tabletsvg.exceptions import TabletBoundsExceeded
from tabletsvg.tablet_config import TabletConfig

_logger = logging.getLogger(__name__)


class ImageDE:
    """
    Image Display Element — manages loading and rendering of PNG/JPEG images into SVG.

    Images are embedded as base64 data URIs so the output SVG is self-contained.
    """
    image_paths = None

    @classmethod
    def build_paths(cls):
        """Build the image name → file path dictionary from images.yaml."""
        raw = Config(app_name=TabletConfig.app_name, lib_config_dir=TabletConfig.config_path,
                     fspec={'images': None})
        image_dict = raw.loaded_data['images']
        root_dir = raw.user_config_dir
        cls.image_paths = {k: Path(root_dir / 'images' / v) for k, v in image_dict.items()}

    @classmethod
    def add(cls, layer: 'Layer', name: str, lower_left: Position, size: Rect_Size):
        """
        Register an image on the layer, converting to device coordinates.

        :param layer: Draw on this Layer
        :param name: Image resource name (key in images.yaml)
        :param lower_left: Lower left corner of the image in tablet coordinates
        :param size: Display size in points
        """
        try:
            ll_dc = layer.Tablet.to_dc(lower_left)
        except TabletBoundsExceeded:
            _logger.warning(f"Lower left corner of image [{name}] is outside Tablet draw region")
            return

        ul = Position(x=ll_dc.x, y=ll_dc.y - size.height)

        try:
            path = cls.image_paths[name]
        except KeyError:
            _logger.warning(f"No path defined for image [{name}]")
            return

        layer.Images.append(element.Image(resource_path=path, upper_left=ul, size=size))
        _logger.info(f'Registered image [{name}] at {ul}')

    @classmethod
    def render(cls, layer: 'Layer') -> list[ET.Element]:
        """
        Render image elements as SVG <image> tags with embedded base64 data URIs.

        :param layer: Draw on this layer
        :return: List of SVG image elements
        """
        elements = []
        for img in layer.Images:
            path: Path = img.resource_path
            if not path.exists():
                _logger.error(f'Image file [{path}] not found')
                continue

            suffix = path.suffix.lower()
            mime = 'image/png' if suffix == '.png' else 'image/jpeg'

            with open(path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('ascii')

            el = ET.Element('image', {
                'href': f'data:{mime};base64,{encoded}',
                'x': str(img.upper_left.x),
                'y': str(img.upper_left.y),
                'width': str(img.size.width),
                'height': str(img.size.height),
            })
            _logger.info(f"> Image [{path.name}] at {img.upper_left}")
            elements.append(el)
        return elements
