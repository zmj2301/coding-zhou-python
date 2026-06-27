import http.server
import socketserver
import urllib.parse
import time

class TestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        params = urllib.parse.parse_qs(parsed.query)
        
        print(f"[TEST] GET path='{path}'")
        
        if path == '/api/files/tree':
            print(f"[TEST] matched /api/files/tree")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "route": "/api/files/tree"}')
            return
        elif path == '/api/likes':
            print(f"[TEST] matched /api/likes")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "route": "/api/likes"}')
            return
        elif path == '/api/screen/health':
            print(f"[TEST] matched /api/screen/health")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "route": "/api/screen/health", "ok": true}')
            return
        elif path == '/api/screen/stream':
            print(f"[TEST] matched /api/screen/stream")
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            return
        elif path == '/api/screen/shot':
            print(f"[TEST] matched /api/screen/shot")
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.end_headers()
            self.wfile.write(b'fake_image_data')
            return
        elif path == '/api/comments/counts':
            print(f"[TEST] matched /api/comments/counts")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "route": "/api/comments/counts"}')
            return
        else:
            print(f"[TEST] NO MATCH for path='{path}' - returning 404")
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "page not found"}')
            return

    def log_message(self, format, *args):
        pass

PORT = 18765
with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
    print(f"Test server running at http://127.0.0.1:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
