@echo off
REM Build script for Windows - LinkedIn Post Scraper
REM Creates both standalone and full executables

echo ========================================
echo LinkedIn Post Scraper - Windows Build
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Check if Playwright browsers are installed
python -c "from pathlib import Path; import sys; sys.exit(0 if (Path.home() / 'AppData' / 'Local' / 'ms-playwright').exists() else 1)" 2>nul
if errorlevel 1 (
    echo [WARNING] Playwright browsers not found. Installing Chromium...
    python -m playwright install chromium
)

echo.
echo [1/2] Building STANDALONE version (no browser bundled)...
echo --------------------------------------------------------
pyinstaller build-standalone.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] Standalone build failed!
    exit /b 1
)
echo [SUCCESS] Standalone build complete: dist\LinkedIn-PostScraper-Standalone\

echo.
echo [2/2] Building FULL version (with Chromium bundled)...
echo --------------------------------------------------------
pyinstaller build-full.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] Full build failed!
    exit /b 1
)
echo [SUCCESS] Full build complete: dist\LinkedIn-PostScraper-Full\

echo.
echo ========================================
echo Build Summary
echo ========================================
echo Standalone: dist\LinkedIn-PostScraper-Standalone\LinkedIn-PostScraper-Standalone.exe
echo Full Bundle: dist\LinkedIn-PostScraper-Full\LinkedIn-PostScraper-Full.exe
echo.
echo Standalone size: ~50-80 MB (downloads browser on first run)
echo Full Bundle size: ~350-400 MB (browser included, works offline)
echo ========================================
