import urllib.request
import urllib.parse
import json

def tplink_cloud_login(username: str, password: str) -> str:
    """登录TP-Link云平台获取token"""
    url = "https://wap.tplinkcloud.com"
    data = {
        "method": "login",
        "params": {
            "appType": "Kasa_Android",
            "cloudUserName": username,
            "cloudPassword": password,
            "terminalUUID": "00000000-0000-0000-0000-000000000000"
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        return result['result']['token']

def get_cloud_devices(token: str) -> list:
    """获取云平台上的所有设备"""
    url = f"https://wap.tplinkcloud.com?token={token}"
    data = {
        "method": "getDeviceList"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        return result['result']['deviceList']

# 使用示例
if __name__ == "__main__":
    USERNAME = "你的TP-Link账号邮箱"
    PASSWORD = "你的TP-Link账号密码"
    
    token = tplink_cloud_login(USERNAME, PASSWORD)
    devices = get_cloud_devices(token)
    
    print("云平台设备列表:")
    for device in devices:
        print(f"- {device['alias']} ({device['deviceModel']})")