#!/usr/bin/env python3
"""
Font Diagnostic Tool for quadre

This utility helps diagnose font availability on different systems and provides
guidance for font configuration using environment variables.
"""

import os
import sys
import platform
from PIL import Image, ImageDraw, ImageFont


def get_system_info():
    """Get system information for font diagnostics."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "pil_version": Image.__version__,
    }


def find_common_font_directories():
    """Find common font directories on the current system."""
    system = platform.system()
    directories = []

    if system == "Darwin":  # macOS
        directories = [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            "/usr/local/share/fonts/",
            "/opt/homebrew/share/fonts/",
            os.path.expanduser("~/Library/Fonts/"),
        ]
    elif system == "Windows":
        directories = [
            "C:/Windows/Fonts/",
            os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/"),
        ]
    else:  # Linux and others
        directories = [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/truetype/",
            "/usr/share/fonts/TTF/",
            os.path.expanduser("~/.fonts/"),
            os.path.expanduser("~/.local/share/fonts/"),
        ]

    # Filter existing directories
    existing_dirs = []
    for directory in directories:
        if os.path.exists(directory):
            existing_dirs.append(directory)

    return existing_dirs


def scan_font_files(directories):
    """Scan directories for font files."""
    font_extensions = {".ttf", ".ttc", ".otf", ".woff", ".woff2"}
    found_fonts = {}

    for directory in directories:
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in font_extensions):
                        font_path = os.path.join(root, file)
                        font_name = os.path.splitext(file)[0]
                        found_fonts[font_name] = font_path
        except PermissionError:
            print(f"Permission denied: {directory}")
        except Exception as e:
            print(f"Error scanning {directory}: {e}")

    return found_fonts


def test_font_loading(font_path, sizes=[12, 18, 24]):
    """Test loading a specific font at different sizes."""
    results = {}
    for size in sizes:
        try:
            _font = ImageFont.truetype(font_path, size)
            results[size] = "✓"
        except Exception as e:
            results[size] = f"✗ {str(e)[:50]}"
    return results


def find_recommended_fonts():
    """Find recommended fonts for quadre."""
    system = platform.system()

    if system == "Darwin":  # macOS
        recommended = {
            "Helvetica": [
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Helvetica.ttf",
            ],
            "Arial": ["/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Arial.ttf"],
            "San Francisco": [
                "/System/Library/Fonts/SFNS.ttf",
                "/System/Library/Fonts/SFNSDisplay.ttf",
            ],
            "DejaVu Sans": [
                "/usr/local/share/fonts/DejaVuSans.ttf",
                "/opt/homebrew/share/fonts/DejaVuSans.ttf",
            ],
        }
    elif system == "Windows":
        recommended = {
            "Arial": ["C:/Windows/Fonts/arial.ttf"],
            "Calibri": ["C:/Windows/Fonts/calibri.ttf"],
            "Segoe UI": ["C:/Windows/Fonts/segoeui.ttf"],
            "Verdana": ["C:/Windows/Fonts/verdana.ttf"],
        }
    else:  # Linux
        recommended = {
            "DejaVu Sans": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/DejaVuSans.ttf",
            ],
            "Liberation Sans": [
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ],
            "Ubuntu": ["/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"],
        }

    available_fonts = {}
    for font_name, paths in recommended.items():
        for path in paths:
            if os.path.exists(path):
                available_fonts[font_name] = path
                break

    return available_fonts


def test_ez_pillow_font_loading():
    """Test the quadre font loading function (same API)."""
    try:
        # Add src to path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(script_dir, "..", "src")
        sys.path.insert(0, src_dir)

        from quadre.components.config import load_font

        sizes = [20, 24, 30, 36, 42]
        results = {}

        for size in sizes:
            try:
                font = load_font(size, False)
                font_name = getattr(font, "path", "Default PIL Font")
                results[size] = f"✓ {font_name}"
            except Exception as e:
                results[size] = f"✗ {str(e)}"

        return results
    except ImportError as e:
        return {"error": f"Could not import quadre config: {e}"}


def create_font_test_image(font_path, output_path="font_test.png"):
    """Create a test image with the specified font."""
    try:
        # Create test image
        img = Image.new("RGB", (800, 400), "white")
        draw = ImageDraw.Draw(img)

        # Test different sizes
        test_text = "The quick brown fox jumps over the lazy dog"
        sizes = [16, 20, 24, 30, 36]
        y_pos = 50

        for size in sizes:
            try:
                font = ImageFont.truetype(font_path, size)
                draw.text(
                    (50, y_pos), f"Size {size}: {test_text}", font=font, fill="black"
                )
                y_pos += size + 10
            except Exception as e:
                draw.text(
                    (50, y_pos), f"Size {size}: Error - {str(e)[:50]}", fill="red"
                )
                y_pos += 25

        # Add font info
        draw.text((50, 10), f"Font: {os.path.basename(font_path)}", fill="blue")

        img.save(output_path)
        return output_path
    except Exception as e:
        return f"Error creating test image: {e}"


def generate_font_installation_guide():
    """Generate installation guide for missing fonts."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return """
macOS Font Installation Guide:
=============================

1. Install Homebrew (if not already installed):
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

2. Install font packages:
   brew install font-dejavu
   brew tap homebrew/cask-fonts
   brew install --cask font-dejavu-sans

3. Or manually download fonts:
   - Download DejaVu fonts from: https://dejavu-fonts.github.io/
   - Copy .ttf files to ~/Library/Fonts/ or /Library/Fonts/

4. Set custom font path (recommended):
   export quadre_FONT_PATH="/Library/Fonts/DejaVuSans.ttf"
   # Add to your ~/.zshrc or ~/.bash_profile
"""
    elif system == "Windows":
        return """
Windows Font Installation Guide:
===============================

1. Download DejaVu fonts from: https://dejavu-fonts.github.io/
2. Extract the archive
3. Right-click on .ttf files and select "Install"
4. Or copy to C:/Windows/Fonts/

5. Set custom font path in environment variables:
   set quadre_FONT_PATH=C:/Windows/Fonts/DejaVuSans.ttf
"""
    else:  # Linux
        return """
Linux Font Installation Guide:
=============================

Ubuntu/Debian:
sudo apt update
sudo apt install fonts-dejavu fonts-liberation

CentOS/RHEL/Fedora:
sudo dnf install dejavu-sans-fonts liberation-sans-fonts

Arch Linux:
sudo pacman -S ttf-dejavu ttf-liberation

Manual installation:
1. Download fonts from https://dejavu-fonts.github.io/
2. Copy to ~/.local/share/fonts/ or /usr/local/share/fonts/
3. Run: fc-cache -fv

Set custom font path:
export quadre_FONT_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
"""


def main():
    """Main diagnostic function."""
    print("quadre Font Diagnostic Tool")
    print("=" * 50)
    print()

    # System information
    sys_info = get_system_info()
    print("System Information:")
    for key, value in sys_info.items():
        print(f"  {key}: {value}")
    print()

    # Environment variables
    print("Environment Variables:")
    custom_font = os.environ.get("quadre_FONT_PATH")
    if custom_font:
        print(f"  quadre_FONT_PATH: {custom_font}")
        if os.path.exists(custom_font):
            print("  ✓ Custom font path exists")
        else:
            print("  ✗ Custom font path does not exist")
    else:
        print("  quadre_FONT_PATH: Not set")
    print()

    # Font directories
    print("Font Directories:")
    font_dirs = find_common_font_directories()
    for directory in font_dirs:
        print(f"  ✓ {directory}")

    if not font_dirs:
        print("  ✗ No common font directories found")
    print()

    # Recommended fonts
    print("Recommended Fonts:")
    recommended = find_recommended_fonts()
    if recommended:
        for font_name, path in recommended.items():
            test_result = test_font_loading(path, [24])
            status = "✓" if "✓" in str(test_result) else "✗"
            print(f"  {status} {font_name}: {path}")
    else:
        print("  ✗ No recommended fonts found")
    print()

    # Test quadre font loading
    print("quadre Font Loading Test:")
    ez_results = test_ez_pillow_font_loading()
    if "error" in ez_results:
        print(f"  ✗ {ez_results['error']}")
    else:
        for size, result in ez_results.items():
            print(f"  Size {size}: {result}")
    print()

    # Scan all fonts (limited output)
    print("Available Fonts (sample):")
    all_fonts = scan_font_files(font_dirs[:2])  # Limit to first 2 directories
    font_count = len(all_fonts)
    print(f"  Found {font_count} font files")

    # Show first 10 fonts as sample
    for i, (name, path) in enumerate(list(all_fonts.items())[:10]):
        print(f"  - {name}")
        if i == 9 and font_count > 10:
            print(f"  ... and {font_count - 10} more")
    print()

    # Create test image if we have a good font
    if recommended:
        best_font = list(recommended.values())[0]
        print("Creating font test image...")
        result = create_font_test_image(best_font)
        if result.endswith(".png"):
            print(f"  ✓ Test image saved: {result}")
        else:
            print(f"  ✗ {result}")
        print()

    # Installation guide
    if not recommended or len(recommended) < 2:
        print("Font Installation Guide:")
        print(generate_font_installation_guide())

    # Recommendations
    print("Recommendations:")
    if custom_font and os.path.exists(custom_font):
        print("  ✓ Custom font path is configured and working")
    elif recommended:
        best_font_path = list(recommended.values())[0]
        print(
            f"  → Set environment variable: export quadre_FONT_PATH='{best_font_path}'"
        )
    else:
        print("  → Install recommended fonts for your system")
        print("  → Use the installation guide above")

    print(
        '  → Test font loading with: python -c "from quadre.components.config import load_font; print(load_font(24))"'
    )


if __name__ == "__main__":
    main()
