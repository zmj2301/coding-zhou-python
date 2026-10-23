package com.workbuddy.xiangtanbus;

import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 实时公交换乘规划器。
 *
 * 每次查询重新拉取实时车辆 ETA，按「步行 + 等车 + 乘车 + 换乘等待」总耗时排序。
 * 实时数据不缓存，仅线路静态站点表做内存缓存。
 */
public final class Planner {

    private static final double WALK_SPEED_KMH = 4.5;
    private static final double ROAD_FACTOR = 1.35;
    private static final double MIN_BOARD_MIN = 2.0;
    private static final double AVG_DWELL_SEC = 25;
    private static final double FALLBACK_SPEED_KMH = 18.0;

    /** 上游偶发的占位站名，不可作为换乘点 */
    private static final Set<String> PLACEHOLDER = new HashSet<>();
    static {
        PLACEHOLDER.add("公交停靠站");
        PLACEHOLDER.add("未知站");
        PLACEHOLDER.add("undefined");
        PLACEHOLDER.add("-");
    }

    private Planner() {}

    // ---------- 基础计算 ----------

    static double haversineM(double lat1, double lng1, double lat2, double lng2) {
        final double r = 6371000.0;
        double p1 = Math.toRadians(lat1), p2 = Math.toRadians(lat2);
        double dp = Math.toRadians(lat2 - lat1);
        double dl = Math.toRadians(lng2 - lng1);
        double h = Math.pow(Math.sin(dp / 2), 2)
                + Math.cos(p1) * Math.cos(p2) * Math.pow(Math.sin(dl / 2), 2);
        return 2 * r * Math.asin(Math.sqrt(h));
    }

    static double walkMinutes(double distM) {
        return (distM * ROAD_FACTOR) / 1000.0 / WALK_SPEED_KMH * 60.0;
    }

    /** 站名精简：去掉括号说明 */
    static String shortStation(String name) {
        if (name == null || name.isEmpty()) return name;
        int i = name.indexOf('（');
        if (i > 0 && name.length() - i >= 3) return name.substring(0, i);
        int j = name.indexOf('(');
        if (j > 0 && name.length() - j >= 3) return name.substring(0, j);
        return name;
    }

    /**
     * 在站点列表中定位目标站。
     * 上游同一站在不同线路表中后缀可能不同（住房公积金中心 / 住房公积金中心东），
     * 故先精确匹配，再退化为前缀匹配、包含匹配。
     */
    static int matchStation(List<String> stations, String name) {
        int idx = stations.indexOf(name);
        if (idx >= 0) return idx;
        for (int i = 0; i < stations.size(); i++) {
            String s = stations.get(i);
            if (s == null || s.isEmpty()) continue;
            if (s.startsWith(name) || name.startsWith(s)) return i;
        }
        for (int i = 0; i < stations.size(); i++) {
            String s = stations.get(i);
            if (s == null || s.isEmpty()) continue;
            if (s.contains(name) || name.contains(s)) return i;
        }
        return -1;
    }

    /** 判断线路当前是否在运营时间内 */
    static boolean inOperation(JSONObject line, int curMinutes) {
        if (line == null) return true;
        int state = line.optInt("state", Integer.MIN_VALUE);
        if (state != Integer.MIN_VALUE) {
            if (state == -12 || state == -3) return false;
            if (state >= 0) return true;
        }
        int f = parseTime(line.optString("firstTime", ""));
        int l = parseTime(line.optString("lastTime", ""));
        if (f < 0 || l < 0) return true;
        if (f <= l) return f <= curMinutes && curMinutes <= l;
        return curMinutes >= f || curMinutes <= l;
    }

    private static int parseTime(String s) {
        try {
            int c = s.indexOf(':');
            return Integer.parseInt(s.substring(0, c)) * 60 + Integer.parseInt(s.substring(c + 1));
        } catch (Exception e) {
            return -1;
        }
    }

    static int nowMinutes() {
        java.util.Calendar c = java.util.Calendar.getInstance();
        return c.get(java.util.Calendar.HOUR_OF_DAY) * 60 + c.get(java.util.Calendar.MINUTE);
    }

    // ---------- 数据模型 ----------

    /** 站点：坐标 + 途经线路 + 各线实时车辆 */
    public static class Stop {
        public String name = "";
        public String sId = "";
        public double lat, lng;
        public double distance = 0;   // 距查询原点距离(m)
        /** key: "sId|线路名" */
        public final Map<String, LineInfo> lines = new LinkedHashMap<>();

        /** 取该线路最近一车的等待分钟；无车返回 null */
        Double bestEta(String lineNo) {
            Double best = null;
            for (Map.Entry<String, LineInfo> e : lines.entrySet()) {
                if (!e.getValue().lineNo.equals(lineNo)) continue;
                Double v = e.getValue().eta;
                if (v != null && (best == null || v < best)) best = v;
            }
            return best;
        }

        Set<String> lineNos() {
            Set<String> s = new HashSet<>();
            for (LineInfo li : lines.values()) s.add(li.lineNo);
            return s;
        }
    }

    /** 线路信息 */
    public static class LineInfo {
        public String lineNo = "?";
        public JSONObject line;      // 上游 line 节点
        public JSONArray states;     // 实时车辆
        public Double eta;           // 最近车辆等待分钟
    }

    public static class Leg {
        public final String kind;    // walk / bus
        public final String title;
        public final double minutes;
        public final String detail;

        public Leg(String kind, String title, double minutes, String detail) {
            this.kind = kind; this.title = title;
            this.minutes = minutes; this.detail = detail == null ? "" : detail;
        }
    }

    public static class Plan {
        public final List<Leg> legs = new ArrayList<>();
        public double total = 0;
        public int transfers = 0;
        public boolean hasRealtime = false;
        public String note = "";

        public void add(String kind, String title, double minutes, String detail) {
            legs.add(new Leg(kind, title, minutes, detail));
            total += minutes;
        }
    }

    // ---------- 线路站点表（静态，可缓存） ----------

    private static final Map<String, LineRoute> ROUTE_CACHE = new HashMap<>();

    /** 线路完整站点序列 */
    public static class LineRoute {
        public String lineNo = "";
        public String lineId = "";
        public final List<String> stations = new ArrayList<>();
        public final List<double[]> coords = new ArrayList<>();
    }

    private static synchronized LineRoute getRoute(String lineNo, String lineId) {
        if (lineId == null || lineId.isEmpty()) return null;
        String key = lineNo + "|" + lineId;
        if (ROUTE_CACHE.containsKey(key)) return ROUTE_CACHE.get(key);
        try {
            JSONObject d = ChelaileClient.lineDetail(lineId);
            JSONArray sts = d.optJSONArray("stations");
            if (sts == null || sts.length() == 0) return null;
            LineRoute r = new LineRoute();
            r.lineNo = lineNo;
            r.lineId = lineId;
            for (int i = 0; i < sts.length(); i++) {
                JSONObject s = sts.getJSONObject(i);
                r.stations.add(s.optString("sn", ""));
                r.coords.add(new double[]{s.optDouble("lat", 0), s.optDouble("lng", 0)});
            }
            ROUTE_CACHE.put(key, r);
            return r;
        } catch (Exception e) {
            return null;
        }
    }

    /** 估算乘车时间：优先真实路径长度推算 */
    private static double rideMinutes(LineRoute r, int i, int j) {
        int stops = j - i;
        double distM = 0;
        int have = 0;
        for (int k = i; k < j && k + 1 < r.coords.size(); k++) {
            double[] a = r.coords.get(k), b = r.coords.get(k + 1);
            if (a[0] != 0 && b[0] != 0) {
                distM += haversineM(a[0], a[1], b[0], b[1]);
                have++;
            }
        }
        if (distM > 0 && have >= 2) {
            double km = distM * ROAD_FACTOR / 1000.0;
            return km / FALLBACK_SPEED_KMH * 60.0 + stops * AVG_DWELL_SEC / 60.0;
        }
        return stops * 1.8 + stops * AVG_DWELL_SEC / 60.0;
    }

    // ---------- 解析 ----------

    /** 取某站所有线路的最近 ETA（毫秒时间戳 → 分钟） */
    private static Double minEta(JSONArray states, long nowMs) {
        if (states == null) return null;
        Double best = null;
        for (int i = 0; i < states.length(); i++) {
            JSONObject s = states.optJSONObject(i);
            if (s == null) continue;
            long at = s.optLong("arrivalTime", -1);
            if (at > 0) {
                double m = (at - nowMs) / 60000.0;
                if (m < 0) m = 0;
                if (best == null || m < best) best = m;
            }
        }
        return best;
    }

    private static Stop buildStop(JSONObject raw, JSONObject detail, long nowMs) {
        Stop st = new Stop();
        st.name = raw.optString("sn", "");
        st.sId = raw.optString("sId", "");
        st.lat = raw.optDouble("lat", detail.optDouble("lat", 0));
        st.lng = raw.optDouble("lng", detail.optDouble("lng", 0));

        JSONArray list = detail.optJSONArray("stationList");
        if (list == null) return st;

        for (int i = 0; i < list.length(); i++) {
            JSONObject sl = list.optJSONObject(i);
            if (sl == null) continue;
            JSONArray lines = sl.optJSONArray("lines");
            if (lines == null) continue;
            for (int k = 0; k < lines.length(); k++) {
                JSONObject ln = lines.optJSONObject(k);
                if (ln == null) continue;
                JSONObject L = ln.optJSONObject("line");
                if (L == null) continue;
                JSONArray states = ln.optJSONArray("stnStates");
                JSONObject ts = ln.optJSONObject("targetStation");
                String sid = (ts != null) ? ts.optString("sId", st.sId) : st.sId;
                String lineNo = L.optString("name", "?");
                String key = sid + "|" + lineNo;

                LineInfo prev = st.lines.get(key);
                Double eta = minEta(states, nowMs);
                if (prev != null) {
                    // 同站同线路的另一方向：合并车辆，保留信息更全的 line
                    JSONArray merged = new JSONArray();
                    try {
                        if (prev.states != null) for (int a = 0; a < prev.states.length(); a++) merged.put(prev.states.get(a));
                        if (states != null) for (int a = 0; a < states.length(); a++) merged.put(states.get(a));
                    } catch (org.json.JSONException ignored) {
                    }
                    prev.states = merged;
                    prev.eta = minEta(merged, nowMs);
                    if (L.length() > prev.line.length()) prev.line = L;
                } else {
                    LineInfo li = new LineInfo();
                    li.lineNo = lineNo;
                    li.line = L;
                    li.states = states;
                    li.eta = eta;
                    st.lines.put(key, li);
                }
            }
        }
        return st;
    }

    /** 解析起点：优先同名站点，否则 POI 坐标就近匹配 */
    public static List<Stop> resolveOrigin(String query, String[] descOut) throws Exception {
        long now = System.currentTimeMillis();
        JSONObject data = ChelaileClient.search(query);
        JSONObject result = data.optJSONObject("result");
        if (result == null) result = new JSONObject();
        List<Stop> out = new ArrayList<>();

        JSONArray stations = result.optJSONArray("stations");
        if (stations != null) {
            for (int i = 0; i < stations.length() && out.size() < 3; i++) {
                JSONObject s = stations.optJSONObject(i);
                if (s == null) continue;
                String pid = s.optString("physicalStId", "");
                if (pid.isEmpty()) continue;
                try {
                    JSONObject detail = ChelaileClient.stopDetail(pid, s.optString("namesakeStId", ""));
                    out.add(buildStop(s, detail, now));
                } catch (Exception ignored) {}
            }
        }
        if (!out.isEmpty()) {
            descOut[0] = "同名公交站";
            return out;
        }

        JSONArray pois = result.optJSONArray("pois");
        if (pois == null || pois.length() == 0) {
            descOut[0] = "未找到站点或地点（" + query + "）";
            return out;
        }
        JSONObject poi = pois.getJSONObject(0);
        double lat = poi.optDouble("lat", 0), lng = poi.optDouble("lng", 0);
        if (lat == 0) {
            descOut[0] = "地点缺少坐标";
            return out;
        }

        JSONObject near = ChelaileClient.nearbyStops(lat, lng);
        JSONArray nearSts = near.optJSONArray("nearSts");
        if (nearSts != null) {
            for (int i = 0; i < nearSts.length() && out.size() < 5; i++) {
                JSONObject ns = nearSts.optJSONObject(i);
                if (ns == null) continue;
                JSONArray lines = ns.optJSONArray("lines");
                if (lines == null || lines.length() == 0) continue;
                JSONObject ts = lines.getJSONObject(0).optJSONObject("targetStation");
                String sid = (ts != null) ? ts.optString("sId", "") : "";
                if (sid.isEmpty()) continue;

                Stop st = new Stop();
                st.name = (ts != null) ? ts.optString("sn", "?") : "?";
                st.sId = sid;
                st.lat = lat;
                st.lng = lng;
                st.distance = ns.optDouble("distance", 0);

                for (int k = 0; k < lines.length(); k++) {
                    JSONObject ln = lines.optJSONObject(k);
                    JSONObject L = ln.optJSONObject("line");
                    if (L == null) continue;
                    String lineNo = L.optString("name", "?");
                    String key = sid + "|" + lineNo;
                    JSONArray states = ln.optJSONArray("stnStates");
                    if (st.lines.containsKey(key)) continue;
                    LineInfo li = new LineInfo();
                    li.lineNo = lineNo;
                    li.line = L;
                    li.states = states;
                    li.eta = minEta(states, now);
                    st.lines.put(key, li);
                }
                out.add(st);
            }
        }
        descOut[0] = "「" + poi.optString("sn1", query) + "」就近匹配";
        return out;
    }

    /** 解析终点站点 */
    public static List<Stop> resolveDestination(String query, String[] descOut) throws Exception {
        long now = System.currentTimeMillis();
        JSONObject data = ChelaileClient.search(query);
        JSONObject result = data.optJSONObject("result");
        if (result == null) result = new JSONObject();
        List<Stop> out = new ArrayList<>();

        JSONArray stations = result.optJSONArray("stations");
        if (stations != null) {
            for (int i = 0; i < stations.length() && out.size() < 3; i++) {
                JSONObject s = stations.optJSONObject(i);
                if (s == null) continue;
                String pid = s.optString("physicalStId", "");
                if (pid.isEmpty()) continue;
                try {
                    JSONObject detail = ChelaileClient.stopDetail(pid, s.optString("namesakeStId", ""));
                    out.add(buildStop(s, detail, now));
                } catch (Exception ignored) {}
            }
        }
        descOut[0] = "同名公交站";
        return out;
    }

    // ---------- 规划 ----------

    public static List<Plan> plan(List<Stop> origins, List<Stop> dests, int maxPlans) {
        int nowMin = nowMinutes();
        Map<String, Plan> best = new LinkedHashMap<>();

        for (Stop dst : dests) {
            Set<String> dstLines = dst.lineNos();

            // 直达
            for (Stop src : origins) {
                for (LineInfo info : src.lines.values()) {
                    if (!dstLines.contains(info.lineNo)) continue;
                    LineRoute r = getRoute(info.lineNo, info.line.optString("lineId", ""));
                    if (r == null) continue;
                    int i = matchStation(r.stations, src.name);
                    int j = matchStation(r.stations, dst.name);
                    if (i < 0 || j <= i) continue;

                    Plan p = new Plan();
                    p.transfers = 0;
                    if (src.distance > 0) {
                        p.add("walk", "步行到" + shortStation(src.name),
                                walkMinutes(src.distance), Math.round(src.distance) + " 米");
                    }
                    boolean op = inOperation(info.line, nowMin);
                    Double eta = src.bestEta(info.lineNo);
                    if (!op) {
                        p.add("walk", "等" + info.lineNo + "路", 5.0,
                                "该线已收班（末班 " + info.line.optString("lastTime", "?") + "），仅供参考");
                        p.note = "包含已收班线路";
                    } else if (eta == null) {
                        p.add("walk", "等" + info.lineNo + "路", 5.0, "暂无实时车，按经验值");
                    } else {
                        p.add("bus", "等" + info.lineNo + "路", Math.max(eta, MIN_BOARD_MIN),
                                String.format("最近一车 %.1f 分钟后到", eta));
                        p.hasRealtime = true;
                    }
                    p.add("bus", info.lineNo + "路 " + shortStation(src.name) + "→" + shortStation(dst.name),
                            rideMinutes(r, i, j), info.line.optString("price", ""));
                    put(best, p);
                }
            }

            // 一次换乘
            for (Stop src : origins) {
                for (LineInfo info : src.lines.values()) {
                    String lineId = info.line.optString("lineId", "");
                    if (lineId.isEmpty()) continue;
                    LineRoute r1 = getRoute(info.lineNo, lineId);
                    if (r1 == null) continue;
                    int i = matchStation(r1.stations, src.name);
                    if (i < 0) continue;
                    boolean op1 = inOperation(info.line, nowMin);

                    for (LineInfo info2 : dst.lines.values()) {
                        if (info2.lineNo.equals(info.lineNo)) continue;
                        LineRoute r2 = getRoute(info2.lineNo, info2.line.optString("lineId", ""));
                        if (r2 == null) continue;
                        int dstIdx = matchStation(r2.stations, dst.name);
                        if (dstIdx < 0) continue;

                        for (int k = i + 1; k < r1.stations.size(); k++) {
                            String transfer = r1.stations.get(k);
                            if (transfer.isEmpty() || PLACEHOLDER.contains(transfer)) continue;
                            int tIdx = matchStation(r2.stations, transfer);
                            if (tIdx < 0 || dstIdx <= tIdx) continue;

                            Plan p = new Plan();
                            p.transfers = 1;
                            if (src.distance > 0) {
                                p.add("walk", "步行到" + shortStation(src.name),
                                        walkMinutes(src.distance), Math.round(src.distance) + " 米");
                            }
                            Double eta1 = src.bestEta(info.lineNo);
                            if (!op1) {
                                p.add("walk", "等" + info.lineNo + "路", 5.0,
                                        "该线已收班（末班 " + info.line.optString("lastTime", "?") + "）");
                                p.note = "包含已收班线路";
                            } else if (eta1 == null) {
                                p.add("walk", "等" + info.lineNo + "路", 5.0, "暂无实时车");
                            } else {
                                p.add("bus", "等" + info.lineNo + "路",
                                        Math.max(eta1, MIN_BOARD_MIN),
                                        String.format("%.1f 分钟后到", eta1));
                                p.hasRealtime = true;
                            }
                            p.add("bus", info.lineNo + "路 至 " + shortStation(transfer),
                                    rideMinutes(r1, i, k), info.line.optString("price", ""));

                            Double eta2 = dst.bestEta(info2.lineNo);
                            if (eta2 == null) {
                                p.add("walk", "换乘等" + info2.lineNo + "路", 5.0, "暂无实时车");
                            } else {
                                p.add("bus", "换乘" + info2.lineNo + "路",
                                        Math.max(eta2, MIN_BOARD_MIN),
                                        String.format("%.1f 分钟后到", eta2));
                                p.hasRealtime = true;
                            }
                            p.add("bus", info2.lineNo + "路 至" + shortStation(dst.name),
                                    rideMinutes(r2, tIdx, dstIdx), info2.line.optString("price", ""));
                            put(best, p);
                        }
                    }
                }
            }
        }

        List<Plan> out = new ArrayList<>(best.values());
        out.sort((a, b) -> {
            int ka = "包含已收班线路".equals(a.note) ? 1 : 0;
            int kb = "包含已收班线路".equals(b.note) ? 1 : 0;
            if (ka != kb) return ka - kb;
            return Double.compare(a.total, b.total);
        });
        if (out.size() > maxPlans) out = new ArrayList<>(out.subList(0, maxPlans));
        for (Plan p : out) {
            if (!p.hasRealtime && !"包含已收班线路".equals(p.note)) {
                p.note = "该方案缺少实时车辆数据，等待时间为估算值";
            }
        }
        if (out.isEmpty()) {
            Plan p = new Plan();
            p.note = "未找到可行公交方案";
            out.add(p);
        }
        return out;
    }

    /** 去重：同(线路组合)只保留最快的 */
    private static void put(Map<String, Plan> best, Plan p) {
        StringBuilder sb = new StringBuilder();
        for (Leg l : p.legs) {
            if ("bus".equals(l.kind)) sb.append(l.title).append('|');
        }
        String key = sb.toString();
        Plan prev = best.get(key);
        if (prev == null || p.total < prev.total) best.put(key, p);
    }
}
