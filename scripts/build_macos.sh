#!/bin/bash
# Build script for macOS - LinkedIn Post Scraper
# Creates both standalone and full executables

set -e  # Exit on error

echo "========================================"
echo "LinkedIn Post Scraper - macOS Build"
echo "========================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "[ERROR] PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi

# Check if Playwright browsers are installed
if [ ! -d "$HOME/Library/Caches/ms-playwright" ]; then
    echo "[WARNING] Playwright browsers not found. Installing Chromium..."
    python3 -m playwright install chromium
fi

echo ""
echo "[1/2] Building STANDALONE version (no browser bundled)..."
echo "--------------------------------------------------------"
pyinstaller build-standalone.spec --clean --noconfirm
echo "[SUCCESS] Standalone build complete: dist/LinkedIn-PostScraper-Standalone.app"

echo ""
echo "[2/2] Building FULL version (with Chromium bundled)..."
echo "--------------------------------------------------------"
pyinstaller build-full.spec --clean --noconfirm
echo "[SUCCESS] Full build complete: dist/LinkedIn-PostScraper-Full.app"

echo ""
echo "========================================"
echo "Build Summary"
echo "========================================"
echo "Standalone: dist/LinkedIn-PostScraper-Standalone.app"
echo "Full Bundle: dist/LinkedIn-PostScraper-Full.app"
echo ""
echo "Standalone size: ~60-90 MB (downloads browser on first run)"
echo "Full Bundle size: ~360-410 MB (browser included, works offline)"
echo "========================================"
echo ""
echo "Note: To bypass Gatekeeper, users should right-click → Open"
echo "      Or run: xattr -cr LinkedIn-PostScraper-*.app"
