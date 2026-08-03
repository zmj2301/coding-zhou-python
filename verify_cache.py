import urllib.request
import time

# Try fetching with cache-busting
url = f'https://codingzhou.dpdns.org/feedback/?_={int(time.time())}'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
})
with urllib.request.urlopen(req, timeout=15) as resp:
    content = resp.read().decode('utf-8')

has_dom = 'DOMContentLoaded' in content
has_old = 'onsubmit="submitFeedback(event); return false;"' in content
has_new_submit = 'feedbackForm.addEventListener' in content

print(f"Size: {len(content)} chars")
print(f"Has DOMContentLoaded: {has_dom}")
print(f"Has OLD onsubmit: {has_old}")
print(f"Has NEW addEventListener submit: {has_new_submit}")

if has_dom and has_new_submit and not has_old:
    print("✅ NEW code is deployed!")
else:
    print("❌ OLD code still deployed!")