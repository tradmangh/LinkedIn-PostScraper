# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for LinkedIn Post Scraper (Standalone - No Browser Bundle)
This creates a smaller executable that downloads the browser on first run.
"""

import sys
from pathlib import Path

block_cipher = None

# Determine platform-specific settings
if sys.platform == 'win32':
    icon_file = 'assets/icon.ico'
    exe_name = 'LinkedIn-PostScraper-Standalone'
elif sys.platform == 'darwin':
    icon_file = 'assets/icon.icns'
    exe_name = 'LinkedIn-PostScraper-Standalone'
else:  # Linux
    icon_file = 'assets/icon.png'
    exe_name = 'linkedin-postscraper-standalone'

# Find CustomTkinter installation path
try:
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent
    ctk_datas = [(str(ctk_path), 'customtkinter')]
except ImportError:
    ctk_datas = []
    print("Warning: CustomTkinter not found, UI may not work correctly")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
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
        bundle_identifier='com.linkedin.postscraper',
        info_plist={
            'CFBundleName': 'LinkedIn Post Scraper',
            'CFBundleDisplayName': 'LinkedIn Post Scraper',
            'CFBundleVersion': '1.2.0',
            'CFBundleShortVersionString': '1.2.0',
            'NSHighResolutionCapable': True,
        },
    )
