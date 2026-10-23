#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""湘潭实时公交·最优乘车方案 —— 命令行入口（v1.1.0）

用法:
    python cli.py "未来素养""翰林居"
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from busapp import planner

APP_VERSION = planner.cl.APP_VERSION


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(u"湘潭实时公交 v%s" % APP_VERSION)
        print(u"用法: python cli.py 起点 终点")
        print(u"示例: python cli.py 未来素养 翰林居")
        return 1

    origin, dest = args[0], args[1]
    print(u"\U0001f68c 湘潭实时公交 v%s  ·  %s" % (APP_VERSION, planner.cl.CITY_NAME))
    print("=" * 58)

    o_stops, o_desc = planner.resolve_origin(origin)
    if not o_stops:
        print(u"\u274c 起点未找到：%s" % o_desc)
        return 1
    d_stops, d_desc = planner.resolve_destination(dest)
    if not d_stops:
        print(u"\u274c 终点未找到：%s" % d_desc)
        return 1

    print(u"起点：%s（%s）" % (o_stops[0].name, o_desc))
    print(u"终点：%s（%s）" % (d_stops[0].name, d_desc))
    print("-" * 58)

    plans = planner.plan_route(o_stops, d_stops)
    now = time.strftime("%H:%M:%S")
    print(u"查询时间 %s  共 %d 个方案\n" % (now, len(plans)))

    for i, p in enumerate(plans, 1):
        tag = u"实时数据" if p.has_realtime else u"估算"
        print(u"【方案 %d】总计 %.0f 分钟  换乘 %d 次  [%s]"
              % (i, p.total, p.transfers, tag))
        for leg in p.legs:
            print(u"    %-32s %5.1f 分钟  %s"
                  % (leg.title, leg.minutes, leg.detail))
        if p.note:
            print(u"    ⚠ %s" % p.note)
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())