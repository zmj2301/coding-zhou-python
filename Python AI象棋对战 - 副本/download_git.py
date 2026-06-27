import urllib.request
url = 'https://github.com/git-for-windows/git/releases/download/v2.54.0.windows.1/Git-2.54.0-64-bit.exe'
urllib.request.urlretrieve(url, 'C:\\GitInstaller.exe')
print('Download completed')