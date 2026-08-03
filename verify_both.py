import urllib.request
import time

# Try the Worker directly
urls = [
    'https://coding-zhou-python.807842821.workers.dev/feedback/',
    'https://codingzhou.dpdns.org/feedback/',
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Cache-Control': 'no-cache',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8')
            has_dom = 'DOMContentLoaded' in content
            has_old = 'onsubmit="submitFeedback(event); return false;"' in content
            print(f"{url}:")
            print(f"  Size: {len(content)} chars")
            print(f"  Has DOMContentLoaded: {has_dom}")
            print(f"  Has OLD onsubmit: {has_old}")
            if has_dom and not has_old:
                print("  ✅ NEW code!")
            else:
                print("  ❌ OLD code!")
            print()
    except Exception as e:
        print(f"{url}: Error - {e}")
        print()