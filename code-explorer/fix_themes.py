#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix theme consistency across all pages.
Adds [data-theme="light"] support to pages that only have :root dark theme.
"""
import os
import re

BASE = r'e:\coding-zhou\Python\code-explorer\public'

# Theme override block to insert after :root definition
LIGHT_THEME_BLOCK = '''
/* ===== 亮色主题支持 ===== */
[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f6f8fa;
  --bg-tertiary: #eaeef2;
  --bg-overlay: #d0d7de;
  --border-color: #d0d7de;
  --border-light: #eaeef2;
  --text-primary: #24292f;
  --text-secondary: #57606a;
  --text-tertiary: #8c959f;
  --accent-blue: #0969da;
  --accent-green: #1a7f37;
  --accent-yellow: #bf8700;
  --accent-red: #cf222e;
  --accent-purple: #8250df;
  --accent-orange: #bf5612;
  --accent-pink: #bf3c5b;
  --accent-cyan: #1a7f37;
  --font-mono: 'JetBrains Mono','Cascadia Code','Fira Code','Consolas','Monaco',monospace;
  --font-sans: -apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
}

[data-theme="light"] body::before {
  background-image:
    linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px);
}

[data-theme="light"] ::-webkit-scrollbar-thumb { background: var(--border-color); }
[data-theme="light"] ::-webkit-scrollbar-thumb:hover { background: #8c959f; }
'''

PAGES_TO_FIX = [
    'scratch/index.html',
    'web-games/index.html',
    'run/local.html',
    'python/index.html',
    'resources/index.html',
]

fixed_count = 0
skipped_count = 0

for page in PAGES_TO_FIX:
    filepath = os.path.join(BASE, page)
    if not os.path.exists(filepath):
        print(f'SKIP (not found): {page}')
        skipped_count += 1
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if it already has light theme support
    if '[data-theme="light"]' in content:
        print(f'OK (already has light theme): {page}')
        skipped_count += 1
        continue
    
    # Find the :root { ... } block and add light theme after it
    # Strategy: find the closing brace of :root and insert after it
    # We look for the pattern ":root {" and then find its matching }
    
    # Simple approach: find "} /* =*" pattern after :root
    # or just find the second } after :root (first is opening of :root, second is closing)
    
    lines = content.split('\n')
    new_lines = []
    in_root = False
    root_depth = 0
    root_started = False
    insert_done = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detect :root start
        if ':root {' in line or ':root{' in line:
            in_root = True
            root_depth = 1
            root_started = True
            new_lines.append(line)
            i += 1
            continue
        
        if in_root:
            root_depth += line.count('{') - line.count('}')
            if root_depth <= 0:
                # This line closes the :root block
                new_lines.append(line)
                in_root = False
                # Insert light theme block here
                new_lines.append('')
                new_lines.append(LIGHT_THEME_BLOCK.strip())
                insert_done = True
                i += 1
                continue
            new_lines.append(line)
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    if insert_done:
        new_content = '\n'.join(new_lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'FIXED (added light theme): {page}')
        fixed_count += 1
    else:
        print(f'WARN (could not find :root): {page}')
        # Fallback: insert before </style>
        if '</style>' in content:
            new_content = content.replace('</style>', LIGHT_THEME_BLOCK + '\n</style>')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'  -> Fallback: inserted before </style>')
            fixed_count += 1

print(f'\nSummary: {fixed_count} fixed, {skipped_count} skipped')
