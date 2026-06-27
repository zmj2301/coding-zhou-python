import cv2
import threading
import time
from tkinter import Tk, Label, Button, Frame, Canvas
from PIL import Image, ImageTk
import pyaudio
import numpy as np
from queue import Queue, Empty

class VideoCall:
    def __init__(self, contact_name="联系人"):
        self.contact_name = contact_name
        self.running = False
        self.root = None
        self.canvas_local = None
        self.canvas_remote = None
        self.cap = None
        self.photo_local = None
        self.photo_remote = None
        
        # 音频相关
        self.audio_stream = None
        self.audio_p = None
        self.audio_queue = Queue()
        self.audio_thread = None
        
        # 人脸检测
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def start_call(self):
        """启动视频通话"""
        self.running = True
        
        # 初始化 GUI
        self.root = Tk()
        self.root.title(f"视频通话 - {self.contact_name}")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a2e")
        
        # 顶部状态栏
        status_frame = Frame(self.root, bg="#16213e", height=50)
        status_frame.pack(fill="x", side="top")
        status_frame.pack_propagate(False)
        
        status_label = Label(status_frame, text=f"正在与 {self.contact_name} 通话中...", 
                            bg="#16213e", fg="#e94560", font=("Arial", 12, "bold"))
        status_label.pack(pady=10)
        
        # 视频区域
        video_frame = Frame(self.root, bg="#0f3460")
        video_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 本地视频（小窗口）
        local_frame = Frame(video_frame, bg="#1a1a2e")
        local_frame.place(relx=0.02, rely=0.02, relwidth=0.25, relheight=0.25)
        
        Label(local_frame, text="本地视频", bg="#1a1a2e", fg="white", font=("Arial", 10)).pack(pady=2)
        self.canvas_local = Canvas(local_frame, bg="black")
        self.canvas_local.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 远程视频（大窗口）
        remote_frame = Frame(video_frame, bg="#1a1a2e")
        remote_frame.pack(fill="both", expand=True)
        
        Label(remote_frame, text=f"{self.contact_name}", bg="#1a1a2e", fg="white", font=("Arial", 14)).pack(pady=5)
        self.canvas_remote = Canvas(remote_frame, bg="black")
        self.canvas_remote.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 底部控制栏
        control_frame = Frame(self.root, bg="#16213e", height=80)
        control_frame.pack(fill="x", side="bottom")
        control_frame.pack_propagate(False)
        
        # 挂断按钮
        hangup_btn = Button(control_frame, text="挂断通话", command=self.end_call,
                          bg="#e94560", fg="white", font=("Arial", 12, "bold"),
                          width=15, height=2, relief="flat")
        hangup_btn.pack(side="right", padx=30, pady=15)
        
        # 静音按钮
        self.muted = False
        self.mute_btn = Button(control_frame, text="静音", command=self.toggle_mute,
                             bg="#533483", fg="white", font=("Arial", 10),
                             width=10, height=2, relief="flat")
        self.mute_btn.pack(side="right", padx=10, pady=15)
        
        # 摄像头切换按钮
        self.camera_on = True
        self.camera_btn = Button(control_frame, text="关闭摄像头", command=self.toggle_camera,
                               bg="#533483", fg="white", font=("Arial", 10),
                               width=12, height=2, relief="flat")
        self.camera_btn.pack(side="right", padx=10, pady=15)
        
        # 打开摄像头
        self.cap = cv2.VideoCapture(0)
        
        # 启动音频
        self.start_audio()
        
        # 开始更新视频
        self.update_video()
        
        # 启动 GUI 主循环
        self.root.mainloop()
    
    def update_video(self):
        """更新视频帧"""
        if not self.running or not self.cap:
            return
        
        # 读取摄像头
        ret, frame = self.cap.read()
        if ret:
            # 镜像翻转
            frame = cv2.flip(frame, 1)
            
            # 人脸检测
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # 转换颜色空间（BGR -> RGB）
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 本地视频
            if self.camera_on:
                image = Image.fromarray(frame_rgb)
                image = image.resize((200, 150), Image.Resampling.LANCZOS)
                self.photo_local = ImageTk.PhotoImage(image)
                self.canvas_local.create_image(0, 0, image=self.photo_local, anchor="nw")
            
            # 远程视频（演示用，使用本地画面）
            image_remote = Image.fromarray(frame_rgb)
            image_remote = image_remote.resize((640, 480), Image.Resampling.LANCZOS)
            self.photo_remote = ImageTk.PhotoImage(image_remote)
            self.canvas_remote.create_image(0, 0, image=self.photo_remote, anchor="nw")
        
        # 继续更新
        if self.running:
            self.root.after(30, self.update_video)
    
    def start_audio(self):
        """启动音频处理"""
        self.audio_p = pyaudio.PyAudio()
        
        def audio_callback(in_data, frame_count, time_info, status):
            if not self.muted:
                self.audio_queue.put(in_data)
            return (in_data, pyaudio.paContinue)
        
        self.audio_stream = self.audio_p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            output=True,
            stream_callback=audio_callback,
            frames_per_buffer=4000
        )
        
        self.audio_stream.start_stream()
    
    def toggle_mute(self):
        """切换静音状态"""
        self.muted = not self.muted
        if self.muted:
            self.mute_btn.config(text="取消静音", bg="#e94560")
        else:
            self.mute_btn.config(text="静音", bg="#533483")
    
    def toggle_camera(self):
        """切换摄像头状态"""
        self.camera_on = not self.camera_on
        if self.camera_on:
            self.camera_btn.config(text="关闭摄像头", bg="#533483")
        else:
            self.camera_btn.config(text="打开摄像头", bg="#e94560")
            # 清空本地视频画面
            self.canvas_local.delete("all")
    
    def end_call(self):
        """结束通话"""
        self.running = False
        
        # 停止音频
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.audio_p:
            self.audio_p.terminate()
        
        # 释放摄像头
        if self.cap:
            self.cap.release()
        
        # 关闭窗口
        if self.root:
            self.root.destroy()
        
        print("通话已结束")


def make_call(contact_name):
    """
    发起视频通话
    :param contact_name: 联系人姓名
    """
    print(f"正在呼叫 {contact_name}...")
    call = VideoCall(contact_name)
    call.start_call()


if __name__ == "__main__":
    # 测试
    make_call("测试联系人")
