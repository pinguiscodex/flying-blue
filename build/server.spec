from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("websockets")

a = Analysis(
    ["../src/server.py"],
    pathex=["../src"],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
)
