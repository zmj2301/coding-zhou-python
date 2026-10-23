# -*- coding: utf-8 -*-
"""积分看板查询服务（ECS 侧）

给桌面宠物「积分看板」面板用。监听 127.0.0.1:8899，纯标准库。

安全设计：只绑定回环地址，不监听公网。本地通过 SSH 隧道访问：
    ssh -N -L 8899:127.0.0.1:8899 root@39.107.96.165
这样不用在公网暴露任何凭据或数据，比直接开端口安全得多。

接口：
    GET /api/credits            三家完整报告（余额/签到/预测/到期规划）
    GET /api/credits?refresh=1  强制重新采集后再返回
    GET /health                 健康检查

数据新鲜度策略：
  采集比较重（要打三家的接口），所以不是每次请求都重新采集。
  服务启动时采集一次，之后每 REFRESH_SECONDS 秒后台刷新一次，
  请求返回的是最近一次的结果 + 数据时间戳。客户端据此显示倒计时。
  带 ?refresh=1 会强制同步采集一次（供手动刷新按钮用）。
"""
import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from credits_engine import collect_all, log

HOST = "127.0.0.1"
PORT = 8899
# 后台自动刷新间隔（秒）。客户端 5 分钟拉一次，这里 2 分钟足够新鲜。
REFRESH_SECONDS = 120

_lock = threading.Lock()
_cache = {"report": None, "at": None, "error": None}


def _collect_bg():
    """后台采集，带锁避免并发重复打接口。"""
    with _lock:
        try:
            rep = collect_all()
            _cache["report"] = rep
            _cache["at"] = time.time()
            _cache["error"] = None
        except Exception as e:
            _cache["error"] = str(e)
            log("后台采集失败: %s" % e)


def _bg_loop():
    while True:
        if _cache["report"] is None:
            _collect_bg()          # 启动时立即采一次
        time.sleep(REFRESH_SECONDS)
        _collect_bg()


class Handler(BaseHTTPRequestHandler):
    # 静默默认的 stderr 日志，改写到统一日志
    def log_message(self, fmt, *args):
        log("http %s - %s" % (self.address_string(), fmt % args))

    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # 面板 5 分钟轮询，不缓存
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        if path == "/health":
            self._send(200, {"ok": True,
                             "has_data": _cache["report"] is not None,
                             "updated_at": _cache["at"],
                             "error": _cache["error"]})
            return

        if path == "/api/credits":
            if qs.get("refresh", ["0"])[0] == "1":
                _collect_bg()
            rep = _cache["report"]
            if rep is None:
                self._send(503, {"error": "尚无数据，请稍后重试",
                                 "detail": _cache["error"]})
                return
            # 附上服务端视角的新鲜度，客户端可据此显示倒计时
            payload = dict(rep)
            payload["_served_at"] = datetime.now().isoformat()
            payload["_age_seconds"] = int(time.time() - (_cache["at"] or time.time()))
            payload["_next_refresh_in"] = max(REFRESH_SECONDS - (time.time() - (_cache["at"] or time.time())), 0)
            self._send(200, payload)
            return

        self._send(404, {"error": "not found", "paths": ["/api/credits", "/health"]})


def main():
    log("=" * 50)
    log("积分看板查询服务启动 %s:%d" % (HOST, PORT))
    log("自动刷新间隔 %d 秒" % REFRESH_SECONDS)
    t = threading.Thread(target=_bg_loop)
    t.daemon = True
    t.start()
    try:
        HTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        log("收到中断，退出")


if __name__ == "__main__":
    main()
