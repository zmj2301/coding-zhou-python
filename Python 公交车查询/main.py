
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from bus_query import BusQuery


def get_input(prompt):
    if sys.version_info[0] == 2:
        return raw_input(prompt).strip()
    else:
        return input(prompt).strip()


def print_menu():
    print("\n" + "="*50)
    print("           湘潭公交查询系统")
    print("="*50)
    print("1. 搜索站点")
    print("2. 查看所有线路")
    print("3. 查询线路详情")
    print("4. 查询站点实时到站")
    print("5. 退出")
    print("="*50)


def search_stations(bq):
    keyword = get_input("\n请输入要搜索的站点关键词: ")
    if not keyword:
        print("请输入有效的关键词！")
        return

    stations = bq.search_stations(keyword)
    if stations:
        print("\n找到 %d 个站点:" % len(stations))
        for i, station in enumerate(stations, 1):
            print("  %d. %s" % (i, station))
    else:
        print("未找到匹配的站点！")


def list_all_lines(bq):
    lines = bq.get_all_lines()
    print("\n共有 %d 条公交线路:" % len(lines))
    for line in lines:
        print("\n【%s】" % line['name'])
        print("  起止: %s → %s" % (line['start_station'], line['end_station']))
        print("  运营时间: %s - %s" % (line['first_bus'], line['last_bus']))
        print("  票价: %s" % line['price'])


def query_line_detail(bq):
    line_name = get_input("\n请输入线路名称（如：1路）: ")
    line = bq.get_line_detail(line_name)
    if line:
        print("\n【%s】线路详情" % line['name'])
        print("起止: %s → %s" % (line['start_station'], line['end_station']))
        print("运营时间: %s - %s" % (line['first_bus'], line['last_bus']))
        print("票价: %s" % line['price'])
        print("\n途经站点（共%d站）:" % len(line['stations']))
        for i, station in enumerate(line['stations'], 1):
            print("  %2d. %s" % (i, station))
    else:
        print("未找到该线路！")


def query_real_time(bq):
    station_name = get_input("\n请输入站点名称: ")
    lines = bq.get_lines_by_station(station_name)
    if not lines:
        print("未找到经过该站点的线路！")
        return

    print("\n经过 '%s' 的线路有:" % station_name)
    for i, line in enumerate(lines, 1):
        print("  %d. %s" % (i, line['name']))

    choice = get_input("\n请选择线路编号查询实时到站（0返回）: ")
    if choice == '0':
        return

    try:
        idx = int(choice) - 1
        if idx >= 0 and idx < len(lines):
            line_name = lines[idx]['name']
            real_time = bq.get_real_time_arrival(station_name, line_name)
            if real_time:
                print("\n【%s】在 '%s' 的实时到站信息" % (line_name, station_name))
                print("查询时间: %s" % real_time['query_time'])
                if real_time['buses']:
                    for bus in real_time['buses']:
                        print("\n• %s" % bus['bus_number'])
                        print("  当前位置: %s" % bus['current_station'])
                        print("  距离: %d 站" % bus['stations_away'])
                        print("  预计: %d 分钟后到达" % bus['eta_minutes'])
                else:
                    print("暂无可查询的车辆信息")
            else:
                print("查询失败！")
        else:
            print("无效的选择！")
    except ValueError:
        print("请输入有效的数字！")


def main():
    bq = BusQuery()
    print("欢迎使用湘潭公交查询系统！")

    while True:
        print_menu()
        choice = get_input("请选择操作（1-5）: ")

        if choice == '1':
            search_stations(bq)
        elif choice == '2':
            list_all_lines(bq)
        elif choice == '3':
            query_line_detail(bq)
        elif choice == '4':
            query_real_time(bq)
        elif choice == '5':
            print("\n感谢使用，再见！")
            break
        else:
            print("\n无效的选择，请重新输入！")


if __name__ == "__main__":
    main()
