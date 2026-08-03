import urllib.request
import hashlib

# Compare GitHub version with the ECS server version
# GitHub raw URL
github_url = 'https://raw.githubusercontent.com/zmj2301/coding-zhou-python/main/code-explorer/public/feedback.html'
ecs_url = 'https://codingzhou.dpdns.org/feedback/'

# Fetch GitHub version
gh_req = urllib.request.Request(github_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(gh_req, timeout=15) as resp:
    gh_content = resp.read()

# Fetch ECS version
ecs_req = urllib.request.Request(ecs_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(ecs_req, timeout=15) as resp:
    ecs_content = resp.read()

gh_hash = hashlib.md5(gh_content).hexdigest()
ecs_hash = hashlib.md5(ecs_content).hexdigest()

print(f"GitHub feedback.html: {len(gh_content)} bytes, MD5: {gh_hash}")
print(f"ECS feedback page:    {len(ecs_content)} bytes, MD5: {ecs_hash}")
print(f"Match: {gh_hash == ecs_hash}")

# Check key features
for name, content in [("GitHub", gh_content.decode()), ("ECS", ecs_content.decode())]:
    has_dom = 'DOMContentLoaded' in content
    has_old = 'onsubmit="submitFeedback(event); return false;"' in content
    has_new_submit = 'feedbackForm.addEventListener' in content
    has_theme = "setTheme(getTheme())" in content
    has_stars = "starRating.addEventListener" in content
    print(f"\n{name}:")
    print(f"  DOMContentLoaded: {has_dom}")
    print(f"  OLD onsubmit: {has_old}")
    print(f"  NEW addEventListener submit: {has_new_submit}")
    print(f"  Theme early apply: {has_theme}")
    print(f"  Star rating event delegation: {has_stars}")