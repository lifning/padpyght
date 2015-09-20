# -*- mode: python -*-
a = Analysis(['start.py'],
             pathex=['/home/lifning/git/padpyght'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

pgu_theme = Tree('/usr/share/pgu/themes/default', prefix='default')
padpyght_skins = Tree('padpyght/skins', prefix='padpyght/skins')

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='padpyght.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='gamepad.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               pgu_theme,
               padpyght_skins,
               strip=None,
               upx=True,
               name='padpyght-bin')
