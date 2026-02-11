# Building LinkedIn Post Scraper

This guide explains how to build standalone executables for Windows, macOS, and Linux.

## Prerequisites

- Python 3.8 or higher
- All dependencies installed: `pip install -r requirements.txt`
- Playwright browsers installed: `python -m playwright install chromium`

## Build Variants

We provide two build variants:

### 1. Standalone (~50-80 MB)

- **Smaller download size**
- Downloads Chromium browser on first run (~300 MB)
- Recommended for most users
- Requires internet connection on first run

### 2. Full Bundle (~350-400 MB)

- **Larger download size**
- Chromium browser included
- Works completely offline
- Recommended if browser download is blocked

## Building Locally

### Windows

```batch
# Run the build script
scripts\build_windows.bat

# Executables will be in:
# - dist\LinkedIn-PostScraper-Standalone\LinkedIn-PostScraper-Standalone.exe
# - dist\LinkedIn-PostScraper-Full\LinkedIn-PostScraper-Full.exe
```

### macOS

```bash
# Make script executable
chmod +x scripts/build_macos.sh

# Run the build script
./scripts/build_macos.sh

# Applications will be in:
# - dist/LinkedIn-PostScraper-Standalone.app
# - dist/LinkedIn-PostScraper-Full.app
```

### Linux

```bash
# Make script executable
chmod +x scripts/build_linux.sh

# Run the build script
./scripts/build_linux.sh

# Binaries will be in:
# - dist/linkedin-postscraper-standalone/linkedin-postscraper-standalone
# - dist/linkedin-postscraper-full/linkedin-postscraper-full
```

## GitHub Actions (Automated Builds)

Builds are automatically triggered when you push a version tag:

```bash
# Update version in main.py and CHANGELOG.md first
git add .
git commit -m "Release v1.2.0"
git tag v1.2.0
git push origin v1.2.0
```

This will:

1. Build executables for Windows, macOS, and Linux
2. Create archives (.zip for Windows/macOS, .tar.gz for Linux)
3. Upload to GitHub Releases as draft
4. Include both standalone and full variants

## Manual PyInstaller Commands

If you prefer to build manually:

### Standalone Build

```bash
pyinstaller build-standalone.spec --clean --noconfirm
```

### Full Build

```bash
pyinstaller build-full.spec --clean --noconfirm
```

## Customization

### Application Icon

Replace the placeholder icons in `assets/` with your own:

- `icon.ico` - Windows (256x256 or multi-size)
- `icon.icns` - macOS (512x512 recommended)
- `icon.png` - Linux (512x512 recommended)

Tools for creating icons:

- [ICO Converter](https://www.icoconverter.com/)
- [png2icons](https://github.com/idesis-gmbh/png2icons) (Python package)

### PyInstaller Spec Files

Edit `build-standalone.spec` or `build-full.spec` to customize:

- Hidden imports
- Data files to include
- Excluded modules
- Build options

## Troubleshooting

### "Module not found" errors

Add missing modules to `hiddenimports` in the spec file:

```python
hiddenimports=[
    'your_module_here',
],
```

### CustomTkinter themes not loading

Ensure the data files path is correct in the spec file:

```python
datas=[
    ('venv/Lib/site-packages/customtkinter', 'customtkinter'),
],
```

### Playwright browser not found (Full build)

Make sure Chromium is installed before building:

```bash
python -m playwright install chromium
```

Check the browser path in `build-full.spec` matches your system:

- Windows: `%USERPROFILE%\AppData\Local\ms-playwright`
- macOS: `~/Library/Caches/ms-playwright`
- Linux: `~/.cache/ms-playwright`

### Windows Defender blocking executable

This is normal for unsigned executables. Users can:

1. Click "More info" → "Run anyway"
2. Or you can sign the executable with a code signing certificate

### macOS Gatekeeper blocking app

Users should:

1. Right-click the app → "Open"
2. Or run: `xattr -cr LinkedIn-PostScraper-*.app`

For distribution, consider:

- Apple Developer account ($99/year)
- Notarization process

## File Size Comparison

| Build Type | Windows | macOS | Linux |
|------------|---------|-------|-------|
| Standalone | ~50-80 MB | ~60-90 MB | ~50-80 MB |
| Full Bundle | ~350-400 MB | ~360-410 MB | ~350-400 MB |

## Distribution

After building, you can distribute the executables:

1. **GitHub Releases** (automated via Actions)
2. **Direct download** from your server
3. **Package managers** (future: Chocolatey, Homebrew, Snap)

## Testing

Always test executables on a clean machine without Python installed:

1. **Windows**: Test on Windows 10/11
2. **macOS**: Test on macOS 11+ (Big Sur or later)
3. **Linux**: Test on Ubuntu 20.04+ or similar

Verify:

- Application launches without errors
- Login to LinkedIn works
- Post scanning works
- Post scraping works
- Markdown files are saved correctly
- Browser download works (standalone build)
