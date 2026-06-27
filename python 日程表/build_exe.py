import PyInstaller.__main__

PyInstaller.__main__.run([
    'show_yourwindows.py',
    '--name=show_yourwindows',
    '--onefile',
    '--windowed',
    '--icon=combined.ico',
    '--distpath=.',
    '--workpath=build',
    '--specpath=.',
    '--add-data=img;img',
    '--add-data=combined.ico;.',
    '--add-data=*.xlsx;.',
    '--add-data=*.json;.',
])