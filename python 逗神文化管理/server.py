#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逗神归来视频学习平台 - 后端服务器
用于扫描本地视频文件并提供HTTP服务
"""

import os
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote

# 视频文件扩展名
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}

# 基础路径
BASE_DIR = Path(__file__).parent
VIDEO_ROOT = Path(r"e:\豆神归来文件资料")


class VideoRequestHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)
    
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        # API路由
        if parsed_path.path == '/api/videos':
            self.handle_get_videos()
        elif parsed_path.path.startswith('/video/'):
            self.handle_serve_video(parsed_path.path)
        else:
            # 静态文件
            super().do_GET()
    
    def handle_get_videos(self):
        """获取视频列表API"""
        videos = self.scan_videos()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {
            'success': True,
            'data': videos,
            'total': len(videos)
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_serve_video(self, path):
        """提供视频文件 - 支持流式传输和Range请求"""
        video_path = unquote(path[7:])  # 去掉 '/video/' 前缀
        full_path = VIDEO_ROOT / video_path
        
        if full_path.exists() and full_path.is_file():
            file_size = full_path.stat().st_size
            
            # 检查Range请求
            range_header = self.headers.get('Range')
            
            if range_header:
                # 处理Range请求
                byte1, byte2 = 0, file_size - 1
                if range_header.startswith('bytes='):
                    range_value = range_header[6:].split('-')
                    if range_value[0]:
                        byte1 = int(range_value[0])
                    if range_value[1]:
                        byte2 = int(range_value[1])
                
                length = byte2 - byte1 + 1
                
                # 发送206 Partial Content响应
                self.send_response(206)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(length))
                self.send_header('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    f.seek(byte1)
                    self.wfile.write(f.read(length))
            else:
                # 正常发送整个文件
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(file_size))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
    
    def scan_videos(self):
        """扫描视频文件"""
        videos = []
        video_id = 1
        
        if not VIDEO_ROOT.exists():
            return videos
        
        for root, dirs, files in os.walk(VIDEO_ROOT):
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                ext = file_path.suffix.lower()
                
                if ext in VIDEO_EXTENSIONS:
                    # 获取相对路径
                    rel_path = file_path.relative_to(VIDEO_ROOT)
                    
                    # 确定分类
                    category = self.get_category(rel_path.parts)
                    
                    videos.append({
                        'id': video_id,
                        'title': file_path.stem,
                        'category': category,
                        'path': str(rel_path).replace('\\', '/'),
                        'thumbnail': f'https://picsum.photos/id/{(video_id % 100) + 20}/640/360',
                        'duration': '--:--'
                    })
                    video_id += 1
        
        return videos
    
    def get_category(self, path_parts):
        """从路径确定分类"""
        category_keywords = {
            '文言文一课通': '文言文',
            '三国演义': '三国演义',
            '水浒传': '水浒传',
            '儒林外史': '儒林外史',
            '唐代文学汇总': '唐代文学',
            '作文': '作文',
            '世界长篇名著': '名著',
            '中国古代短篇小说': '名著',
            '元代文学汇总': '元曲',
            '两汉文学汇总': '两汉',
            '元明清文学考点汇总': '元明清',
            '诗词鉴赏技巧': '诗词',
            '魏晋南北朝文学汇总': '魏晋',
            '讽刺喜剧': '戏剧',
            '六国论': '议论文',
            '轴心时代': '历史',
            '名人传': '传记',
            '戏剧仿写': '写作',
            '关汉卿': '元曲',
            '近现代名家散文': '散文',
            '现实主义文学': '文学',
            '近现代小说': '小说',
            '赠送': '赠送资料'
        }
        
        for part in path_parts:
            for keyword, category in category_keywords.items():
                if keyword in part:
                    return category
        
        return '其他'


def main():
    """主函数"""
    port = 8000
    server_address = ('', port)
    
    print("=" * 60)
    print("  逗神归来 - 视频学习平台")
    print("=" * 60)
    print(f"  视频根目录: {VIDEO_ROOT}")
    print(f"  服务器地址: http://localhost:{port}")
    print("=" * 60)
    print("  按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        httpd = HTTPServer(server_address, VideoRequestHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.shutdown()


if __name__ == '__main__':
    main()