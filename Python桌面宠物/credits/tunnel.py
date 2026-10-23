# -*- coding: utf-8 -*-
"""SSH 隧道管理 —— 保证本地 127.0.0.1:8899 能访问 ECS 上的查询服务

为什么要隧道：查询服务只监听 ECS 的 127.0.0.1，不对公网开放。
本地通过端口转发访问，凭据和数据都不经过公网。

三种用法：
  1) 面板自动调用：面板检测到隧道不通时会调 ensure_tunnel() 自动拉起
  2) 手动常驻：python tunnel.py start   （前台阻塞，Ctrl+C 退出）
  3) 后台守护：python tunnel.py daemon  （写 pid 文件，日志到 tunnel.log）

密钥路径：沙箱/服务化环境的 $HOME 未必是登录用户家目录，这里按序探测。
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
PID_FILE = BASE_DIR / "tunnel.pid"
LOG_FILE = BASE_DIR / "tunnel.log"

ECS_HOST = "39.107.96.165"
# ssh 目标必须是 user@host 形式。写成裸 IP 会用本机用户名去登录，
# 结果就是 "Administrator@39.107.96.165: Permission denied (publickey)"。
SSH_TARGET = "root@" + ECS_HOST
LOCAL_PORT = 8899
REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 8899
HEALTH_URL = "http://127.0.0.1:%d/health" % LOCAL_PORT

_SSH_KEY_CANDIDATES = [
    os.environ.get("ECS_SSH_KEY", ""),
    str(Path.home() / ".ssh" / "id_ed25519"),
    r"C:\Users\Administrator\.ssh\id_ed25519",
]


def ssh_key():
    for p in _SSH_KEY_CANDIDATES:
        if p and Path(p).exists():
            return p
    return None


def health(timeout: float = 3.0) -> bool:
    """隧道是否已通（能拿到 health 且 ok）。

    注意：必须显式绕过系统代理。本机设了 http_proxy 环境变量，
    urllib 会把 127.0.0.1 的请求也发给代理，直接返回 502 Bad Gateway——
    这是个很容易误判成「隧道没通」的坑。
    """
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(HEALTH_URL, timeout=timeout) as r:
            import json
            return json.loads(r.read().decode("utf-8")).get("ok", False)
    except Exception:
        return False


def _read_pid():
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None
    # 确认进程还活着。tasklist 输出在中文 Windows 下可能是 GBK，
    # 强制用 errors="replace" 兜住，否则一个解码异常会让 stop/status 直接崩。
    if sys.platform.startswith("win"):
        r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                           capture_output=True)
        out = (r.stdout or b"").decode("utf-8", errors="replace")
        return pid if str(pid) in out else None
    try:
        os.kill(pid, 0)
        return pid
    except OSError:
        return None


def _ssh_args():
    args = ["ssh"]
    key = ssh_key()
    if key:
        args += ["-i", key]
    args += [
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=accept-new",
        # 隧道要长连，关闭保活探测以免网络抖动时静默断开
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes",
    ]
    return args


def start_tunnel(wait: float = 4.0) -> bool:
    """后台拉起隧道。成功返回 True。

    关键：用 DETACHED_PROCESS / CREATE_NEW_PROCESS_GROUP 让 ssh 脱离当前会话，
    否则父进程（终端、面板进程）一退出隧道就被一起带走。
    隧道是长连接，任何形式的"父进程连带杀掉"都会导致看板取不到数。
    """
    if health():
        return True

    pid = _read_pid()
    if pid:
        return False   # 进程在但不通，等它重连

    if not ssh_key():
        print("[ERR] 找不到 SSH 私钥，无法建立隧道")
        return False

    args = _ssh_args() + [
        "-N",                    # 只转发，不执行命令
        "-L", "%d:%s:%d" % (LOCAL_PORT, REMOTE_HOST, REMOTE_PORT),
        SSH_TARGET,
    ]
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    # CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS 让 ssh 脱离当前会话，
    # 否则父进程（终端 / 面板进程）一退出，隧道就被一起带走。
    flags = 0
    if sys.platform.startswith("win"):
        flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                 | getattr(subprocess, "DETACHED_PROCESS", 0)
                 | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        with open(str(LOG_FILE), "ab") as lf:
            proc = subprocess.Popen(
                args, stdout=lf, stderr=lf,
                stdin=subprocess.DEVNULL, close_fds=True, creationflags=flags)
    except Exception as e:
        print("[ERR] 启动隧道失败: %s" % e)
        return False

    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    time.sleep(wait)
    if health():
        print("[OK] 隧道已建立 pid=%d  127.0.0.1:%d -> %s:%d"
              % (proc.pid, LOCAL_PORT, SSH_TARGET, REMOTE_PORT))
        return True
    print("[WARN] 隧道已拉起但暂未连通（pid=%d），请稍候或查看 %s" % (proc.pid, LOG_FILE.name))
    return False


def stop_tunnel() -> bool:
    pid = _read_pid()
    if not pid:
        print("[--] 没有运行中的隧道")
        return False
    try:
        if sys.platform.startswith("win"):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True)
        else:
            os.kill(pid, 15)
    except Exception as e:
        print("[WARN] 停止失败: %s" % e)
        return False
    try:
        PID_FILE.unlink()
    except Exception:
        pass
    print("[OK] 隧道已停止 (pid=%d)" % pid)
    return True


def status() -> bool:
    ok = health()
    pid = _read_pid()
    print("隧道状态: %s" % ("通" if ok else "不通"))
    print("本地端口: %d" % LOCAL_PORT)
    print("目标: %s:%d" % (SSH_TARGET, REMOTE_PORT))
    print("进程: %s" % (pid if pid else "无"))
    print("私钥: %s" % (ssh_key() or "未找到"))
    return ok


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        # 前台阻塞运行，方便单独开一个终端常驻
        if health():
            print("[OK] 隧道已在运行")
            return
        if not ssh_key():
            print("[ERR] 找不到 SSH 私钥")
            sys.exit(1)
        print("[INFO] 建立隧道中，Ctrl+C 退出…")
        try:
            subprocess.run(_ssh_args() + [
                "-N", "-L", "%d:%s:%d" % (LOCAL_PORT, REMOTE_HOST, REMOTE_PORT),
                SSH_TARGET])
        except KeyboardInterrupt:
            print("\n[OK] 已退出")
    elif cmd == "daemon":
        start_tunnel()
    elif cmd == "stop":
        stop_tunnel()
    elif cmd == "restart":
        stop_tunnel()
        time.sleep(1)
        start_tunnel()
    else:
        status()


if __name__ == "__main__":
    main()
