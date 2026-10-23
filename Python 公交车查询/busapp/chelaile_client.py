#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""车来了实时公交客户端。

协议实现参考 MIT 项目 Justintunsday/chelaile-api-server，
在其基础上做了 Python 化与移动端适配（curl 作为传输层）。
"""
import base64
import hashlib
import json
import subprocess
import time
import urllib.parse

APP_VERSION = "1.1.0"

BASE_DOMAIN = "https://web.chelaile.net.cn"
BASE_URL = BASE_DOMAIN + "/api"
SIGN_SALT = "qwihrnbtmj"
AES_KEY = b"FF32AE65FBFD19414EAAFF6291A54B42"

# 城市 ID：湘潭=173（无地铁）
CITY_ID = "173"
CITY_NAME = "湘潭"

DEFAULT_PARAMS = {
    "s": "h5",
    "wxs": "wx_app",
    "sign": "1",
    "h5RealData": "1",
    "v": "3.11.28",
    "src": "weixinapp_cx",
    "ctm_mp": "mp_wx",
    "vc": "2",
    "favoriteGray": "1",
    "gpstype": "wgs",
    "geo_type": "wgs",
    "scene": "1256",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 "
    "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
    "MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) "
    "UnifiedPCWindowsWechat(0xf254160a) XWEB/18055"
)


class ChelaileError(Exception):
    pass


def crypto_sign(params):
    """参数按加入顺序拼接后追加盐值，做 MD5。"""
    raw = "&".join('"%s"="%s"' % (k, v) for k, v in params.items()) + SIGN_SALT
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _decrypt(ciphertext):
    """AES-256-ECB 解密（上游响应加密方式）。"""
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
    except ImportError:
        from busapp.aes import decrypt as _fallback
        return _fallback(ciphertext)
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return unpad(cipher.decrypt(base64.b64decode(ciphertext)), AES.block_size).decode("utf-8")


def _transport(url, timeout=20):
    """用 curl 作为传输层。

    本机Python urllib 走 HTTPS 代理时CONNECT 隧道会 502，而 curl 正常，
    因此统一走 curl 子进程。移动端(Android)上无 curl 时自动回退到 urllib。
    """
    cmd = [
        "curl", "-s", "-m", str(timeout), "-A", UA,
        "-H", "xweb_xhr: 1",
        "-H", "Content-Type: text",
        "-H", "Accept: */*",
        "-H", "Referer: https://servicewechat.com/wx71d589ea01ce3321/814/page-frame.html",
        "-H", "Accept-Language: zh-CN,zh;q=0.9",
        url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
        raw = proc.stdout.decode("utf-8", "replace")
        if raw.strip():
            return raw
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    # 回退：urllib（Android 环境）
    import urllib.request
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "xweb_xhr": "1",
        "Content-Type": "text",
        "Accept": "*/*",
        "Referer": "https://servicewechat.com/wx71d589ea01ce3321/814/page-frame.html",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    opener = urllib.request.build_opener(urllib.request.ProxyHandler())
    with opener.open(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _extract_json(raw):
    """上游返回带 JSONP 包裹，需从第一个 { 精确截取到配对的 }。"""
    start = raw.find("{")
    if start < 0:
        raise ChelaileError("上游返回非 JSON: %s" % raw[:120])
    depth = 0
    for i in range(start, len(raw)):
        ch = raw[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start:i + 1])
    raise ChelaileError("JSON 截取失败")


def request(path, extra, city_id=CITY_ID, retries=2):
    """发起一次签名请求并解包加密信封。"""
    last = None
    for attempt in range(retries):
        try:
            params = dict(DEFAULT_PARAMS)
            params.update({"cityId": city_id, "localCityId": city_id})
            params.update(extra)
            params["cryptoSign"] = crypto_sign(params)
            url = "%s%s?%s" % (BASE_URL, path, urllib.parse.urlencode(params))
            env = _extract_json(_transport(url))

            if env.get("status") not in (1, "1", None):
                raise ChelaileError("上游状态异常: %s" % env.get("msg", env))

            data = env.get("jsonr", {}).get("data", {})
            if data.get("encryptResult"):
                return json.loads(_decrypt(data["encryptResult"]))
            return data
        except ChelaileError:
            raise
        except Exception as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(0.8)
    raise ChelaileError("请求失败: %s" % last)


# ---------------- 业务接口 ----------------

def search(keyword, city_id=CITY_ID):
    """关键词搜索：站点 + 线路 + POI。"""
    return request("/bus/query!nSearch.action",
                   {"key": keyword, "supportPhyStn": "true"}, city_id)


def nearby_stops(lat, lng, city_id=CITY_ID):
    """按坐标找附近站点（含各线实时车辆）。"""
    return request("/bus/stop!encryptedHomePage.action", {
        "localCityId": "undefined",
        "lat": "%.6f" % lat, "lng": "%.6f" % lng,
        "geo_lat": "%.6f" % lat, "geo_lng": "%.6f" % lng,
        "type": "5", "permission": "0",
    }, city_id)


def stop_detail(physical_st_id, namesake_st_id="", city_id=CITY_ID):
    """站点详情：途经全部线路 + 每条线的实时车辆。"""
    return request("/bus/stop!encryptedPhyStnDetail.action", {
        "physicalStId": physical_st_id,
        "namesakeStId": namesake_st_id,
        "stationId": "", "lat": "", "lng": "",
    }, city_id)


def line_detail(line_id, city_id=CITY_ID):
    """线路详情：完整站点序列 + 坐标 + 首末班。"""
    return request("/bus/line!encryptedLineDetail.action",
                   {"lineId": line_id}, city_id)


def parse_arrivals(states, now=None):
    """解析 stnStates，输出带分钟级 ETA 的车辆列表。"""
    out = []
    for s in states or []:
        item = {
            "bus_id": s.get("busId") or "未知车辆",
            "stops_away": s.get("value", -1),
            "distance_m": s.get("distanceToDest", -1),
            "travel_seconds": s.get("travelTime", -1),
            "arrival_time": s.get("arrivalTime", -1),
            "eta_min": None,
        }
        if s.get("arrivalTime", -1) > 0:
            import datetime
            eta = (datetime.datetime.fromtimestamp(s["arrivalTime"] / 1000) - now).total_seconds() / 60.0
            item["eta_min"] = max(0.0, round(eta, 1))
        out.append(item)
    return out