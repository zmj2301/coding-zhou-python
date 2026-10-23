#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""实时公交换乘规划器。

核心思想：每一次查询都重新拉取实时车辆 ETA，
按「步行 + 等车 + 乘车 + 换乘等待」总耗时排序。
实时数据永不缓存，只有静态线路站点表可缓存。
"""
import math
import time

from busapp import chelaile_client as cl

WALK_SPEED_KMH = 4.5# 步行速度
ROAD_FACTOR = 1.35        # 直线距离 → 实际路网距离 的放大系数
MIN_BOARD_MIN = 2.0       # 最小候车时间（提前到站也要等）
MAX_TRANSFERS = 3
AVG_DWELL_SEC = 25# 每站平均停靠秒数
FALLBACK_SPEED_KMH = 18.0  # 无实时数据时的公交平均时速

# 上游偶发的占位/无效站名，不可作为换乘点
_PLACEHOLDER_STOPS = {"公交停靠站", "未知站", "undefined", "null", "-"}


def haversine_m(lat1, lng1, lat2, lng2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def walk_minutes(dist_m):
    return (dist_m * ROAD_FACTOR) / 1000.0 / WALK_SPEED_KMH * 60.0


def in_operation(line, now=None):
    """判断线路当前是否在运营时间内。

    上游用 state 字段表达：-12=不在运营时间，-3=末班已过，其余为正常。
    优先采信上游判断，缺失时才用首末班时间估算。
    """
    import datetime
    now = now or datetime.datetime.now()

    state = line.get("state")
    if state is not None:
        try:
            st = int(state)
            if st in (-12, -3):
                return False
            if st >= 0:
                return True
        except (TypeError, ValueError):
            pass

    cur = now.hour * 60 + now.minute

    def parse(s):
        try:
            h, m = s.split(":")
            return int(h) * 60 + int(m)
        except Exception:
            return None

    f, l = parse(line.get("firstTime", "")), parse(line.get("lastTime", ""))
    if f is None or l is None:
        return True
    if f <= l:
        return f <= cur <= l
    # 跨零点线路
    return cur >= f or cur <= l


class Stop(object):
    """站点：坐标 + 途经线路 + 各线实时车辆。"""

    def __init__(self, name, s_id, lat, lng, distance=0):
        self.name = name
        self.s_id = s_id
        self.lat = lat
        self.lng = lng
        self.distance = distance      # 距查询原点的距离(m)
        self.lines = {}               # lineNo -> {"line":…, "states":[…], "eta": float|None}

    def entries(self):
        """产出 (线路名, 信息) 列表。lines 以 sId 为键，线路名在 line_no。"""
        for info in self.lines.values():
            yield info.get("line_no", "?"), info

    def best_eta(self, line_no):
        """该线路最近一辆车的等待分钟数；无车返回 None。"""
        best = None
        for name, info in self.entries():
            if name != line_no or not info["states"]:
                continue
            e = info["eta"]
            if e is not None and (best is None or e < best):
                best = e
        return best

    def line_nos(self):
        return [v.get("line_no", "?") for v in self.lines.values()]


def resolve_origin(query):
    """把用户输入解析成 (候选站点列表, 描述)。

    优先：同名公交站 → 否则用 POI 坐标就近匹配（本次验证路径）。
    """
    import datetime
    now = datetime.datetime.now()

    try:
        data = cl.search(query)
        result = data.get("result", {})
    except cl.ChelaileError as exc:
        return [], "搜索失败: %s" % exc

    stops = []

    # 路径1：直接命中同名站点
    for s in result.get("stations") or []:
        if s.get("physicalStId"):
            try:
                detail = cl.stop_detail(s["physicalStId"], s.get("namesakeStId", ""))
                stops.append(_build_stop_from_detail(s, detail, now, 0))
            except cl.ChelaileError:
                continue

    if stops:
        return stops[:3], "同名公交站"

    # 路径2：POI 坐标 → 就近匹配
    pois = result.get("pois") or []
    if not pois:
        return [], "未找到站点或地点（%s）" % query

    poi = pois[0]
    lat, lng = poi.get("lat"), poi.get("lng")
    if lat is None:
        return [], "地点缺少坐标"

    try:
        near = cl.nearby_stops(lat, lng)
    except cl.ChelaileError as exc:
        return [], "附近站点查询失败: %s" % exc

    # 取前 12 个站而非 5 个：常见走法需要的线路可能停靠在较远站点
    # （实测：未来素养→电调中心 657m，能上综保区河东专线，但排在第 10 位）
    for st in (near.get("nearSts") or [])[:12]:
        lines = st.get("lines") or []
        if not lines:
            continue
        tgt = lines[0].get("targetStation", {})
        sid = tgt.get("sId", "")
        if not sid:
            continue
        lines_map = {}
        for ln in lines:
            L = ln.get("line") or {}
            states = list(ln.get("stnStates") or [])
            ts = ln.get("targetStation") or {}
            key = "%s|%s" % (ts.get("sId") or sid, L.get("name", "?"))
            eta = _min_eta(states, now)
            if key in lines_map and lines_map[key]["states"]:
                merged = lines_map[key]["states"] + states
                best_line = lines_map[key]["line"]
                if len(L) > len(best_line):
                    best_line = L
                lines_map[key] = dict(lines_map[key], line=best_line,
                                       states=merged, eta=_min_eta(merged, now))
            else:
                lines_map[key] = {"line": L, "states": states, "eta": eta,
                                  "start": L.get("startSn", ""), "end": L.get("endSn", ""),
                                  "first": L.get("firstTime", ""), "last": L.get("lastTime", ""),
                                  "price": L.get("price", ""), "line_no": L.get("name", "?")}
        s_obj = Stop(tgt.get("sn", "?"), sid, lat, lng, st.get("distance", 0))
        s_obj.lines = lines_map
        stops.append(s_obj)

    return stops, "「%s」就近匹配" % poi.get("sn1", query)


def resolve_destination(query):
    """解析终点站点（只需静态线路集合 + 坐标）。"""
    import datetime
    now = datetime.datetime.now()
    try:
        data = cl.search(query)
        result = data.get("result", {})
    except cl.ChelaileError as exc:
        return [], "终点搜索失败: %s" % exc

    out = []
    for s in (result.get("stations") or [])[:3]:
        if not s.get("physicalStId"):
            continue
        try:
            detail = cl.stop_detail(s["physicalStId"], s.get("namesakeStId", ""))
        except cl.ChelaileError:
            continue
        st = _build_stop_from_detail(s, detail, now, 0)
        st.distance = 0
        out.append(st)
    return out, "同名公交站"


def _build_stop_from_detail(raw, detail, now, distance):
    sid = raw.get("sId", "")
    name = raw.get("sn", "")
    lat = raw.get("lat") or detail.get("lat") or 0
    lng = raw.get("lng") or detail.get("lng") or 0
    st = Stop(name, sid, lat, lng, distance)

    # 用 sId 做索引（同名线路的不同方向共享 sId，可合并实时车辆）
    lines_map = {}
    for sl in detail.get("stationList") or []:
        for ln in sl.get("lines") or []:
            L = ln.get("line") or {}
            states = list(ln.get("stnStates") or [])
            ts = ln.get("targetStation") or {}
            key = "%s|%s" % (ts.get("sId") or sid, L.get("name", "?"))
            eta = _min_eta(states, now)
            if key in lines_map:
                # 同站同线路的另一方向：合并车辆，保留信息更完整的 line
                merged = lines_map[key]["states"] + states
                best_line = lines_map[key]["line"]
                if len(L) > len(best_line):
                    best_line = L
                lines_map[key] = {
                    "line": best_line,
                    "states": merged,
                    "eta": _min_eta(merged, now),
                    "start": best_line.get("startSn", ""),
                    "end": best_line.get("endSn", ""),
                    "first": best_line.get("firstTime", ""),
                    "last": best_line.get("lastTime", ""),
                    "price": best_line.get("price", ""),
                    "line_no": best_line.get("name", "?"),
                }
            else:
                lines_map[key] = {
                    "line": L,
                    "states": states,
                    "eta": eta,
                    "start": L.get("startSn", ""),
                    "end": L.get("endSn", ""),
                    "first": L.get("firstTime", ""),
                    "last": L.get("lastTime", ""),
                    "price": L.get("price", ""),
                    "line_no": L.get("name", "?"),
                }
    st.lines = lines_map
    return st


def _min_eta(states, now):
    best = None
    for s in states or []:
        at = s.get("arrivalTime", -1)
        if at and at > 0:
            import datetime
            m = (datetime.datetime.fromtimestamp(at / 1000) - now).total_seconds() / 60.0
            m = max(0.0, m)
            if best is None or m < best:
                best = m
    return best


_LINE_CACHE = {}
# 线路名 -> [(lineId, 方向描述)]，枚举该线路所有方向（换乘必须考虑全部方向）
_DIRECTION_CACHE = {}


def get_line_directions(line_no):
    """枚举一条线路的所有运行方向。

    站点接口只返回单个方向，直接拿来做换乘会把另一方向的可行方案误判为逆行。
    """
    if line_no in _DIRECTION_CACHE:
        return _DIRECTION_CACHE[line_no]
    dirs = []
    try:
        result = cl.search(line_no).get("result", {})
        seen = set()
        for l in (result.get("lines") or []):
            lid = l.get("lineId")
            if not lid or lid in seen:
                continue
            seen.add(lid)
            dirs.append((lid, "%s→%s" % (l.get("startSn", ""), l.get("endSn", ""))))
    except cl.ChelaileError:
        pass
    _DIRECTION_CACHE[line_no] = dirs
    return dirs


def get_line_stations(line_no, line_id):
    """取线路完整站点序列（含坐标）。静态数据，可缓存。"""
    ck = (line_no, line_id)
    if ck in _LINE_CACHE:
        return _LINE_CACHE[ck]
    try:
        d = cl.line_detail(line_id)
    except cl.ChelaileError:
        return None
    sts = d.get("stations") or []
    if not sts:
        return None
    names = [s.get("sn", "") for s in sts]
    coords = [(s.get("lat"), s.get("lng")) for s in sts]
    info = {
        "name": line_no,
        "start": names[0] if names else "",
        "end": names[-1] if names else "",
        "first": (d.get("line") or {}).get("firstTime", ""),
        "last": (d.get("line") or {}).get("lastTime", ""),
        "price": (d.get("line") or {}).get("price", ""),
        "stations": names,
        "coords": coords,
        "n": len(names),
    }
    _LINE_CACHE[ck] = info
    return info


class Leg(object):
    def __init__(self, kind, title, minutes, detail=""):
        self.kind = kind          # walk / bus
        self.title = title
        self.minutes = minutes
        self.detail = detail

    def as_dict(self):
        return {"kind": self.kind, "title": self.title,
                "minutes": round(self.minutes, 1), "detail": self.detail}


class Plan(object):
    def __init__(self):
        self.legs = []
        self.total = 0.0
        self.transfers = 0
        self.has_realtime = False
        self.note = ""

    def add(self, kind, title, minutes, detail=""):
        """追加一段行程并累加总耗时。"""
        self.legs.append(Leg(kind, title, minutes, detail))
        self.total += minutes
        return self

    def as_dict(self):
        return {
            "total_minutes": round(self.total, 1),
            "transfers": self.transfers,
            "has_realtime": self.has_realtime,
            "legs": [l.as_dict() for l in self.legs],
            "note": self.note,
        }


def _short_station(name):
    """站名精简：去掉括号说明，保留主干名。"""
    if not name:
        return name
    if "（" in name:
        head = name.split("（")[0]
        if len(head) >= 3:
            return head
    if "(" in name:
        head = name.split("(")[0]
        if len(head) >= 3:
            return head
    return name


def _match_station(stations, name):
    """在站点列表中定位目标站。

    上游同一站在不同线路表中后缀可能不同（如「住房公积金中心」/「住房公积金中心东」），
    故先精确匹配，失败再退化为包含匹配，并保证可反向到达（index+1）。
    """
    if name in stations:
        return stations.index(name)
    # 精确匹配失败：尝试「A 是 B 的前缀」或反之
    for i, s in enumerate(stations):
        if not s:
            continue
        if s.startswith(name) or name.startswith(s):
            return i
    # 再退化为包含
    for i, s in enumerate(stations):
        if s and (s in name or name in s):
            return i
    return None


def _ride_minutes(route, i, j):
    """估算从 route 的第 i 站到第 j 站的乘车时间。

    优先用线路真实路径长度推算，无坐标时按站数估算。
    """
    if route is None or i is None or j is None or j <= i:
        return None
    stops = j - i

    dist_m = 0.0
    coords = route["coords"]
    have = 0
    for k in range(i, min(j, len(coords) - 1)):
        a, b = coords[k], coords[k + 1]
        if a[0] and b[0]:
            dist_m += haversine_m(a[0], a[1], b[0], b[1])
            have += 1
    if dist_m > 0 and have >= 2:
        km = dist_m * ROAD_FACTOR / 1000.0
        return km / FALLBACK_SPEED_KMH * 60.0 + stops * AVG_DWELL_SEC / 60.0
    return stops * 1.8 + stops * AVG_DWELL_SEC / 60.0


def plan_route(origin_stops, dest_stops, max_plans=6):
    """核心规划：在起终点站点集合间搜索换乘方案，按总耗时排序。"""
    import datetime
    now = datetime.datetime.now()

    plans = []
    for dst in dest_stops:
        # 直达：起点某站有某线同时停靠起终点
        for src in origin_stops:
            for line_no, info in src.entries():
                if line_no not in dst.line_nos():
                    continue
                L = info["line"]
                # 直达也需枚举方向：站点接口返回的 lineId 只是其中一个方向
                for lid, _dir in get_line_directions(line_no) or [(L.get("lineId", ""), "")]:
                    route = get_line_stations(line_no, lid)
                    if not route:
                        continue
                    i = _match_station(route["stations"], src.name)
                    j = _match_station(route["stations"], dst.name)
                    if i is None or j is None or j <= i:
                        continue
                    ride = _ride_minutes(route, i, j)
                    if ride is None:
                        continue
                eta = src.best_eta(line_no)
                p = Plan()
                if src.distance:
                    p.legs.append(Leg("walk", "步行到%s" % src.name,
                                      walk_minutes(src.distance),
                                      "%d 米" % src.distance))
                if not in_operation(L, now):
                    p.legs.append(Leg("walk", "等%s路" % line_no, 5.0,
                                      "该线已收班（末班 %s），仅供参考" % L.get("lastTime", "?")))
                    p.note = "包含已收班线路"
                elif eta is None:
                    wait = 5.0
                    p.legs.append(Leg("walk", "等%s路" % line_no, wait, "暂无实时车，按经验值"))
                else:
                    wait = max(eta, MIN_BOARD_MIN)
                    p.legs.append(Leg("bus", "等%s路" % line_no, wait,
                                      "最近一车 %.1f 分钟后到" % eta))
                    p.has_realtime = True
                p.legs.append(Leg("bus", "%s路 %s→%s" % (line_no, _short_station(src.name), _short_station(dst.name)),
                                  ride, info.get("price", "")))
                p.total = sum(l.minutes for l in p.legs)
                p.transfers = 0
                plans.append(p)

    # 一次换乘：起点站上车 → 换乘站 → 终点站下车
    #
    # 关键：两段都必须枚举线路的所有运行方向。
    # 站点接口只返回单个方向，若只用它做换乘，会把另一方向的可行方案误判为逆行而丢弃
    # （实测：K2 从「住房公积金中心」到「铭鸿翰林居」仅在「建设路口→湘潭北站」方向成立）。
    for src in origin_stops:
        for dst in dest_stops:
            if src.s_id == dst.s_id:
                continue
            for line_no, info in src.entries():
                if not in_operation(info["line"], now):
                    op1 = False
                else:
                    op1 = True
                L = info["line"]

                # 第一段：枚举所有方向，取包含起点站的那个
                for lid1, dir1 in get_line_directions(line_no):
                    r1 = get_line_stations(line_no, lid1)
                    if not r1:
                        continue
                    i = _match_station(r1["stations"], src.name)
                    if i is None:
                        continue

                    for line2_no, info2 in dst.entries():
                        if line2_no == line_no:
                            continue
                        # 第二段：枚举所有方向，须同时含换乘点与终点且顺序正确
                        for lid2, dir2 in get_line_directions(line2_no):
                            r2 = get_line_stations(line2_no, lid2)
                            if not r2:
                                continue
                            d_idx = _match_station(r2["stations"], dst.name)
                            if d_idx is None:
                                continue

                            for k in range(i + 1, len(r1["stations"])):
                                transfer = r1["stations"][k]
                                if not transfer or transfer in _PLACEHOLDER_STOPS:
                                    continue
                                t_idx = _match_station(r2["stations"], transfer)
                                if t_idx is None or d_idx <= t_idx:
                                    continue

                                ride1 = _ride_minutes(r1, i, k)
                                if ride1 is None:
                                    continue
                                ride2 = _ride_minutes(r2, t_idx, d_idx)
                                if ride2 is None:
                                    continue

                                eta1 = src.best_eta(line_no)
                                eta2 = dst.best_eta(line2_no)
                                p = Plan()
                                if src.distance:
                                    p.add("walk", "步行到%s" % _short_station(src.name),
                                          walk_minutes(src.distance),
                                          "%d 米" % src.distance)
                                if not op1:
                                    p.add("walk", "等%s路" % line_no, 5.0,
                                          "该线已收班（末班 %s）" % L.get("lastTime", "?"))
                                    p.note = "包含已收班线路"
                                elif eta1 is None:
                                    p.add("walk", "等%s路" % line_no, 5.0, "暂无实时车")
                                else:
                                    p.add("bus", "等%s路" % line_no,
                                          max(eta1, MIN_BOARD_MIN),
                                          "%.1f 分钟后到" % eta1)
                                    p.has_realtime = True
                                p.add("bus", "%s路 至 %s" % (line_no, _short_station(transfer)),
                                      ride1, info.get("price", ""))
                                if eta2 is None:
                                    p.add("walk", "换乘等%s路" % line2_no, 5.0, "暂无实时车")
                                else:
                                    p.add("bus", "换乘%s路" % line2_no,
                                          max(eta2, MIN_BOARD_MIN),
                                          "%.1f 分钟后到" % eta2)
                                    p.has_realtime = True
                                p.add("bus", "%s路 至%s" % (line2_no, _short_station(dst.name)),
                                      ride2, info2.get("price", ""))
                                p.transfers = 1
                                plans.append(p)

    # 去重：保留每组不同(线路组合)中最快的
    best = {}
    for p in plans:
        key = tuple(l.title for l in p.legs if l.kind == "bus")
        if key not in best or p.total < best[key].total:
            best[key] = p

    # 排序：可用方案优先，其次按总耗时
    ranked = sorted(best.values(),
                    key=lambda x: (1 if x.note == "包含已收班线路" else 0, x.total))

    # 起点多样性：每个出发站至少保留一个最快方案。
    # 否则最近的站点会占满名额，把用户常用的远站走法（如 657m 外的电调中心上综保区河东专线）
    # 全部挤掉——实测这就是"为什么没有我的走法"的直接原因。
    by_origin = {}
    for p in ranked:
        origin = p.legs[0].title if p.legs else "?"
        if origin not in by_origin:
            by_origin[origin] = p
    out = list(by_origin.values())
    for p in ranked:
        if len(out) >= max_plans:
            break
        if p not in out:
            out.append(p)
    out.sort(key=lambda x: (1 if x.note == "包含已收班线路" else 0, x.total))
    if not out:
        fallback = Plan()
        fallback.note = "未找到可行公交方案"
        return [fallback]
    for p in out[:max_plans]:
        if not p.has_realtime and p.note != "包含已收班线路":
            p.note = "该方案缺少实时车辆数据，等待时间为估算值"
    return out[:max_plans]


def _transfer_eta(dst_stop, line_no, transfer_name, now):
    """换乘点上车等待时间：若终点站数据里含该线则用它，否则按经验值。"""
    return dst_stop.best_eta(line_no)