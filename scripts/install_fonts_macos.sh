#!/bin/bash

# quadre Font Installation Script for macOS
# This script installs recommended fonts for the quadre dashboard renderer

set -e

echo "🔤 quadre Font Installation for macOS"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is for macOS only"
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing Homebrew first..."
    echo "This will install Homebrew package manager."
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for M1/M2 Macs
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        print_error "Homebrew is required for font installation"
        exit 1
    fi
fi

print_status "Homebrew is available"

# Update Homebrew
print_info "Updating Homebrew..."
brew update

# Install font casks
print_info "Adding font taps..."
brew tap homebrew/cask-fonts

# List of recommended fonts
fonts_to_install=(
    "font-dejavu-sans"
    "font-liberation"
    "font-roboto"
    "font-open-sans"
    "font-source-sans-pro"
)

echo
print_info "Installing recommended fonts..."

installed_count=0
for font in "${fonts_to_install[@]}"; do
    echo -n "Installing $font... "
    if brew install --cask "$font" &>/dev/null; then
        print_status "installed"
        ((installed_count++))
    else
        # Check if already installed
        if brew list --cask | grep -q "$font"; then
            echo -e "${YELLOW}already installed${NC}"
            ((installed_count++))
        else
            print_error "failed"
        fi
    fi
done

echo
print_status "Font installation completed ($installed_count/${#fonts_to_install[@]} fonts)"

# Find installed font paths
echo
print_info "Locating installed fonts..."

font_paths=()

# Common font locations on macOS
search_paths=(
    "/Library/Fonts"
    "/System/Library/Fonts"
    "/usr/local/share/fonts"
    "/opt/homebrew/share/fonts"
    "$HOME/Library/Fonts"
)

# Look for DejaVu Sans specifically (recommended for quadre)
dejavu_paths=(
    "/Library/Fonts/DejaVuSans.ttf"
    "/usr/local/share/fonts/DejaVuSans.ttf"
    "/opt/homebrew/share/fonts/DejaVuSans.ttf"
    "/System/Library/Fonts/Helvetica.ttc"
    "/Library/Fonts/Arial.ttf"
)

recommended_font=""
for path in "${dejavu_paths[@]}"; do
    if [[ -f "$path" ]]; then
        recommended_font="$path"
        print_status "Found recommended font: $path"
        break
    fi
done

# List available fonts in common directories
echo
print_info "Available fonts in system directories:"
font_count=0
for search_path in "${search_paths[@]}"; do
    if [[ -d "$search_path" ]]; then
        while IFS= read -r -d '' font_file; do
            if [[ $font_count -lt 5 ]]; then  # Show first 5 fonts
                basename_font=$(basename "$font_file")
                echo "  - $basename_font"
                ((font_count++))
            fi
        done < <(find "$search_path" -name "*.ttf" -o -name "*.ttc" -o -name "*.otf" 2>/dev/null | head -5 | tr '\n' '\0')
    fi
done

if [[ $font_count -eq 0 ]]; then
    print_warning "No fonts found in common directories"
fi

# Set environment variable
echo
print_info "Setting up environment variable..."

if [[ -n "$recommended_font" ]]; then
    # Add to shell configuration files
    shell_configs=(
        "$HOME/.zshrc"
        "$HOME/.bash_profile"
        "$HOME/.bashrc"
    )

    env_line="export quadre_FONT_PATH=\"$recommended_font\""

    for config_file in "${shell_configs[@]}"; do
        if [[ -f "$config_file" ]]; then
            if ! grep -q "quadre_FONT_PATH" "$config_file"; then
                echo "" >> "$config_file"
                echo "# quadre Font Configuration" >> "$config_file"
                echo "$env_line" >> "$config_file"
                print_status "Added quadre_FONT_PATH to $config_file"
            else
                print_info "quadre_FONT_PATH already exists in $config_file"
            fi
        fi
    done

    # Set for current session
    export quadre_FONT_PATH="$recommended_font"
    print_status "quadre_FONT_PATH set to: $recommended_font"

else
    print_warning "No recommended font found. Using system defaults."
fi

# Test font loading
echo
print_info "Testing font loading..."

# Create a simple test script
test_script=$(cat << 'EOF'
import sys
import os
sys.path.append('src')
try:
    from quadre.components.config import load_font
    font = load_font(24)
    font_path = getattr(font, 'path', 'Default PIL font')
    print(f"✓ Font loaded successfully: {font_path}")
except Exception as e:
    print(f"✗ Error loading font: {e}")
EOF
)

if command -v python3 &> /dev/null; then
    cd "$(dirname "$0")/.."
    echo "$test_script" | python3
else
    print_warning "Python3 not found. Cannot test font loading."
fi

# Final instructions
echo
echo "🎉 Font installation completed!"
echo
print_info "To use the fonts immediately, restart your terminal or run:"
echo "  source ~/.zshrc  # or ~/.bash_profile"
echo
print_info "To test quadre with the new fonts:"
echo "  cd ez-pillow"
echo "  python utils/font_diagnostic.py"
echo
print_info "To generate a dashboard:"
echo "  uv run -m quadre.cli render data.json out/dashboard.png"

if [[ -n "$recommended_font" ]]; then
    echo
    print_status "Recommended font configured: $(basename "$recommended_font")"
    echo "Environment variable quadre_FONT_PATH is set and ready to use."
fi

echo
print_info "For more font options, visit:"
echo "  https://formulae.brew.sh/cask/font-dejavu-sans"
echo "  https://github.com/Homebrew/homebrew-cask-fonts"
