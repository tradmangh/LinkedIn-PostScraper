# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for LinkedIn Post Scraper (Full Bundle - With Browser)
This creates a larger executable with Chromium bundled for offline use.
"""

import sys
from pathlib import Path

block_cipher = None

# Determine platform-specific settings
if sys.platform == 'win32':
    icon_file = 'assets/icon.ico'
    exe_name = 'LinkedIn-PostScraper-Full'
    # Path to Playwright browsers (Windows)
    playwright_browsers = Path.home() / 'AppData' / 'Local' / 'ms-playwright'
elif sys.platform == 'darwin':
    icon_file = 'assets/icon.icns'
    exe_name = 'LinkedIn-PostScraper-Full'
    # Path to Playwright browsers (macOS)
    playwright_browsers = Path.home() / 'Library' / 'Caches' / 'ms-playwright'
else:  # Linux
    icon_file = 'assets/icon.png'
    exe_name = 'linkedin-postscraper-full'
    # Path to Playwright browsers (Linux)
    playwright_browsers = Path.home() / '.cache' / 'ms-playwright'

# Find CustomTkinter installation path
try:
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent
    ctk_datas = [(str(ctk_path), 'customtkinter')]
    print(f"✓ Found CustomTkinter at: {ctk_path}")
except (ImportError, AttributeError) as e:
    # Fallback: try to find it in site-packages
    import site
    ctk_datas = []
    for site_pkg in site.getsitepackages():
        ctk_candidate = Path(site_pkg) / 'customtkinter'
        if ctk_candidate.exists():
            ctk_datas = [(str(ctk_candidate), 'customtkinter')]
            print(f"✓ Found CustomTkinter at: {ctk_candidate}")
            break
    if not ctk_datas:
        print("⚠ Warning: CustomTkinter not found, UI may not work correctly")

# Find Chromium browser directory
chromium_dir = None
if playwright_browsers.exists():
    for browser_dir in playwright_browsers.iterdir():
        if 'chromium' in browser_dir.name.lower():
            chromium_dir = browser_dir
            break

# Prepare browser binaries for bundling
browser_binaries = []
if chromium_dir and chromium_dir.exists():
    browser_binaries = [(str(chromium_dir), 'ms-playwright')]
    print(f"✓ Found Chromium at: {chromium_dir}")
else:
    print("⚠ Warning: Chromium not found. Run 'python -m playwright install chromium' first.")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=browser_binaries,
    datas=ctk_datas,
    hiddenimports=[
        'playwright',
        'playwright._impl',
        'playwright.sync_api',
        'beautifulsoup4',
        'bs4',
        'customtkinter',
        'slugify',
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest-mock',
        'pytest-cov',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if Path(icon_file).exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=exe_name,
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{exe_name}.app',
        icon=icon_file,
        bundle_identifier='com.linkedin.postscraper.full',
        info_plist={
            'CFBundleName': 'LinkedIn Post Scraper (Full)',
            'CFBundleDisplayName': 'LinkedIn Post Scraper (Full)',
            'CFBundleVersion': '1.2.0',
            'CFBundleShortVersionString': '1.2.0',
            'NSHighResolutionCapable': True,
        },
    )
