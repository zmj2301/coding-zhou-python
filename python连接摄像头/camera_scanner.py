
import cv2
import socket
import ipaddress
import threading
import time

def get_local_ip_range():
    """获取本地网络的IP范围"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        network = ipaddress.IPv4Network("%s/24" % local_ip, strict=False)
        return [str(ip) for ip in network.hosts()]
    except Exception as e:
        print("获取网络范围失败: %s" % e)
        return []

def scan_ip(ip, results, username="admin", password=""):
    """扫描单个IP是否有摄像头"""
    try:
        rtsp_urls = [
            "rtsp://%s:%s@%s:554/stream1" % (username, password, ip),
            "rtsp://%s:%s@%s:554/stream2" % (username, password, ip),
            "rtsp://%s:%s@%s:554/cam/realmonitor?channel=1&amp;subtype=0" % (username, password, ip),
            "rtsp://%s:%s@%s:554/Streaming/Channels/101" % (username, password, ip),
        ]
        
        for rtsp_url in rtsp_urls:
            cap = cv2.VideoCapture(rtsp_url)
            if cap.isOpened():
                print("✓ 发现摄像头: %s" % ip)
                results.append({
                    "ip": ip,
                    "url": rtsp_url,
                    "username": username,
                    "password": password
                })
                cap.release()
                return
            cap.release()
    except Exception as e:
        pass

def scan_network(username="admin", password="", max_threads=50):
    """扫描整个局域网"""
    print("=" * 60)
    print("开始扫描局域网内的摄像头...")
    print("=" * 60)
    
    ip_list = get_local_ip_range()
    if not ip_list:
        print("无法获取本地网络范围")
        return []
    
    print("正在扫描 %s 个IP地址..." % len(ip_list))
    
    results = []
    threads = []
    
    for i in range(0, len(ip_list), max_threads):
        batch = ip_list[i:i + max_threads]
        
        for ip in batch:
            t = threading.Thread(target=scan_ip, args=(ip, results, username, password))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        if (i + max_threads) % 200 == 0:
            print("已扫描 %s 个IP，已发现 %s 个摄像头" % (i + max_threads, len(results)))
    
    print("\n扫描完成！共发现 %s 个摄像头" % len(results))
    return results

def play_rtsp_stream(rtsp_url, window_name="Camera"):
    """播放RTSP视频流"""
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("无法打开视频流: %s" % rtsp_url)
        return False
    
    print("成功连接！按 'q' 退出")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) &amp; 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    print("摄像头自动发现工具")
    print("=" * 60)
    
    USERNAME = "admin"
    PASSWORD = ""
    
    print("默认用户名: %s" % USERNAME)
    print("请输入摄像头密码（如果为空直接回车）:")
    try:
        PASSWORD = raw_input().strip()
    except NameError:
        # Python 3
        PASSWORD = input().strip()
    except KeyboardInterrupt:
        print("\n操作已取消")
        exit()
    
    cameras = scan_network(USERNAME, PASSWORD)
    
    if not cameras:
        print("\n未发现摄像头，请检查:")
        print("1. 摄像头是否已连接到网络")
        print("2. 用户名密码是否正确")
        print("3. 电脑与摄像头是否在同一局域网")
        print("4. 摄像头是否已启用RTSP服务")
    else:
        print("\n发现的摄像头列表:")
        print("-" * 60)
        for i, cam in enumerate(cameras, 1):
            print("%s. IP: %s" % (i, cam['ip']))
            print("   URL: %s" % cam['url'])
        
        print("\n请选择要连接的摄像头编号（输入0退出）:")
        try:
            try:
                choice = int(raw_input().strip())
            except NameError:
                # Python 3
                choice = int(input().strip())
            
            if choice == 0:
                print("退出")
                exit()
            if 1 &lt;= choice &lt;= len(cameras):
                selected_cam = cameras[choice - 1]
                print("\n正在连接 %s..." % selected_cam['ip'])
                play_rtsp_stream(selected_cam['url'], "Camera %s" % selected_cam['ip'])
            else:
                print("无效的选择")
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            print("\n操作已取消")

