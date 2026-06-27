# 人脸表情分析工具
import cv2
import requests
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 全局变量
analysis_results = {}
current_frame = None
face_cascade = None

def draw_chinese_text(img, text, position, font_size=30, color=(255, 255, 255)):
    """在图像上绘制中文文本，支持自动换行"""
    # 将OpenCV图像转换为PIL图像
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # 使用用户指定的字体文件
    font_path = "E:\\coding-zhou\\font.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        try:
            font = ImageFont.truetype("msyh.ttc", font_size)  # 微软雅黑
        except:
            try:
                font = ImageFont.truetype("simsun.ttc", font_size)  # 宋体
            except:
                font = ImageFont.load_default()
    
    # 自动换行处理
    max_width = img.shape[1] - position[0] - 20  # 留出边距
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        # 获取文本边界框
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    
    if current_line:
        lines.append(current_line)
    
    # 绘制每一行文本
    x, y = position
    line_height = font_size + 5
    for i, line in enumerate(lines):
        # 绘制黑色描边
        draw.text((x+1, y+1 + i*line_height), line, font=font, fill=(0, 0, 0))
        # 绘制白色文字
        draw.text((x, y + i*line_height), line, font=font, fill=color)
    
    # 转换回OpenCV图像
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# 全局变量
analysis_results = {}
current_frame = None
face_cascade = None

def start_analysis(choice, image_path=None):
    """开始分析"""
    global current_frame, face_cascade
    
    if choice != "1" and choice != "2":
        messagebox.showerror("错误", "无效的选择，请重新输入")
        return

    # 智谱AI API配置
    API_KEY = os.environ.get('ZHIPUAI_API_KEY', '')  # 填写您自己的 APIKey
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    # 加载预训练的人脸检测分类器
    if face_cascade is None:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # 局部变量，用于存储分析结果
    local_analysis_results = {}

    # 确保text_image目录存在
    import os
    if not os.path.exists('text_image'):
        os.makedirs('text_image')
        print("创建text_image目录成功")

    # AI分析函数
    def analyze_face(image):
        """使用智谱AI分析人脸表情"""
        import base64
        
        # 将图像转换为base64
        _, buffer = cv2.imencode('.jpg', image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        # 请求体
        payload = {
            "model": "glm-4v",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请分析图片中人物的表情"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_base64
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.5,
            "max_tokens": 100
        }
        
        # 发送请求
        try:
            response = requests.post(
                BASE_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"分析失败: {str(e)}")
            return "分析失败"

    # 鼠标点击事件处理函数
    def mouse_callback(event, x, y, flags, param):
        global current_frame
        if event == cv2.EVENT_LBUTTONDOWN and current_frame is not None:
            print(f"点击位置: ({x}, {y})")  # 调试信息
            # 检测人脸
            gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            print(f"检测到的人脸数量: {len(faces)}")  # 调试信息
            
            # 检查点击位置是否在人脸区域内
            for (fx, fy, fw, fh) in faces:
                print(f"人脸区域: ({fx}, {fy}, {fw}, {fh})")  # 调试信息
                if fx <= x <= fx + fw and fy <= y <= fy + fh:
                    # 提取人脸区域
                    face_roi = current_frame[fy:fy+fh, fx:fx+fw]
                    # 分析表情
                    emotion = analyze_face(face_roi)
                    # 存储分析结果
                    local_analysis_results[(fx, fy, fw, fh)] = emotion
                    print(f"分析结果: {emotion}")
                    
                    # 保存整个屏幕到text_image目录
                    import time
                    timestamp = int(time.time())
                    save_path = f"text_image/screenshot_{timestamp}.jpg"
                    cv2.imwrite(save_path, current_frame)
                    print(f"屏幕已保存到: {save_path}")
                    break
    

    if choice == "1":
        # 尝试打开摄像头
        cap = None
        # 尝试不同的后端
        backends = [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]
        for backend in backends:
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                print(f"成功打开摄像头，使用后端: {backend}")
                break
        
        if not cap or not cap.isOpened():
            print("无法打开摄像头，切换到本地图片模式")
            choice = "2"

    if choice == "2":
        # 使用本地图片
        if image_path:
            current_frame = cv2.imread(image_path)
            if current_frame is not None:
                print(f"成功加载图片: {image_path}")
            else:
                print("无法加载图片，使用默认测试图片")
                current_frame = cv2.imread("test.jpg")
                if current_frame is None:
                    print("无法加载任何图片，程序退出")
                    exit()
        else:
            # 如果没有提供图片路径，列出当前目录下的图片文件
            print("请选择本地图片进行分析")
            image_files = [f for f in os.listdir('.') if f.endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            if image_files:
                print("可用的图片文件:")
                for i, img_file in enumerate(image_files):
                    print(f"{i+1}. {img_file}")
                # 尝试打开文件对话框让用户选择
                try:
                    from tkinter import filedialog
                    img_path = filedialog.askopenfilename(
                        title="选择图片文件",
                        filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")]
                    )
                    if img_path:
                        current_frame = cv2.imread(img_path)
                        if current_frame is not None:
                            print(f"成功加载图片: {img_path}")
                        else:
                            current_frame = cv2.imread("test.jpg")
                            if current_frame is None:
                                print("无法加载任何图片，程序退出")
                                exit()
                    else:
                        current_frame = cv2.imread("test.jpg")
                        if current_frame is None:
                            print("无法加载任何图片，程序退出")
                            exit()
                except:
                    # 如果tkinter不可用，使用input
                    img_choice = int(input("请选择图片编号: ")) - 1
                    if 0 <= img_choice < len(image_files):
                        img_path = image_files[img_choice]
                        current_frame = cv2.imread(img_path)
                        if current_frame is not None:
                            print(f"成功加载图片: {img_path}")
                        else:
                            current_frame = cv2.imread("test.jpg")
                            if current_frame is None:
                                print("无法加载任何图片，程序退出")
                                exit()
            else:
                print("当前目录没有图片文件，使用默认测试图片")
                current_frame = cv2.imread("test.jpg")

    # 创建窗口并设置鼠标回调
    cv2.namedWindow('Face Detection')
    cv2.setMouseCallback('Face Detection', mouse_callback)

    print("提示: 点击图片中的人脸区域进行表情分析")
    print("按ESC键退出")

    if choice == "1" and cap is not None:
        # 摄像头模式
        while True:
            # 读取视频帧
            ret, frame = cap.read()
            if not ret:
                break
            
            current_frame = frame.copy()
            
            # 转换为灰度图像以提高检测效率
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 检测人脸
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            print(f"[主循环] 检测到 {len(faces)} 个人脸, 已分析 {len(local_analysis_results)} 个")  # 调试信息
            
            # 绘制检测结果和分析结果
            for (x, y, w, h) in faces:
                # 绘制绿色矩形框
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # 检查是否与分析结果中的人脸匹配（使用中心点距离匹配）
                matched = False
                for (rx, ry, rw, rh) in local_analysis_results.keys():
                    # 计算中心点
                    cx1, cy1 = x + w//2, y + h//2
                    cx2, cy2 = rx + rw//2, ry + rh//2
                    # 计算距离
                    distance = ((cx1-cx2)**2 + (cy1-cy2)**2) ** 0.5
                    # 如果中心点距离小于阈值，认为是同一个人脸
                    if distance < max(w, h) * 0.5:
                        emotion = local_analysis_results[(rx, ry, rw, rh)]
                        # 使用新的中文绘制函数
                        frame = draw_chinese_text(frame, emotion, (x, y-40), font_size=30, color=(255, 255, 255))
                        matched = True
                        break
            
            # 显示结果
            cv2.imshow('Face Detection', frame)
            
            # 按ESC键退出
            if cv2.waitKey(1) == 27:
                break
        
        # 释放资源
        cap.release()
    else:
        # 图片模式
        while True:
            if current_frame is not None:
                frame = current_frame.copy()
                
                # 转换为灰度图像以提高检测效率
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 检测人脸
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                
                # 绘制检测结果和分析结果
                for (x, y, w, h) in faces:
                    # 绘制绿色矩形框
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # 检查是否与分析结果中的人脸匹配（使用中心点距离匹配）
                    matched = False
                    for (rx, ry, rw, rh) in local_analysis_results.keys():
                        # 计算中心点
                        cx1, cy1 = x + w//2, y + h//2
                        cx2, cy2 = rx + rw//2, ry + rh//2
                        # 计算距离
                        distance = ((cx1-cx2)**2 + (cy1-cy2)**2) ** 0.5
                        # 如果中心点距离小于阈值，认为是同一个人脸
                        if distance < max(w, h) * 0.5:
                            emotion = local_analysis_results[(rx, ry, rw, rh)]
                            # 使用新的中文绘制函数
                            frame = draw_chinese_text(frame, emotion, (x, y-40), font_size=30, color=(255, 255, 255))
                            matched = True
                            break
                
                # 显示结果
                cv2.imshow('Face Detection', frame)
            
            # 按ESC键退出
            if cv2.waitKey(1) == 27:
                break

    # 释放资源
    cv2.destroyAllWindows()

def main():
    root = tk.Tk()
    root.title("人脸表情分析工具")
    root.geometry("400x300")
    
    # 使用列表来存储选择的值，以便在函数间共享
    choice_value = [None]
    
    label = tk.Label(root, text="请选择模式:")
    label.pack(pady=10)
    
    # 创建下拉框，仅支持选择，不能修改文字
    mode_var = tk.StringVar()
    mode_var.set("使用摄像头进行实时分析")
    mode_choices = ["使用摄像头进行实时分析", "使用本地图片进行分析"]
    mode_menu = ttk.Combobox(root, values=mode_choices, textvariable=mode_var, state="readonly")
    mode_menu.pack(pady=10)
    
    # 使用列表来存储选择的图片路径，以便在函数间共享
    selected_image_path = [None]  # 使用列表来存储可变的值
    
    # 创建图片选择按钮（初始状态为禁用）
    def select_image():
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            selected_image_path[0] = file_path
            image_label.config(text=f"已选择: {os.path.basename(file_path)}")
    
    image_button = ttk.Button(root, text="选择图片", command=select_image)
    image_button.pack(pady=5)
    
    # 显示选择的图片路径
    image_label = tk.Label(root, text="未选择图片")
    image_label.pack(pady=5)
    
    # 创建开始按钮
    def on_start_click():
        mode_index = mode_choices.index(mode_var.get()) + 1
        choice_value[0] = str(mode_index)
        
        # 如果选择本地图片但没有选择文件，提示用户
        if mode_index == 2 and selected_image_path[0] is None:
            messagebox.showwarning("提示", "请先选择一张图片")
            return
        
        root.destroy()  # 关闭GUI窗口
        start_analysis(choice_value[0], selected_image_path[0])
    
    start_button = ttk.Button(root, text="开始分析", command=on_start_click)
    start_button.pack(pady=20)
    
    root.mainloop()
    
if __name__ == "__main__":
    main()
