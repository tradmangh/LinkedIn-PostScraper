#!/bin/bash
# Build script for Linux - LinkedIn Post Scraper
# Creates both standalone and full executables

set -e  # Exit on error

echo "========================================"
echo "LinkedIn Post Scraper - Linux Build"
echo "========================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "[ERROR] PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi

# Check if Playwright browsers are installed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "[WARNING] Playwright browsers not found. Installing Chromium..."
    python3 -m playwright install chromium
fi

echo ""
echo "[1/2] Building STANDALONE version (no browser bundled)..."
echo "--------------------------------------------------------"
pyinstaller build-standalone.spec --clean --noconfirm
echo "[SUCCESS] Standalone build complete: dist/linkedin-postscraper-standalone/"

echo ""
echo "[2/2] Building FULL version (with Chromium bundled)..."
echo "--------------------------------------------------------"
pyinstaller build-full.spec --clean --noconfirm
echo "[SUCCESS] Full build complete: dist/linkedin-postscraper-full/"

# Make binaries executable
chmod +x dist/linkedin-postscraper-standalone/linkedin-postscraper-standalone
chmod +x dist/linkedin-postscraper-full/linkedin-postscraper-full

echo ""
echo "========================================"
echo "Build Summary"
echo "========================================"
echo "Standalone: dist/linkedin-postscraper-standalone/linkedin-postscraper-standalone"
echo "Full Bundle: dist/linkedin-postscraper-full/linkedin-postscraper-full"
echo ""
echo "Standalone size: ~50-80 MB (downloads browser on first run)"
echo "Full Bundle size: ~350-400 MB (browser included, works offline)"
echo "========================================"
echo ""
echo "To run: ./dist/linkedin-postscraper-standalone/linkedin-postscraper-standalone"
echo "    or: ./dist/linkedin-postscraper-full/linkedin-postscraper-full"
