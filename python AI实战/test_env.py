# 实时人脸检测示例（使用Haar级联）
import cv2

# 加载预训练的人脸检测分类器
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 打开摄像头
cap = cv2.VideoCapture(0)

while True:
    # 读取视频帧
    ret, frame = cap.read()
    if not ret:
        break
    
    # 转换为灰度图像以提高检测效率
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 检测人脸
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    
    # 绘制检测结果
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # 显示结果
    cv2.imshow('Face Detection', frame)
    
    # 按ESC键退出
    if cv2.waitKey(1) == 27:
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()