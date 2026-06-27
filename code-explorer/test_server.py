#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code Explorer 服务器测试脚本
测试所有 API 端点是否正常响应
"""

import urllib.request
import urllib.parse
import json
import sys
import time
import subprocess
import os
import signal

SERVER_URL = "http://localhost:8765"
PASSWORD = "admin@2026"
ADMIN_PASSWORD = "admin@2026"

tests_passed = 0
tests_failed = 0
server_process = None


def log(msg):
    print(f"  {msg}")


def check(name, condition, detail=""):
    global tests_passed, tests_failed
    if condition:
        log(f"  ✓ {name}")
        tests_passed += 1
    else:
        log(f"  ✗ {name}: {detail}" if detail else f"  ✗ {name}")
        tests_failed += 1


def test_api(name, method="GET", path="/", body=None, expected_status=200, check_json=None):
    url = f"{SERVER_URL}{path}"
    try:
        data = json.dumps(body).encode('utf-8') if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        resp = urllib.request.urlopen(req, timeout=10)
        content = resp.read().decode('utf-8')
        status = resp.status
        
        if status != expected_status:
            check(f"{name}", False, f"期望状态 {expected_status}，实际 {status}")
            return
        
        if check_json:
            try:
                j = json.loads(content)
                for key, val in check_json.items():
                    if j.get(key) != val:
                        check(f"{name}", False, f"字段 {key} 期望 {val}，实际 {j.get(key)}")
                        return
            except json.JSONDecodeError:
                check(f"{name}", False, "响应不是有效 JSON")
                return
        
        check(f"{name}", True)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode('utf-8', errors='replace')
        if e.code == expected_status:
            check(f"{name}", True)
        else:
            check(f"{name}", False, f"期望状态 {expected_status}，实际 {e.code} -> {body_text[:60]}")
    except urllib.error.URLError as e:
        check(f"{name}", False, f"连接失败 - {e.reason}")
    except Exception as e:
        check(f"{name}", False, f"异常 - {e}")


def test_auth_api(token, name, method="GET", path="/", expected_status=200, check_json=None):
    url = f"{SERVER_URL}{path}"
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("Cookie", f"wg_token={token}")
        resp = urllib.request.urlopen(req, timeout=10)
        content = resp.read().decode('utf-8')
        status = resp.status
        
        if status != expected_status:
            check(f"{name}", False, f"期望状态 {expected_status}，实际 {status}")
            return
        
        if check_json:
            try:
                j = json.loads(content)
                for key, val in check_json.items():
                    if j.get(key) != val:
                        check(f"{name}", False, f"字段 {key} 期望 {val}，实际 {j.get(key)}")
                        return
            except json.JSONDecodeError:
                check(f"{name}", False, "响应不是有效 JSON")
                return
        
        check(f"{name}", True)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode('utf-8', errors='replace')
        if e.code == expected_status:
            check(f"{name}", True)
        else:
            check(f"{name}", False, f"期望状态 {expected_status}，实际 {e.code} -> {body_text[:60]}")
    except Exception as e:
        check(f"{name}", False, f"异常 - {e}")


def wait_for_server(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except:
            time.sleep(0.5)
    return False


def start_server():
    global server_process
    env = os.environ.copy()
    env["CODE_EXPLORER_KEY"] = PASSWORD
    env["CODE_EXPLORER_ADMINISTRATOR"] = ADMIN_PASSWORD
    
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    
    print("  等待服务器启动...")
    if wait_for_server(f"{SERVER_URL}/"):
        print("  服务器已启动！\n")
        return True
    else:
        print("  ✗ 服务器启动超时")
        return False


def stop_server():
    global server_process
    if server_process:
        print("\n  正在停止服务器...")
        if sys.platform == 'win32':
            os.kill(server_process.pid, signal.CTRL_BREAK_EVENT)
        else:
            server_process.terminate()
        server_process.wait(timeout=5)
        server_process = None
        print("  服务器已停止。")


def main():
    global tests_passed, tests_failed
    print("=" * 55)
    print("  Code Explorer API 测试")
    print("=" * 55)
    print()
    
    if not start_server():
        return
    
    try:
        # ========== 1. 静态页面 ==========
        print("【1. 静态页面服务】")
        test_api("首页 HTML", "GET", "/", expected_status=200)
        test_api("不存在页面返回 404", "GET", "/no-exist.html", expected_status=404)
        print()
        
        # ========== 2. 认证 API ==========
        print("【2. 认证 API（未登录）】")
        test_api("auth-check 未登录", "GET", "/api/auth-check",
                 check_json={"authenticated": False, "passwordSet": True})
        test_api("未登录访问文件树", "GET", "/api/files/tree", expected_status=401)
        test_api("空密码登录", "POST", "/api/login",
                 body={"password": ""}, expected_status=401)
        test_api("错误密码登录", "POST", "/api/login",
                 body={"password": "wrong"}, expected_status=401)
        print()
        
        # ========== 3. 用户登录 ==========
        print("【3. 用户登录】")
        test_api("正确密码登录", "POST", "/api/login",
                 body={"password": PASSWORD}, expected_status=200)
        print()
        
        # ========== 4. 登录后 API ==========
        print("【4. 登录后 API 访问】")
        try:
            data = json.dumps({"password": PASSWORD}).encode('utf-8')
            req = urllib.request.Request(f"{SERVER_URL}/api/login", data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            resp = urllib.request.urlopen(req, timeout=10)
            login_data = json.loads(resp.read().decode('utf-8'))
            token = login_data.get("token", "")
            
            if token:
                check("获取登录 token", True)
                test_auth_api(token, "文件树接口", "GET", "/api/files/tree", expected_status=200)
                test_auth_api(token, "auth-check 已登录", "GET", "/api/auth-check",
                             check_json={"authenticated": True})
                
                # 管理员登录
                admin_data = json.dumps({"password": ADMIN_PASSWORD}).encode('utf-8')
                admin_req = urllib.request.Request(f"{SERVER_URL}/api/admin/login",
                                                   data=admin_data, method="POST")
                admin_req.add_header("Content-Type", "application/json")
                admin_resp = urllib.request.urlopen(admin_req, timeout=10)
                admin_data = json.loads(admin_resp.read().decode('utf-8'))
                admin_token = admin_data.get("token", "")
                
                if admin_token:
                    check("管理员登录", True)
                    test_auth_api(admin_token, "管理员仪表盘", "GET", "/api/admin/dashboard",
                                 expected_status=200)
                else:
                    check("管理员登录", False, "未获取到 token")
            else:
                check("获取登录 token", False)
        except Exception as e:
            check("登录/管理员测试", False, str(e))
        
        print()
        
        # ========== 5. 登出 ==========
        print("【5. 登出】")
        test_api("登出接口", "POST", "/api/logout", expected_status=200)
        print()
        
        # ========== 结果 ==========
        print("=" * 55)
        total = tests_passed + tests_failed
        print(f"  测试完成: {total} 项")
        print(f"  ✓ 通过: {tests_passed}")
        print(f"  ✗ 失败: {tests_failed}")
        if tests_failed == 0:
            print("\n  🎉 所有测试通过！API 全部正常")
        else:
            print(f"\n  ⚠ 有 {tests_failed} 项测试失败")
        print("=" * 55)
        
    finally:
        stop_server()


if __name__ == "__main__":
    main()