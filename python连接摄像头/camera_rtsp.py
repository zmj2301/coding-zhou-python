
import cv2
import time
import socket
import urllib.parse

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

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return True

def build_rtsp_url(username, password, ip, port=554, stream_type="stream1"):
    """
    构建RTSP URL

    Args:
        username: 摄像头账号用户名（Tapo App 里自定义，不是 admin）
        password: 摄像头账号密码
        ip: 摄像头IP地址
        port: RTSP端口（默认554）
        stream_type: stream1=主码流, stream2=子码流

    Returns:
        RTSP URL
    """
    user = urllib.parse.quote(username, safe='')
    pwd = urllib.parse.quote(password, safe='')
    return "rtsp://%s:%s@%s:%s/%s" % (user, pwd, ip, port, stream_type)

def precheck_ip(ip, port=554):
    """预检IP与RTSP端口是否可达（避免卡在OpenCV超时上）"""
    if ip == "0.0.0.0":
        return False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((ip, port))
        return True
    except Exception:
        return False
    finally:
        s.close()

if __name__ == "__main__":
    print("TP-Link（Tapo/VIGI）摄像头 RTSP 连接工具")
    print("=" * 55)
    print("说明：")
    print("  · VIGI IPC 系列（如 TL-IPC683-EZ）：用户名 admin，密码是第一次激活时设的密码")
    print("  · Tapo 系列：用户名密码是在 Tapo App 里『高级设置 → 摄像头账号』创建的\n")

    USERNAME = input("用户名 [回车默认 admin]: ").strip() or "admin"
    PASSWORD = input("密码（激活/摄像头账号对应的密码）: ").strip()
    CAMERA_IP = input("摄像头IP地址(如 192.168.1.100): ").strip()
    stream = input("码流 [1=主码流高清, 2=子码流省带宽] 默认1: ").strip() or "1"
    stream_type = "stream1" if stream != "2" else "stream2"

    if not precheck_ip(CAMERA_IP):
        print("\n无法连通 %s:%d —— 请确认：")
        print("1. 电脑与摄像头是否在同一局域网")
        print("2. 摄像头IP地址是否正确")
        print("3. 路由器是否开启了端口隔离")
        print("4. 若在外地，请先建立 Tailscale 内网再使用本机IP")
        exit(1)

    rtsp_url = build_rtsp_url(USERNAME, PASSWORD, CAMERA_IP, stream_type=stream_type)

    print("\nRTSP地址: %s" % rtsp_url)
    print("正在连接...")

    success = play_rtsp_stream(rtsp_url)

    if success:
        print("连接已结束")
    else:
        print("\n连接失败，请检查：")
        print("1. 摄像头账号用户名密码是否正确（Tapo App → 高级设置 → 摄像头账号）")
        print("2. 摄像头是否已启用RTSP服务")
        print("3. 若摄像头是电池供电款（如C410/C420/C425/D230），RTSP可能不支持")
        print("4. 电脑与摄像头是否在同一局域网")

