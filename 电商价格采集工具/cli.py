#!/usr/bin/env python3
"""电商价格采集对比工具 - 命令行界面"""
import argparse
import json
import os
import sys
import time
from typing import List, Optional

# 确保项目目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════╗
║       电商商品价格自动化采集与对比工具 v1.0           ║
║   支持京东 / 淘宝 / 拼多多 多平台商品价格采集对比       ║
╚══════════════════════════════════════════════════════╝
    """
    print(banner)


def print_table(products: List[dict], max_rows: int = 30):
    """以表格形式打印商品列表"""
    if not products:
        print("  暂无数据")
        return
    
    # 计算列宽
    cols = {
        "序号": 5,
        "商品名称": 40,
        "价格": 10,
        "原价": 10,
        "平台": 8,
        "店铺": 18,
        "评分": 6,
        "月销": 10,
    }
    
    def format_row(i, p):
        name = p["name"][:38] + ".." if len(p["name"]) > 40 else p["name"]
        shop = p["shop_name"][:16] + ".." if len(p["shop_name"]) > 18 else p["shop_name"]
        return f"| {i+1:>3} | {name:<40} | {p['price']:>8.2f} | {p['original_price']:>8.2f} | {p['platform']:<6} | {shop:<16} | {p['shop_score']:>4.1f} | {p['sales']:>8} |"
    
    # 打印表头
    header = f"| {'序号':>3} | {'商品名称':<40} | {'价格':>8} | {'原价':>8} | {'平台':<6} | {'店铺':<16} | {'评分':>4} | {'月销':>8} |"
    sep = f"|{'-'*5}|{'-'*42}|{'-'*10}|{'-'*10}|{'-'*8}|{'-'*18}|{'-'*6}|{'-'*10}|"
    
    print()
    print(header)
    print(sep)
    
    display = products[:max_rows]
    for i, p in enumerate(display):
        print(format_row(i, p))
    
    if len(products) > max_rows:
        print(f"  ... 共 {len(products)} 条结果，仅显示前 {max_rows} 条")
    print()


def print_recommendations(recommendations: List[dict]):
    """打印推荐结果"""
    if not recommendations:
        return
    
    print("=" * 70)
    print("  性价比推荐 TOP 5（综合评分 = 40%价格 + 30%销量 + 20%店铺 + 10%折扣）")
    print("=" * 70)
    
    for r in recommendations:
        print(f"\n  #{r['rank']}  综合评分: {r['score']:.3f}")
        print(f"  商品: {r['name']}")
        print(f"  价格: {r['price']}元  |  平台: {r['platform']}  |  店铺: {r['shop_name']}")
        print(f"  月销: {r['sales']}  |  评分: {r['shop_score']}  |  标签: {', '.join(r['tags'])}")


def print_stats(result: dict):
    """打印统计信息"""
    print(f"\n{'─' * 50}")
    print(f"  采集关键词: {result['keyword']}")
    print(f"  去重后商品: {result['total']} 件")
    print(f"  采集耗时: {result['time_elapsed']}s")
    print(f"{'─' * 50}")
    
    pr = result["price_range"]
    print(f"  价格区间: {pr['min']:.2f} ~ {pr['max']:.2f} 元")
    print(f"  平均价格: {pr['avg']:.2f} 元")
    print(f"  中位价格: {pr['median']:.2f} 元")
    
    print(f"\n  各平台数据:")
    for plat, stat in result["platform_stats"].items():
        print(f"    {plat}: {stat['count']}件, 均价{stat['avg_price']}元, 最低{stat['min_price']}元")


def main():
    parser = argparse.ArgumentParser(
        description="电商商品价格自动化采集与对比工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("-p", "--platforms", nargs="+", choices=["京东", "淘宝", "拼多多"],
                        default=["京东", "淘宝", "拼多多"], help="指定采集平台")
    parser.add_argument("-n", "--num", type=int, default=30, help="显示条数 (默认30)")
    parser.add_argument("-o", "--output", type=str, help="输出JSON文件路径")
    parser.add_argument("--json", action="store_true", help="仅输出JSON格式")
    
    args = parser.parse_args()
    
    print_banner()
    print(f"\n> 正在搜索: {args.keyword}")
    print(f"> 采集平台: {', '.join(args.platforms)}")
    print(f"> 请稍候...\n")
    
    # 执行采集
    from engine import CollectorEngine
    engine = CollectorEngine(platforms=args.platforms)
    result = engine.collect(args.keyword)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 打印统计
    print_stats(result)
    
    # 打印商品表格
    print_table(result["products"], max_rows=args.num)
    
    # 打印推荐
    print_recommendations(result["recommendations"])
    
    # 保存JSON
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n> 结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
