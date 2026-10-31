#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建脚本：生成文件树、复制静态文件到 public 目录
"""

import os
import re
import shutil
import json
import sys
from html import escape
from urllib.parse import quote
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = Path(__file__).resolve().parent / 'public'
CODE_EXPLORER_DIR = Path(__file__).resolve().parent
WEB_GAMES_DIR = CODE_EXPLORER_DIR / 'web-games'
FATHERS_DAY_DIR = CODE_EXPLORER_DIR / 'fathers-day'


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f'  复制: {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}')


def copy_dir(src: Path, dst: Path, exclude_dirs=None, exclude_exts=None):
    if exclude_dirs is None:
        exclude_dirs = set()
    if exclude_exts is None:
        exclude_exts = set()

    if not src.exists():
        return

    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name.startswith('.'):
            continue
        if item.is_dir():
            if item.name in exclude_dirs:
                continue
            copy_dir(item, dst / item.name, exclude_dirs, exclude_exts)
        elif item.is_file():
            ext = item.suffix.lower()
            if ext in exclude_exts:
                continue
            copy_file(item, dst / item.name)


# 技术文章源文件 → 生成的静态页 slug
ARTICLES = [
    ('python-subproject-fix', '文章/Python子项目集成问题排查.md'),
    ('branch-switch-incident', '文章/分支切换回退事故复盘.md'),
    ('v2.6.9-upload-history', '文章/v2.6.9文件上传历史记录.md'),
    ('agents-manual', 'AGENTS.md'),
]

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · Code Explorer</title>
<meta name="description" content="__TITLE__">
<style>
:root{--bg:#ffffff;--fg:#1f2328;--muted:#656d76;--border:#d8dee4;--code:#f6f8fa;--link:#0550ae}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#8b949e;--border:#30363d;--code:#161b22;--link:#6cb6ff}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,"Microsoft YaHei",sans-serif;line-height:1.75}
.wrap{max-width:820px;margin:0 auto;padding:40px 20px 80px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;border-bottom:1px solid var(--border);padding-bottom:14px;margin-bottom:28px}
.top a{color:var(--muted);text-decoration:none;font-size:14px}
.top a:hover{color:var(--fg)}
h1,h2,h3,h4{line-height:1.3;margin:1.6em 0 .6em}
h1{font-size:28px;margin-top:0}
h2{font-size:22px;border-bottom:1px solid var(--border);padding-bottom:.3em}
h3{font-size:18px}
a{color:var(--link)}
code{background:var(--code);padding:.15em .4em;font-size:.9em;font-family:ui-monospace,Consolas,monospace}
pre{background:var(--code);padding:14px 16px;overflow:auto;border:1px solid var(--border)}
pre code{background:none;padding:0}
blockquote{margin:1em 0;padding:.2em 1em;border-left:3px solid var(--border);color:var(--muted)}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:14px}
td,th{border:1px solid var(--border);padding:6px 10px;text-align:left}
hr{border:none;border-top:1px solid var(--border);margin:2em 0}
img{max-width:100%}
.art-index{list-style:none;padding:0}
.art-index li{padding:12px 0;border-bottom:1px solid var(--border)}
.art-index a{text-decoration:none;font-size:17px}
</style>
</head>
<body>
<div class="wrap">
<div class="top"><a href="/">← Code Explorer</a><a href="__MD_HREF__">Markdown 原文</a></div>
__BODY__
</div>
</body>
</html>
"""


def article_html(title: str, body: str, slug: str) -> str:
    md_href = '/articles/' if slug == 'index' else f'/articles/{slug}.md'
    return (ARTICLE_TEMPLATE
            .replace('__TITLE__', title)
            .replace('__BODY__', body)
            .replace('__MD_HREF__', md_href))


def main():
    print('=' * 50)
    print('  构建 Cloudflare Pages 项目')
    print('=' * 50)
    print()

    if PUBLIC_DIR.exists():
        print(f'清理旧的 public 目录...')
        shutil.rmtree(PUBLIC_DIR)

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print('步骤 1: 生成文件树和项目列表 JSON...')
    sys.path.insert(0, str(CODE_EXPLORER_DIR / 'code-explorer'))
    import generate_filetree
    generate_filetree.main()

    print()
    print('步骤 2: 复制首页 index.html...')
    # 单一事实源: code-explorer/index.html（根目录 index.html 只是副本）。
    # 两份不一致时中止构建，防止部署旧版首页（v2.6.7 的教训，见 AGENTS.md 3.6）。
    canonical_index = CODE_EXPLORER_DIR / 'code-explorer' / 'index.html'
    root_index = CODE_EXPLORER_DIR / 'index.html'
    if canonical_index.exists():
        if root_index.exists():
            import filecmp
            if not filecmp.cmp(canonical_index, root_index, shallow=False):
                print('  ✗ 构建中止: 根目录 index.html 与 code-explorer/index.html 内容不一致！')
                print('    处理: 确认最新版后用 cp 覆盖另一份，使两份一致，再重新构建。')
                sys.exit(1)
        copy_file(canonical_index, PUBLIC_DIR / 'index.html')
    else:
        print('  ⚠ code-explorer/index.html 不存在，退回复制根目录 index.html')
        copy_file(root_index, PUBLIC_DIR / 'index.html')

    print()
    print('步骤 2.3: 复制反馈页 feedback.html...')
    feedback_src = CODE_EXPLORER_DIR / 'feedback.html'
    if feedback_src.exists():
        copy_file(feedback_src, PUBLIC_DIR / 'feedback.html')
    else:
        print('  跳过: feedback.html 不存在')

    print()
    print('步骤 2.2: 复制 images 目录...')
    images_src = CODE_EXPLORER_DIR / 'code-explorer' / 'public' / 'images'
    if images_src.exists():
        copy_dir(images_src, PUBLIC_DIR / 'images')
    else:
        print('  跳过: images 目录不存在')

    print()
    print('步骤 2.5: 复制 changelog.json...')
    changelog_src = CODE_EXPLORER_DIR / 'changelog.json'
    if changelog_src.exists():
        copy_file(changelog_src, PUBLIC_DIR / 'changelog.json')
    else:
        print('  跳过: changelog.json 不存在')

    print()
    print('步骤 2.6: 复制 python 导航页...')
    python_src = CODE_EXPLORER_DIR / 'code-explorer' / 'python'
    if python_src.exists():
        copy_dir(python_src, PUBLIC_DIR / 'python')
    else:
        print('  跳过: python 目录不存在')

    print()
    print('步骤 2.7: 复制 project-list.json...')
    gen_src = CODE_EXPLORER_DIR / 'code-explorer' / 'public'
    project_list_src = gen_src / 'project-list.json'
    if project_list_src.exists():
        copy_file(project_list_src, PUBLIC_DIR / 'project-list.json')
    else:
        print('  跳过: project-list.json 不存在')

    print()
    print('步骤 2.7: 复制 project-trees 目录...')
    project_trees_src = gen_src / 'project-trees'
    if project_trees_src.exists():
        copy_dir(project_trees_src, PUBLIC_DIR / 'project-trees')
    else:
        print('  跳过: project-trees 目录不存在')

    print()
    print('步骤 2.8: 生成技术文章静态页（public/articles/）...')
    try:
        import markdown as md_lib
    except ImportError:
        # 绝不能静默跳过：public/ 在这一步之前已经被整个清空了，
        # 跳过 HTML 生成会让 /articles/* 全部 404。
        # 2026-10-31 踩过：本地换了没装 markdown 的 Python，构建后文章页全丢。
        print('  ✗ 构建中止: 缺少 markdown 库，无法生成 public/articles/*.html')
        print('    处理: pip install markdown')
        sys.exit(1)

    art_dir = PUBLIC_DIR / 'articles'
    art_dir.mkdir(parents=True, exist_ok=True)
    index_items = []
    for slug, rel in ARTICLES:
        src = CODE_EXPLORER_DIR / rel
        if not src.exists():
            print(f'  跳过（源文件不存在）: {rel}')
            continue
        text = src.read_text(encoding='utf-8')
        (art_dir / f'{slug}.md').write_text(text, encoding='utf-8')
        title = slug
        for line in text.splitlines():
            if line.startswith('# '):
                title = line[2:].strip()
                break
        if md_lib:
            body = md_lib.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists'])
            (art_dir / f'{slug}.html').write_text(article_html(title, body, slug), encoding='utf-8')
        index_items.append((slug, title))
        print(f'  生成: articles/{slug}.md' + (' + .html' if md_lib else ''))

    if md_lib and index_items:
        links = ''.join(f'<li><a href="/articles/{s}">{t}</a></li>' for s, t in index_items)
        (art_dir / 'index.html').write_text(
            article_html('技术文章', f'<ul class="art-index">{links}</ul>', 'index'), encoding='utf-8')
        print('  生成: articles/index.html')

    print()
    print('步骤 2.8.5: 复制积分规划页（public/articles/credit-plan.html）...')
    # 这份页面不走 ARTICLES 那条 markdown 管线 —— 它是数据驱动的单页应用，
    # 运行时从 /api/credits 拉 JSON 渲染，塞进文章模板反而会被模板 CSS 压坏。
    credits_page_src = CODE_EXPLORER_DIR / 'code-explorer' / 'credits-page.html'
    if credits_page_src.exists():
        copy_file(credits_page_src, PUBLIC_DIR / 'articles' / 'credit-plan.html')
    else:
        print('  跳过: code-explorer/credits-page.html 不存在')

    print()
    print('步骤 2.9: 复制 AGENTS.md 到 public/share/agents.md...')
    agents_src = CODE_EXPLORER_DIR / 'AGENTS.md'
    if agents_src.exists():
        copy_file(agents_src, PUBLIC_DIR / 'share' / 'agents.md')
    else:
        print('  跳过: AGENTS.md 不存在')

    print()
    print('步骤 2.9.5: 生成项目静态页 + sitemap.xml + robots.txt...')
    SITE = 'https://codingzhou.top'
    TYPE_CN = {
        'game': '游戏', 'ai': 'AI', 'tool': '工具', 'other': '其他',
        'web-game': '网页游戏', 'system-file': '系统文件', 'popup-preview': '弹出预览',
    }
    projects_data = []
    if project_list_src.exists():
        try:
            projects_data = json.loads(project_list_src.read_text(encoding='utf-8'))
        except Exception as e:
            print(f'  读取 project-list.json 失败: {e}')

    proj_dir = PUBLIC_DIR / 'projects'
    proj_dir.mkdir(parents=True, exist_ok=True)
    project_urls = []
    for i, p in enumerate(projects_data):
        name = (p.get('name') or p.get('path') or f'项目 {i + 1}').strip()
        ppath = (p.get('path') or name).strip()
        desc = (p.get('desc') or f'{name} —— 站内可在线浏览与运行的项目').strip()
        type_cn = TYPE_CN.get(p.get('type') or 'other', '其他')
        raw_slug = re.sub(r'[^a-zA-Z0-9]+', '-', name).strip('-').lower()
        slug = f'{i + 1:02d}-{raw_slug}' if raw_slug else f'project-{i + 1:02d}'
        open_url = f'/plaza?project={quote(ppath, safe="")}'
        meta_desc = escape(desc[:150])
        page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(name)} - Code Explorer</title>
<meta name="description" content="{meta_desc}">
<meta property="og:title" content="{escape(name)}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE}/projects/{slug}">
<link rel="canonical" href="{SITE}/projects/{slug}">
<style>
body{{margin:0;padding:48px 20px;background:#0a0e1a;color:#e2e8f0;font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.7}}
main{{max-width:760px;margin:0 auto}}
a{{color:#38bdf8}}
h1{{font-size:28px;margin:0 0 12px}}
.meta{{color:#94a3b8;font-size:14px;margin-bottom:24px}}
p{{color:#cbd5e1}}
.btn{{display:inline-block;margin-top:28px;padding:10px 18px;border-radius:8px;background:#38bdf8;color:#0a0e1a;text-decoration:none;font-weight:600}}
</style>
</head>
<body>
<main>
<h1>{escape(name)}</h1>
<div class="meta">{escape(type_cn)} · 共 {p.get('fileCount', 0)} 个文件{f" · 入口 {escape(str(p.get('mainFile')))}" if p.get('mainFile') else ''}</div>
<p>{escape(desc)}</p>
<a class="btn" href="{open_url}">在站内打开这个项目</a>
<p style="margin-top:32px"><a href="/plaza">返回项目广场</a></p>
</main>
</body>
</html>
'''
        (proj_dir / f'{slug}.html').write_text(page, encoding='utf-8')
        # Cloudflare Assets 会把 *.html 307 到无扩展名地址，canonical/sitemap 直接用最终地址
        project_urls.append(f'{SITE}/projects/{slug}')
    print(f'  生成项目页: {len(project_urls)} 个')

    urls = [f'{SITE}/', f'{SITE}/plaza', f'{SITE}/res/windows']
    urls += [f'{SITE}/articles/{slug}' for slug, _ in index_items]
    urls += project_urls
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        sitemap += f'  <url><loc>{escape(u)}</loc></url>\n'
    sitemap += '</urlset>\n'
    (PUBLIC_DIR / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    (PUBLIC_DIR / 'robots.txt').write_text(
        f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
    print(f'  生成: sitemap.xml（{len(urls)} 条）+ robots.txt')

    print()
    print('步骤 2.10: 复制 vendor 目录（自托管前端依赖）...')
    # public 每次构建都会重建，自托管的第三方库必须从源码目录复制，
    # 否则 /vendor/marked.umd.js 会在部署后 404，README 又退回纯文本。
    vendor_src = CODE_EXPLORER_DIR / 'code-explorer' / 'vendor'
    if vendor_src.exists():
        copy_dir(vendor_src, PUBLIC_DIR / 'vendor')
    else:
        print('  跳过: code-explorer/vendor 目录不存在')

    print()
    print('步骤 3: 复制 web-games 目录...')
    if WEB_GAMES_DIR.exists():
        copy_dir(WEB_GAMES_DIR, PUBLIC_DIR / 'web-games')
    else:
        print('  跳过: web-games 目录不存在')

    print()
    print('步骤 4: 复制 fathers-day 目录...')
    if FATHERS_DAY_DIR.exists():
        copy_dir(FATHERS_DAY_DIR, PUBLIC_DIR / 'fathers-day')
    else:
        print('  跳过: fathers-day 目录不存在')

    print()
    print('步骤 5: 清理大文件（超过 5MB 的文件，Worker 不支持）...')
    for f in PUBLIC_DIR.rglob('*'):
        if not f.is_file():
            continue
        size = f.stat().st_size
        if size > 5 * 1024 * 1024:
            f.unlink()
            print(f'  删除: {f.relative_to(BASE_DIR)} ({size / 1024 / 1024:.1f} MB)')

    print()
    print('=' * 50)
    print('  构建完成！')
    print(f'  输出目录: {PUBLIC_DIR}')
    print('=' * 50)


if __name__ == '__main__':
    main()
