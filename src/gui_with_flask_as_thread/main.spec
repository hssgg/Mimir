# -*- mode: python -*-

block_cipher = pyi_crypto.PyiBlockCipher(key='123')


a = Analysis(['main.py'],
             pathex=['D:\\Documents\\GitHub\\Mimir\\src\\gui_with_flask_as_thread'],
             binaries=[
             ('..\\..\\venv\\Lib\\site-packages\\cefpython3\\locales\*.pak', '.\locales'),
             ('..\\..\\venv\\Lib\\site-packages\\cefpython3\\*.dll', '.'),
             ('..\\..\\venv\\Lib\\site-packages\\cefpython3\\*.dat', '.'),
             ('..\\..\\venv\\Lib\\site-packages\\cefpython3\\*.bin', '.'),
             ('..\\..\\venv\\Lib\\site-packages\\cefpython3\\*.pak', '.'),
             ('..\\..\\venv\\Lib\\site-packages\\cefpython3\\*.exe', '.'),
             ],
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
          exclude_binaries=True,
          name='main',
          debug=False,
          strip=False,
          upx=True,
          console=True , icon='static\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='main')

