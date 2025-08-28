# Ez-Pillow Dashboard Generator

A Python CLI tool that generates beautiful dashboard images from JSON data using PIL/Pillow.

## Features

- Generate professional-looking dashboards from JSON data
- Customizable KPIs, tables, and metrics
- Support for percentage changes with visual indicators
- Clean, modern design with rounded cards and proper typography
- Cross-platform font support

## Installation

- Python: 3.12+
- Recommended: [uv](https://github.com/astral-sh/uv) for fast, isolated runs

Docker setup is also available (handy for production):

```bash
# Build the Docker image
make build

# Run with Docker
make run
```

## Usage (uv)

### Basic Usage

```bash
uv run -m ezp.main -i data.json
```

This generates `dashboard.png` from your JSON data.

### Specify Output File

```bash
uv run -m ezp.main -i data.json -o my_dashboard.png
```

### Command Line Options

- `-i, --input`: Input JSON file containing dashboard data (required)
- `-o, --output`: Output PNG file (default: dashboard.png)
- `-h, --help`: Show help message

### Examples

```bash
# Generate dashboard with default output name
uv run -m ezp.main -i examples/flex_e2e.json

# Generate dashboard with custom output name
uv run -m ezp.main -i my_data.json -o report_2024.png

# Using long form arguments
uv run -m ezp.main --input quarterly_data.json --output q4_report.png

# Docker examples
make run
make run DATA=my_data.json OUT_FILE=custom_report.png
```

## Docker Integration

The project includes full Docker support with a Makefile for easy deployment:

### Docker Commands

```bash
# Build the Docker image
make build

# Run with default data.json
make run

# Run with custom data and output
make run DATA=my_data.json OUT_FILE=report.png

# Interactive shell for debugging
make shell

# Clean generated files
make clean

# Rebuild without cache
make rebuild
```

### Makefile Variables

You can override these variables:

- `DATA`: Input JSON file (default: `$(PWD)/data.json`)
- `OUT_DIR`: Output directory (default: `$(PWD)/out`)
- `OUT_FILE`: Output filename (default: `dashboard.png`)
- `IMAGE`: Docker image name (default: `dash-render-uv`)
- `TAG`: Docker image tag (default: `latest`)
- `RUN_ARGS`: Extra Docker run arguments
```

<old_text line=97>
}
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
uv run -m ezp.main your_data.json output.png
```

Images are written to `out/`.

## Flex Layout (Default)

The renderer now uses a flexbox-like engine under `src/ezp/flex` as the only path. It provides:

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

## JSON Data Format

Your input JSON file should follow this structure:

```json
{
  "title": "Dashboard Title",
  "date_note": "Optional date/period note",
  "layout": {
    "type": "horizontal|priority|grid_2x3|grid_3x2|pyramid|featured|responsive|custom",
    "positions": [
      {"x": 400, "y": 0, "width": 350}
    ]
  },
  "top_kpis": [
    {
      "title": "KPI Name",
      "value": "123.4 k€",
      "delta": {
        "pct": -5,
        "from": "130.0 k€"
      }
    }
  ],
  "platform_rows": [
    ["Platform", "Col1 Value", "Col2 Value", "..."]
  ],
  "notes_left": "Left side note",
  "notes_right": "Right side note",
  "mid_section": {
    "title": "Middle Section Title",
    "cards": [
      {
        "title": "Card Title",
        "value": "Card Value",
        "delta": {
          "pct": 10,
          "from": "Previous Value"
        }
      }
    ]
  },
  "bottom_section": {
    "title": "Bottom Section Title",
    "cards": [
      // Same structure as mid_section cards
    ]
  }
}
```

### Required Fields
- `title`: Dashboard title (string)
- `top_kpis`: Array of KPI objects

### Optional Fields
- `date_note`: Subtitle or date information (string)
- `layout`: Layout configuration object
  - `type`: Layout type (string, default: "horizontal")  
  - `positions`: For custom layout only - array of position objects
- `platform_rows`: Table data as array of arrays
- `notes_left`, `notes_right`: Footer notes (strings)
- `mid_section`, `bottom_section`: Additional card sections

### KPI Object Structure
- `title`: KPI name (string)
- `value`: Current value (string)
- `delta`: Change information (object, optional)
  - `pct`: Percentage change (number)
  - `from`: Previous value (string, optional)

See `example_data.json` for a complete working example.

## Font Configuration

EZ Pillow automatically detects system fonts but you can customize font usage for better consistency across platforms.

### Automatic Font Detection

The system automatically finds suitable fonts based on your platform:

- **macOS**: Helvetica, Arial, San Francisco
- **Windows**: Arial, Calibri, Segoe UI, Verdana  
- **Linux**: DejaVu Sans, Liberation Sans, Ubuntu

### Custom Font Configuration

Set a custom font using the `EZP_FONT_PATH` environment variable:

```bash
# macOS
export EZP_FONT_PATH="/System/Library/Fonts/Helvetica.ttc"

# Windows  
set EZP_FONT_PATH=C:/Windows/Fonts/arial.ttf

# Linux
export EZP_FONT_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
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
# - Current EZ Pillow font configuration
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
- Set `EZP_FONT_PATH` to a valid font file
- Use the diagnostic tool to find available fonts

**Docker font issues:**
- Fonts are pre-installed in the Docker image
- Custom fonts can be mounted as volumes
- Use the `EZP_FONT_PATH` environment variable in containers

## Output

Default canvas: 1920×1280 PNG with:

- Header (title + date note)
- KPI row (evenly distributed)
- Platform table (auto columns, zebra rows)

## Customization

Customize via `src/ezp/components/config.py` and Flex widgets in `src/ezp/flex`. The Flex renderer composes existing components (KPI cards, tables) with a simpler layout model.

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
