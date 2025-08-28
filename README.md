# Ez-Pillow Dashboard Generator

A Python CLI tool that generates beautiful dashboard images from JSON data using PIL/Pillow.

## Features

- Generate professional-looking dashboards from JSON data
- Customizable KPIs, tables, and metrics
- Support for percentage changes with visual indicators
- Clean, modern design with rounded cards and proper typography
- Cross-platform font support

## Installation

Make sure you have Python 3.6+ and install the required dependencies:

```bash
pip install pillow
```

Or use the Docker setup (recommended for production):

```bash
# Build the Docker image
make build

# Run with Docker
make run
```

## Usage

### Basic Usage

```bash
python main.py -i data.json
```

This will generate a `dashboard.png` file from your JSON data.

### Specify Output File

```bash
python main.py -i data.json -o my_dashboard.png
```

### Command Line Options

- `-i, --input`: Input JSON file containing dashboard data (required)
- `-o, --output`: Output PNG file (default: dashboard.png)
- `-h, --help`: Show help message

### Examples

```bash
# Generate dashboard with default output name
python main.py -i example_data.json

# Generate dashboard with custom output name
python main.py -i my_data.json -o report_2024.png

# Using long form arguments
python main.py --input quarterly_data.json --output q4_report.png

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

See `example_data.json` for a complete working example.

## KPI Layout System

EZ Pillow provides flexible layout options for organizing your KPI cards. You can specify the layout type in your JSON data to control how KPIs are arranged.

### Available Layout Types

1. **`horizontal`** (default) - Standard horizontal row with equal-width cards
2. **`priority`** - First KPI gets larger space (40%), others share remaining space
3. **`grid_2x3`** - 2 rows × 3 columns grid layout
4. **`grid_3x2`** - 3 rows × 2 columns grid layout  
5. **`pyramid`** - Pyramid arrangement with fewer cards on top
6. **`featured`** - One large card on left, others stacked vertically on right
7. **`responsive`** - Auto-adapts based on KPI count (recommended)
8. **`custom`** - Custom positioning with exact coordinates

### Layout Configuration

Add a `layout` section to your JSON data:

```json
{
  "title": "My Dashboard",
  "layout": {
    "type": "priority"
  },
  "top_kpis": [...]
}
```

### Layout Examples

#### Priority Layout
```json
{
  "layout": {
    "type": "priority"
  },
  "top_kpis": [
    {"title": "Main Revenue", "value": "2,847k€", "delta": {"pct": 18}},
    {"title": "Users", "value": "156k", "delta": {"pct": -2}},
    {"title": "Orders", "value": "8,901", "delta": {"pct": 8}},
    {"title": "AOV", "value": "127€", "delta": {"pct": 7}}
  ]
}
```

#### Custom Layout
```json
{
  "layout": {
    "type": "custom",
    "positions": [
      {"x": 400, "y": 0, "width": 350},
      {"x": 100, "y": 180, "width": 300},
      {"x": 650, "y": 180, "width": 300}
    ]
  },
  "top_kpis": [...]
}
```

### Automatic Layout Suggestions

When using `"type": "responsive"` or no layout specified, the system automatically chooses the best layout based on KPI count:

- **1-4 KPIs** → `horizontal` layout
- **5 KPIs** → `priority` layout (featured first KPI)
- **6 KPIs** → `grid_2x3` layout
- **7-8 KPIs** → `grid_3x2` layout
- **9+ KPIs** → `pyramid` layout

### Testing Layouts

Generate examples of different layouts:

```bash
# Generate layout comparison examples
python examples/kpi_layouts_demo.py

# Test specific layout with your data
python -m src.ezp.main your_data.json output.png
```

This will create visual examples of all layout types in the `out/` directory.

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
python utils/font_diagnostic.py

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

The tool generates a 1920x1280 PNG image featuring:

- **Header**: Title and date note
- **Top KPIs**: Up to 5 key performance indicators with percentage changes
- **Platform Table**: Tabular data with alternating row colors
- **Middle Section**: 3 metric cards
- **Bottom Section**: 5 metric cards
- **Visual Indicators**: Green/red arrows for positive/negative changes

## Customization

You can modify the styling by editing the constants in `main.py`:

- `W, H`: Image dimensions (default: 1920x1280)
- `PADDING`: Page margins
- `CARD_R`: Corner radius for rounded rectangles
- Font sizes and colors in the style section

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