import urllib.request

# Check GitHub raw content
url = 'https://raw.githubusercontent.com/zmj2301/coding-zhou-python/main/code-explorer/public/feedback.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as resp:
    content = resp.read().decode('utf-8')

has_dom = 'DOMContentLoaded' in content
has_old = 'onsubmit="submitFeedback(event); return false;"' in content

print(f"GitHub feedback.html size: {len(content)} chars")
print(f"Has DOMContentLoaded: {has_dom}")
print(f"Has OLD onsubmit: {has_old}")

# Also check feedback/index.html
url2 = 'https://raw.githubusercontent.com/zmj2301/coding-zhou-python/main/public/feedback/index.html'
try:
    req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        content2 = resp2.read().decode('utf-8')
    has_dom2 = 'DOMContentLoaded' in content2
    has_old2 = 'onsubmit="submitFeedback(event); return false;"' in content2
    print(f"\nGitHub public/feedback/index.html size: {len(content2)} chars")
    print(f"Has DOMContentLoaded: {has_dom2}")
    print(f"Has OLD onsubmit: {has_old2}")
except Exception as e:
    print(f"\nGitHub public/feedback/index.html: Error - {e}")