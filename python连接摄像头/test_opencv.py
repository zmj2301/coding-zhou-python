
import cv2

print("OpenCV版本:", cv2.__version__)
print("测试成功！")

# 测试一下简单的操作
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("\n摄像头已打开！")
    cap.release()
else:
    print("\n未找到本地摄像头，但这是正常的（我们要连接的是网络摄像头）")

cv2.destroyAllWindows()

