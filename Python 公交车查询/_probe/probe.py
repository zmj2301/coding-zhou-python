#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最小复现：直连车来了上游，验证湘潭实时到站数据可用性。
参考 MIT 项目 Justintunsday/chelaile-api-server 的协议实现。
仅用于验证可行性，非长期运行代码。
"""
import hashlib
import json
import sys
import urllib.parse
import urllib.request

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

BASE_DOMAIN = "https://web.chelaile.net.cn"
SIGN_SALT = "qwihrnbtmj"
AES_KEY = b"FF32AE65FBFD19414EAAFF6291A54B42"
CITY_ID = "173"  # 湘潭

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 "
        "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
        "MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) "
        "UnifiedPCWindowsWechat(0xf254160a) XWEB/18055"
    ),
    "xweb_xhr": "1",
    "Content-Type": "text",
    "Accept": "*/*",
    "Referer": "https://servicewechat.com/wx71d589ea01ce3321/814/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def crypto_sign(params):
    s = "&".join('"%s"="%s"' % (k, v) for k, v in params.items()) + SIGN_SALT
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def decrypt(ciphertext):
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return unpad(cipher.decrypt(base64.b64decode(ciphertext)), AES.block_size).decode("utf-8")


import base64  # noqa: E402


def call(path, extra):
    params = dict(DEFAULT_PARAMS)
    params.update({"cityId": CITY_ID, "localCityId": CITY_ID})
    params.update(extra)
    params["cryptoSign"] = crypto_sign(params)
    url = "%s%s?%s" % (BASE_DOMAIN, path, urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers=HEADERS)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler())
    with opener.open(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", "replace")
    start = raw.index("{")
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
        if depth == 0:
            return json.loads(raw[start:i + 1])
    raise RuntimeError("no json")


def unwrap(env):
    data = env.get("jsonr", {}).get("data", {})
    if data.get("encryptResult"):
        return json.loads(decrypt(data["encryptResult"]))
    return data


BASE = "https://web.chelaile.net.cn/api"

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "search"
    kw = sys.argv[2] if len(sys.argv) > 2 else "翰林居"

    if step == "search":
        r = unwrap(call(BASE + "/bus/query!nSearch.action",
                        {"key": kw, "supportPhyStn": "true"}))
        print(json.dumps(r, ensure_ascii=False)[:4000])

    elif step == "refresh":
        # lineStn = 线路ID_方向序号
        r = unwrap(call(BASE + "/bus/line!encryptedTsfRealInfos.action",
                        {"reqSrc": "2", "lineStn": kw}))
        print(json.dumps(r, ensure_ascii=False)[:5000])

    elif step == "stop":
        r = unwrap(call(BASE + "/bus/stop!encryptedHomePage.action", {"key": kw}))
        print(json.dumps(r, ensure_ascii=False)[:4000])