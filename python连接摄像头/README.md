
# TP-Link 摄像头连接工具

本项目提供多种方法连接 TP-Link 摄像头。

## 文件说明

- `test.py` - 通过 TP-Link 云平台获取设备列表
- `camera_rtsp.py` - 使用已知 IP 地址通过 RTSP 连接摄像头
- `camera_scanner.py` - 自动扫描局域网内的摄像头

## 安装依赖

```bash
pip install opencv-python
```

## 使用方法

### 方法一：自动扫描（推荐）

如果您不知道摄像头的 IP 地址，使用 `camera_scanner.py`：

```bash
python camera_scanner.py
```

程序会：
1. 自动扫描整个局域网
2. 尝试多种常见的 RTSP 地址格式
3. 列出所有发现的摄像头
4. 让您选择并连接

### 方法二：已知 IP 连接

如果您知道摄像头的 IP 地址，使用 `camera_rtsp.py`：

1. 编辑文件中的配置：
```python
PASSWORD = "你的摄像头密码"
CAMERA_IP = "192.168.1.100"
```

2. 运行：
```bash
python camera_rtsp.py
```

### 方法三：使用云平台

使用 `test.py` 通过 TP-Link 云平台获取设备列表：

1. 编辑文件中的配置：
```python
USERNAME = "你的TP-Link账号邮箱"
PASSWORD = "你的TP-Link账号密码"
```

2. 运行：
```bash
python test.py
```

## 常见 RTSP 地址格式

### TP-Link
- 主码流: `rtsp://admin:password@192.168.1.100:554/stream1`
- 子码流: `rtsp://admin:password@192.168.1.100:554/stream2`

### 海康威视
- `rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101`

### 大华
- `rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&amp;subtype=0`

## 获取摄像头 IP 的方法

1. **查看路由器设备列表** - 登录路由器管理界面查看已连接设备
2. **使用 TP-Link Kasa/Tapo APP** - 在 APP 中查看设备信息
3. **使用网络扫描工具** - 如 Advanced IP Scanner
4. **使用本工具自动扫描** - 运行 `camera_scanner.py`

## 启用摄像头 RTSP 服务

某些摄像头需要手动启用 RTSP 服务：

1. 通过浏览器访问摄像头的 Web 管理界面
2. 登录后找到"网络设置"或"媒体设置"
3. 找到 RTSP 选项并启用
4. 记录下 RTSP 端口（默认 554）

## 故障排除

如果无法连接摄像头，请检查：

1. 摄像头是否已通电并连接到网络
2. 电脑与摄像头是否在同一局域网
3. 用户名和密码是否正确
4. RTSP 服务是否已启用
5. 防火墙是否阻止了连接

## 快捷键

- `q` - 退出视频播放窗口

