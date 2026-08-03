import urllib.request

# Check what the custom domain serves for feedback
urls = [
    'https://codingzhou.dpdns.org/feedback/',
    'http://39.107.96.165/feedback/',
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8')
            has_dom = 'DOMContentLoaded' in content
            has_old = 'onsubmit="submitFeedback(event); return false;"' in content
            print(f"{url}:")
            print(f"  Size: {len(content)} chars")
            print(f"  Has DOMContentLoaded: {has_dom}")
            print(f"  Has OLD onsubmit: {has_old}")
            print()
    except Exception as e:
        print(f"{url}: Error - {e}")
        print()