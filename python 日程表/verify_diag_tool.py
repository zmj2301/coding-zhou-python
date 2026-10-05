# -*- coding: utf-8 -*-
"""验证「配置诊断工具」能正确发现问题。

造几种典型故障场景，检查诊断报告是否都能指出问题：
  [1] 配置完全不存在（设置从没保存成功）
  [2] 配置 JSON 损坏
  [3] 配置存在但内容是旧值（被覆盖）
  [4] exe 目录残留旧配置、APPDATA 没有（迁移没生效）
  [5] Excel 数据文件指向已删除的路径
  [6] 正常场景：无异常告警
"""
import os
import sys
import io
import json
import time
import tempfile
import shutil
import importlib.util

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

spec = importlib.util.spec_from_file_location("diag_tool", "诊断工具.py")
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)

FAIL = []


def check(name, cond, extra=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, ("  " + extra) if extra else ""))
    if not cond:
        FAIL.append(name)


def run_case(title, setup, expect_markers, expect_clean=False):
    """搭一个场景、跑一次诊断、返回报告文本。"""
    print("=" * 76)
    print(title)
    print("=" * 76)
    tmp = tempfile.mkdtemp(prefix="diagcase_")
    cfg = os.path.join(tmp, "cfg")
    exedir = os.path.join(tmp, "exe")
    os.makedirs(cfg, exist_ok=True)
    os.makedirs(exedir, exist_ok=True)
    setup(cfg, exedir)
    # 让诊断工具认这个临时环境
    diag.settings_dir = lambda: cfg
    diag.app_dir = lambda: exedir
    text, saved = diag.main()
    for m in expect_markers:
        check("报告指出「%s」" % m, m in text)
    if expect_clean:
        check("无「严重」告警（正常场景）", "【严重】" not in text)
    if saved and os.path.exists(saved):
        os.remove(saved)
    shutil.rmtree(tmp, ignore_errors=True)
    return text


# ---------------------------------------------------------------- 场景 1
def setup1(cfg, exedir):
    pass  # 什么都不建：配置完全不存在


run_case("[1] 配置完全不存在", setup1,
         ["文件是否存在      ：否", "【严重】", "从来没保存成功过"])


# ---------------------------------------------------------------- 场景 2
def setup2(cfg, exedir):
    with io.open(os.path.join(cfg, diag.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
        f.write("{ this is not valid json ")


run_case("[2] 配置 JSON 损坏（诊断工具自身不能崩）", setup2,
         ["解析 JSON 失败", "【严重】", "JSON 解析失败"])


# ---------------------------------------------------------------- 场景 3
def setup3(cfg, exedir):
    # 配置存在但都是默认值 —— 说明用户的设置被覆盖回默认了
    data = dict(diag.DEFAULT_USER_SETTINGS)
    with io.open(os.path.join(cfg, diag.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))


t3 = run_case("[3] 配置存在但内容是默认值（疑似被覆盖）", setup3,
              ["桌面图标透明度  ：100%", "文件是否存在      ：是",
               "有别的程序/旧版本在覆盖它"])
# 配置存在时不应再出现「无配置文件」的字样（那会把两种故障混为一谈）
check("配置存在时不误报「无配置文件」", "（无配置文件" not in t3)


# ---------------------------------------------------------------- 场景 4
def setup4(cfg, exedir):
    # exe 目录有旧配置，APPDATA 没有 -> 迁移没生效
    data = dict(diag.DEFAULT_USER_SETTINGS)
    data['event_length'] = 333
    with io.open(os.path.join(exedir, diag.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))


run_case("[4] 旧配置在 exe 目录、新配置缺失（迁移未生效）", setup4,
         ["旧配置路径", "是否存在          ：是", "搬迁"])


# ---------------------------------------------------------------- 场景 5
def setup5(cfg, exedir):
    data = dict(diag.DEFAULT_USER_SETTINGS)
    data['user_data'] = [r"D:\不存在的路径\待办.xlsx"]
    with io.open(os.path.join(cfg, diag.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))


run_case("[5] Excel 数据文件已被删除", setup5,
         ["数据文件", "文件被移动/改名/删除了"])


# ---------------------------------------------------------------- 场景 6
def setup6(cfg, exedir):
    xlsx = os.path.join(cfg, "真实数据.xlsx")
    with open(xlsx, 'wb') as f:
        f.write(b'PK\x03\x04dummy')
    data = dict(diag.DEFAULT_USER_SETTINGS)
    data['user_data'] = [xlsx]
    data['window_opacity'] = 0.0
    data['text_size'] = 18
    data['event_length'] = 400
    data['auto_fit_box'] = False
    with io.open(os.path.join(cfg, diag.USER_SETTINGS_FILE), 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
    with io.open(os.path.join(cfg, 'error.log'), 'w', encoding='utf-8') as f:
        f.write("2026-10-02 10:00:00 读取 user_data.json 失败: 演示用\n")


t6 = run_case("[6] 正常场景（配置完整、Excel 在位）", setup6,
              ["桌面图标透明度  ：0%", "文字大小        ：18 px",
               "事件框长度      ：400 px", "白框自动加高    ：关",
               "演示用"],
              expect_clean=True)
check("Excel 存在时正确报「是」", "是否存在        ：是" in t6)
check("报告含旧配置残留检查段", "6. exe 目录里的旧配置" in t6)
check("报告含开机自启检查段", "8. 开机自动启动" in t6)

print("=" * 76)
print("汇总:", "全部通过 ✅" if not FAIL else "失败项 %s" % FAIL)
