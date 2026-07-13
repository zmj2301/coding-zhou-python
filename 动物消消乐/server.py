from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import webbrowser

POST = 8800

handler = SimpleHTTPRequestHandler
with TCPServer(("", POST),handler) as httpd:
    print(f"本地服务已启动，端口：{POST}，访问地址：http://localhost:{POST}")
    # webbrowser.open(f"http://localhost:{POST}")
    httpd.serve_forever()