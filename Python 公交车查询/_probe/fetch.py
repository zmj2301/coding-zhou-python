# -*- coding: utf-8 -*-
"""用 curl 作为传输层（代理兼容），Python 只负责签名与解密。"""
import base64, hashlib, json, subprocess, urllib.parse, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

DOMAIN="https://web.chelaile.net.cn"; API=DOMAIN+"/api"
SALT="qwihrnbtmj"; KEY=b"FF32AE65FBFD19414EAAFF6291A54B42"; CITY="173"
DEF={"s":"h5","wxs":"wx_app","sign":"1","h5RealData":"1","v":"3.11.28",
     "src":"weixinapp_cx","ctm_mp":"mp_wx","vc":"2","favoriteGray":"1",
     "gpstype":"wgs","geo_type":"wgs","scene":"1256"}
UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
    "MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) "
    "UnifiedPCWindowsWechat(0xf254160a) XWEB/18055")

def sign(p):
    return hashlib.md5(("&".join('"%s"="%s"'%(k,v) for k,v in p.items())+SALT).encode()).hexdigest()

def call(path, extra):
    p=dict(DEF); p.update({"cityId":CITY,"localCityId":CITY}); p.update(extra)
    p["cryptoSign"]=sign(p)
    url="%s%s?%s"%(API,path,urllib.parse.urlencode(p))
    cmd=["curl","-s","-m","25","-A",UA,"-H","xweb_xhr: 1",
         "-H","Content-Type: text","-H","Accept: */*",
         "-H","Referer: https://servicewechat.com/wx71d589ea01ce3321/814/page-frame.html",
         "-H","Accept-Language: zh-CN,zh;q=0.9", url]
    raw=subprocess.run(cmd,capture_output=True).stdout.decode("utf-8","replace")
    s=raw.index("{"); d=0
    for i in range(s,len(raw)):
        if raw[i]=="{": d+=1
        elif raw[i]=="}": d-=1
        if d==0: return json.loads(raw[s:i+1])
    raise RuntimeError(raw[:400])

def unwrap(env):
    data=env.get("jsonr",{}).get("data",{})
    if data.get("encryptResult"):
        c=AES.new(KEY,AES.MODE_ECB)
        return json.loads(unpad(c.decrypt(base64.b64decode(data["encryptResult"])),AES.block_size).decode())
    return data

if __name__=="__main__":
    mode=sys.argv[1]; kw=sys.argv[2] if len(sys.argv)>2 else ""
    ep={"search":("/bus/query!nSearch.action",{"key":kw,"supportPhyStn":"true"}),
        "refresh":("/bus/line!encryptedTsfRealInfos.action",{"reqSrc":"2","lineStn":kw}),
        "stop":("/bus/stop!encryptedHomePage.action",{"key":kw})}[mode]
    print(json.dumps(unwrap(call(*ep)),ensure_ascii=False,indent=1))
