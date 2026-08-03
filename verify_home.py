import urllib.request
import socket

socket.setdefaulttimeout(30)

try:
    req = urllib.request.Request('https://coding-zhou-python.807842821.workers.dev/', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
        print(f"Worker direct: {resp.status}, {len(content)} chars")
except Exception as e:
    print(f"Worker direct error: {e}")

try:
    req = urllib.request.Request('https://codingzhou.dpdns.org/', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
        print(f"Custom domain: {resp.status}, {len(content)} chars")
except Exception as e:
    print(f"Custom domain error: {e}")