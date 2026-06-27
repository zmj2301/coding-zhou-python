
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bus_query import BusQuery


def test_bus_query():
    bq = BusQuery()

    print("="*60)
    print("测试 1: 获取所有线路")
    print("="*60)
    lines = bq.get_all_lines()
    print("找到 %d 条线路" % len(lines))
    for line in lines:
        print("  • %s: %s → %s" % (line['name'], line['start_station'], line['end_station']))

    print("\n" + "="*60)
    print("测试 2: 搜索站点（关键词：基建营）")
    print("="*60)
    stations = bq.search_stations("基建营")
    print("找到 %d 个站点: %s" % (len(stations), stations))

    print("\n" + "="*60)
    print("测试 3: 查询 1路 线路详情")
    print("="*60)
    line1 = bq.get_line_detail("1路")
    if line1:
        print("线路: %s" % line1['name'])
        print("起止: %s → %s" % (line1['start_station'], line1['end_station']))
        print("站点数: %d" % len(line1['stations']))

    print("\n" + "="*60)
    print("测试 4: 查询 基建营 站点经过的线路")
    print("="*60)
    passing_lines = bq.get_lines_by_station("基建营")
    line_names = [line['name'] for line in passing_lines]
    print("经过的线路: %s" % line_names)

    print("\n" + "="*60)
    print("测试 5: 查询 基建营 站 1路 实时到站信息")
    print("="*60)
    real_time = bq.get_real_time_arrival("基建营", "1路")
    if real_time:
        print("查询时间: %s" % real_time['query_time'])
        for bus in real_time['buses']:
            print("  • %s: %s → 预计 %d 分钟" % (bus['bus_number'], bus['current_station'], bus['eta_minutes']))

    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    test_bus_query()
