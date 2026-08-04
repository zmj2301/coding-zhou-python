import urllib.request
req = urllib.request.Request('https://codingzhou.dpdns.org/?v=verify7', headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
with urllib.request.urlopen(req, timeout=15) as resp:
    content = resp.read().decode('utf-8')

checks = [
    ('projectListSection', 'projectListSection' in content),
    ('carousel click scroll', 'Click on carousel image' in content),
    ('cursor:pointer CSS', 'cursor: pointer' in content),
    ('scale hover', 'scale(1.02)' in content),
    ('smooth scroll', "behavior: 'smooth'" in content),
    ('headerOffset', 'headerOffset' in content),
]

for name, result in checks:
    print(f'[{"PASS" if result else "FAIL"}] {name}')

if 'carousel-slide img' in content:
    css_idx = content.find('carousel-slide img')
    print('\nCSS section:')
    print(content[css_idx:css_idx+250])