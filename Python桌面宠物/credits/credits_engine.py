# -*- coding: utf-8 -*-
"""三家 AI 工具积分看板 —— ECS 侧数据采集 + 预测引擎

为桌面宠物「积分看板」面板提供统一数据。三家：
  - TRAE        /opt/trae-work/  （有会话级用量历史）
  - WorkBuddy   /opt/workbuddy/  （只有签到 + 余额，用轮询差值推算日消耗）
  - MiniMax     /opt/minimax/    （签到面板 + 积分明细，消耗同上推算）

部署：/opt/credits/，Python 3.6.8 兼容，纯标准库。
数据落到 credits_state.json，query_server.py 读它对外提供 HTTP 查询。

为什么要自己存历史：
  - WorkBuddy 客户端没有「用量历史」接口（源码里 usage() 是空桩），
    只能定时轮询余额，用差值近似当日消耗 → 必须本地存档才能算趋势
  - MiniMax 同理（只有 credit/details，没有逐日消耗）
  - TRAE 本来有 trae_usage_daily.csv，但为了统一 schema，这里也自己存一份

消耗口径说明（重要）：
  WorkBuddy / MiniMax 的「今日消耗」是从上次快照的 used 值做差，
  得到的是【两次快照之间】的消耗，不是自然日。跨天时会在 day_rollover
  里归一化，避免把昨天的量算到今天头上。
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "credits_state.json"
TRAE_DIR = Path("/opt/trae-work")
LOGS = BASE_DIR / "collect.log"

# 三家的运行目录（与既有签到脚本一致）
TRAE_DIR_CFG = TRAE_DIR / "config.json"
TRAE_USAGE_JSON = TRAE_DIR / "trae_usage_data.json"
TRAE_CSV = TRAE_DIR / "trae_usage_daily.csv"
TRAE_SIGNIN_HIST = TRAE_DIR / "trae_signin_history.json"
WORKBUDDY_DIR = Path("/opt/workbuddy")
MINIMAX_DIR = Path("/opt/minimax")

# 各家签到积分（用于未来签到收入预测）
CHECKIN_CREDITS = {
    "trae": 200,        # config 里的签到奖励，见 auto_daily.py
    "workbuddy": 100,   # daily_credit 默认值
    "minimax": 400,     # 官方：每日 400，第 4/7 天 1000
}
# 积分有效期（天）——到期压力主要来自这些
VALID_DAYS = {"trae": 31, "workbuddy": 31, "minimax": 30}


def log(msg):
    line = "[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    try:
        with LOGS.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _to_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ---------------- 状态存取 ----------------
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            log("状态文件损坏，重建: %s" % e)
    return {"providers": {}, "updated_at": None}


def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(STATE_FILE))


def _prov(state, key):
    """取某个平台的持久化槽位，不存在则初始化。"""
    providers = state.setdefault("providers", {})
    return providers.setdefault(key, {
        "balance": None,        # {"total": , "used": , "remaining": }
        "packs": [],            # [{"name","limit","used","remaining","expire_ts"}]
        "checkin": {},          # {"done": , "streak": , "credit": }
        "used_samples": [],     # [{"ts", "used"}] 用于差值推算消耗
        "daily": {},            # {"YYYY-MM-DD": consumed}
        "last_seen_date": None, # 上次记账的日期，用于跨天归一化
    })


def record_usage_sample(prov, used_total):
    """记一个余额快照，并算出「本次新增消耗」累加到今天。

    WorkBuddy / MiniMax 都没有逐日消耗接口，只能用余额差值近似：
        本次消耗 = 上次 used - 本次 used
    差值 <= 0 时不记账（可能跨周期重置或精度截断）。
    """
    now_ts = int(time.time())
    today = datetime.now().strftime("%Y-%m-%d")

    samples = prov.get("used_samples") or []
    prev = samples[-1] if samples else None
    prov["used_samples"] = (samples + [{"ts": now_ts, "used": used_total}])[-200:]

    if prev is None:
        return 0.0

    delta = _to_float(prev.get("used"), 0.0) - used_total
    # 跨天：把这段消耗记到更早的那天，避免污染今天
    day = today
    if prov.get("last_seen_date") and prov["last_seen_date"] != today:
        day = prov["last_seen_date"]
        log("跨天归一化：%s 之前的消耗记到 %s" % (today, day))
    prov["last_seen_date"] = today

    if delta <= 0:
        return 0.0
    daily = prov.setdefault("daily", {})
    daily[day] = _to_float(daily.get(day), 0.0) + round(delta, 4)
    # 只留 60 天
    for k in list(daily.keys()):
        if k < (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"):
            del daily[k]
    return round(delta, 2)


# ---------------- TRAE ----------------
def collect_trae(state):
    """TRAE 数据最完整：直接读 auto_daily.py 生成的产物即可。"""
    prov = _prov(state, "trae")
    out = {"ok": False}

    if not TRAE_USAGE_JSON.exists():
        out["error"] = "trae_usage_data.json 不存在（auto_daily.py 未跑？）"
        return out

    try:
        d = json.loads(TRAE_USAGE_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        out["error"] = "解析 usage_data 失败: %s" % e
        return out

    overall = d.get("overall_usage") or {}
    total = _to_float(overall.get("total_limit"))
    used = _to_float(overall.get("total_used"))
    prov["balance"] = {
        "total": total,
        "used": used,
        "remaining": _to_float(overall.get("remaining"), max(total - used, 0.0)),
    }

    # packs 里有每个包的过期时间，这是做「到期规划」的关键
    packs = []
    for p in (d.get("packs") or []):
        packs.append({
            "name": p.get("name", ""),
            "group": p.get("group", ""),
            "limit": _to_float(p.get("limit")),
            "used": _to_float(p.get("used")),
            "remaining": _to_float(p.get("remaining")),
            "expire_ts": int(p.get("expire_time") or 0),
            "expire_str": p.get("expire_str", ""),
            "alive": bool(p.get("alive", True)),
        })
    prov["packs"] = packs

    ck = d.get("checkin") or {}
    prov["checkin"] = {
        "done": bool(ck.get("checked_in")),
        "streak": int(ck.get("continuous_days") or 0),
        "credit": int(ck.get("credits") or CHECKIN_CREDITS["trae"]),
    }

    # 权威的每日消耗来自 TRAE 自己的接口，直接用，不做差值近似
    daily = {}
    for row in (d.get("daily") or []):
        dt = row.get("date")
        if dt:
            daily[dt] = _to_float(row.get("consumed"))
    if daily:
        prov["daily"] = daily
    # 补上 CSV 里更早的历史（daily 只有 7 天，CSV 有更长的）
    if TRAE_CSV.exists():
        try:
            for line in TRAE_CSV.read_text(encoding="utf-8-sig").splitlines()[1:]:
                parts = line.split(",")
                if len(parts) >= 2 and parts[0].strip():
                    dt = parts[0].strip()
                    if dt not in prov["daily"]:
                        prov["daily"][dt] = _to_float(parts[1])
        except Exception:
            pass

    prov["daily"] = dict(sorted(prov["daily"].items()))
    out.update({"ok": True,
                "user": d.get("user") or {},
                "month_total": _to_float(d.get("month_total")),
                "month_peak": d.get("month_peak") or {},
                "continuous_days": int(d.get("continuous_days") or 0),
                "fetched_at": d.get("fetched_at")})
    return out


# ---------------- WorkBuddy ----------------
def collect_workbuddy(state):
    """WorkBuddy：调 get-user-resource-summary 拿余额，轮询差值算日消耗。"""
    sys.path.insert(0, str(WORKBUDDY_DIR))
    prov = _prov(state, "workbuddy")
    out = {"ok": False}

    try:
        os.chdir(str(WORKBUDDY_DIR))
        import workbuddy_checkin as wb
    except Exception as e:
        out["error"] = "导入 workbuddy_checkin 失败: %s" % e
        return out
    finally:
        os.chdir(str(BASE_DIR))

    try:
        wb.load_env()
        token, uid = wb.load_credentials()
        if not token or not uid:
            out["error"] = "缺少凭据（需 sync_wb_token.py 同步）"
            return out

        base = wb.api_base_from_token(token)
        wb.API_BASE = base
        # 注意：积分类接口不带 /v2，和签到接口前缀不同
        r = wb.api_post(base + "/billing/meter/get-user-resource-summary", token, uid)
        if r.get("code") != 0:
            out["error"] = "余额查询失败: %s" % r.get("msg", str(r))[:120]
            return out

        data = r.get("data") or {}
        pkgs = data.get("Packages") or []
        total = sum(_to_float(p.get("CycleTotalCapacity")) for p in pkgs)
        remain = sum(_to_float(p.get("CycleRemainCapacity")) for p in pkgs)
        used = sum(_to_float(p.get("CycleUsedCapacity")) for p in pkgs)
        prov["balance"] = {"total": total, "used": used, "remaining": remain}
        # 周期额度整体重置，用 need_reset 表示「无按包过期概念」
        prov["packs"] = []
        prov["subscription"] = data.get("SubscriptionPackageName", "")

        delta = record_usage_sample(prov, used)

        # 签到状态（已有接口，直接复用）
        try:
            done, streak, credit = wb.check_status(token, uid)
            prov["checkin"] = {"done": done, "streak": streak, "credit": credit}
        except Exception as e:
            log("WorkBuddy 签到状态查询失败: %s" % e)

        out.update({"ok": True, "delta": delta,
                    "api_base": base,
                    "note": "消耗由余额差值推算，WorkBuddy 无逐日消耗接口"})
        return out
    except Exception as e:
        out["error"] = "采集异常: %s" % e
        return out


# ---------------- MiniMax ----------------
def collect_minimax(state):
    """MiniMax：签到面板 + credit/details 余额。"""
    sys.path.insert(0, str(MINIMAX_DIR))
    prov = _prov(state, "minimax")
    out = {"ok": False}

    try:
        os.chdir(str(MINIMAX_DIR))
        import minimax_checkin as mm
    except Exception as e:
        out["error"] = "导入 minimax_checkin 失败: %s" % e
        return out
    finally:
        os.chdir(str(BASE_DIR))

    try:
        mm.load_env()
        token, expires_ms = mm.load_credentials()
        if not token:
            out["error"] = "缺少凭据（需 sync_mm_token.py 同步）"
            return out

        # 每天跑一次时 token 只活 1 小时，先续期再用
        token, expires_ms, _ = mm.ensure_fresh_token(token, expires_ms)
        if not mm.env_str("MINIMAX_REFRESH_TOKEN"):
            rt = mm._read_token_file()[1]
            if rt:
                os.environ["MINIMAX_REFRESH_TOKEN"] = rt

        bal = mm.credit_balance(token)
        if bal is None:
            out["error"] = "积分余额查询失败"
            return out
        prov["balance"] = {"total": None, "used": None, "remaining": bal}

        try:
            today_done, claimable, day_no, points, scene = mm.check_status(token)
            prov["checkin"] = {"done": today_done, "streak": day_no,
                               "credit": points, "claimable": claimable}
        except Exception as e:
            log("MiniMax 签到状态查询失败: %s" % e)

        out.update({"ok": True,
                    "note": "消耗由余额差值推算，MiniMax 无逐日消耗接口"})
        return out
    except Exception as e:
        out["error"] = "采集异常: %s" % e
        return out


# ---------------- 日历（日型权重）----------------
# 复用 TRAE 项目的 school_calendar，避免两套节假日数据不一致
def load_school_calendar():
    try:
        sys.path.insert(0, str(TRAE_DIR))
        import school_calendar
        return school_calendar
    except Exception as e:
        log("导入 school_calendar 失败，使用内置默认（全部 full）: %s" % e)
        return None


def day_weight(cal, d):
    """某天的可用权重：full=1.0, half=0.5, off=0.0"""
    if cal is None:
        return 1.0
    try:
        return float(cal.day_weight(d))
    except Exception:
        return 1.0


def day_type(cal, d):
    if cal is None:
        return "full"
    try:
        return cal.day_type(d)
    except Exception:
        return "full"


def _school_mode(cal):
    """是否处于开学模式。school_calendar 没有暴露 is_school_mode，
    这里读它自己的 config（/opt/trae-work/config.json）。"""
    if cal is None:
        return False
    try:
        return bool(cal.load_cfg().get("school_mode"))
    except Exception:
        return False


# ---------------- 预测 ----------------
def recent_avg(prov, cal, n_days=14, today=None):
    """近 n 天【按可用容量归一化】的日均消耗。

    直接对历史求平均会把「上学日用得少」误当成「用得少」，
    所以要除以那天的可用权重，得到的是「一个可用日的平均消耗」，
    再乘今天权重才是今天的预测值。
    """
    now = today or datetime.now()
    daily = prov.get("daily") or {}
    if not daily:
        return 0.0
    total_w, total_c = 0.0, 0.0
    for i in range(1, n_days + 1):
        d = (now - timedelta(days=i))
        key = d.strftime("%Y-%m-%d")
        consumed = _to_float(daily.get(key))
        if consumed <= 0:
            continue
        w = day_weight(cal, d.date())
        if w <= 0:
            # 上学日几乎不用，样本价值低，剔除
            continue
        total_w += w
        total_c += consumed / w
    if total_w <= 0:
        return 0.0
    return total_c / total_w


def predict(state, key, cal, today=None):
    """对单个平台做预测，产出看板需要的全部指标。"""
    prov = _prov(state, key)
    now = today or datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    bal = prov.get("balance") or {}
    remaining = _to_float(bal.get("remaining"))
    total = bal.get("total")
    used = bal.get("used")

    w_today = day_weight(cal, now.date())
    t_type = day_type(cal, now.date())
    daily = prov.get("daily") or {}
    used_today = _to_float(daily.get(today_str))

    avg = recent_avg(prov, cal, today=now)
    predicted_today = round(avg * w_today, 1)

    res = {
        "key": key,
        "balance": {"total": total, "used": used, "remaining": remaining},
        "checkin": prov.get("checkin") or {},
        "used_today": round(used_today, 2),
        "predicted_today": predicted_today,
        "avg_per_usable_day": round(avg, 1),
        "day_type": t_type,
        "day_weight": w_today,
        "daily": dict(sorted(daily.items())[-30:]),
        "packs": prov.get("packs") or [],
    }

    # 1) 今日可用量：在「不超上限」前提下尽量多用
    res["today_advice"] = _today_advice(prov, bal, predicted_today, used_today, w_today, avg, now)

    # 2) 低余额告警（类似钉钉的剩余提醒）
    res["alert"] = _alert(key, bal, remaining, avg, used_today, predicted_today, w_today)

    # 3) 耗尽预测 + 临近过期积分规划
    res["runway"] = _runway(prov, bal, avg, w_today, now, cal)
    res["expiry_plan"] = _expiry_plan(prov, cal, now, avg)

    # 未来 7 天签到收入
    res["future_checkin"] = _future_checkin(prov, cal, now, key)
    return res


def _today_advice(prov, bal, predicted, used_today, w_today, avg, now):
    """今日用量建议：给一个「目标区间」而不是单点。

    下限 R = 到最近到期事件前必须烧掉的量（防浪费）
    上限   = 该包的 remaining（超了就是浪费，且账单按上限算）
    目标   = 常规节奏预测值，并夹在 [R, 上限] 内
    """
    packs = [p for p in (prov.get("packs") or [])
             if p.get("alive") and _to_float(p.get("remaining")) > 0]
    cap = sum(_to_float(p.get("remaining")) for p in packs) if packs else _to_float(bal.get("remaining"))

    # 防浪费底线：最近一个到期日前必须用掉的量
    must = 0.0
    nearest = None
    if packs:
        soon = sorted([p for p in packs if p.get("expire_ts")],
                      key=lambda p: p["expire_ts"])
        for p in soon:
            must += _to_float(p.get("remaining"))
            left_days = (p["expire_ts"] - time.time()) / 86400.0
            if left_days > 0:
                nearest = p
                break
        if nearest is not None:
            # 折算到今天：到期前的可用容量
            cap_days = 0.0
            d = now.date()
            while d <= datetime.fromtimestamp(nearest["expire_ts"]).date():
                cap_days += day_weight(cal_ref[0], d) if cal_ref[0] else 1.0
                d += timedelta(days=1)
            if cap_days > 0:
                must_per_day = must / cap_days
            else:
                must_per_day = must
        else:
            must_per_day = 0.0
    else:
        must_per_day = 0.0

    # 目标 = 预测值与防浪费底线取大，再夹在上限内
    target = max(predicted, must_per_day)
    if cap > 0:
        target = min(target, cap)
    target = max(target, 0.0)

    # 上学日用不着，降到 0
    if w_today <= 0:
        target = 0.0

    left = max(target - used_today, 0.0)
    return {
        "target": round(target, 1),
        "min_must_use": round(must_per_day, 1),
        "cap": round(cap, 1),
        "suggest_remaining": round(left, 1),
        "nearest_expire": (nearest or {}).get("expire_str", ""),
        "note": ("今日是上学日，无需使用" if w_today <= 0 else
                 "建议在 %s 前用完 %s 分" % ((nearest or {}).get("expire_str", "—"),
                                       round(left, 1)) if left > 0 else
                 "今日节奏正常，无需额外使用"),
    }


def _alert(key, bal, remaining, avg, used_today, predicted, w_today):
    """剩余告警：分档给级别 + 文案。类似钉钉的剩余提醒。"""
    total = bal.get("total")
    pct = None
    if total and _to_float(total) > 0:
        pct = round(remaining / _to_float(total) * 100, 1)

    # 可用天数（按加权日均）
    days_left = None
    if avg > 0 and w_today > 0:
        days_left = int(remaining / (avg * w_today)) if remaining > 0 else 999

    level = "ok"
    if remaining <= 0:
        level = "critical"
    elif days_left is not None and days_left <= 2:
        level = "critical"
    elif pct is not None and pct <= 10:
        level = "warning"
    elif days_left is not None and days_left <= 5:
        level = "warning"

    msg = "余额充足"
    if level == "critical":
        msg = "积分即将耗尽（剩余 %s 分）" % round(remaining, 1)
    elif level == "warning":
        msg = "余额偏低（剩余 %s 分%s）" % (
            round(remaining, 1),
            "，约 %d 个可用日" % days_left if days_left is not None else "")
    return {"level": level, "message": msg, "percent": pct, "days_left": days_left}


def _runway(prov, bal, avg, w_today, now, cal):
    """预测何时耗尽（跳过上学日）。"""
    remaining = _to_float(bal.get("remaining"))
    if avg <= 0:
        return {"days": None, "date": None, "note": "暂无足够历史数据，无法预测耗尽时间"}
    if remaining <= 0:
        return {"days": 0, "date": now.strftime("%Y-%m-%d"), "note": "积分已耗尽"}

    acc, d = 0.0, now
    for i in range(400):  # 上限约 13 个月
        w = day_weight(cal, d.date())
        acc += avg * w
        if acc >= remaining:
            return {
                "days": i + 1,
                "date": d.strftime("%Y-%m-%d"),
                "note": "按加权日均 %s 分/可用日计算" % round(avg, 1),
            }
        d += timedelta(days=1)
    return {"days": None, "date": None, "note": "预计 13 个月内不会耗尽"}


def _expiry_plan(prov, cal, now, avg):
    """临近过期积分规划。

    核心：算出每个即将到期的包「必须在到期前用掉多少」，
    并按剩余可用日摊到每天；上学日不安排任务（权重 0）。
    """
    packs = [p for p in (prov.get("packs") or [])
             if p.get("alive") and _to_float(p.get("remaining")) > 0
             and p.get("expire_ts", 0) > time.time()]
    if not packs:
        return {"items": [], "note": "无按包过期的积分（周期额度统一重置）"}

    packs = sorted(packs, key=lambda p: p["expire_ts"])
    items = []
    for p in packs[:6]:
        remain = _to_float(p.get("remaining"))
        expire_dt = datetime.fromtimestamp(p["expire_ts"])
        # 过期前的可用容量（上学日权重 0 不算）
        cap = 0.0
        d = now.date()
        while d <= expire_dt.date():
            cap += day_weight(cal, d)
            d += timedelta(days=1)
        # 中午前到期算前一天（用户中午前用不了电脑）
        deadline = expire_dt
        if expire_dt.hour < 12:
            deadline = expire_dt - timedelta(days=1)
        usable_days = max(int(round(cap)), 0)
        per_day = round(remain / usable_days, 1) if usable_days > 0 else remain

        items.append({
            "name": p.get("name", ""),
            "group": p.get("group", ""),
            "remaining": round(remain, 1),
            "expire_str": p.get("expire_str") or expire_dt.strftime("%m-%d %H:%M"),
            "usable_days": usable_days,
            "per_day_need": per_day,
            "risk": ("高" if per_day > avg * 1.5 and usable_days > 0 else
                     "中" if per_day > avg else "低"),
        })
    return {"items": items, "note": "上学日不计入可用容量"}


def _future_checkin(prov, cal, now, key):
    """未来 7 天预计签到入账（含周末/上学日区分）。"""
    items = []
    for i in range(1, 8):
        d = now + timedelta(days=i)
        c = CHECKIN_CREDITS.get(key, 0)
        items.append({
            "date": d.strftime("%m-%d"),
            "day_type": day_type(cal, d.date()),
            "credit": c,
        })
    total = sum(CHECKIN_CREDITS.get(key, 0) for _ in range(7))
    return {"items": items, "total_7d": total}


# 供 _today_advice 内部使用（避免层层传参）
cal_ref = [None]


def collect_all():
    """跑一遍三家采集 + 预测，落盘并返回完整报告。"""
    cal_mod = load_school_calendar()
    cal_ref[0] = cal_mod

    state = load_state()
    results = {}

    for key, fn in (("trae", collect_trae),
                    ("workbuddy", collect_workbuddy),
                    ("minimax", collect_minimax)):
        try:
            results[key] = fn(state)
        except Exception as e:
            results[key] = {"ok": False, "error": "未捕获异常: %s" % e}
        log("%s 采集: %s" % (key, "OK" if results[key].get("ok") else
                             results[key].get("error", "失败")))

    state["updated_at"] = datetime.now().isoformat()
    save_state(state)

    # 预测（三家统一口径）
    report = {"updated_at": state["updated_at"],
              "school_mode": _school_mode(cal_mod),
              "providers": {}}
    for key in ("trae", "workbuddy", "minimax"):
        try:
            report["providers"][key] = predict(state, key, cal_mod)
        except Exception as e:
            report["providers"][key] = {"error": "预测失败: %s" % e}
    # 采集错误一并带出，前端可见
    for key, r in results.items():
        if not r.get("ok") and r.get("error"):
            report["providers"].setdefault(key, {})["error"] = r["error"]
        else:
            report["providers"].setdefault(key, {})["meta"] = {
                k: v for k, v in r.items() if k != "ok"}
    return report


if __name__ == "__main__":
    rep = collect_all()
    print(json.dumps(rep, ensure_ascii=False, indent=2))
