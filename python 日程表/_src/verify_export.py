# -*- coding: utf-8 -*-
"""校验「保存为 Excel」导出的文件结构是否与源文件一致（两列 / 数字型月.日 / 标题逐条相同）。

用法：python _src/verify_export.py <导出的 xlsx> [源 xlsx]
"""
import os
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def _col_index(ref):
    m = __import__('re').match(r'([A-Z]+)', ref or '')
    if not m:
        return 0
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_rows(xlsx_path):
    """返回 [(row_values, row_types)]，types 里 'n' 表示数字型单元格。"""
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

    for sh in sheets:
        tgt = relmap.get(sh.get(RNS + 'id'), '')
        cand = None
        for c in (tgt, 'xl/' + tgt.lstrip('/'), tgt.lstrip('/')):
            if c in names:
                cand = c
                break
        if not cand:
            continue
        root = ET.fromstring(z.read(cand))
        out = []
        for r in root.iter(NS + 'row'):
            vals = {}
            types = {}
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
                i = _col_index(ref)
                vals[i] = val
                types[i] = 'n' if t is None else t   # 无 t 属性即为数字型
            if not vals:
                continue
            width = max(vals) + 1
            out.append(([vals.get(i, '') for i in range(width)],
                        [types.get(i, '') for i in range(width)]))
        if out:
            return out
    return []


def main():
    if len(sys.argv) < 2:
        sys.exit('用法: python _src/verify_export.py <未改动导出的 xlsx> [改动后导出的 xlsx]')
    exported = sys.argv[1]
    modified = sys.argv[2] if len(sys.argv) > 2 else None
    source = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '测试待办数据.xlsx')

    rows = read_rows(exported)
    if not rows:
        sys.exit('导出文件里读不到数据行')

    header, _ = rows[0]
    data = rows[1:]
    src = read_rows(source)
    src_data = src[1:]

    plain = [r for r, _ in data]          # 导出的数据行（只取值）
    src_plain = [r for r, _ in src_data]  # 源文件的数据行

    checks = {
        '表头就是 time / things 两列': [str(x).strip() for x in header] == ['time', 'things'],
        '没有多余的状态/优先级列': len(header) == 2,
        '数据行数与源文件相同': len(plain) == len(src_plain),
        'time 列是数字型单元格': all(r_t[0] == 'n' for _, r_t in data),
        'things 列是文本': all(r_t[1] in ('s', 'str', 'inlineStr') for _, r_t in data),
        '标题集合与源文件完全一致': sorted(r[1] for r in plain) == sorted(r[1] for r in src_plain),
    }

    def norm(v):
        try:
            return round(float(v), 6)
        except Exception:
            return None

    def mult(rows):
        return sorted((norm(r[0]), r[1]) for r in rows)

    checks['每条 time 数值与源文件一致（按标题配对）'] = (
        {r[1]: norm(r[0]) for r in plain} == {r[1]: norm(r[0]) for r in src_plain})
    checks['整体内容（标题+日期）与源文件一致'] = mult(plain) == mult(src_plain)
    # 源文件的行数顺序是录入顺序；导出按日期升序重排，属于预期差异
    # 源文件的行顺序是录入顺序；导出按真实日期升序重排（注意 9.2 是 9月2日，
    # 数值上大于 9.15，所以只能拆成月/日比较，不能用浮点值排序）
    def mdkey(v):
        try:
            r = round(float(v) * 100) / 100
            s = '%g' % r
            m, _, d = s.partition('.')
            return (int(m), int(d) if d else 0)
        except Exception:
            return (99, 99)

    datekeys = [mdkey(r[0]) for r in plain]
    checks['导出按真实日期升序排列'] = datekeys == sorted(datekeys)
    # 源里 9.2 被 Excel 存成 9.199999999999999，导出时应还原为干净的 9.2
    checks['浮点脏值已还原（9.2 / 9.3）'] = set(norm(r[0]) for r in plain) <= {round(float(v), 6) for v in
                                                  ['9.2', '9.3', '9.15', '9.24', '9.25', '9.26',
                                                   '9.27', '10.1', '10.8', '11.11', '12.28', '12.31']}

    # 改动后导出的那一份：测试把「提交悬浮球功能测试反馈」从 09-27 拖到了 09-26
    if modified and os.path.isfile(modified):
        mrows = read_rows(modified)
        mheader, _ = mrows[0]
        mdata = [r for r, _ in mrows[1:]]
        mmap = {r[1]: norm(r[0]) for r in mdata}
        checks['改动后导出仍为 time / things 两列'] = [str(x).strip() for x in mheader] == ['time', 'things']
        checks['改动后导出仍 13 条'] = len(mdata) == len(src_plain)
        checks['改动后标题一条不少'] = sorted(r[1] for r in mdata) == sorted(r[1] for r in src_plain)
        checks['被拖动的待办日期已写成 9.26'] = mmap.get('提交悬浮球功能测试反馈') == 9.26
        checks['原来占位的 9.27 不再出现'] = 9.27 not in [v for v in mmap.values()]

    print('导出文件 : %s (%.1f KB)' % (exported, os.path.getsize(exported) / 1024))
    print('源文件   : %s' % os.path.basename(source))
    print('导出行数 : %d' % len(data))
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
