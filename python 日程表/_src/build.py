# -*- coding: utf-8 -*-
"""
把内联依赖 + 真实 Excel 种子数据注入模板，产出最终的单文件 HTML。

用法：python _src/build.py
产出：output/待办中心.html

种子数据来自 SEED_FILE 指定的 Excel（time + things 两列），
日期按「月.日」字面规则解析（9.2 = 9月2日），与 JS 端 importExcel 一致。
"""
import io
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, '_src', 'todo-app.template.html')
SHEETJS = os.path.join(ROOT, '_src', 'xlsx.mini.min.js')
SEED_FILE = os.path.join(ROOT, '测试待办数据.xlsx')
OUT_DIR = os.path.join(ROOT, 'output')
OUT_FILE = os.path.join(OUT_DIR, '待办中心.html')

PLACEHOLDER_LIB = '/*__SHEETJS__*/'
PLACEHOLDER_SEED = '/*__SEED__*/'
PLACEHOLDER_SOURCE = '/*__SOURCE__*/'

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
HEADER_A = ('time', 'date', '日期', '时间')
HEADER_B = ('things', 'task', 'tasks', 'todo', 'title', '事项', '待办', '任务', '内容')


def _col_index(ref):
    m = re.match(r'([A-Z]+)', ref or '')
    if not m:
        return 0
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _num_to_md(v):
    """数字型 月.日 -> 'MM-DD'（字面规则：9.2 -> 09-02）。"""
    try:
        r = round(float(v) * 100) / 100
    except Exception:
        return ''
    s = '%g' % r
    parts = s.split('.')
    try:
        mo = int(parts[0])
        da = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        return ''
    if 1 <= mo <= 12 and 1 <= da <= 31:
        return '%02d-%02d' % (mo, da)
    return ''


def read_seed_rows(xlsx_path):
    """从 xlsx 提取 (MM-DD, 标题) 行；返回 list[tuple]，找不到则 []。"""
    z = zipfile.ZipFile(xlsx_path)
    names = z.namelist()

    shared = []
    try:
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    except Exception:
        pass

    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}

    sheets = wb.find(NS + 'sheets')
    if sheets is None:
        return []

    for sh in sheets:
        tgt = relmap.get(sh.get(RNS + 'id'), '')
        cand = None
        for c in (tgt, 'xl/' + tgt.lstrip('/'), tgt.lstrip('/')):
            if c in names:
                cand = c
                break
        if not cand:
            continue
        try:
            root = ET.fromstring(z.read(cand))
        except Exception:
            continue

        rows = []
        first = True
        for r in root.iter(NS + 'row'):
            cells = {}
            for c in r.findall(NS + 'c'):
                ref = c.get('r') or ''
                t = c.get('t')
                v = c.find(NS + 'v')
                isel = c.find(NS + 'is')
                if t == 's' and v is not None:
                    val = shared[int(v.text)]
                elif t == 'inlineStr' and isel is not None:
                    val = ''.join(x.text or '' for x in isel.iter(NS + 't'))
                elif v is not None:
                    val = v.text
                else:
                    val = ''
                cells[_col_index(ref)] = val
            if not cells:
                continue
            a = cells.get(0, '')
            b = cells.get(1, '')
            if first:
                first = False
                if str(a).strip().lower() in HEADER_A or str(b).strip().lower() in HEADER_B:
                    continue  # 表头行
            title = str(b).strip()
            if not title:
                continue
            rows.append((_num_to_md(a), title))

        if rows:
            return rows
    return []


def main():
    if not os.path.isfile(TEMPLATE):
        sys.exit('模板不存在: ' + TEMPLATE)
    if not os.path.isfile(SHEETJS):
        sys.exit('SheetJS 不存在: ' + SHEETJS)

    tpl = io.open(TEMPLATE, encoding='utf-8').read()
    lib = io.open(SHEETJS, encoding='utf-8').read()

    for ph in (PLACEHOLDER_LIB, PLACEHOLDER_SEED, PLACEHOLDER_SOURCE):
        if ph not in tpl:
            sys.exit('模板里找不到占位符 ' + ph)

    if '</script' in lib.lower():
        sys.exit('SheetJS 内含 </script 字面量，无法安全内联')

    # 种子：从真实 Excel 提取
    if not os.path.isfile(SEED_FILE):
        sys.exit('种子 Excel 不存在: ' + SEED_FILE)
    rows = read_seed_rows(SEED_FILE)
    seed_js = '[' + ','.join(
        '["%s",%s]' % (md, json.dumps(title, ensure_ascii=False)) for md, title in rows
    ) + ']'

    os.makedirs(OUT_DIR, exist_ok=True)
    # 导出 xlsx 时的默认文件名 = 种子来源文件名，方便直接覆盖原文件
    source_js = json.dumps(os.path.basename(SEED_FILE), ensure_ascii=False)
    out = (tpl.replace(PLACEHOLDER_LIB, lib)
              .replace(PLACEHOLDER_SEED, seed_js)
              .replace(PLACEHOLDER_SOURCE, source_js))
    io.open(OUT_FILE, 'w', encoding='utf-8', newline='\n').write(out)

    checks = {
        'SheetJS 版本标记': 'xlsx.js (C) 2013-present SheetJS' in out,
        '全局 XLSX 定义': 'XLSX={}' in out,
        '无残留占位符': not any(ph in out for ph in (PLACEHOLDER_LIB, PLACEHOLDER_SEED, PLACEHOLDER_SOURCE)),
        '种子已注入且非空': len(rows) > 0,
        '无外部 http 资源': not re.search(r'(src|href)=["\']https?://', out),
        '无 <script src>': '<script src' not in out.lower(),
        'script 标签配对': out.lower().count('<script') == out.lower().count('</script>'),
    }

    print('模板      : %.1f KB' % (len(tpl.encode('utf-8')) / 1024))
    print('SheetJS   : %.1f KB' % (len(lib.encode('utf-8')) / 1024))
    print('种子      : %d 条（来自 %s）' % (len(rows), os.path.basename(SEED_FILE)))
    print('产出      : %s  (%.1f KB)' % (OUT_FILE, os.path.getsize(OUT_FILE) / 1024))
    print('-' * 56)
    ok = True
    for name, passed in checks.items():
        print(('  [OK]   ' if passed else '  [FAIL] ') + name)
        ok = ok and passed
    print('-' * 56)
    print('结果: ' + ('全部通过' if ok else '存在失败项'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
