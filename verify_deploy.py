import urllib.request
import sys

try:
    url = 'https://codingzhou.dpdns.org/feedback/'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode('utf-8')
    
    has_dom = 'DOMContentLoaded' in content
    has_onsubmit_old = 'onsubmit="submitFeedback(event); return false;"' in content
    has_onsubmit_new = 'onsubmit="submitFeedback(event)"' in content
    has_addEventListener_submit = 'feedbackForm.addEventListener' in content
    
    print(f"Page length: {len(content)} chars")
    print(f"Has DOMContentLoaded: {has_dom}")
    print(f"Has OLD onsubmit: {has_onsubmit_old}")
    print(f"Has NEW addEventListener submit: {has_addEventListener_submit}")
    
    if has_dom and not has_onsubmit_old:
        print("✅ New code is deployed!")
    else:
        print("❌ Old code still deployed!")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)