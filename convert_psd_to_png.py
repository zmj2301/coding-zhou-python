"""
批量将 .psd 文件转换为 .png（保留图层合并后的完整图像）
用法：python convert_psd_to_png.py [目录1] [目录2] ...
若不指定目录，自动扫描整个 Python 项目下所有 assets/ 和 images/ 目录。
"""

import os
import sys
import glob

# psd-tools 库
try:
    from psd_tools import PSDImage
except ImportError:
    print("[!] 请先安装: pip install psd-tools pillow")
    sys.exit(1)

from PIL import Image


def merge_psd_to_pil(psd_path):
    """将 PSD 所有图层合并为一张 PIL Image"""
    psd = PSDImage.open(psd_path)
    # 合并所有图层
    merged = psd.composite()
    return merged


def convert_psd(psd_path):
    """转换单个 PSD，返回输出的 PNG 路径"""
    png_path = os.path.splitext(psd_path)[0] + '.png'
    try:
        img = merge_psd_to_pil(psd_path)
        # 确保是 RGB 模式（不含 alpha 则直接保存）
        if img.mode == 'RGBA':
            img.save(png_path)
        else:
            img.convert('RGB').save(png_path)
        return png_path
    except Exception as e:
        return None


def find_psd_files(paths):
    """递归查找指定目录下的 .psd 文件"""
    psd_files = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                # 跳过一些目录
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env']]
                for f in files:
                    if f.lower().endswith('.psd'):
                        psd_files.append(os.path.join(root, f))
        elif os.path.isfile(p):
            psd_files.append(p)
    return psd_files


def main():
    # 待转换的 PSD 源目录（去重：只处理原始位置，不处理 public/ 和 code-explorer/ 的副本）
    exclude_patterns = ['\\public\\', '\\code-explorer\\', '02 侯老师编程网站相关素材']

    if len(sys.argv) > 1:
        # 用户指定了目录
        psd_files = find_psd_files(sys.argv[1:])
    else:
        # 自动扫描整个 Python 目录下的 assets/ 和 images/interface/ 目录
        base = 'e:\\coding-zhou\\Python'
        psd_files = find_psd_files([base])
        # 过滤副本
        psd_files = [f for f in psd_files
                     if not any(p in f for p in exclude_patterns)]

    if not psd_files:
        print("[!] 未找到 .psd 文件")
        return

    print(f"[*] 找到 {len(psd_files)} 个 .psd 文件，开始转换...\n")

    success = 0
    failed = 0

    for psd_path in sorted(set(psd_files)):
        print(f"  转换: {os.path.basename(psd_path)}...", end=' ')
        result = convert_psd(psd_path)
        if result:
            # 检查文件大小，过小的可能是空图
            size = os.path.getsize(result)
            if size > 1000:
                print(f"-> {os.path.basename(result)} ({size:,} bytes)")
                success += 1
            else:
                print(f"失败（文件过小 {size} bytes，可能是空图层）")
                failed += 1
        else:
            print("失败")
            failed += 1

    print(f"\n[*] 完成: {success} 成功, {failed} 失败")


if __name__ == '__main__':
    main()
