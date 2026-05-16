# TabletSVG — Qt-to-SVG Migration Notes

## Overall Goal

Replicate the full capabilities of **TabletQT** (`~/SDEV/Python/PyCharm/TabletQT`, also on GitHub as `modelint/tablet-qt`) but generate SVG files directly using Python's stdlib, with no dependency on PyQt6. The package is named **mi-tabletsvg** and lives at `~/SDEV/Python/PyCharm/TabletSVG`.

Client applications (e.g. Flatland diagram generator) should be able to call the same drawing API with no significant changes. Only the rendering backend differs.

---

## Repository / Environment

| Item | Value |
|------|-------|
| Project root | `~/SDEV/Python/PyCharm/TabletSVG` |
| Virtualenv | `~/SDEV/Environments/TabletSVG/` |
| Run tests | `/Users/starr/SDEV/Environments/TabletSVG/bin/pytest tests/ -v` |
| Active branch | `refine` |
| Remote | `https://github.com/modelint/tablet-svg` |
| Reference project | `~/SDEV/Python/PyCharm/TabletQT` |
| Shared config dir | `~/.config/mi_tablet/` (yaml files shared with TabletQT) |

---

## Key Architectural Decisions

### SVG generation
- Use Python stdlib `xml.etree.ElementTree` — no extra graphics library needed.
- All drawing elements are accumulated in layer render lists, then flushed to a single SVG `<svg>` tree by `Tablet.render()`.
- Output is a self-contained SVG (no external file references).

### Coordinate system
- **Tablet coords**: origin at bottom-left, y increases upward (what client apps supply).
- **Device/SVG coords**: origin at top-left, y increases downward.
- Conversion: `to_dc(pos)` → `Position(x=pos.x, y=tablet.height - pos.y)`.

### Config loading (`mi_config`)
- Loads yaml files from `~/.config/mi_tablet/` first; falls back to the package's `lib_config_dir` if a file is missing.
- Files: `colors.yaml`, `line_styles.yaml`, `dash_patterns.yaml`, `typefaces.yaml`, `text_styles.yaml`, `color_usages.yaml`, `symbols.yaml`, `stickers.yaml`, `images.yaml`, `drawing_types.yaml`.
- `StyleDB.load_config_files()` must be called before anything else (done in `Tablet.__init__`).

### Font metrics (no Qt)
- Qt `QFontMetrics.boundingRect()` replaced with approximation:
  - `height = style.size` (font size in points)
  - `width = int(style.size * 0.6 * len(text))` (0.6× average for proportional fonts)
- Used for underlay rectangle sizing and multi-line block layout.

### Image embedding
- PNG images embedded as `data:image/png;base64,...` data URIs → self-contained SVG.
- Display size uses **natural PNG pixel dimensions** read from the IHDR header (first 24 bytes), NOT the `size` hint passed to `ImageDE.add()`. This matches the Qt behaviour where `QPixmap` renders at native resolution.
- IHDR parsing: skip 16 bytes (8-byte PNG sig + 4-byte length + 4-byte 'IHDR'), then `struct.unpack('>II', 8 bytes)` → `(width, height)`.

### Rounded rectangles
- SVG `<rect rx ry>` rounds all corners uniformly.
- We need top-only or bottom-only rounding for compartments, so `_rounded_rect_path()` in `rectangle_se.py` builds an SVG `<path>` with arc commands (`A rx,ry 0 0 1 x y`).

### Symbol rotation
- Each symbol builds an SVG `<g>` element.
- Rotation uses `transform="rotate(angle, cx, cy)"` where `cx,cy` is the device-coord pin. This matches Qt's `setTransformOriginPoint` + `setRotation` in y-down space.

### Optional PDF output
- `Tablet(... pdf=True)` writes a `.pdf` alongside the `.svg` using **CairoSVG** (`pip install cairosvg`).
- Import is lazy (`import cairosvg` inside `render()`) so tests pass without `libcairo` installed.
- `libcairo` is installed via Homebrew (`brew install cairo`) at `/opt/homebrew/lib/libcairo.2.dylib`.
- **Known issue**: `cairocffi` (CairoSVG's dependency) doesn't search `/opt/homebrew/lib` by default on Apple Silicon. Fix: add to shell profile:
  ```sh
  export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
  ```

### Docstring style
- All docstrings use **Google style** (converted from reStructuredText in the last session).
- Multi-line docstrings have a blank line after the opening `"""`.

---

## Important Type Notes

```python
# CRITICAL: height is the FIRST positional field, width is SECOND
Rect_Size = namedtuple('Rect_Size', 'height width')

Position = namedtuple('Position', 'x y')
```

---

## Completed Work

### Package infrastructure
- `pyproject.toml` — package name `mi-tabletsvg`, dependencies: `mi-configurator`, `PyYAML`, `cairosvg`
- `src/tabletsvg/` package layout with `where = ["src"]` in setuptools config
- Installed editable: `pip install -e .` in the TabletSVG virtualenv

### Core modules converted/created
| File | Status | Notes |
|------|--------|-------|
| `tablet.py` | Complete | `render()` writes SVG; optional `pdf=True` via CairoSVG |
| `layer.py` | Complete | All element lists wired; z-order rendering |
| `styledb.py` | Complete | Fixed `config_path` NameError (→ `TabletConfig.config_path`) |
| `presentation.py` | Complete | Loads `drawing_types.yaml` |
| `element.py` | Complete | Namedtuples: `Line_Segment`, `Rectangle`, `FillRect`, `Text_line`, `Image`, `Raw_Line`, `Raw_Rectangle` |
| `configuration/styles.py` | Complete | `FloatRGB`, `LineStyle`, `TextStyle`, `DashPattern` |
| `tablet_config.py` | Complete | Paths + app name |
| `resource_library.py` | Complete | Copies startup images to `~/.config/mi_tablet/images/` |
| `exceptions.py` | Complete | |
| `geometry_types.py` | Complete | |

### Graphics modules
| File | Status | Notes |
|------|--------|-------|
| `graphics/line_segment.py` | Complete | `add()` + `render()` → SVG `<line>` |
| `graphics/diagnostic_marker.py` | Complete | Crosshairs + raw rectangles |
| `graphics/crayon_box.py` | Complete | Returns SVG stroke attribute dicts |
| `graphics/text_element.py` | Complete | `add_line()`, `add_block()`, `add_sticker()`, `pin_block()`, underlay support, `render()` / `render_underlays()` |
| `graphics/symbol.py` | Complete | Polygon, polyline, circle components; rotation via SVG transform |
| `graphics/rectangle_se.py` | Complete | Plain `<rect>` or `<path>` with rounded corners |
| `graphics/image.py` | Complete | PNG/JPEG embedded as base64 data URIs at natural pixel size |

### Tests (all passing — 16/16)
| Test file | Tests |
|-----------|-------|
| `tests/test_cd_text.py` | `test_cd_text`, `test_bp_cd_text`, `test_Starr_underlay`, `test_xUML_underlay` |
| `tests/test_images.py` | `test_images` |
| `tests/test_rectangles.py` | `test_grid_boundary`, `test_class_compartment`, `test_bp_class_compartment`, `test_state_compartment`, `test_bp_state_compartment` |
| `tests/test_starrcd_symbols.py` | `test_starrcd_symbols`, `test_bp_starrcd_symbols` |
| `tests/test_state_symbols.py` | `test_state_symbols`, `test_bp_state_symbols` |
| `tests/test_xuml_stickers.py` | `test_xuml_stickers`, `test_bp_xuml_stickers` |

Output SVGs go to `tests/output/` (gitignored).

### Demo files converted
- `demo/demo4_lines.py` — line drawing + diagnostic markers
- `demo/demo2_stickers.py` — text stickers
- `demo/demo5_symbols.py` — Starr class diagram symbols
- `demo/demo5sm_symbols.py` — state machine symbols

---

## In Progress / Partially Done

### Uncommitted changes in working tree
- `src/tabletsvg/__main__.py` — user made edits in the IDE (cleaned up comments, updated description string). **Needs review**: the `args.colors` block now imports from `tabletqt.styledb` which will fail at runtime — should import from `tabletsvg.styledb`.
- `src/tabletsvg/tablet.py` — user/linter cleaned up (removed commented-out Qt lines).
- `README.md` — user modified.
- `.idea/TabletSVG.iml` — IDE metadata.

These changes are **not yet committed**.

---

## Still To Do

The following items from TabletQT have not yet been ported:

1. **`CircleSE`** (`graphics/circle_se.py`) — draws standalone circle shapes. Commented out in `layer.py` (`# CircleSE.render(self)`). TabletQT reference: `tabletqt/graphics/circle_se.py`.

2. **`PolygonSE`** (`graphics/polygon_se.py`) — draws standalone closed polygons. Also commented out in `layer.py`. TabletQT reference: `tabletqt/graphics/polygon_se.py`.

3. **`__main__.py` cleanup** — fix `args.colors` block: replace `from tabletqt.styledb import StyleDB` with `from tabletsvg.styledb import StyleDB`. Also verify `StyleDB.report_colors()` works (it currently calls `cls.rgbF` which may not exist in the SVG version).

4. **PDF test** — no test currently exercises `pdf=True`. Consider adding one to `test_rectangles.py` or a dedicated `test_pdf.py`.

5. **`DYLD_LIBRARY_PATH` documentation** — add note to README about needing `export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"` for PDF output on macOS Apple Silicon.

6. **Merge `refine` → `main`** — once the above items are resolved.

---

## Layer Rendering Z-Order (in `layer.py`)

```python
elements.extend(LineSegment.render(self))       # bottom
elements.extend(Symbol.render(self))
# CircleSE.render(self)                         # not yet ported
elements.extend(RectangleSE.render(self))
# PolygonSE.render(self)                        # not yet ported
elements.extend(TextElement.render_underlays(self))
elements.extend(TextElement.render(self))
elements.extend(ImageDE.render(self))
elements.extend(DiagnosticMarker.render(self))  # top (diagnostic only)
```

---

## How to Hand Off to a New Claude Session

1. Point Claude at this file first.
2. Reference the TabletQT project at `~/SDEV/Python/PyCharm/TabletQT` for any missing functionality.
3. Run tests first to confirm baseline: `/Users/starr/SDEV/Environments/TabletSVG/bin/pytest tests/ -v`
4. The active branch is `refine`; there are uncommitted changes in `__main__.py`, `tablet.py`, and `README.md` that should be reviewed and committed before starting new work.
