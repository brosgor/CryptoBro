# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Linux / Windows (GitHub Actions)
import os
import sys
from pathlib import Path

block_cipher = None

# uv/cpython embebido trae Tcl/Tk 9; hay que empaquetarlos o el AppImage falla al abrir.
_tcl_bins = []
_tcl_datas = []
_prefix = Path(sys.base_prefix)
_lib = _prefix / "lib"
if (_lib / "libtcl9.0.so").exists():
    _tcl_bins = [
        (str(_lib / "libtcl9.0.so"), "."),
        (str(_lib / "libtcl9tk9.0.so"), "."),
    ]
    if (_lib / "tcl9.0").is_dir():
        _tcl_datas.append((str(_lib / "tcl9.0"), "tcl9.0"))
    if (_lib / "tk9.0").is_dir():
        _tcl_datas.append((str(_lib / "tk9.0"), "tk9.0"))

a = Analysis(
    ['../src/main.py'],
    pathex=['../src'],
    binaries=_tcl_bins,
    datas=[
        ('../src/assets/words.json', 'assets'),
        ('../src/assets/images', 'assets/images'),
        *_tcl_datas,
    ],
    hiddenimports=[
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat.primitives.kdf.scrypt',
        'cryptography.hazmat.primitives.asymmetric.rsa',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.font',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(Path(SPECPATH) / 'runtime_tcltk.py')] if _tcl_bins else [],  # noqa: F821
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CryptoBro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../src/assets/images/favicon.ico',
)
