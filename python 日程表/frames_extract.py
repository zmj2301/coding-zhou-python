# -*- coding: utf-8 -*-
"""用 opencv 读 mp4，均匀抽帧存为 PNG。"""
import os
import cv2

IN = r"D:\xwechat_files\wxid_ild90ortr7wy22_1fb5\msg\video\2026-10\db85b4c5e88581996a7c14ad0b7cb0ea.mp4"
OUT = r"E:\tf"
os.makedirs(OUT, exist_ok=True)

cap = cv2.VideoCapture(IN)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
dur = total / fps if fps else 8.5
print("fps=%s frames=%s dur=%s" % (fps, total, dur))

TIMES = [round(dur * i / 8, 2) for i in range(9)]  # 9 帧覆盖全程
ok_count = 0
for t in TIMES:
    cap.set(cv2.CAP_PROP_POS_MSEC, int(t * 1000))
    ret, frame = cap.read()
    if not ret or frame is None:
        print("FAIL @%.2fs" % t)
        continue
    # 旋转：竖屏手机录屏通常是旋转的，这里直接保存，再人工看
    cv2.imwrite("%s/f_%05d.png" % (OUT, int(t * 1000)), frame)
    print("OK @%.2fs -> %s" % (t, (frame.shape[1], frame.shape[0])))
    ok_count += 1
cap.release()
print("done, ok=%d" % ok_count)
