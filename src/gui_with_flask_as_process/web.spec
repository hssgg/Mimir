# -*- mode: python -*-

block_cipher = None


a = Analysis(['web.py'],
             pathex=['D:\\Documents\\GitHub\\Mimir\\src\\gui_with_flask_as_process'],
             binaries=[],
             datas=[
             ('.\\static', 'static'),
             ('.\\templates', 'templates')
              ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='web',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
