
import cv2
import time

def play_rtsp_stream(rtsp_url, window_name="Camera"):
    """
    播放RTSP视频流
    
    Args:
        rtsp_url: RTSP流地址
        window_name: 窗口名称
    """
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("无法打开视频流: %s" % rtsp_url)
        return False
    
    print("成功连接摄像头！按 'q' 退出...")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("视频帧率: %s FPS" % fps)
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("无法接收帧，连接可能中断...")
            break
        
        cv2.imshow(window_name, frame)
        
        if cv2.waitKey(1) &amp; 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True

def build_rtsp_url(username, password, ip, port=554, stream_type="stream1"):
    """
    构建RTSP URL
    
    Args:
        username: 摄像头用户名（默认admin）
        password: 摄像头密码
        ip: 摄像头IP地址
        port: RTSP端口（默认554）
        stream_type: stream1=主码流, stream2=子码流
    
    Returns:
        RTSP URL
    """
    return "rtsp://%s:%s@%s:%s/%s" % (username, password, ip, port, stream_type)

if __name__ == "__main__":
    print("TP-Link摄像头RTSP连接工具")
    print("=" * 50)
    
    USERNAME = "admin"  # TP-Link摄像头默认用户名
    PASSWORD = "你的摄像头密码"  # 请修改为您的摄像头密码
    CAMERA_IP = "192.168.1.100"  # 请修改为您摄像头的IP地址
    
    rtsp_url = build_rtsp_url(USERNAME, PASSWORD, CAMERA_IP)
    
    print("RTSP地址: %s" % rtsp_url)
    print("正在连接...")
    
    success = play_rtsp_stream(rtsp_url)
    
    if success:
        print("连接已结束")
    else:
        print("连接失败，请检查：")
        print("1. 摄像头IP地址是否正确")
        print("2. 用户名密码是否正确")
        print("3. 摄像头是否已启用RTSP服务")
        print("4. 电脑与摄像头是否在同一局域网")

