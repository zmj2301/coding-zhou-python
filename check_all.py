import os

# Compare all feedback files
files = [
    r'e:\coding-zhou\Python\feedback.html',
    r'e:\coding-zhou\Python\public\feedback.html',
    r'e:\coding-zhou\Python\public\feedback\index.html',
    r'e:\coding-zhou\Python\code-explorer\public\feedback.html',
]

for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as fh:
            content = fh.read()
        has_dom = 'DOMContentLoaded' in content
        has_old_onsubmit = 'onsubmit="submitFeedback(event); return false;"' in content
        print(f"{f}:")
        print(f"  Size: {len(content)} chars")
        print(f"  Has DOMContentLoaded: {has_dom}")
        print(f"  Has OLD onsubmit: {has_old_onsubmit}")
    else:
        print(f"{f}: NOT FOUND")
    print()