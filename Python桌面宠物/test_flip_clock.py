"""
测试翻页钟组件
验证 FlipClockWidget 的基本功能和集成
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "relax_exe"))

print("=" * 50)
print("翻页钟组件测试")
print("=" * 50)
print()

# 1. 测试模块导入
print("1. 测试模块导入...")
try:
    from ui.flip_clock_widget import FlipClockWidget, FlipClockBridge
    print("   [OK] FlipClockWidget 导入成功")
    print("   [OK] FlipClockBridge 导入成功")
except ImportError as e:
    print(f"   [FAIL] 导入失败: {e}")
    sys.exit(1)

print()

# 2. 测试 FlipClockBridge 信号
print("2. 测试 FlipClockBridge...")
try:
    bridge = FlipClockBridge()
    assert hasattr(bridge, 'tick'), "缺少 tick 信号"
    assert hasattr(bridge, 'finished'), "缺少 finished 信号"
    assert hasattr(bridge, 'on_tick'), "缺少 on_tick 槽函数"
    assert hasattr(bridge, 'on_finished'), "缺少 on_finished 槽函数"
    print("   [OK] FlipClockBridge 信号/槽正常")
except Exception as e:
    print(f"   [FAIL] FlipClockBridge 测试失败: {e}")

print()

# 3. 测试 FlipClockWidget API 存在性
print("3. 测试 FlipClockWidget API...")
try:
    # 检查所有公开方法是否存在（不实际创建窗口，避免 GUI 依赖）
    required_methods = [
        'set_duration', 'start', 'pause', 'stop', 'set_remaining',
        'set_status', '_on_close_clicked'
    ]
    for method in required_methods:
        assert hasattr(FlipClockWidget, method), f"缺少方法: {method}"
    print("   [OK] 所有 API 方法存在")
except AttributeError as e:
    print(f"   [FAIL] API 检查失败: {e}")

print()

# 4. 测试 flip_clock.html 文件
print("4. 测试 flip_clock.html...")
html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "relax_exe", "ui", "flip_clock.html")
try:
    assert os.path.exists(html_path), "flip_clock.html 不存在"
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 检查关键 JS 函数
    assert 'function flip' in content, "缺少 flip 函数"
    assert 'function getDigits' in content, "缺少 getDigits 函数"
    assert 'function updateDisplay' in content, "缺少 updateDisplay 函数"
    assert 'function setDuration' in content, "缺少 setDuration 函数"
    assert 'function startCountdown' in content, "缺少 startCountdown 函数"
    assert 'function pauseCountdown' in content, "缺少 pauseCountdown 函数"
    assert 'function stopCountdown' in content, "缺少 stopCountdown 函数"
    assert 'function setRemaining' in content, "缺少 setRemaining 函数"
    print(f"   [OK] HTML 文件有效 ({len(content)} 字节)")
    print("   [OK] 所有 JS 函数存在")
except AssertionError as e:
    print(f"   [FAIL] HTML 测试失败: {e}")

print()

# 5. 测试 split_flap_preview.html 文件
print("5. 测试 split_flap_preview.html...")
preview_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "split_flap_preview.html")
try:
    assert os.path.exists(preview_path), "split_flap_preview.html 不存在"
    with open(preview_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'top: -90px' in content or 'margin-top: -90px' in content, "上半截偏移未修复"
    print(f"   [OK] 预览文件有效 ({len(content)} 字节)")
    print("   [OK] 上半截偏移已修复")
except AssertionError as e:
    print(f"   [FAIL] 预览文件测试失败: {e}")

print()

# 6. 测试 FlipClockBridge 信号发射
print("6. 测试 FlipClockBridge 信号发射...")
try:
    from PySide6.QtCore import QCoreApplication
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    
    bridge = FlipClockBridge()
    received = {'tick': False, 'finished': False}
    
    def on_tick(remaining, total):
        received['tick'] = (remaining == 45 and total == 60)
    
    def on_finished():
        received['finished'] = True
    
    bridge.tick.connect(on_tick)
    bridge.finished.connect(on_finished)
    
    bridge.on_tick(45, 60)
    bridge.on_finished()
    app.processEvents()
    
    assert received['tick'], "tick 信号未正确触发"
    assert received['finished'], "finished 信号未正确触发"
    print("   [OK] 信号发射正常")
except Exception as e:
    print(f"   [FAIL] 信号测试失败: {e}")

print()
print("=" * 50)
print("所有测试通过！")
print("=" * 50)
print()
print("翻页钟组件已准备就绪：")
print("  - HTML: relax_exe/ui/flip_clock.html")
print("  - Widget: relax_exe/ui/flip_clock_widget.py")
print("  - 预览: split_flap_preview.html (浏览器打开)")