# quadre

A Python tool that generates beautiful, serializable dashboard images from JSON using Pillow.
Dashboard images are easy to share across slack, emails or any communication software that manage.

Use image to make your dashboards accessible by everyone.

For complete docs, see docs/index.md.

## Quickstart

Render an example dashboard to PNG using uv (no install required):

```bash
uv run -m quadre.cli examples/declarative_featured.json out/featured.png
```

Validate a JSON document (schema + friendly warnings):

```bash
quadre validate examples/declarative_featured.json
```

Using the installed CLI instead of uv:

```bash
quadre render examples/declarative_featured.json out.png
quadre validate examples/declarative_featured.json
```

## Python API

Install and render from Python without touching disk or with custom outputs:

```python
from quadre import render, build_image, to_bytes

# 1) Simple: write a file (default plugin)
render(doc, path="out.png")

# 2) Multiple outputs: file + anything else
render(doc, outputs=[
  {"plugin": "file", "path": "out.webp", "format": "WEBP"},
  # Example: if you installed a third-party plugin registered as "s3"
  {"plugin": "s3", "bucket": "my-bucket", "key": "dashboards/out.png"},
])

# 3) In-memory usage
img = build_image(doc)          # PIL.Image
data = to_bytes(doc, "PNG")     # bytes
```

### Typed Builder (optional)

Prefer composer code in Python? Use the typed builder to generate the same declarative JSON and keep a single rendering path:

```python
from quadre.flex import Text, KPI, Row, Title, dref, make_doc

doc = make_doc(
    Title("Awesome dashboard"),
    Row().gap(12).add(
        Text("Headline").font("heading").no_grow(),
        KPI(title=dref("$.perf.title"), value=dref("$.perf.value")),
        KPI(title="Orders", value="12,345"),
    ),
    data={
        "perf": {"title": "Revenue", "value": "4,567k€"}
    },
    canvas={"height": "auto"},
)

# Render (uses the same validator + adapter + flex engine)
from quadre import render
render(doc.to_dict(), path="out.png")
```

Notes:
- `.grow(r)` on children inside a Row maps to `properties.width_ratio` (use `.no_grow()` to keep intrinsic width).
- For Column children, use `.fill_remaining()` to stretch or `.height(px)` to suggest a fixed basis.
- You can mix builder-generated nodes with hand-written JSON in the same document if needed.

To add your own output destination, expose a function and register it:

```python
from quadre import register_output_plugin

def my_sink(image, ctx, cfg):
    # image: PIL.Image.Image
    # ctx: OutputContext(path, format, doc, size)
    # cfg: dict from your outputs spec
    ...

register_output_plugin("my_sink", my_sink)
```


## Features

- Generate professional-looking dashboards from JSON data
- Customizable KPIs, tables, and metrics
- Support for percentage changes with visual indicators
- Clean, modern design with rounded cards and proper typography
- Cross-platform font support

## Installation

- Python: 3.12+
- Recommended: [uv](https://github.com/astral-sh/uv) for fast, isolated runs

From PyPI (CLI + library):

```bash
pip install quadre
```


## Usage (uv)

### Basic Usage

```bash
uv run -m quadre.cli render -h
```

This generates `dashboard.png` from your JSON data.

### Specify Output File

```bash
uv run -m quadre.cli render examples/declarative_featured.json out.png
```

### Command Line Options

- `-i, --input`: Input JSON file containing dashboard data (required)
- `-o, --output`: Output PNG file (default: dashboard.png)
- `-h, --help`: Show help message

### Examples

```bash
# Generate dashboard with default output name
uv run -m quadre.cli render -h

# Generate dashboard with custom output name
quadre render -h

# Using long form arguments
quadre render examples/declarative_featured.json out.png

```

See `examples/flex_e2e.json` for a complete working example.

## Legacy KPI Layouts (Optional)

Older presets (horizontal, priority, grids, pyramid, featured, responsive, custom) remain available via the legacy or declarative paths. Flex is the default for new dashboards.

### Testing Layouts

```bash
# Flex demos
uv run examples/flex_demo.py
uv run examples/flex_e2e.py

# Render your JSON with the default (Flex) path
uv run -m quadre.cli render your_data.json output.png
```

Images are written to `out/`.

## Flex Layout (Default)

The renderer now uses a flexbox-like engine under `src/quadre/flex` as the only path. It provides:

- Flex containers with `direction` (row/column), `gap`, `align_items`, `padding`
- Per-child `grow`, `shrink`, and `basis` properties to distribute space
- Main-axis `justify_content`: start | center | end | space-between | space-around | space-evenly
- Optional container background rendering with rounded corners
- Simple `TextWidget` and `FixedBox` examples

Auto-height is enabled by default: the image height grows to fit content (bounded). To force a fixed page height, set `"canvas": { "height": "fixed" }` or `"canvas": { "height": 1280 }`.

High-quality rendering via supersampling is available (optional). Enable with:

```json
"canvas": {
  "height": "auto",
  "scale": 2.0,           // render at 2x
  "downscale": true       // downscale to base size with Lanczos
}
```

Run the demo:

```bash
python examples/flex_demo.py
```

This generates `out/flex_demo.png`. The main CLI also uses Flex for the default path.

### End-to-End Example

A JSON-driven example is also included:

```bash
python examples/flex_e2e.py               # uses examples/flex_e2e.json
python examples/flex_e2e.py data.json out/flex_e2e.png
```

This renders a header, a KPI row, and a simple platform list using the Flex engine.

## Declarative JSON

See docs/declarative-layout.md for the JSON model, components, and examples.

## Theme System

quadre supports a Pydantic‑validated theme that defines the color palette, font sizes, and per‑widget defaults (e.g., `FlexContainer` gaps/padding and `TableWidget` styles). A theme is loaded for every render, then the layout can still override any property via `properties`.

- Default theme file: `src/quadre/theme/theme.json`
- Env override: set `quadre_THEME=/path/to/theme.json`
- CLI override: `quadre render --theme dark data.json out.png` or `--theme /path/to/theme.json`
- Keys are case‑insensitive, but the bundled themes use lowercase (e.g., `colors.foreground`, `fonts.h1`).

Example theme (partial):

```json
{
  "colors": {
    "background": "#ffffff",
    "foreground": "#0f172a",
    "border": "#d1d5db",
    "muted": "#f1f5f9"
  },
  "fonts": { "h1": 42, "number": 40, "body": 24 },
  "widgets": {
    "TextWidget": { "fill": "foreground", "font": "body" },
    "TableWidget": {
      "min_row_height": 28,
      "style": {
        "background_color": "card_background",
        "header_background": "muted",
        "text_color": "foreground"
      }
    }
  }
}
```

Example CLI usage:

```bash
# Use bundled dark theme
quadre render --theme dark examples/declarative_featured.json out_dark.png

# Use a custom theme file
quadre render --theme /configs/my_theme.json examples/declarative_featured.json out.png
```

Notes:
- The layout can override any property per widget via `properties`. For tables, you can pass `properties.style` to override theme table styles locally.
- A top‑level `theme` object in the document can still adjust colors/fonts quickly, but per‑widget defaults come from the validated theme file.

## Font Configuration

quadre automatically detects system fonts but you can customize font usage for better consistency across platforms.

### Automatic Font Detection

The system automatically finds suitable fonts based on your platform:

- **macOS**: Helvetica, Arial, San Francisco
- **Windows**: Arial, Calibri, Segoe UI, Verdana  
- **Linux**: DejaVu Sans, Liberation Sans, Ubuntu

### Custom Font Configuration

Set a custom font using the `quadre_FONT_PATH` environment variable:

```bash
# macOS
export quadre_FONT_PATH="/System/Library/Fonts/Helvetica.ttc"

# Windows  
set quadre_FONT_PATH=C:/Windows/Fonts/arial.ttf

# Linux
export quadre_FONT_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
```

Add to your shell configuration file (`~/.zshrc`, `~/.bashrc`) to make it permanent.

### Font Installation

#### macOS (Recommended)
```bash
# Run the automated installer
./scripts/install_fonts_macos.sh

# Or install manually with Homebrew
brew tap homebrew/cask-fonts
brew install --cask font-dejavu-sans
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install fonts-dejavu fonts-liberation

# CentOS/RHEL/Fedora
sudo dnf install dejavu-sans-fonts liberation-sans-fonts

# Arch Linux
sudo pacman -S ttf-dejavu ttf-liberation
```

#### Windows
1. Download fonts from [DejaVu Fonts](https://dejavu-fonts.github.io/)
2. Right-click `.ttf` files and select "Install"

### Font Diagnostics

Test font availability and configuration:

```bash
# Run font diagnostic tool
uv run utils/font_diagnostic.py

# This will show:
# - Available system fonts
# - Current quadre font configuration
# - Installation recommendations
# - Generate a font test image
```

### Troubleshooting

**Fonts appear incorrect or distorted:**
- Ensure the font file exists at the specified path
- Try a different font from your system
- Check file permissions

**"Font not found" errors:**
- Install recommended fonts for your platform
- Set `quadre_FONT_PATH` to a valid font file
- Use the diagnostic tool to find available fonts

**Docker font issues:**
- Fonts are pre-installed in the Docker image
- Custom fonts can be mounted as volumes
- Use the `quadre_FONT_PATH` environment variable in containers

## Output

Default canvas: 1920×1280 PNG with:

- Header (title + date note)
- KPI row (evenly distributed)
- Platform table (auto columns, zebra rows)

## Customization

Customize via `src/quadre/components/config.py` and Flex widgets in `src/quadre/flex`. The Flex renderer composes existing components (KPI cards, tables) with a simpler layout model.

## Font Support

The tool automatically detects and uses system fonts:
- Docker/Linux: DejaVu Sans fonts (installed in container)
- Local: DejaVu Sans or Liberation Sans fonts
- Fallback: PIL default font

## Docker Details

The Docker setup uses:
- **Base Image**: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
- **Package Manager**: UV for fast dependency resolution
- **Fonts**: DejaVu fonts pre-installed for consistent rendering
- **Architecture**: Multi-platform support (linux/amd64, linux/arm64)

## Error Handling

The CLI provides clear error messages for:
- Missing input files
- Invalid JSON format
- File permission issues
- Image generation errors

## License

MIT License - feel free to use and modify as needed.
