import os
import re
import requests
import hashlib

HTML_FILE = r"e:\coding-zhou\Python\code-explorer\index.html"
OUTPUT_DIR = r"e:\coding-zhou\Python\public\images\covers"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(HTML_FILE, "r", encoding="utf-8") as f:
    html = f.read()

match = re.search(r"const PROJECT_COVERS = \{([^}]+)\};", html, re.DOTALL)
if not match:
    print("ERROR: PROJECT_COVERS not found")
    exit(1)

covers_block = match.group(1)
entries = re.findall(r"'([^']+)':\s*'([^']+)'", covers_block)

print(f"Found {len(entries)} covers")

url_to_filename = {}
url_count = {}

for name, url in entries:
    if url not in url_count:
        url_count[url] = 0
    url_count[url] += 1

for name, url in entries:
    if url.startswith("data:image") or url.startswith("<svg"):
        continue
    if not url.startswith("http"):
        continue
    
    if url in url_to_filename:
        continue
    
    safe_name = re.sub(r'[\\/:*?"<>|\s]+', '_', name)
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{safe_name}_{url_hash}.jpg"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"  [skip] {name} -> {filename} (exists)")
        url_to_filename[url] = filename
        continue
    
    print(f"  [download] {name} ...")
    try:
        r = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        r.raise_for_status()
        
        content_type = r.headers.get("content-type", "")
        if "png" in content_type:
            filename = f"{safe_name}_{url_hash}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
        elif "webp" in content_type:
            filename = f"{safe_name}_{url_hash}.webp"
            filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(r.content)
        
        size_kb = len(r.content) / 1024
        print(f"    -> {filename} ({size_kb:.1f} KB)")
        url_to_filename[url] = filename
    except Exception as e:
        print(f"    ERROR: {e}")

print(f"\nDone. Downloaded {len(url_to_filename)} unique images.")

new_html = html
for url, filename in url_to_filename.items():
    new_html = new_html.replace(url, f"/images/covers/{filename}")

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(new_html)

public_html = HTML_FILE.replace("code-explorer", "public")
with open(public_html, "w", encoding="utf-8") as f:
    f.write(new_html.replace("code-explorer", "public"))

print("Updated index.html files with local paths")
