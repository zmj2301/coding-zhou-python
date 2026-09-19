"""
实时状态上报模块
将定时休息的实时状态通过 HTTP 转发到后端，供微信小程序/家长端查看。

协议：HTTP POST JSON（按需开启无鉴权公开，本实现不携带令牌）。
所有网络请求都在后台线程执行，绝不阻塞 GUI 线程（倒计时/锁屏）。

可复用接口：
    make_payload(device_id, type, data) -> dict
    StatusReporter(endpoint, device_id=None, heartbeat_interval=30, timeout=5.0)
        .start() / .stop()
        .report(type, data)                  # 上报一条事件
        .report_state(stage, remaining=None, total=None)  # 上报当前阶段状态
"""
from __future__ import annotations

import json
import queue
import socket
import threading
import time
import uuid
from urllib import error as urllib_error
from urllib import request as urllib_request

from core.logger import logger

APP_NAME = "pet-timer"


def make_payload(device_id: str, type_: str, data: dict) -> dict:
    """构造一条统一格式的上报负载。"""
    return {
        "device_id": device_id,      # 设备唯一标识
        "app": APP_NAME,             # 应用标识
        "ts": int(time.time()),      # Unix 时间戳（秒）
        "type": type_,               # 事件类型
        "data": data,                # 各类型负载
    }


class StatusReporter:
    """后台线程上报器。

    事件/心跳进入队列，由单个后台线程串行 POST 到后端。
    网络失败仅记日志，不影响主程序。
    """

    def __init__(
        self,
        endpoint: str,
        device_id: str | None = None,
        heartbeat_interval: int = 30,
        timeout: float = 5.0,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._device_id = device_id or _make_default_device_id()
        self._heartbeat_interval = max(5, int(heartbeat_interval))
        self._timeout = max(1.0, float(timeout))
        self._queue: queue.Queue = queue.Queue()
        self._stop_evt = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_stage = "idle"

    # ---- 生命周期 ----
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="status-reporter")
        self._thread.start()
        logger.info(f"状态上报已启动 -> {self._endpoint} (device_id={self._device_id})")

    def stop(self) -> None:
        self._stop_evt.set()

    # ---- 对外上报接口 ----
    def report(self, type_: str, data: dict) -> None:
        """异步上报一条事件。"""
        self._queue.put(make_payload(self._device_id, type_, data))

    def report_state(self, stage: str, remaining: int | None = None,
                     total: int | None = None) -> None:
        """异步上报当前阶段状态。stage: idle | working | locked | break_done"""
        data: dict = {"state": stage}
        if remaining is not None:
            data["remaining"] = remaining
        if total is not None:
            data["total"] = total
        self.report("state", data)

    # ---- 内部实现 ----
    def _run(self) -> None:
        next_heartbeat = time.monotonic() + self._heartbeat_interval
        while not self._stop_evt.is_set():
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                item = None
            if item is not None:
                self._send(item)
            if time.monotonic() >= next_heartbeat:
                self._send(make_payload(
                    self._device_id, "heartbeat", {"state": self._last_stage}
                ))
                next_heartbeat = time.monotonic() + self._heartbeat_interval

    def _send(self, payload: dict) -> None:
        # 记录最近一次已知阶段，供随后的心跳使用
        state = payload.get("data", {}).get("state")
        if state:
            self._last_stage = state
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib_request.Request(
            self._endpoint,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib_request.urlopen(req, timeout=self._timeout) as resp:
                if resp.status != 200:
                    logger.warning(f"状态上报非200响应: {resp.status} type={payload['type']}")
                else:
                    logger.debug(f"状态上报成功 type={payload['type']} state={state}")
        except (urllib_error.URLError, OSError) as e:
            logger.warning(f"状态上报失败 type={payload['type']}: {e}")
        except Exception as e:  # noqa: BLE001 上报失败绝不影响主程序
            logger.warning(f"状态上报异常 type={payload['type']}: {e}")


def _make_default_device_id() -> str:
    """生成本机稳定标识：主机名 + 本机MAC地址短哈希。"""
    node = uuid.getnode()
    node_id = f"{node:x}"[-8:]
    return f"{socket.gethostname()}-{node_id}"