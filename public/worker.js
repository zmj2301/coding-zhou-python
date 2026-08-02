var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// code-explorer/worker.ts
function base64UrlEncode(data) {
  let str = "";
  for (let i = 0; i < data.length; i++) {
    str += String.fromCharCode(data[i]);
  }
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
__name(base64UrlEncode, "base64UrlEncode");
function base64UrlDecode(str) {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  while (str.length % 4) str += "=";
  const binary = atob(str);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}
__name(base64UrlDecode, "base64UrlDecode");
async function getKey(secret) {
  const enc = new TextEncoder();
  return crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}
__name(getKey, "getKey");
async function signJwt(payload, secret, expiresInSeconds = 604800) {
  const header = { alg: "HS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1e3);
  const fullPayload = { ...payload, iat: now, exp: now + expiresInSeconds };
  const headerB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(header)));
  const payloadB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(fullPayload)));
  const key = await getKey(secret);
  const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const signature = await crypto.subtle.sign("HMAC", key, data);
  const sigB64 = base64UrlEncode(new Uint8Array(signature));
  return `${headerB64}.${payloadB64}.${sigB64}`;
}
__name(signJwt, "signJwt");
async function verifyJwt(token, secret) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const [headerB64, payloadB64, sigB64] = parts;
    const key = await getKey(secret);
    const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const signature = base64UrlDecode(sigB64);
    const isValid = await crypto.subtle.verify("HMAC", key, signature, data);
    if (!isValid) return null;
    const payload = JSON.parse(new TextDecoder().decode(base64UrlDecode(payloadB64)));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1e3)) return null;
    return payload;
  } catch {
    return null;
  }
}
__name(verifyJwt, "verifyJwt");
function parseCookies(cookieHeader) {
  const cookies = {};
  if (!cookieHeader) return cookies;
  for (const cookie of cookieHeader.split(";")) {
    const [name, ...rest] = cookie.trim().split("=");
    if (name) cookies[name] = rest.join("=");
  }
  return cookies;
}
__name(parseCookies, "parseCookies");
function getTokenFromRequest(request) {
  const cookieHeader = request.headers.get("Cookie");
  const cookies = parseCookies(cookieHeader);
  return cookies["wg_token"] || null;
}
__name(getTokenFromRequest, "getTokenFromRequest");
async function checkAuth(request, env) {
  if (!env.USER_PASSWORD) return true;
  const token = getTokenFromRequest(request);
  if (!token) return false;
  const payload = await verifyJwt(token, env.JWT_SECRET || "default-secret-change-me");
  return payload !== null;
}
__name(checkAuth, "checkAuth");
async function checkAdmin(request, env) {
  if (!env.ADMIN_PASSWORD) return false;
  const token = getTokenFromRequest(request);
  if (!token) return false;
  const payload = await verifyJwt(token, env.JWT_SECRET || "default-secret-change-me");
  return payload !== null && payload.is_admin === true;
}
__name(checkAdmin, "checkAdmin");
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: corsHeaders()
  });
}
__name(jsonResponse, "jsonResponse");
function errorResponse(message, status = 400) {
  return jsonResponse({ error: message }, status);
}
__name(errorResponse, "errorResponse");
function corsHeaders() {
  const h = new Headers();
  h.set("Content-Type", "application/json; charset=utf-8");
  h.set("Access-Control-Allow-Origin", "*");
  h.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  h.set("Access-Control-Allow-Headers", "Content-Type");
  return h;
}
__name(corsHeaders, "corsHeaders");
function setCookie(response, name, value, maxAge = 86400 * 7) {
  const cookie = `${name}=${value}; Path=/; Max-Age=${maxAge}; HttpOnly; SameSite=Lax`;
  const newHeaders = new Headers(response.headers);
  newHeaders.append("Set-Cookie", cookie);
  return new Response(response.body, { status: response.status, headers: newHeaders });
}
__name(setCookie, "setCookie");
function clearCookie(response, name) {
  const cookie = `${name}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax`;
  const newHeaders = new Headers(response.headers);
  newHeaders.append("Set-Cookie", cookie);
  return new Response(response.body, { status: response.status, headers: newHeaders });
}
__name(clearCookie, "clearCookie");
function isBrowserRequest(request) {
  const accept = request.headers.get("Accept") || "";
  return accept.includes("text/html");
}
__name(isBrowserRequest, "isBrowserRequest");
function redirectResponse(url, status = 302) {
  return new Response(null, { status, headers: { Location: url } });
}
__name(redirectResponse, "redirectResponse");
function optionsResponse() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    }
  });
}
__name(optionsResponse, "optionsResponse");
async function fetchFromGitHub(path, env) {
  const repo = env.GITHUB_REPO || "zmj2301/coding-zhou-python";
  const branch = env.GITHUB_BRANCH || "main";
  const cleanPath = path.replace(/^\/+/, "");
  const url = `https://raw.githubusercontent.com/${repo}/${branch}/${encodeURI(cleanPath)}`;
  return fetch(url);
}
__name(fetchFromGitHub, "fetchFromGitHub");
async function fetchFromEcs(path, env, request) {
  const ecsUrl = env.ECS_SERVER_URL || "http://39.107.96.165";
  const url = `${ecsUrl}${path}`;
  const headers = new Headers(request.headers);
  headers.set("Host", new URL(ecsUrl).host);
  const cookie = request.headers.get("Cookie");
  if (cookie) {
    headers.set("Cookie", cookie);
  }
  return fetch(url, { method: request.method, headers });
}
__name(fetchFromEcs, "fetchFromEcs");
async function proxyStreamToEcs(path, env, request) {
  const ecsUrl = env.ECS_SERVER_URL || "http://39.107.96.165";
  const url = `${ecsUrl}${path}`;
  const headers = new Headers();
  const contentType = request.headers.get("Content-Type");
  if (contentType) headers.set("Content-Type", contentType);
  const cookie = request.headers.get("Cookie");
  if (cookie) headers.set("Cookie", cookie);
  headers.set("Accept", "text/event-stream");
  const body = request.method === "POST" ? await request.text() : void 0;
  const ecsResp = await fetch(url, {
    method: request.method,
    headers,
    body
  });
  const { readable, writable } = new TransformStream({
    transform(chunk, controller) {
      controller.enqueue(chunk);
    }
  });
  ecsResp.body?.pipeTo(writable).catch(() => {
  });
  const responseHeaders = new Headers();
  responseHeaders.set("Content-Type", "text/event-stream; charset=utf-8");
  responseHeaders.set("Cache-Control", "no-cache, no-transform");
  responseHeaders.set("Connection", "keep-alive");
  responseHeaders.set("Access-Control-Allow-Origin", "*");
  responseHeaders.set("X-Accel-Buffering", "no");
  responseHeaders.delete("Content-Length");
  responseHeaders.delete("Content-Encoding");
  return new Response(readable, { status: ecsResp.status, headers: responseHeaders });
}
__name(proxyStreamToEcs, "proxyStreamToEcs");
async function fetchAsset(path, env) {
  try {
    if (env.ASSETS && typeof env.ASSETS.fetch === "function") {
      const cleanPath = path.startsWith("/") ? path.substring(1) : path;
      const resp = await env.ASSETS.fetch(new Request("/" + cleanPath));
      if (resp.ok) return resp;
    }
  } catch {
  }
  return fetchFromGitHub("code-explorer/public" + path, env);
}
__name(fetchAsset, "fetchAsset");
function getLanguage(ext) {
  const langMap = {
    ".py": "python",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sql": "sql",
    ".sh": "bash",
    ".bat": "bash",
    ".rs": "rust",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".lua": "lua",
    ".dart": "dart",
    ".vue": "html",
    ".svelte": "html",
    ".toml": "ini",
    ".ini": "ini",
    ".cfg": "ini",
    ".csv": "plaintext",
    ".txt": "plaintext",
    ".spec": "plaintext"
  };
  return langMap[ext.toLowerCase()] || "plaintext";
}
__name(getLanguage, "getLanguage");
var CONTENT_TYPE_MAP = {
  ".html": "text/html; charset=utf-8",
  ".htm": "text/html; charset=utf-8",
  ".svg": "image/svg+xml",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".ico": "image/x-icon"
};
function getExt(filePath) {
  const idx = filePath.lastIndexOf(".");
  return idx >= 0 ? filePath.substring(idx).toLowerCase() : "";
}
__name(getExt, "getExt");
function rewriteHtmlResourcePaths(html, filePath) {
  const dirPath = filePath.substring(0, filePath.lastIndexOf("/") + 1);
  function makePreviewUrl(original) {
    if (!original || original.startsWith("/") || original.startsWith("http://") || original.startsWith("https://") || original.startsWith("data:") || original.startsWith("#") || original.startsWith("mailto:")) {
      return null;
    }
    try {
      const resolved = new URL(original, "http://base/" + dirPath).pathname.substring(1);
      return "/api/files/preview?path=" + encodeURIComponent(resolved);
    } catch {
      return null;
    }
  }
  __name(makePreviewUrl, "makePreviewUrl");
  return html.replace(
    /(src|href|srcset|data-src|poster|action)\s*=\s*(['"])([^'">]+?)\2/gi,
    (match, attr, quote, value) => {
      const newUrl = makePreviewUrl(value);
      return newUrl ? `${attr}=${quote}${newUrl}${quote}` : match;
    }
  ).replace(
    /url\(\s*(['"]?)([^)'"']+?)\1\s*\)/gi,
    (match, quote, value) => {
      const newUrl = makePreviewUrl(value.trim());
      return newUrl ? `url(${newUrl})` : match;
    }
  );
}
__name(rewriteHtmlResourcePaths, "rewriteHtmlResourcePaths");
function searchInTree(tree, query) {
  const results = [];
  query = query.toLowerCase();
  for (const item of tree) {
    if (item.type === "file") {
      if (item.name.toLowerCase().includes(query)) {
        results.push({ name: item.name, path: item.path, ext: item.ext });
      }
    } else if (item.type === "directory" && item.children) {
      results.push(...searchInTree(item.children, query));
    }
  }
  return results;
}
__name(searchInTree, "searchInTree");
function safeProjectName(project) {
  return project.replace(/[\/\\:*?"<>|]/g, "_");
}
__name(safeProjectName, "safeProjectName");
var STATIC_EXT = /* @__PURE__ */ new Set([
  ".js",
  ".css",
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".svg",
  ".ico",
  ".webp",
  ".ttf",
  ".woff",
  ".woff2",
  ".eot",
  ".otf",
  ".mp3",
  ".wav",
  ".ogg",
  ".mp4",
  ".webm",
  ".json",
  ".md"
]);
function isStaticAsset(ext) {
  return STATIC_EXT.has(ext.toLowerCase());
}
__name(isStaticAsset, "isStaticAsset");
function addCacheHeader(headers, maxAgeSeconds) {
  headers.set("Cache-Control", `public, max-age=${maxAgeSeconds}`);
}
__name(addCacheHeader, "addCacheHeader");
var fileTreeCache = null;
var fileTreeCacheTime = 0;
async function getFileTree(env) {
  const now = Date.now();
  if (fileTreeCache && now - fileTreeCacheTime < 3e5) {
    return fileTreeCache;
  }
  try {
    const cached = await env.CODE_EXPLORER_KV.get("cache:file-tree", { type: "json" });
    if (cached) {
      fileTreeCache = cached;
      fileTreeCacheTime = now;
      return fileTreeCache;
    }
  } catch {
  }
  try {
    const resp = await fetchAsset("/file-tree.json", env);
    if (resp.ok) {
      const tree = await resp.json();
      fileTreeCache = tree;
      fileTreeCacheTime = now;
      try {
        await env.CODE_EXPLORER_KV.put("cache:file-tree", JSON.stringify(tree), {
          expirationTtl: 86400
        });
      } catch {
      }
      return tree;
    }
  } catch {
  }
  return [];
}
__name(getFileTree, "getFileTree");
async function handleApi(request, env, path) {
  const url = new URL(request.url);
  if (request.method === "OPTIONS") return optionsResponse();
  if (path === "/api/auth-check") {
    const authenticated = await checkAuth(request, env);
    return jsonResponse({ authenticated, passwordSet: Boolean(env.USER_PASSWORD) });
  }
  if (path === "/api/login" && request.method === "POST") {
    try {
      const data = await request.json();
      const password = data.password || "";
      if (!env.USER_PASSWORD) return errorResponse("\u670D\u52A1\u5668\u672A\u8BBE\u7F6E\u5BC6\u7801", 500);
      if (password !== env.USER_PASSWORD) return errorResponse("\u5BC6\u7801\u9519\u8BEF", 401);
      const token = await signJwt(
        { sub: "user", is_admin: false },
        env.JWT_SECRET || "default-secret-change-me",
        604800
      );
      const resp = jsonResponse({ token });
      return setCookie(resp, "wg_token", token, 604800);
    } catch {
      return errorResponse("\u65E0\u6548\u7684\u8BF7\u6C42", 400);
    }
  }
  if (path === "/api/logout" && request.method === "POST") {
    const resp = jsonResponse({ success: true });
    return clearCookie(resp, "wg_token");
  }
  if (path === "/api/admin/login" && request.method === "POST") {
    try {
      const data = await request.json();
      const password = data.password || "";
      if (!env.ADMIN_PASSWORD) return errorResponse("\u670D\u52A1\u5668\u672A\u8BBE\u7F6E\u7BA1\u7406\u5458\u5BC6\u7801", 500);
      if (password !== env.ADMIN_PASSWORD) return errorResponse("\u7BA1\u7406\u5458\u5BC6\u7801\u9519\u8BEF", 401);
      const token = await signJwt(
        { sub: "admin", is_admin: true },
        env.JWT_SECRET || "default-secret-change-me",
        604800
      );
      const resp = jsonResponse({ token });
      return setCookie(resp, "wg_token", token, 604800);
    } catch {
      return errorResponse("\u65E0\u6548\u7684\u8BF7\u6C42", 400);
    }
  }
  if (path === "/api/admin/clear-cache" && request.method === "POST") {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse("\u9700\u8981\u7BA1\u7406\u5458\u6743\u9650", 401);
    let deletedCount = 0;
    try {
      let cursor = void 0;
      do {
        const list = await env.CODE_EXPLORER_KV.list({ prefix: "cache:", cursor });
        const deletePromises = list.keys.map((k) => env.CODE_EXPLORER_KV.delete(k.name));
        await Promise.all(deletePromises);
        deletedCount += list.keys.length;
        cursor = list.cursor;
      } while (cursor);
    } catch {
    }
    return jsonResponse({ success: true, message: `\u7F13\u5B58\u5DF2\u6E05\u9664\uFF0C\u5171\u5220\u9664 ${deletedCount} \u4E2A\u7F13\u5B58\u9879` });
  }
  const needAuth = path.startsWith("/api/files/") || path.startsWith("/api/comments") || path.startsWith("/api/run/") || path === "/api/likes" || path === "/api/admin/dashboard";
  if (needAuth) {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse("\u8BF7\u5148\u767B\u5F55", 401);
  }
  if (path === "/api/run/start") {
    return proxyStreamToEcs(path + (url.search || ""), env, request);
  }
  if (path === "/api/run/stop") {
    return fetchFromEcs(path, env, request);
  }
  if (path === "/api/files/tree") {
    try {
      const ecsResp = await fetchFromEcs(`/api/files/tree${url.search}`, env, request);
      if (ecsResp.ok) {
        const data = await ecsResp.json();
        const resp2 = jsonResponse(data);
        addCacheHeader(resp2.headers, 300);
        return resp2;
      }
    } catch {
    }
    const tree = await getFileTree(env);
    const resp = jsonResponse(tree);
    addCacheHeader(resp.headers, 300);
    return resp;
  }
  if (path === "/api/projects/list") {
    const CACHE_KEY = "cache:project-meta";
    const CACHE_TTL = 1800;
    try {
      const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: "json" });
      if (cached && Date.now() - cached.timestamp < CACHE_TTL * 1e3) {
        const resp2 = jsonResponse(cached.projects);
        addCacheHeader(resp2.headers, 300);
        return resp2;
      }
    } catch {
    }
    const listResp = await fetchAsset("/project-list.json", env);
    if (!listResp.ok) return errorResponse("\u9879\u76EE\u5217\u8868\u4E0D\u5B58\u5728", 404);
    const projects = await listResp.json();
    const likesMap = {};
    const commentsMap = {};
    try {
      const cachedLikes = await env.CODE_EXPLORER_KV.get("cache:likes", { type: "json" });
      if (cachedLikes) {
        Object.assign(likesMap, cachedLikes);
      } else {
        const likesList = await env.CODE_EXPLORER_KV.list({ prefix: "likes:" });
        for (const key of likesList.keys) {
          const project = key.name.substring("likes:".length);
          const value = await env.CODE_EXPLORER_KV.get(key.name);
          likesMap[project] = parseInt(value || "0", 10) || 0;
        }
        try {
          await env.CODE_EXPLORER_KV.put("cache:likes", JSON.stringify(likesMap), {
            expirationTtl: 1800
          });
        } catch {
        }
      }
    } catch {
    }
    try {
      const cachedComments = await env.CODE_EXPLORER_KV.get("cache:comment-counts", { type: "json" });
      if (cachedComments) {
        Object.assign(commentsMap, cachedComments);
      } else {
        const commentsList = await env.CODE_EXPLORER_KV.list({ prefix: "comments:" });
        for (const key of commentsList.keys) {
          const project = key.name.substring("comments:".length);
          const value = await env.CODE_EXPLORER_KV.get(key.name);
          try {
            const parsed = JSON.parse(value || "{}");
            commentsMap[project] = (parsed.comments || []).length;
          } catch {
            commentsMap[project] = 0;
          }
        }
        try {
          await env.CODE_EXPLORER_KV.put("cache:comment-counts", JSON.stringify(commentsMap), {
            expirationTtl: 1800
          });
        } catch {
        }
      }
    } catch {
    }
    const projectsWithMeta = projects.map((p) => ({
      ...p,
      likes: likesMap[p.path] || 0,
      comments: commentsMap[p.path] || 0
    }));
    try {
      await env.CODE_EXPLORER_KV.put(CACHE_KEY, JSON.stringify({
        projects: projectsWithMeta,
        timestamp: Date.now()
      }), { expirationTtl: CACHE_TTL });
    } catch {
    }
    const resp = jsonResponse(projectsWithMeta);
    addCacheHeader(resp.headers, 300);
    return resp;
  }
  if (path === "/api/projects/tree") {
    const projPath = url.searchParams.get("path") || "";
    if (!projPath) return errorResponse("\u7F3A\u5C11 path \u53C2\u6570");
    if (projPath.includes("..") || projPath.startsWith("/")) return errorResponse("\u8BBF\u95EE\u88AB\u62D2\u7EDD", 403);
    try {
      const ecsResp = await fetchFromEcs(`/api/projects/tree${url.search}`, env, request);
      if (ecsResp.ok) {
        const treeData2 = await ecsResp.json();
        const resp2 = jsonResponse(treeData2);
        addCacheHeader(resp2.headers, 300);
        return resp2;
      }
    } catch {
    }
    const safeName = projPath.replace(/\//g, "__").replace(/\\/g, "__");
    const treeResp = await fetchAsset(`/project-trees/${safeName}.json`, env);
    if (!treeResp.ok) return errorResponse("\u9879\u76EE\u6587\u4EF6\u6811\u4E0D\u5B58\u5728", 404);
    const treeData = await treeResp.json();
    const resp = jsonResponse(treeData);
    addCacheHeader(resp.headers, 86400);
    return resp;
  }
  if (path === "/api/files/subtree") {
    const projectPath = url.searchParams.get("project") || "";
    const dirPath = url.searchParams.get("dir") || "";
    if (!projectPath || !dirPath) return errorResponse("\u7F3A\u5C11 project \u6216 dir \u53C2\u6570");
    if (projectPath.includes("..") || dirPath.includes("..")) return errorResponse("\u8BBF\u95EE\u88AB\u62D2\u7EDD", 403);
    try {
      const ecsResp = await fetchFromEcs(`/api/files/subtree${url.search}`, env, request);
      if (ecsResp.ok) {
        const data = await ecsResp.json();
        const resp = jsonResponse(data);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {
    }
    return errorResponse("\u65E0\u6CD5\u52A0\u8F7D\u76EE\u5F55\u5185\u5BB9", 502);
  }
  if (path === "/api/files/content") {
    const filePath = url.searchParams.get("path") || "";
    if (!filePath) return errorResponse("\u7F3A\u5C11 path \u53C2\u6570");
    if (filePath.includes("..") || filePath.startsWith("/")) return errorResponse("\u8BBF\u95EE\u88AB\u62D2\u7EDD\uFF1A\u8DEF\u5F84\u8D8A\u754C", 403);
    const ecsResp = await fetchFromEcs(`/api/files/content${url.search}`, env, request);
    if (ecsResp.ok) {
      const data = await ecsResp.json();
      const resp2 = jsonResponse(data);
      addCacheHeader(resp2.headers, 3600);
      return resp2;
    }
    const cacheKey = `cache:file:${filePath}`;
    try {
      const cached = await env.CODE_EXPLORER_KV.get(cacheKey, { type: "json" });
      if (cached) {
        const resp2 = jsonResponse(cached);
        addCacheHeader(resp2.headers, 3600);
        return resp2;
      }
    } catch {
    }
    const ghResp = await fetchFromGitHub(filePath, env);
    if (!ghResp.ok) {
      if (ghResp.status === 404) return errorResponse("\u6587\u4EF6\u4E0D\u5B58\u5728", 404);
      return errorResponse("\u8BFB\u53D6\u6587\u4EF6\u5931\u8D25", ghResp.status);
    }
    const content = await ghResp.text();
    const ext = getExt(filePath);
    const name = filePath.split("/").pop() || filePath;
    const result = {
      path: filePath,
      name,
      content,
      language: getLanguage(ext),
      size: new Blob([content]).size
    };
    try {
      await env.CODE_EXPLORER_KV.put(cacheKey, JSON.stringify(result), {
        expirationTtl: 3600
      });
    } catch {
    }
    const resp = jsonResponse(result);
    addCacheHeader(resp.headers, 3600);
    return resp;
  }
  if (path === "/api/files/preview") {
    const filePath = url.searchParams.get("path") || "";
    if (!filePath) return errorResponse("\u7F3A\u5C11 path \u53C2\u6570");
    if (filePath.includes("..") || filePath.startsWith("/")) return errorResponse("\u8BBF\u95EE\u88AB\u62D2\u7EDD\uFF1A\u8DEF\u5F84\u8D8A\u754C", 403);
    const ecsResp = await fetchFromEcs(`/api/files/preview${url.search}`, env, request);
    if (ecsResp.ok) {
      return ecsResp;
    }
    const ext = getExt(filePath);
    const contentType = CONTENT_TYPE_MAP[ext] || "application/octet-stream";
    if (ext === ".html" || ext === ".htm") {
      const ghResp2 = await fetchFromGitHub(filePath, env);
      if (!ghResp2.ok) {
        if (ghResp2.status === 404) return errorResponse("\u6587\u4EF6\u4E0D\u5B58\u5728", 404);
        return errorResponse("\u8BFB\u53D6\u6587\u4EF6\u5931\u8D25", ghResp2.status);
      }
      let html = await ghResp2.text();
      html = rewriteHtmlResourcePaths(html, filePath);
      return new Response(html, {
        status: 200,
        headers: {
          "Content-Type": contentType,
          "Cache-Control": "no-store"
        }
      });
    }
    const cacheKey = `cache:preview:${filePath}`;
    const isStatic = isStaticAsset(ext);
    if (isStatic) {
      try {
        const cached = await env.CODE_EXPLORER_KV.get(cacheKey, { type: "arrayBuffer" });
        if (cached) {
          return new Response(cached, {
            status: 200,
            headers: {
              "Content-Type": contentType,
              "Cache-Control": `public, max-age=${86400 * 30}`
            }
          });
        }
      } catch {
      }
    }
    const ghResp = await fetchFromGitHub(filePath, env);
    if (!ghResp.ok) {
      if (ghResp.status === 404) return errorResponse("\u6587\u4EF6\u4E0D\u5B58\u5728", 404);
      return errorResponse("\u8BFB\u53D6\u6587\u4EF6\u5931\u8D25", ghResp.status);
    }
    const body = contentType.startsWith("text/") || contentType.startsWith("application/") ? await ghResp.text() : await ghResp.arrayBuffer();
    if (isStatic) {
      try {
        const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body).buffer;
        await env.CODE_EXPLORER_KV.put(cacheKey, buf, {
          expirationTtl: 86400 * 7
        });
      } catch {
      }
      return new Response(body, {
        status: 200,
        headers: {
          "Content-Type": contentType,
          "Cache-Control": `public, max-age=${86400 * 30}`
        }
      });
    }
    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "no-store"
      }
    });
  }
  if (path === "/api/files/search") {
    const query = (url.searchParams.get("q") || "").toLowerCase();
    if (!query) return jsonResponse([]);
    try {
      const ecsResp = await fetchFromEcs(`/api/files/search${url.search}`, env, request);
      if (ecsResp.ok) {
        const data = await ecsResp.json();
        const resp2 = jsonResponse(data);
        addCacheHeader(resp2.headers, 300);
        return resp2;
      }
    } catch {
    }
    const tree = await getFileTree(env);
    const results = searchInTree(tree, query);
    const resp = jsonResponse(results.slice(0, 100));
    addCacheHeader(resp.headers, 300);
    return resp;
  }
  if (path === "/api/comments") {
    const project = url.searchParams.get("project") || "";
    if (request.method === "GET") {
      if (!project) return errorResponse("\u7F3A\u5C11 project \u53C2\u6570");
      const key = `comments:${safeProjectName(project)}`;
      try {
        const data = await env.CODE_EXPLORER_KV.get(key);
        if (data) {
          try {
            return jsonResponse(JSON.parse(data));
          } catch {
          }
        }
        return jsonResponse({ project, comments: [] });
      } catch (e) {
        return errorResponse(`\u52A0\u8F7D\u8BC4\u8BBA\u5931\u8D25: ${e}`, 500);
      }
    }
    if (request.method === "POST") {
      try {
        const data = await request.json();
        const project2 = data.project || "";
        const text = (data.text || "").trim();
        if (!project2 || !text) return errorResponse("\u7F3A\u5C11 project \u6216 text \u53C2\u6570");
        const key = `comments:${safeProjectName(project2)}`;
        let projectData = { project: project2, comments: [] };
        const existing = await env.CODE_EXPLORER_KV.get(key);
        if (existing) {
          try {
            projectData = JSON.parse(existing);
          } catch {
          }
        }
        const commentId = Math.random().toString(36).substring(2, 10);
        const comment = {
          id: commentId,
          project: project2,
          text,
          timestamp: Date.now(),
          image: null,
          likes: 0
        };
        projectData.comments.push(comment);
        await env.CODE_EXPLORER_KV.put(key, JSON.stringify(projectData));
        try {
          await env.CODE_EXPLORER_KV.delete("cache:comment-counts");
        } catch {
        }
        try {
          await env.CODE_EXPLORER_KV.delete("cache:project-meta");
        } catch {
        }
        try {
          await env.CODE_EXPLORER_KV.delete("cache:home-page-v2");
        } catch {
        }
        return jsonResponse(comment, 201);
      } catch {
        return errorResponse("\u65E0\u6548\u7684\u8BF7\u6C42", 400);
      }
    }
  }
  if (path === "/api/comments/counts") {
    try {
      const cached = await env.CODE_EXPLORER_KV.get("cache:comment-counts", { type: "json" });
      if (cached) {
        const resp = jsonResponse(cached);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {
    }
    const counts = {};
    try {
      const list = await env.CODE_EXPLORER_KV.list({ prefix: "comments:" });
      for (const key of list.keys) {
        try {
          const data = await env.CODE_EXPLORER_KV.get(key.name);
          if (data) {
            const parsed = JSON.parse(data);
            if (parsed.project && Array.isArray(parsed.comments)) {
              counts[parsed.project] = parsed.comments.length;
            }
          }
        } catch {
        }
      }
      try {
        await env.CODE_EXPLORER_KV.put("cache:comment-counts", JSON.stringify(counts), {
          expirationTtl: 300
        });
      } catch {
      }
      const resp = jsonResponse(counts);
      addCacheHeader(resp.headers, 300);
      return resp;
    } catch (e) {
      return errorResponse(`\u52A0\u8F7D\u8BC4\u8BBA\u6570\u5931\u8D25: ${e}`, 500);
    }
  }
  if (path === "/api/comments/like" && request.method === "POST") {
    try {
      const data = await request.json();
      const project = data.project || "";
      const commentId = data.id || "";
      if (!project || !commentId) return errorResponse("\u7F3A\u5C11 project \u6216 id \u53C2\u6570");
      const key = `comments:${safeProjectName(project)}`;
      const existing = await env.CODE_EXPLORER_KV.get(key);
      if (!existing) return errorResponse("\u8BC4\u8BBA\u4E0D\u5B58\u5728", 404);
      let projectData;
      try {
        projectData = JSON.parse(existing);
      } catch {
        return errorResponse("\u8BC4\u8BBA\u4E0D\u5B58\u5728", 404);
      }
      let found = false;
      for (const c of projectData.comments || []) {
        if (c.id === commentId) {
          c.likes = (c.likes || 0) + 1;
          found = true;
          break;
        }
      }
      if (!found) return errorResponse("\u8BC4\u8BBA\u4E0D\u5B58\u5728", 404);
      await env.CODE_EXPLORER_KV.put(key, JSON.stringify(projectData));
      try {
        await env.CODE_EXPLORER_KV.delete("cache:comment-counts");
      } catch {
      }
      return jsonResponse({ success: true });
    } catch {
      return errorResponse("\u70B9\u8D5E\u5931\u8D25", 500);
    }
  }
  if (path === "/api/likes") {
    if (request.method === "GET") {
      try {
        const cached = await env.CODE_EXPLORER_KV.get("cache:likes", { type: "json" });
        if (cached) {
          const resp = jsonResponse(cached);
          addCacheHeader(resp.headers, 300);
          return resp;
        }
      } catch {
      }
      const likes = {};
      try {
        const list = await env.CODE_EXPLORER_KV.list({ prefix: "likes:" });
        for (const key of list.keys) {
          const project = key.name.substring("likes:".length);
          const value = await env.CODE_EXPLORER_KV.get(key.name);
          likes[project] = parseInt(value || "0", 10) || 0;
        }
        try {
          await env.CODE_EXPLORER_KV.put("cache:likes", JSON.stringify(likes), {
            expirationTtl: 300
          });
        } catch {
        }
        const resp = jsonResponse(likes);
        addCacheHeader(resp.headers, 300);
        return resp;
      } catch (e) {
        return errorResponse(`\u52A0\u8F7D\u70B9\u8D5E\u6570\u636E\u5931\u8D25: ${e}`, 500);
      }
    }
    if (request.method === "POST") {
      try {
        const data = await request.json();
        const project = data.project || "";
        if (!project) return errorResponse("\u7F3A\u5C11 project \u53C2\u6570");
        const key = `likes:${project}`;
        let current = 0;
        const existing = await env.CODE_EXPLORER_KV.get(key);
        if (existing) current = parseInt(existing, 10) || 0;
        current += 1;
        await env.CODE_EXPLORER_KV.put(key, String(current));
        try {
          await env.CODE_EXPLORER_KV.delete("cache:likes");
        } catch {
        }
        try {
          await env.CODE_EXPLORER_KV.delete("cache:project-meta");
        } catch {
        }
        try {
          await env.CODE_EXPLORER_KV.delete("cache:home-page-v2");
        } catch {
        }
        return jsonResponse({ project, likes: current });
      } catch {
        return errorResponse("\u70B9\u8D5E\u5931\u8D25", 500);
      }
    }
  }
  if (path === "/api/admin/dashboard") {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse("\u7BA1\u7406\u5458\u672A\u767B\u5F55", 401);
    let totalComments = 0, commentProjects = 0, totalLikes = 0, likeProjects = 0;
    try {
      const commentsList = await env.CODE_EXPLORER_KV.list({ prefix: "comments:" });
      commentProjects = commentsList.keys.length;
      for (const key of commentsList.keys) {
        const data = await env.CODE_EXPLORER_KV.get(key.name);
        if (data) {
          try {
            const parsed = JSON.parse(data);
            if (parsed.comments && Array.isArray(parsed.comments)) {
              totalComments += parsed.comments.length;
            }
          } catch {
          }
        }
      }
    } catch {
    }
    try {
      const likesList = await env.CODE_EXPLORER_KV.list({ prefix: "likes:" });
      likeProjects = likesList.keys.length;
      for (const key of likesList.keys) {
        const count = await env.CODE_EXPLORER_KV.get(key.name);
        if (count) totalLikes += parseInt(count, 10) || 0;
      }
    } catch {
    }
    return jsonResponse({
      server: { uptime: "Cloudflare Worker (\u65E0\u72B6\u6001)", uptime_seconds: 0, base_dir: "GitHub Repository", port: 443, total_files: 0 },
      auth: { active_sessions: "\u65E0\u72B6\u6001", admin_sessions: "\u65E0\u72B6\u6001", password_set: Boolean(env.USER_PASSWORD), admin_password_set: Boolean(env.ADMIN_PASSWORD) },
      data: {
        likes_count: likeProjects,
        total_likes: totalLikes,
        likes_label: "\u4E2A\u9879\u76EE\u6709\u70B9\u8D5E",
        comment_files: commentProjects,
        total_comments: totalComments,
        comments_label: "\u4E2A\u9879\u76EE\u6709\u8BC4\u8BBA",
        uploaded_files_count: 0,
        uploads_label: "\u6682\u672A\u542F\u7528\u4E0A\u4F20\u529F\u80FD"
      }
    });
  }
  if (path === "/api/recommend" && request.method === "POST") {
    try {
      const data = await request.json();
      let messages = data.messages;
      const contextInfo = data.context;
      const model = data.model;
      const needsProjects = data.needsProjects !== false;
      if (!messages && (data.input || data.preferences)) {
        const userInput = (data.input || data.preferences || "").trim();
        if (!userInput) return errorResponse("\u8BF7\u8F93\u5165\u4F60\u7684\u5174\u8DA3\u6216\u9700\u6C42", 400);
        messages = [{ role: "user", content: `\u6211\u7684\u5174\u8DA3\uFF1A${userInput}` }];
      }
      if (!messages || messages.length === 0) {
        return errorResponse("\u8BF7\u8F93\u5165\u6D88\u606F", 400);
      }
      let projects = [];
      if (needsProjects) {
        projects = await loadProjectsForRecommend(env);
        if (projects.length === 0) return errorResponse("\u9879\u76EE\u5217\u8868\u4E3A\u7A7A", 503);
      }
      const result = await getConversationalAI(messages, projects, env, contextInfo, model);
      try {
        const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
        const usageKey = `ai-usage:${today}`;
        const currentUsage = parseInt(await env.CODE_EXPLORER_KV.get(usageKey) || "0", 10);
        await env.CODE_EXPLORER_KV.put(usageKey, String(currentUsage + 1), { expirationTtl: 86400 });
      } catch {
      }
      return jsonResponse({ success: true, response: result.text, recommendations: result.recommendations, reasoning: result.reasoning });
    } catch (e) {
      return errorResponse(`\u8BF7\u6C42\u5931\u8D25: ${e.message || e}`, 500);
    }
  }
  if (path === "/api/recommend" && request.method === "OPTIONS") {
    return optionsResponse();
  }
  if (path === "/api/ai-quota") {
    try {
      const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
      const usageKey = `ai-usage:${today}`;
      const usage = parseInt(await env.CODE_EXPLORER_KV.get(usageKey) || "0", 10);
      const DAILY_LIMIT = 1e4;
      const neuronsPerRequest = 100;
      const remaining = Math.max(0, DAILY_LIMIT - usage * neuronsPerRequest);
      return jsonResponse({ usage, remaining, limit: DAILY_LIMIT, neuronsPerRequest });
    } catch (e) {
      return jsonResponse({ usage: 0, remaining: 1e4, limit: 1e4, neuronsPerRequest: 100 });
    }
  }
  return errorResponse("\u672A\u627E\u5230\u63A5\u53E3", 404);
}
__name(handleApi, "handleApi");
var AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8";
var ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions";
var ZHIPU_MODEL = "glm-4.7-flash";
async function loadProjectsForRecommend(env) {
  const CACHE_KEY = "cache:project-meta";
  try {
    const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: "json" });
    if (cached && cached.projects) return cached.projects;
  } catch {
  }
  const listResp = await fetchAsset("/project-list.json", env);
  if (!listResp.ok) return [];
  try {
    return await listResp.json();
  } catch {
    return [];
  }
}
__name(loadProjectsForRecommend, "loadProjectsForRecommend");
function buildConversationalPrompt(projects, contextInfo) {
  let projectSection = "";
  if (projects && projects.length > 0) {
    const projectList = projects.map(
      (p) => `- ${p.name} (path: ${p.path}, type: ${p.type || "unknown"}, desc: ${p.description || "none"})`
    ).join("\n");
    projectSection = `
\u53EF\u7528\u7684\u9879\u76EE\u5217\u8868\uFF1A
${projectList}
`;
  }
  let contextNote = "";
  if (contextInfo?.folder) {
    contextNote = `
\u7528\u6237\u5F53\u524D\u5173\u6CE8\u7684\u6587\u4EF6\u5939\uFF1A${contextInfo.folder}
`;
  }
  const recommendInstruction = projects && projects.length > 0 ? `
\u5F53\u7528\u6237\u8868\u8FBE\u5174\u8DA3\u6216\u9700\u6C42\u65F6\uFF0C\u63A8\u8350 3-5 \u4E2A\u6700\u76F8\u5173\u7684\u9879\u76EE\u3002\u63A8\u8350\u65F6\u5728\u56DE\u590D\u672B\u5C3E\u9644\u4E0A JSON \u683C\u5F0F\uFF1A
---RECOMMEND---
[{"path": "\u9879\u76EE\u8DEF\u5F84", "reason": "\u63A8\u8350\u7406\u7531", "name": "\u9879\u76EE\u540D\u79F0"}]
---END---
\u6CA1\u6709\u63A8\u8350\u9700\u6C42\u65F6\u6B63\u5E38\u804A\u5929\uFF0C\u4E0D\u8981\u5F3A\u884C\u63A8\u8350\u3002` : "";
  return `\u4F60\u662F\u4E00\u4E2A\u70ED\u60C5\u53CB\u597D\u7684\u7F16\u7A0B\u52A9\u624B\uFF0C\u540D\u53EB"\u5C0F\u7801"\u3002\u4F60\u53EF\u4EE5\u548C\u7528\u6237\u81EA\u7136\u5730\u804A\u5929\u3001\u89E3\u7B54\u7F16\u7A0B\u95EE\u9898\uFF0C\u4E5F\u53EF\u4EE5\u63A8\u8350\u9879\u76EE\u3002

\u4F60\u7684\u6027\u683C\uFF1A
- \u8BF4\u8BDD\u8BED\u6C14\u50CF\u670B\u53CB\u4E00\u6837\u81EA\u7136\uFF0C\u4E0D\u8981\u592A\u6B63\u5F0F
- \u63A8\u8350\u9879\u76EE\u65F6\u8981\u8BF4\u660E\u63A8\u8350\u7406\u7531\uFF0C\u8BA9\u4EBA\u89C9\u5F97\u6709\u8BF4\u670D\u529B
- \u5982\u679C\u7528\u6237\u95EE\u4E86\u5177\u4F53\u9700\u6C42\uFF0C\u5C31\u5E2E\u4ED6\u5339\u914D\u6700\u5408\u9002\u7684\u9879\u76EE
- \u5982\u679C\u53EA\u662F\u804A\u5929\uFF0C\u5C31\u8F7B\u677E\u6109\u5FEB\u5730\u804A\uFF0C\u4E0D\u7528\u6BCF\u6B21\u90FD\u63A8\u8350\u9879\u76EE
${projectSection}${contextNote}${recommendInstruction}`;
}
__name(buildConversationalPrompt, "buildConversationalPrompt");
async function callZhipuAI(messages, apiKey, projects, contextInfo, model = ZHIPU_MODEL) {
  const systemPrompt = buildConversationalPrompt(projects, contextInfo);
  const payload = {
    model,
    messages: [
      { role: "system", content: systemPrompt },
      ...messages
    ],
    temperature: 0.7,
    max_tokens: 800,
    stream: false,
    thinking: { type: "enabled" }
  };
  const resp = await fetch(ZHIPU_API_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Zhipu API error: ${resp.status} ${err}`);
  }
  const data = await resp.json();
  let text = data.choices?.[0]?.message?.content || "";
  const reasoning = data.choices?.[0]?.message?.reasoning_content || "";
  const recMatch = text.match(/---RECOMMEND---\n?([\s\S]*?)\n?---END---/);
  let recommendations = [];
  if (recMatch) {
    try {
      const parsed = JSON.parse(recMatch[1]);
      if (Array.isArray(parsed)) {
        recommendations = parsed.filter((r) => r.path && r.reason).map((r) => ({
          path: r.path,
          reason: r.reason,
          name: r.name || r.path
        })).slice(0, 5);
      }
    } catch {
    }
    text = text.replace(/---RECOMMEND---[\s\S]*?---END---/, "").trim();
  }
  if (!text && recommendations.length > 0) {
    text = "\u4E3A\u4F60\u63A8\u8350\u4EE5\u4E0B\u9879\u76EE\uFF1A";
  } else if (!text) {
    text = "\u62B1\u6B49\uFF0CAI \u6682\u65F6\u65E0\u6CD5\u751F\u6210\u56DE\u590D\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002";
  }
  return { text, recommendations, reasoning };
}
__name(callZhipuAI, "callZhipuAI");
async function getConversationalAI(messages, projects, env, contextInfo, model) {
  if (model === "glm-4.7-flash") {
    const apiKey = env.ZHIPU_API_KEY;
    if (apiKey) {
      try {
        return await callZhipuAI(messages, apiKey, projects, contextInfo);
      } catch (e) {
        console.error("Zhipu AI call failed:", e);
      }
    }
  }
  const ai = env.AI;
  if (ai) {
    try {
      const systemPrompt = buildConversationalPrompt(projects, contextInfo);
      const response = await ai.run(AI_MODEL, {
        messages: [
          { role: "system", content: systemPrompt },
          ...messages
        ],
        max_tokens: 800,
        temperature: 0.7
      });
      let text = "";
      if (typeof response === "string") text = response;
      else if (response.response) text = response.response;
      else if (response.content) text = typeof response.content === "string" ? response.content : JSON.stringify(response.content);
      const recMatch = text.match(/---RECOMMEND---\n?([\s\S]*?)\n?---END---/);
      let recommendations = [];
      if (recMatch) {
        try {
          const parsed = JSON.parse(recMatch[1]);
          if (Array.isArray(parsed)) {
            recommendations = parsed.filter((r) => r.path && r.reason).map((r) => ({
              path: r.path,
              reason: r.reason,
              name: r.name || r.path
            })).slice(0, 5);
          }
        } catch {
        }
        text = text.replace(/---RECOMMEND---[\s\S]*?---END---/, "").trim();
      }
      if (!text && recommendations.length > 0) {
        text = "\u4E3A\u4F60\u63A8\u8350\u4EE5\u4E0B\u9879\u76EE\uFF1A";
      } else if (!text) {
        text = "\u62B1\u6B49\uFF0CAI \u6682\u65F6\u65E0\u6CD5\u751F\u6210\u56DE\u590D\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002";
      }
      return { text, recommendations };
    } catch (e) {
      console.error("AI call failed:", e);
    }
  }
  return { text: "", recommendations: [] };
}
__name(getConversationalAI, "getConversationalAI");
async function serveHomePage(request, env) {
  const CACHE_KEY = "cache:home-page-v2";
  const CACHE_TTL = 1800;
  try {
    const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: "text" });
    if (cached) {
      return new Response(cached, {
        status: 200,
        headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=60, stale-while-revalidate=300" }
      });
    }
  } catch {
  }
  const [htmlResp, listResp] = await Promise.all([
    fetchAsset("/index.html", env),
    fetchAsset("/project-list.json", env)
  ]);
  if (!htmlResp.ok) return new Response("\u9996\u9875\u52A0\u8F7D\u5931\u8D25", { status: 500 });
  let html = await htmlResp.text();
  let projects = [];
  if (listResp.ok) {
    try {
      projects = await listResp.json();
    } catch {
    }
  }
  const likesMap = {};
  const commentsMap = {};
  try {
    const cachedLikes = await env.CODE_EXPLORER_KV.get("cache:likes", { type: "json" });
    if (cachedLikes) {
      Object.assign(likesMap, cachedLikes);
    } else {
      const likesList = await env.CODE_EXPLORER_KV.list({ prefix: "likes:" });
      for (const key of likesList.keys) {
        const project = key.name.substring("likes:".length);
        const value = await env.CODE_EXPLORER_KV.get(key.name);
        likesMap[project] = parseInt(value || "0", 10) || 0;
      }
      try {
        await env.CODE_EXPLORER_KV.put("cache:likes", JSON.stringify(likesMap), {
          expirationTtl: 1800
        });
      } catch {
      }
    }
  } catch {
  }
  try {
    const cachedComments = await env.CODE_EXPLORER_KV.get("cache:comment-counts", { type: "json" });
    if (cachedComments) {
      Object.assign(commentsMap, cachedComments);
    } else {
      const commentsList = await env.CODE_EXPLORER_KV.list({ prefix: "comments:" });
      for (const key of commentsList.keys) {
        const project = key.name.substring("comments:".length);
        const value = await env.CODE_EXPLORER_KV.get(key.name);
        try {
          const parsed = JSON.parse(value || "{}");
          commentsMap[project] = (parsed.comments || []).length;
        } catch {
          commentsMap[project] = 0;
        }
      }
      try {
        await env.CODE_EXPLORER_KV.put("cache:comment-counts", JSON.stringify(commentsMap), {
          expirationTtl: 1800
        });
      } catch {
      }
    }
  } catch {
  }
  const projectsWithMeta = projects.map((p) => ({
    ...p,
    likes: likesMap[p.path] || 0,
    comments: commentsMap[p.path] || 0
  }));
  const injectScript = `<script>window.__INITIAL_PROJECTS__ = ${JSON.stringify(projectsWithMeta)};<\/script>`;
  html = html.replace("</head>", injectScript + "</head>");
  try {
    await env.CODE_EXPLORER_KV.put(CACHE_KEY, html, { expirationTtl: CACHE_TTL });
  } catch {
  }
  return new Response(html, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=60, stale-while-revalidate=300" }
  });
}
__name(serveHomePage, "serveHomePage");
async function handleStatic(request, env, path) {
  if (path === "/" || path === "") {
    return serveHomePage(request, env);
  }
  if (path.startsWith("/web-games/") || path === "/web-games") {
    if (isBrowserRequest(request)) {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) return redirectResponse("/");
    }
  }
  if (path.startsWith("/fathers-day/") || path === "/fathers-day") {
    if (isBrowserRequest(request)) {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) return redirectResponse("/");
    }
  }
  const ext = getExt(path);
  const isStatic = isStaticAsset(ext);
  const isHtml = ext === ".html" || ext === ".htm";
  const isChangelog = path === "/changelog.json";
  if (isStatic && !isHtml && !isChangelog) {
    const cacheKey = `cache:static:${path}`;
    try {
      const cached = await env.CODE_EXPLORER_KV.get(cacheKey, { type: "arrayBuffer" });
      if (cached) {
        const ctype = CONTENT_TYPE_MAP[ext] || "application/octet-stream";
        return new Response(cached, {
          status: 200,
          headers: {
            "Content-Type": ctype,
            "Cache-Control": `public, max-age=${86400 * 30}`
          }
        });
      }
    } catch {
    }
  }
  let assetResp = await fetchAsset(path, env);
  if (assetResp.ok) {
    const ctype = CONTENT_TYPE_MAP[ext] || assetResp.headers.get("Content-Type") || "application/octet-stream";
    const body = ctype.startsWith("text/") || ctype.startsWith("application/") ? await assetResp.text() : await assetResp.arrayBuffer();
    const headers = new Headers({ "Content-Type": ctype });
    if (isHtml) {
      headers.set("Cache-Control", "no-cache");
    } else if (isChangelog) {
      headers.set("Cache-Control", "no-cache, must-revalidate");
    } else if (isStatic) {
      headers.set("Cache-Control", `public, max-age=${86400 * 30}`);
      try {
        const cacheKey = `cache:static:${path}`;
        const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body).buffer;
        await env.CODE_EXPLORER_KV.put(cacheKey, buf, {
          expirationTtl: 86400 * 7
        });
      } catch {
      }
    }
    return new Response(body, { status: 200, headers });
  }
  const rootGhPath = "code-explorer/public/" + path.substring(1);
  const rootGhResp = await fetchFromGitHub(rootGhPath, env);
  if (rootGhResp.ok) {
    const ctype = CONTENT_TYPE_MAP[ext] || rootGhResp.headers.get("Content-Type") || "application/octet-stream";
    const body = ctype.startsWith("text/") || ctype.startsWith("application/") ? await rootGhResp.text() : await rootGhResp.arrayBuffer();
    const headers = new Headers({ "Content-Type": ctype });
    if (isHtml) {
      headers.set("Cache-Control", "no-cache");
    } else if (isChangelog) {
      headers.set("Cache-Control", "no-cache, must-revalidate");
    } else if (isStatic) {
      headers.set("Cache-Control", `public, max-age=${86400 * 30}`);
      try {
        const cacheKey = `cache:static:${path}`;
        const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body).buffer;
        await env.CODE_EXPLORER_KV.put(cacheKey, buf, {
          expirationTtl: 86400 * 7
        });
      } catch {
      }
    }
    return new Response(body, { status: 200, headers });
  }
  return new Response("Not Found", { status: 404 });
}
__name(handleStatic, "handleStatic");
var worker_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    ctx.waitUntil(
      Promise.all([
        env.CODE_EXPLORER_KV.delete("cache:home-page").catch(() => {
        }),
        env.CODE_EXPLORER_KV.delete("cache:home-page-v2").catch(() => {
        })
      ])
    );
    if (path.startsWith("/api/")) {
      return handleApi(request, env, path);
    }
    return handleStatic(request, env, path);
  }
};
export {
  worker_default as default
};
//# sourceMappingURL=worker.js.map
