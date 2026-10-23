package com.workbuddy.xiangtanbus;

import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import java.util.Base64;

/**
 * 车来了实时公交客户端（Android 版）。
 *
 * 协议实现与 Python 版保持一致：
 *   - 签名：参数按加入顺序拼 "k"="v" 后追加盐值qwihrnbtmj，做 MD5
 *   - 加密：AES-256-ECB，响应体在 jsonr.data.encryptResult 中
 */
public final class ChelaileClient {

    public static final String APP_VERSION = "1.1.0";

    private static final String BASE_DOMAIN = "https://web.chelaile.net.cn";
    private static final String BASE_URL = BASE_DOMAIN + "/api";
    private static final String SIGN_SALT = "qwihrnbtmj";
    private static final String AES_KEY = "FF32AE65FBFD19414EAAFF6291A54B42";

    /** 湘潭 */
    private static final String CITY_ID = "173";

    private static final Map<String, String> DEFAULT_PARAMS = new LinkedHashMap<>();
    static {
        DEFAULT_PARAMS.put("s", "h5");
        DEFAULT_PARAMS.put("wxs", "wx_app");
        DEFAULT_PARAMS.put("sign", "1");
        DEFAULT_PARAMS.put("h5RealData", "1");
        DEFAULT_PARAMS.put("v", "3.11.28");
        DEFAULT_PARAMS.put("src", "weixinapp_cx");
        DEFAULT_PARAMS.put("ctm_mp", "mp_wx");
        DEFAULT_PARAMS.put("vc", "2");
        DEFAULT_PARAMS.put("favoriteGray", "1");
        DEFAULT_PARAMS.put("gpstype", "wgs");
        DEFAULT_PARAMS.put("geo_type", "wgs");
        DEFAULT_PARAMS.put("scene", "1256");
    }

    private static final String UA =
            "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) "
            + "Chrome/132.0.0.0 Mobile Safari/537.36";

    private ChelaileClient() {}

    public static class ApiException extends Exception {
        public ApiException(String msg) { super(msg); }
    }

    // ---------- 基础 ----------

    private static String cryptoSign(Map<String, String> params) throws Exception {
        StringBuilder sb = new StringBuilder();
        Iterator<Map.Entry<String, String>> it = params.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<String, String> e = it.next();
            sb.append('"').append(e.getKey()).append("\"=\"").append(e.getValue()).append('"');
            if (it.hasNext()) sb.append('&');
        }
        sb.append(SIGN_SALT);
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] d = md.digest(sb.toString().getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder();
        for (byte b : d) hex.append(String.format("%02x", b));
        return hex.toString();
    }

    private static String decrypt(String b64) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/ECB/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(AES_KEY.getBytes(StandardCharsets.UTF_8), "AES"));
        byte[] raw = Base64.getDecoder().decode(b64);
        return new String(cipher.doFinal(raw), StandardCharsets.UTF_8);
    }

    private static String httpGet(String url) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(20000);
        conn.setRequestProperty("User-Agent", UA);
        conn.setRequestProperty("xweb_xhr", "1");
        conn.setRequestProperty("Accept", "*/*");
        conn.setRequestProperty("Referer", "https://servicewechat.com/wx71d589ea01ce3321/814/page-frame.html");
        conn.setRequestProperty("Accept-Language", "zh-CN,zh;q=0.9");

        int code = conn.getResponseCode();
        InputStream is = (code >= 200 && code < 400) ? conn.getInputStream() : conn.getErrorStream();
        if (is == null) throw new ApiException("HTTP " + code);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = is.read(buf)) > 0) bos.write(buf, 0, n);
        is.close();
        conn.disconnect();
        return bos.toString("UTF-8");
    }

    /** 发起签名请求并解包加密信封，返回 data 节点。 */
    public static JSONObject request(String path, Map<String, String> extra) throws Exception {
        Map<String, String> p = new LinkedHashMap<>(DEFAULT_PARAMS);
        p.put("cityId", CITY_ID);
        p.put("localCityId", CITY_ID);
        if (extra != null) p.putAll(extra);
        p.put("cryptoSign", cryptoSign(p));

        StringBuilder qs = new StringBuilder();
        for (Map.Entry<String, String> e : p.entrySet()) {
            if (qs.length() > 0) qs.append('&');
            qs.append(URLEncoder.encode(e.getKey(), "UTF-8")).append('=')
              .append(URLEncoder.encode(e.getValue(), "UTF-8"));
        }
        String url = BASE_URL + path + "?" + qs;

        Exception last = null;
        for (int attempt = 0; attempt < 2; attempt++) {
            try {
                String raw = httpGet(url);
                JSONObject env = extractJson(raw);
                JSONObject data = env.optJSONObject("jsonr").optJSONObject("data");
                String enc = data.optString("encryptResult", "");
                if (!enc.isEmpty()) return new JSONObject(decrypt(enc));
                return data;
            } catch (Exception e) {
                last = e;
                if (attempt == 0) Thread.sleep(700);
            }
        }
        throw new ApiException("请求失败: " + last.getMessage());
    }

    /** 从 JSONP 包裹中精确截取 JSON 对象。 */
    private static JSONObject extractJson(String raw) throws Exception {
        int start = raw.indexOf('{');
        if (start < 0) throw new ApiException("返回非 JSON: " + raw.substring(0, Math.min(80, raw.length())));
        int depth = 0;
        for (int i = start; i < raw.length(); i++) {
            char c = raw.charAt(i);
            if (c == '{') depth++;
            else if (c == '}') {
                depth--;
                if (depth == 0) return new JSONObject(raw.substring(start, i + 1));
            }
        }
        throw new ApiException("JSON 截取失败");
    }

    private static Map<String, String> map(String... kv) {
        Map<String, String> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) m.put(kv[i], kv[i + 1]);
        return m;
    }

    // ---------- 业务接口 ----------

    /** 关键词搜索：站点 + 线路 + POI */
    public static JSONObject search(String keyword) throws Exception {
        return request("/bus/query!nSearch.action",
                map("key", keyword, "supportPhyStn", "true"));
    }

    /** 按坐标找附近站点（含各线实时车辆） */
    public static JSONObject nearbyStops(double lat, double lng) throws Exception {
        return request("/bus/stop!encryptedHomePage.action", map(
                "localCityId", "undefined",
                "lat", String.format("%.6f", lat),
                "lng", String.format("%.6f", lng),
                "geo_lat", String.format("%.6f", lat),
                "geo_lng", String.format("%.6f", lng),
                "type", "5", "permission", "0"));
    }

    /** 站点详情：途经全部线路 + 每条线实时车辆 */
    public static JSONObject stopDetail(String physicalStId, String namesakeStId) throws Exception {
        return request("/bus/stop!encryptedPhyStnDetail.action", map(
                "physicalStId", physicalStId,
                "namesakeStId", namesakeStId == null ? "" : namesakeStId,
                "stationId", "", "lat", "", "lng", ""));
    }

    /** 线路详情：完整站点序列 + 坐标 + 首末班 */
    public static JSONObject lineDetail(String lineId) throws Exception {
        return request("/bus/line!encryptedLineDetail.action", map("lineId", lineId));
    }
}
