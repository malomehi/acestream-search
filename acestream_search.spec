# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['acestream_search/acestream_search_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tzdata'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_a = PYZ(a.pure)

exe_a = EXE(
    pyz_a,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='acestream-search',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

b = Analysis(
    ['acestream_search/acestream_search_gui_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tzdata'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_b = PYZ(b.pure)

exe_b = EXE(
    pyz_b,
    b.scripts,
    b.binaries,
    b.datas,
    [],
    name='acestream-search-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
