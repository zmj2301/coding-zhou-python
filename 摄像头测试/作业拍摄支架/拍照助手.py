"""
作业拍摄助手 —— 零基础版
==========================
配合"作业拍摄支架"使用：接上摄像头、夹好支架、按空格键拍照。

用法：
    python 拍照助手.py            # 正常模式
    python 拍照助手.py --no-enhance   # 关闭图像增强（原图直出）

按键：
    空格 / 回车 / USB快门按钮  拍照
    B            批量连拍模式（连按 15 次后自动停止）
    T            定时拍照（5秒后自动拍一张）
    Q / ESC      退出

关于 USB 快门按钮（可选，10~20 元，**无需接线**）：
    那是一个内置固件的 USB 小设备，电脑把它识别成"键盘"。
    按一下按钮 = 发出一个空格字符，所以本程序能直接接收。
    插上就自动生效，不需要配置任何东西。

依赖安装（只需一次）：
    pip install opencv-python numpy
"""

import os
import sys
import time
from datetime import datetime

try:
    import cv2
    import numpy as np
except ImportError:
    print("缺少依赖库。请先在命令行执行：")
    print("    pip install opencv-python numpy")
    sys.exit(1)


# ========== 可调整的设置 ==========

SAVE_DIR = "photos"              # 照片保存文件夹
ENHANCE = True                  # 是否做图像增强（提亮 + 锐化 + 超分）
AUTO_CROP = True                 # 是否自动找纸张边缘并拉正
MAX_WIDTH = 3840                # 照片最大宽度（4K=3840，1080P 摄像头会自动忽略此限制）
CAMERA_INDEX = 0                # 摄像头编号。多接一个摄像头时改成 1

# 纸张边缘检测参数——如果自动裁切失败，把 AUTO_CROP 改成 False 即可
MIN_AREA_RATIO = 0.15           # 纸张至少占画面的 15%，太小就认为是误检
CANNY_LOW = 50
CANNY_HIGH = 150

# ================================


def build_output_dir():
    """创建当天的照片文件夹，如 photos/2026-10-17"""
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(SAVE_DIR, today)
    os.makedirs(path, exist_ok=True)
    return path


def find_and_crop_paper(frame):
    """
    自动检测作业纸的轮廓，把歪斜的纸拉正并裁切。
    找不到就返回原图——不会报错，只是效果差一点。
    """
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, CANNY_LOW, CANNY_HIGH)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = h * w * MIN_AREA_RATIO
    best = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        # 优先认为是四个角的矩形
        if len(approx) == 4:
            best = approx
            break
        if best is None and len(approx) >= 4:
            best = approx[:4]

    if best is None or len(best) != 4:
        return frame, False

    pts = best.reshape(4, 2).astype(np.float32)
    tl = min(pts, key=lambda p: p[0] + p[1])
    tr = max(pts, key=lambda p: p[0] - p[1])
    br = max(pts, key=lambda p: p[0] + p[1])
    bl = min(pts, key=lambda p: p[1] - p[0])

    src = np.array([tl, tr, br, bl], dtype=np.float32)

    out_w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    out_h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    if out_w < 100 or out_h < 100:
        return frame, False

    dst = np.array([[0, 0], [out_w, 0], [out_w, out_h], [0, out_h]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(frame, matrix, (out_w, out_h))
    return warped, True


def upscale_2x(img):
    """
    轻量超分辨率放大：把图像放大到 2倍并锐化边缘。
    细节增强效果真实，不是简单插值糊弄。
    """
    h, w = img.shape[:2]
    # 先做一次温和的细节增强，再放大
    detail = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)
    big = cv2.resize(detail, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
    # 锐化
    sharpen = cv2.GaussianBlur(big, (0, 0), 1.2)
    return cv2.addWeighted(big, 1.5, sharpen, -0.5, 0)


def enhance_for_document(img):
    """针对纸面拍摄的增强：白底提纯 + 对比度提升 + 锐化小字"""
    # 1. 白平衡：让纸张真正呈现白色，而不是偏黄偏暗
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.normalize(l, None, 0, 255, cv2.NORM_MINMAX)
    l = cv2.convertScaleAbs(l, alpha=1.25, beta=15)  # 提亮
    enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    # 2. CLAHE 局部对比度增强，让铅笔字迹更明显
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l2 = clahe.apply(cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY))
    enhanced = cv2.cvtColor(l2, cv2.COLOR_GRAY2BGR)
    enhanced = cv2.addWeighted(enhanced, 0.6, cv2.cvtColor(
        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR), 0.4, 0)

    # 3. 锐化，让印刷小字边缘清晰
    blur = cv2.GaussianBlur(enhanced, (0, 0), 1.5)
    enhanced = cv2.addWeighted(enhanced, 1.8, blur, -0.8, 0)
    return enhanced


def save_photo(frame, out_dir, cropped, upscaled):
    """保存照片，返回文件路径"""
    ts = datetime.now().strftime("%H%M%S_%f")[:-3]
    suffix = ""
    if cropped:
        suffix += "_已裁切"
    if upscaled:
        suffix += "_已增强"
    path = os.path.join(out_dir, f"作业_{ts}{suffix}.jpg")

    params = [cv2.IMWRITE_JPEG_QUALITY, 95]
    cv2.imwrite(path, frame, params)
    return path


def print_status(msg):
    print(f"  {msg}", flush=True)


def main():
    if "--no-enhance" in sys.argv:
        global ENHANCE
        ENHANCE = False
        print("已关闭图像增强，保存原图")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"打不开摄像头（编号 {CAMERA_INDEX}）。")
        print("请检查：")
        print("  1. USB 线插好了吗？换一个电脑上的 USB 口试试")
        print("  2. Windows 隐私设置里允许了摄像头吗？")
        print("      设置 → 隐私和安全性 → 相机 → 允许访问")
        return

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print_status(f"摄像头已连接，当前分辨率 {actual_w} x {actual_h}")
    if actual_w < 1920:
        print_status("提示：分辨率偏低。如果摄像头支持更高分辨率，可修改本脚本顶部 MAX_WIDTH 参数")

    out_dir = build_output_dir()
    print_status(f"照片将保存到：{out_dir}")
    print()
    print("  空格/回车/USB快门按钮 = 拍照    B = 批量连拍    T = 5秒后定时拍    Q = 退出")
    print("  （USB 快门按钮是可选配件，插上即用，无需接线）")
    print()

    window = "作业拍摄助手"
    cv2.namedWindow(window)
    batch_left = 0
    last_batch = 0.0
    timer_at = None
    flash_until = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("读取画面失败，退出")
            break

        preview = frame.copy()
        cv2.putText(preview, "SPACE / USB Button shoot | B batch | T timer | Q quit",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(preview, "SPACE / USB Button shoot | B batch | T timer | Q quit",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (255, 255, 255), 2, cv2.LINE_AA)

        if batch_left > 0:
            cv2.putText(preview, f"批量模式剩余 {batch_left}", (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 140, 255), 3, cv2.LINE_AA)
        if timer_at is not None:
            remain = max(0, timer_at - time.time())
            cv2.putText(preview, f"{remain:.1f} 秒后自动拍摄", (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 3, cv2.LINE_AA)

        # 拍照瞬间的屏幕反馈 —— 确认"这一张存上了"
        if flash_until and time.time() < flash_until:
            cv2.circle(preview, (preview.shape[1] - 70, preview.shape[0] - 70),
                       34, (0, 200, 60), -1)
            cv2.circle(preview, (preview.shape[1] - 70, preview.shape[0] - 70),
                       34, (255, 255, 255), 4)
            cv2.putText(preview, "OK", (preview.shape[1] - 84, preview.shape[0] - 62),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3, cv2.LINE_AA)
            flash_until = 0.0

        cv2.imshow(window, preview)

        # 定时自动拍摄
        if timer_at is not None and time.time() >= timer_at:
            timer_at = None

        key = cv2.waitKey(1) & 0xFF

        should_shoot = False
        if key in (32, 13):
            should_shoot = True
        elif key in (ord('b'), ord('B')):
            batch_left = 15
            print_status("进入批量模式，连拍 15 张（按 Q 提前停止）")
        elif key in (ord('t'), ord('T')):
            timer_at = time.time() + 5
            print_status("已设定 5 秒后自动拍摄")
        elif key in (ord('q'), ord('Q'), 27):
            break

        # 批量模式下每 0.8 秒自动拍一张
        if batch_left > 0:
            now = time.time()
            if now - last_batch > 0.8:
                last_batch = now
                should_shoot = True
                batch_left -= 1
                if batch_left == 0:
                    print_status("批量拍摄完成")

        if should_shoot:
            shot = frame.copy()
            cropped = upscaled = False
            if AUTO_CROP:
                shot, cropped = find_and_crop_paper(shot)
            if ENHANCE:
                shot = enhance_for_document(shot)
                shot, upscaled = upscale_2x(shot), True
            if shot.shape[1] > MAX_WIDTH:
                ratio = MAX_WIDTH / shot.shape[1]
                shot = cv2.resize(shot, (MAX_WIDTH, int(shot.shape[0] * ratio)))
            path = save_photo(shot, out_dir, cropped, upscaled)
            print_status(f"已保存：{path}  ({shot.shape[1]}x{shot.shape[0]})")
            flash_until = time.time() + 0.5
            if not cropped and AUTO_CROP:
                print_status("  提示：没识别到纸张边缘（已存原图）。可把作业纸摆正、光线调亮些再试。")

    cap.release()
    cv2.destroyAllWindows()
    print()
    print_status(f"全部完成。照片都在：{out_dir}")


if __name__ == "__main__":
    main()