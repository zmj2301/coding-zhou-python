// ============================================================
// Code Explorer - Cloudflare Worker 版本
// 纯动态 Worker，静态文件从 GitHub 代理
// ============================================================

export interface Env {
  CODE_EXPLORER_KV: KVNamespace;
  USER_PASSWORD: string;
  ADMIN_PASSWORD: string;
  JWT_SECRET: string;
  GITHUB_REPO: string;
  GITHUB_BRANCH: string;
  ZHIPU_API_KEY: string;
  ECS_SERVER_URL: string;
  OLLAMA_TUNNEL_URL: string;
  ASSETS: {
    fetch: (request: Request) => Promise<Response>;
  };
}

// ------------------------------------------------------------
// 工具函数：JWT
// ------------------------------------------------------------

function base64UrlEncode(data: Uint8Array): string {
  let str = '';
  for (let i = 0; i < data.length; i++) {
    str += String.fromCharCode(data[i]);
  }
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlDecode(str: string): Uint8Array {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) str += '=';
  const binary = atob(str);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function getKey(secret: string): Promise<CryptoKey> {
  const enc = new TextEncoder();
  return crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify']
  );
}

async function signJwt(
  payload: Record<string, any>,
  secret: string,
  expiresInSeconds: number = 604800
): Promise<string> {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const fullPayload = { ...payload, iat: now, exp: now + expiresInSeconds };
  const headerB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(header)));
  const payloadB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(fullPayload)));
  const key = await getKey(secret);
  const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const signature = await crypto.subtle.sign('HMAC', key, data);
  const sigB64 = base64UrlEncode(new Uint8Array(signature));
  return `${headerB64}.${payloadB64}.${sigB64}`;
}

async function verifyJwt(token: string, secret: string): Promise<any | null> {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const [headerB64, payloadB64, sigB64] = parts;
    const key = await getKey(secret);
    const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const signature = base64UrlDecode(sigB64);
    const isValid = await crypto.subtle.verify('HMAC', key, signature, data);
    if (!isValid) return null;
    const payload = JSON.parse(new TextDecoder().decode(base64UrlDecode(payloadB64)));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch {
    return null;
  }
}

// ------------------------------------------------------------
// 工具函数：Cookie 和响应
// ------------------------------------------------------------

function parseCookies(cookieHeader: string | null): Record<string, string> {
  const cookies: Record<string, string> = {};
  if (!cookieHeader) return cookies;
  for (const cookie of cookieHeader.split(';')) {
    const [name, ...rest] = cookie.trim().split('=');
    if (name) cookies[name] = rest.join('=');
  }
  return cookies;
}

function getTokenFromRequest(request: Request): string | null {
  const cookieHeader = request.headers.get('Cookie');
  const cookies = parseCookies(cookieHeader);
  return cookies['wg_token'] || null;
}

// 密码哈希（SHA-256）
async function hashPassword(password: string): Promise<string> {
  const enc = new TextEncoder();
  const buf = await crypto.subtle.digest('SHA-256', enc.encode(password));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function checkAuth(request: Request, env: Env): Promise<boolean> {
  const token = getTokenFromRequest(request);
  if (!token) return false;
  const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
  return payload !== null;
}

async function checkAdmin(request: Request, env: Env): Promise<boolean> {
  if (!env.ADMIN_PASSWORD) return false;
  const token = getTokenFromRequest(request);
  if (!token) return false;
  const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
  return payload !== null && payload.is_admin === true;
}

function jsonResponse(data: any, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: corsHeaders()
  });
}

function errorResponse(message: string, status: number = 400): Response {
  return jsonResponse({ error: message }, status);
}

function corsHeaders(): Headers {
  const h = new Headers();
  h.set('Content-Type', 'application/json; charset=utf-8');
  h.set('Access-Control-Allow-Origin', '*');
  h.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  h.set('Access-Control-Allow-Headers', 'Content-Type');
  return h;
}

function setCookie(response: Response, name: string, value: string, maxAge: number = 86400 * 7): Response {
  const cookie = `${name}=${value}; Path=/; Max-Age=${maxAge}; HttpOnly; SameSite=Lax`;
  const newHeaders = new Headers(response.headers);
  newHeaders.append('Set-Cookie', cookie);
  return new Response(response.body, { status: response.status, headers: newHeaders });
}

function clearCookie(response: Response, name: string): Response {
  const cookie = `${name}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax`;
  const newHeaders = new Headers(response.headers);
  newHeaders.append('Set-Cookie', cookie);
  return new Response(response.body, { status: response.status, headers: newHeaders });
}

function isBrowserRequest(request: Request): boolean {
  const accept = request.headers.get('Accept') || '';
  return accept.includes('text/html');
}

function redirectResponse(url: string, status: number = 302): Response {
  return new Response(null, { status, headers: { Location: url } });
}

function optionsResponse(): Response {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}

// ------------------------------------------------------------
// 工具：GitHub 代理
// ------------------------------------------------------------

async function fetchFromGitHub(path: string, env: Env): Promise<Response> {
  const repo = env.GITHUB_REPO || 'zmj2301/coding-zhou-python';
  const branch = env.GITHUB_BRANCH || 'main';
  const cleanPath = path.replace(/^\/+/, '');
  const url = `https://raw.githubusercontent.com/${repo}/${branch}/${encodeURI(cleanPath)}`;
  return fetch(url);
}

// ------------------------------------------------------------
// 工具：ECS 服务器代理
// ------------------------------------------------------------

async function fetchFromEcs(path: string, env: Env, request: Request): Promise<Response> {
  const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165.nip.io';
  const url = `${ecsUrl}${path}`;
  const headers = new Headers(request.headers);
  headers.set('Host', new URL(ecsUrl).host);
  // 保留 Cookie 用于认证
  const cookie = request.headers.get('Cookie');
  if (cookie) {
    headers.set('Cookie', cookie);
  }
  return fetch(url, { method: request.method, headers });
}

async function proxyStreamToEcs(path: string, env: Env, request: Request): Promise<Response> {
  const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165.nip.io';
  const url = `${ecsUrl}${path}`;
  const headers = new Headers(request.headers);
  headers.set('Host', new URL(ecsUrl).host);
  headers.set('Accept', 'text/event-stream');
  const body = request.method === 'POST' ? await request.text() : undefined;
  const ecsResp = await fetch(url, {
    method: request.method,
    headers,
    body,
  });
  // 使用 TransformStream 确保不缓冲，立即转发
  const { readable, writable } = new TransformStream({
    transform(chunk, controller) {
      controller.enqueue(chunk);
    },
  });
  ecsResp.body?.pipeTo(writable).catch(() => {});
  const responseHeaders = new Headers();
  responseHeaders.set('Content-Type', 'text/event-stream; charset=utf-8');
  responseHeaders.set('Cache-Control', 'no-cache, no-transform');
  responseHeaders.set('Connection', 'keep-alive');
  responseHeaders.set('Access-Control-Allow-Origin', '*');
  responseHeaders.set('X-Accel-Buffering', 'no');
  responseHeaders.delete('Content-Length');
  responseHeaders.delete('Content-Encoding');
  return new Response(readable, { status: ecsResp.status, headers: responseHeaders });
}

// 给 text/* 和 application/json 响应补 charset=utf-8，防止浏览器按系统默认编码（GBK）解 UTF-8 导致乱码
function ensureUtf8Charset(resp: Response): Response {
  const ct = resp.headers.get('content-type') || resp.headers.get('Content-Type') || '';
  if (!ct) return resp;
  // text/* 系列 + application/json + application/javascript，都补 charset=utf-8
  if ((ct.startsWith('text/') || ct.startsWith('application/json') || ct.startsWith('application/javascript')) && !/charset=/i.test(ct)) {
    const newCt = ct + '; charset=utf-8';
    const headers = new Headers(resp.headers);
    headers.set('Content-Type', newCt);
    return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers });
  }
  return resp;
}

async function fetchAsset(path: string, env: Env): Promise<Response> {
  try {
    if (env.ASSETS && typeof env.ASSETS.fetch === 'function') {
      const cleanPath = path.startsWith('/') ? path.substring(1) : path;
      const resp = await env.ASSETS.fetch(new Request('/' + cleanPath));
      if (resp.ok) return ensureUtf8Charset(resp);
    }
  } catch {}
  // 先尝试 code-explorer/public/，再尝试 public/
  let resp = await fetchFromGitHub('code-explorer/public' + path, env);
  if (!resp.ok) {
    resp = await fetchFromGitHub('public' + path, env);
  }
  return ensureUtf8Charset(resp);
}

// ------------------------------------------------------------
// 语言检测
// ------------------------------------------------------------

function getLanguage(ext: string): string {
  const langMap: Record<string, string> = {
    '.py': 'python', '.cpp': 'cpp', '.c': 'c', '.h': 'c',
    '.java': 'java', '.js': 'javascript', '.jsx': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript', '.html': 'html',
    '.css': 'css', '.json': 'json', '.xml': 'xml',
    '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown',
    '.sql': 'sql', '.sh': 'bash', '.bat': 'bash',
    '.rs': 'rust', '.go': 'go', '.rb': 'ruby', '.php': 'php',
    '.swift': 'swift', '.kt': 'kotlin', '.scala': 'scala', '.r': 'r',
    '.lua': 'lua', '.dart': 'dart', '.vue': 'html', '.svelte': 'html',
    '.toml': 'ini', '.ini': 'ini', '.cfg': 'ini',
    '.csv': 'plaintext', '.txt': 'plaintext', '.spec': 'plaintext'
  };
  return langMap[ext.toLowerCase()] || 'plaintext';
}

// ------------------------------------------------------------
// HTML 资源路径重写
// ------------------------------------------------------------

const CONTENT_TYPE_MAP: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon'
};

function getExt(filePath: string): string {
  const idx = filePath.lastIndexOf('.');
  return idx >= 0 ? filePath.substring(idx).toLowerCase() : '';
}

function rewriteHtmlResourcePaths(html: string, filePath: string): string {
  const dirPath = filePath.substring(0, filePath.lastIndexOf('/') + 1);

  function makePreviewUrl(original: string): string | null {
    if (!original || original.startsWith('/') || original.startsWith('http://') ||
        original.startsWith('https://') || original.startsWith('data:') ||
        original.startsWith('#') || original.startsWith('mailto:')) {
      return null;
    }
    try {
      const resolved = new URL(original, 'http://base/' + dirPath).pathname.substring(1);
      return '/api/files/preview?path=' + encodeURIComponent(resolved);
    } catch {
      return null;
    }
  }

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

// ------------------------------------------------------------
// 文件搜索
// ------------------------------------------------------------

function searchInTree(tree: any[], query: string): any[] {
  const results: any[] = [];
  query = query.toLowerCase();
  for (const item of tree) {
    if (item.type === 'file') {
      if (item.name.toLowerCase().includes(query)) {
        results.push({ name: item.name, path: item.path, ext: item.ext });
      }
    } else if (item.type === 'directory' && item.children) {
      results.push(...searchInTree(item.children, query));
    }
  }
  return results;
}

// ------------------------------------------------------------
// KV 工具：安全文件名
// ------------------------------------------------------------

function safeProjectName(project: string): string {
  return project.replace(/[\/\\:*?"<>|]/g, '_');
}

// ------------------------------------------------------------
// 缓存工具
// ------------------------------------------------------------

const STATIC_EXT = new Set([
  '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
  '.webp', '.ttf', '.woff', '.woff2', '.eot', '.otf', '.mp3',
  '.wav', '.ogg', '.mp4', '.webm', '.json', '.md'
]);

function isStaticAsset(ext: string): boolean {
  return STATIC_EXT.has(ext.toLowerCase());
}

function addCacheHeader(headers: Headers, maxAgeSeconds: number): void {
  headers.set('Cache-Control', `public, max-age=${maxAgeSeconds}`);
}

// ------------------------------------------------------------
// 全局缓存：文件树（内存 + KV 双层缓存）
// ------------------------------------------------------------

let fileTreeCache: any = null;
let fileTreeCacheTime = 0;

async function getFileTree(env: Env): Promise<any[]> {
  const now = Date.now();
  if (fileTreeCache && now - fileTreeCacheTime < 300000) {
    return fileTreeCache;
  }
  try {
    const cached = await env.CODE_EXPLORER_KV.get('cache:file-tree', { type: 'json' });
    if (cached) {
      fileTreeCache = cached as any[];
      fileTreeCacheTime = now;
      return fileTreeCache;
    }
  } catch {}
  try {
    const resp = await fetchAsset('/file-tree.json', env);
    if (resp.ok) {
      const tree = await resp.json();
      fileTreeCache = tree;
      fileTreeCacheTime = now;
      try {
        await env.CODE_EXPLORER_KV.put('cache:file-tree', JSON.stringify(tree), {
          expirationTtl: 86400
        });
      } catch {}
      return tree;
    }
  } catch {}
  return [];
}

// ------------------------------------------------------------
// API 处理函数
// ------------------------------------------------------------

async function handleApi(request: Request, env: Env, path: string): Promise<Response> {
  const url = new URL(request.url);

  // OPTIONS 预检
  if (request.method === 'OPTIONS') return optionsResponse();

  // ---- 认证相关（公开） ----
  if (path === '/api/auth-check') {
    const authenticated = await checkAuth(request, env);
    let user = null;
    if (authenticated) {
      const token = getTokenFromRequest(request);
      if (token) {
        const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
        if (payload) {
          user = {
            id: 1,
            username: payload.sub || 'user',
            role: payload.is_admin ? 'admin' : 'user'
          };
        }
      }
    }
    return jsonResponse({ authenticated, passwordSet: Boolean(env.USER_PASSWORD), user });
  }

  if (path === '/api/login' && request.method === 'POST') {
    try {
      const data = await request.json();
      const username = (data.username || '').trim();
      const password = data.password || '';
      if (!username || !password) return errorResponse('请输入用户名和密码', 400);

      let valid = false;
      // 1. 优先检查 KV 中注册的用户
      const userStr = await env.CODE_EXPLORER_KV.get(`user:${username}`);
      if (userStr) {
        const user = JSON.parse(userStr);
        const hashed = await hashPassword(password);
        valid = (user.passwordHash === hashed);
      }
      // 2. 回退到共享密码（向后兼容）
      if (!valid && env.USER_PASSWORD && password === env.USER_PASSWORD) {
        valid = true;
      }

      if (!valid) return errorResponse('用户名或密码错误', 401);

      const token = await signJwt(
        { sub: username, is_admin: false },
        env.JWT_SECRET || 'default-secret-change-me',
        604800
      );
      const resp = jsonResponse({
        token,
        user: { id: 1, username, role: 'user' }
      });
      return setCookie(resp, 'wg_token', token, 604800);
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  // 用户注册
  if (path === '/api/register' && request.method === 'POST') {
    try {
      const data = await request.json();
      const username = (data.username || '').trim();
      const password = data.password || '';
      if (!username || !password) return errorResponse('请填写用户名和密码', 400);
      if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) return errorResponse('用户名需为3-20位字母、数字或下划线', 400);
      if (password.length < 6) return errorResponse('密码长度至少6位', 400);

      // 检查用户名是否已存在
      const existing = await env.CODE_EXPLORER_KV.get(`user:${username}`);
      if (existing) return errorResponse('用户名已被注册', 409);

      // 存储用户（密码哈希）
      const passwordHash = await hashPassword(password);
      await env.CODE_EXPLORER_KV.put(`user:${username}`, JSON.stringify({
        username,
        passwordHash,
        createdAt: Math.floor(Date.now() / 1000),
      }));

      return jsonResponse({ success: true, username });
    } catch (e: any) {
      return errorResponse('注册失败: ' + (e.message || '未知错误'), 500);
    }
  }

  if (path === '/api/logout' && request.method === 'POST') {
    const resp = jsonResponse({ success: true });
    return clearCookie(resp, 'wg_token');
  }

  if (path === '/api/admin/login' && request.method === 'POST') {
    try {
      const data = await request.json();
      const password = data.password || '';
      if (!env.ADMIN_PASSWORD) return errorResponse('服务器未设置管理员密码', 500);
      if (password !== env.ADMIN_PASSWORD) return errorResponse('管理员密码错误', 401);
      const token = await signJwt(
        { sub: 'admin', is_admin: true },
        env.JWT_SECRET || 'default-secret-change-me',
        604800
      );
      const resp = jsonResponse({
        token,
        user: { id: 0, username: 'admin', role: 'admin' }
      });
      return setCookie(resp, 'wg_token', token, 604800);
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/admin/clear-cache' && request.method === 'POST') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    let deletedCount = 0;
    try {
      let cursor: string | undefined = undefined;
      do {
        const list = await env.CODE_EXPLORER_KV.list({ prefix: 'cache:', cursor });
        const deletePromises = list.keys.map(k => env.CODE_EXPLORER_KV.delete(k.name));
        await Promise.all(deletePromises);
        deletedCount += list.keys.length;
        cursor = list.cursor as string | undefined;
      } while (cursor);
    } catch {}
    return jsonResponse({ success: true, message: `缓存已清除，共删除 ${deletedCount} 个缓存项` });
  }

  // ---- 意见反馈 API ----
  if (path === '/api/feedback' && request.method === 'POST') {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
    try {
      const data: any = await request.json();
      const content = (data.content || '').toString().trim();
      const type = ['bug', 'feature', 'suggestion', 'praise', 'other'].includes(data.type) ? data.type : 'other';
      const rating = Math.max(1, Math.min(5, parseInt(data.rating, 10) || 0));
      const project = (data.project || '').toString().trim().slice(0, 100);
      if (!content) return errorResponse('请输入反馈内容', 400);
      if (content.length < 5) return errorResponse('反馈内容至少 5 个字', 400);
      if (!rating) return errorResponse('请选择评分', 400);

      const token = getTokenFromRequest(request);
      const payload = token ? await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me') : null;
      const username = payload?.sub || (payload?.username as string) || '用户';
      const id = `fb_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

      const item = {
        id,
        username,
        type,
        content: content.slice(0, 2000),
        rating,
        project,
        created_at: Math.floor(Date.now() / 1000),
        status: 'new'
      };
      await env.CODE_EXPLORER_KV.put(`feedback:${id}`, JSON.stringify(item));
      return jsonResponse({ success: true, id, message: '反馈提交成功' });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/feedback/list') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    const items: any[] = [];
    try {
      let cursor: string | undefined = undefined;
      do {
        const list = await env.CODE_EXPLORER_KV.list({ prefix: 'feedback:', cursor });
        for (const key of list.keys) {
          const raw = await env.CODE_EXPLORER_KV.get(key.name);
          if (raw) {
            try { items.push(JSON.parse(raw)); } catch {}
          }
        }
        cursor = list.cursor as string | undefined;
      } while (cursor);
    } catch {}
    items.sort((a, b) => (b.created_at || 0) - (a.created_at || 0));
    return jsonResponse({ feedback: items });
  }

  if (path === '/api/feedback/delete' && request.method === 'POST') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    try {
      const data: any = await request.json();
      const id = (data.id || '').toString();
      if (!id) return errorResponse('缺少反馈 ID', 400);
      await env.CODE_EXPLORER_KV.delete(`feedback:${id}`);
      return jsonResponse({ success: true });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  // ---- 需要认证的 API ----
  const needAuth = path.startsWith('/api/files/') ||
    path.startsWith('/api/comments') ||
    path.startsWith('/api/code/') ||
    path === '/api/likes' ||
    path === '/api/admin/dashboard';

  if (needAuth) {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
  }

  // ---- 代码执行 API（流式）----
  if (path === '/api/code/start') {
    return proxyStreamToEcs('/api/run/start' + (url.search || ''), env, request);
  }
  if (path === '/api/code/stop') {
    return fetchFromEcs('/api/run/stop', env, request);
  }

  // ---- 文件 API ----
  if (path === '/api/files/tree') {
    const tree = await getFileTree(env);
    const resp = jsonResponse(tree);
    addCacheHeader(resp.headers, 300);
    return resp;
  }

  // ---- 项目列表 API（轻量级，合并点赞/评论数）----
  if (path === '/api/projects/list') {
    const CACHE_KEY = 'cache:project-meta-v2';
    const CACHE_TTL = 1800;
    try {
      const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: 'json' });
      if (cached && (Date.now() - cached.timestamp) < CACHE_TTL * 1000) {
        const resp = jsonResponse(cached.projects);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {}

    const listResp = await fetchAsset('/project-list.json', env);
    if (!listResp.ok) return errorResponse('项目列表不存在', 404);
    const projects = await listResp.json();

    const likesMap: Record<string, number> = {};
    const commentsMap: Record<string, number> = {};
    try {
      const cachedLikes = await env.CODE_EXPLORER_KV.get('cache:likes', { type: 'json' });
      if (cachedLikes) {
        Object.assign(likesMap, cachedLikes);
      } else {
        const likesList = await env.CODE_EXPLORER_KV.list({ prefix: 'likes:' });
        for (const key of likesList.keys) {
          const project = key.name.substring('likes:'.length);
          const value = await env.CODE_EXPLORER_KV.get(key.name);
          likesMap[project] = parseInt(value || '0', 10) || 0;
        }
        try {
          await env.CODE_EXPLORER_KV.put('cache:likes', JSON.stringify(likesMap), {
            expirationTtl: 1800
          });
        } catch {}
      }
    } catch {}
    try {
      const cachedComments = await env.CODE_EXPLORER_KV.get('cache:comment-counts', { type: 'json' });
      if (cachedComments) {
        Object.assign(commentsMap, cachedComments);
      } else {
        const commentsList = await env.CODE_EXPLORER_KV.list({ prefix: 'comments:' });
        for (const key of commentsList.keys) {
          const project = key.name.substring('comments:'.length);
          const value = await env.CODE_EXPLORER_KV.get(key.name);
          try {
            const parsed = JSON.parse(value || '{}');
            commentsMap[project] = (parsed.comments || []).length;
          } catch { commentsMap[project] = 0; }
        }
        try {
          await env.CODE_EXPLORER_KV.put('cache:comment-counts', JSON.stringify(commentsMap), {
            expirationTtl: 1800
          });
        } catch {}
      }
    } catch {}

    const projectsWithMeta = projects.map((p: any) => ({
      ...p,
      likes: likesMap[p.path] || 0,
      comments: commentsMap[p.path] || 0
    }));

    try {
      await env.CODE_EXPLORER_KV.put(CACHE_KEY, JSON.stringify({
        projects: projectsWithMeta,
        timestamp: Date.now()
      }), { expirationTtl: CACHE_TTL });
    } catch {}

    const resp = jsonResponse(projectsWithMeta);
    addCacheHeader(resp.headers, 300);
    return resp;
  }

  // ---- 项目文件树 API（按需加载，优先代理到ECS）----
  if (path === '/api/projects/tree') {
    const projPath = url.searchParams.get('path') || '';
    if (!projPath) return errorResponse('缺少 path 参数');
    if (projPath.includes('..') || projPath.startsWith('/')) return errorResponse('访问被拒绝', 403);
    // 优先代理到 ECS 服务器（ECS 有实际文件系统，可以实时扫描项目结构）
    try {
      const ecsResp = await fetchFromEcs(`/api/projects/tree${url.search}`, env, request);
      if (ecsResp.ok) {
        const treeData = await ecsResp.json();
        const resp = jsonResponse(treeData);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {}
    // ECS 失败时回退到 GitHub Assets（预生成的project-trees JSON）
    const safeName = projPath.replace(/\//g, '__').replace(/\\/g, '__');
    const treeResp = await fetchAsset(`/project-trees/${safeName}.json`, env);
    if (!treeResp.ok) return errorResponse('项目文件树不存在', 404);
    const treeData = await treeResp.json();
    const resp = jsonResponse(treeData);
    addCacheHeader(resp.headers, 86400);
    return resp;
  }

  if (path === '/api/files/content') {
    const filePath = url.searchParams.get('path') || '';
    if (!filePath) return errorResponse('缺少 path 参数');
    if (filePath.includes('..') || filePath.startsWith('/')) return errorResponse('访问被拒绝：路径越界', 403);

    // 代理到 ECS 服务器（ECS 服务器有实际文件）
    const ecsResp = await fetchFromEcs(`/api/files/content${url.search}`, env, request);
    if (ecsResp.ok) {
      // 成功时直接返回 ECS 响应
      const data = await ecsResp.json();
      const resp = jsonResponse(data);
      addCacheHeader(resp.headers, 3600);
      return resp;
    }

    // ECS 失败时回退到 GitHub
    const cacheKey = `cache:file:${filePath}`;
    try {
      const cached = await env.CODE_EXPLORER_KV.get(cacheKey, { type: 'json' });
      if (cached) {
        const resp = jsonResponse(cached);
        addCacheHeader(resp.headers, 3600);
        return resp;
      }
    } catch {}

    const ghResp = await fetchFromGitHub(filePath, env);
    if (!ghResp.ok) {
      if (ghResp.status === 404) return errorResponse('文件不存在', 404);
      return errorResponse('读取文件失败', ghResp.status);
    }
    const content = await ghResp.text();
    const ext = getExt(filePath);
    const name = filePath.split('/').pop() || filePath;
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
    } catch {}
    const resp = jsonResponse(result);
    addCacheHeader(resp.headers, 3600);
    return resp;
  }

  if (path === '/api/projects/readme') {
    // 扫描项目 README：依次尝试常见大小写文件名，找不到则返回 found:false（由前端生成预览）
    const projPath = url.searchParams.get('path') || '';
    if (!projPath) return errorResponse('缺少 path 参数');
    if (projPath.includes('..') || projPath.startsWith('/')) return errorResponse('访问被拒绝：路径越界', 403);
    const readmeNames = ['README.md', 'readme.md', 'Readme.md', 'README.markdown', 'README.MD', 'readme.markdown'];
    for (const name of readmeNames) {
      const filePath = `${projPath}/${name}`;
      try {
        const ghResp = await fetchFromGitHub(filePath, env);
        if (ghResp.ok) {
          const content = await ghResp.text();
          if (content && content.trim()) {
            const result = { found: true, path: filePath, name, content };
            const resp = jsonResponse(result);
            addCacheHeader(resp.headers, 3600);
            return resp;
          }
        }
      } catch {}
    }
    const resp = jsonResponse({ found: false, path: projPath });
    addCacheHeader(resp.headers, 360);
    return resp;
  }

  if (path === '/api/files/preview') {
    const filePath = url.searchParams.get('path') || '';
    if (!filePath) return errorResponse('缺少 path 参数');
    if (filePath.includes('..') || filePath.startsWith('/')) return errorResponse('访问被拒绝：路径越界', 403);

    // 优先代理到 ECS 服务器
    const ecsResp = await fetchFromEcs(`/api/files/preview${url.search}`, env, request);
    if (ecsResp.ok) {
      return ecsResp;
    }

    const ext = getExt(filePath);
    const contentType = CONTENT_TYPE_MAP[ext] || 'application/octet-stream';

    if (ext === '.html' || ext === '.htm') {
      const ghResp = await fetchFromGitHub(filePath, env);
      if (!ghResp.ok) {
        if (ghResp.status === 404) return errorResponse('文件不存在', 404);
        return errorResponse('读取文件失败', ghResp.status);
      }
      let html = await ghResp.text();
      html = rewriteHtmlResourcePaths(html, filePath);
      return new Response(html, {
        status: 200,
        headers: {
          'Content-Type': contentType,
          'Cache-Control': 'no-store'
        }
      });
    }

    const cacheKey = `cache:preview:${filePath}`;
    const isStatic = isStaticAsset(ext);

    if (isStatic) {
      try {
        const cached = await env.CODE_EXPLORER_KV.get(cacheKey, { type: 'arrayBuffer' });
        if (cached) {
          return new Response(cached, {
            status: 200,
            headers: {
              'Content-Type': contentType,
              'Cache-Control': `public, max-age=${86400 * 30}`
            }
          });
        }
      } catch {}
    }

    const ghResp = await fetchFromGitHub(filePath, env);
    if (!ghResp.ok) {
      if (ghResp.status === 404) return errorResponse('文件不存在', 404);
      return errorResponse('读取文件失败', ghResp.status);
    }

    const body = contentType.startsWith('text/') || contentType.startsWith('application/')
      ? await ghResp.text()
      : await ghResp.arrayBuffer();

    if (isStatic) {
      try {
        const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body as string).buffer;
        await env.CODE_EXPLORER_KV.put(cacheKey, buf as any, {
          expirationTtl: 86400 * 7
        });
      } catch {}
      return new Response(body, {
        status: 200,
        headers: {
          'Content-Type': contentType,
          'Cache-Control': `public, max-age=${86400 * 30}`
        }
      });
    }

    return new Response(body, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'no-store'
      }
    });
  }

  if (path === '/api/files/search') {
    const query = (url.searchParams.get('q') || '').toLowerCase();
    if (!query) return jsonResponse([]);
    const tree = await getFileTree(env);
    const results = searchInTree(tree, query);
    const resp = jsonResponse(results.slice(0, 100));
    addCacheHeader(resp.headers, 300);
    return resp;
  }

  // ---- 评论 API ----
  if (path === '/api/comments') {
    const project = url.searchParams.get('project') || '';

    if (request.method === 'GET') {
      if (!project) return errorResponse('缺少 project 参数');
      const key = `comments:${safeProjectName(project)}`;
      try {
        const data = await env.CODE_EXPLORER_KV.get(key);
        if (data) {
          try { return jsonResponse(JSON.parse(data)); } catch {}
        }
        return jsonResponse({ project, comments: [] });
      } catch (e) {
        return errorResponse(`加载评论失败: ${e}`, 500);
      }
    }

    if (request.method === 'POST') {
      try {
        const data = await request.json();
        const project = data.project || '';
        const text = (data.text || '').trim();
        if (!project || !text) return errorResponse('缺少 project 或 text 参数');

        const key = `comments:${safeProjectName(project)}`;
        let projectData: any = { project, comments: [] };
        const existing = await env.CODE_EXPLORER_KV.get(key);
        if (existing) { try { projectData = JSON.parse(existing); } catch {} }

        const commentId = Math.random().toString(36).substring(2, 10);
        const comment = {
          id: commentId, project, text,
          timestamp: Date.now(), image: null, likes: 0
        };
        projectData.comments.push(comment);
        await env.CODE_EXPLORER_KV.put(key, JSON.stringify(projectData));
        try { await env.CODE_EXPLORER_KV.delete('cache:comment-counts'); } catch {}
        try { await env.CODE_EXPLORER_KV.delete('cache:project-meta-v2'); } catch {}
        try { await env.CODE_EXPLORER_KV.delete('cache:home-page-v3'); } catch {}
        return jsonResponse(comment, 201);
      } catch {
        return errorResponse('无效的请求', 400);
      }
    }
  }

  if (path === '/api/comments/counts') {
    try {
      const cached = await env.CODE_EXPLORER_KV.get('cache:comment-counts', { type: 'json' });
      if (cached) {
        const resp = jsonResponse(cached);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {}
    const counts: Record<string, number> = {};
    try {
      const list = await env.CODE_EXPLORER_KV.list({ prefix: 'comments:' });
      for (const key of list.keys) {
        try {
          const data = await env.CODE_EXPLORER_KV.get(key.name);
          if (data) {
            const parsed = JSON.parse(data);
            if (parsed.project && Array.isArray(parsed.comments)) {
              counts[parsed.project] = parsed.comments.length;
            }
          }
        } catch {}
      }
      try {
        await env.CODE_EXPLORER_KV.put('cache:comment-counts', JSON.stringify(counts), {
          expirationTtl: 300
        });
      } catch {}
      const resp = jsonResponse(counts);
      addCacheHeader(resp.headers, 300);
      return resp;
    } catch (e) {
      return errorResponse(`加载评论数失败: ${e}`, 500);
    }
  }

  if (path === '/api/comments/like' && request.method === 'POST') {
    try {
      const data = await request.json();
      const project = data.project || '';
      const commentId = data.id || '';
      if (!project || !commentId) return errorResponse('缺少 project 或 id 参数');

      const key = `comments:${safeProjectName(project)}`;
      const existing = await env.CODE_EXPLORER_KV.get(key);
      if (!existing) return errorResponse('评论不存在', 404);

      let projectData: any;
      try { projectData = JSON.parse(existing); } catch { return errorResponse('评论不存在', 404); }

      let found = false;
      for (const c of projectData.comments || []) {
        if (c.id === commentId) {
          c.likes = (c.likes || 0) + 1;
          found = true;
          break;
        }
      }
      if (!found) return errorResponse('评论不存在', 404);
      await env.CODE_EXPLORER_KV.put(key, JSON.stringify(projectData));
      try { await env.CODE_EXPLORER_KV.delete('cache:comment-counts'); } catch {}
      return jsonResponse({ success: true });
    } catch {
      return errorResponse('点赞失败', 500);
    }
  }

  // ---- 点赞 API ----
  if (path === '/api/likes') {
    if (request.method === 'GET') {
      try {
        const cached = await env.CODE_EXPLORER_KV.get('cache:likes', { type: 'json' });
        if (cached) {
          const resp = jsonResponse(cached);
          addCacheHeader(resp.headers, 300);
          return resp;
        }
      } catch {}
      const likes: Record<string, number> = {};
      try {
        const list = await env.CODE_EXPLORER_KV.list({ prefix: 'likes:' });
        for (const key of list.keys) {
          const project = key.name.substring('likes:'.length);
          const value = await env.CODE_EXPLORER_KV.get(key.name);
          likes[project] = parseInt(value || '0', 10) || 0;
        }
        try {
          await env.CODE_EXPLORER_KV.put('cache:likes', JSON.stringify(likes), {
            expirationTtl: 300
          });
        } catch {}
        const resp = jsonResponse(likes);
        addCacheHeader(resp.headers, 300);
        return resp;
      } catch (e) {
        return errorResponse(`加载点赞数据失败: ${e}`, 500);
      }
    }

    if (request.method === 'POST') {
      try {
        const data = await request.json();
        const project = data.project || '';
        if (!project) return errorResponse('缺少 project 参数');
        const key = `likes:${project}`;
        let current = 0;
        const existing = await env.CODE_EXPLORER_KV.get(key);
        if (existing) current = parseInt(existing, 10) || 0;
        current += 1;
        await env.CODE_EXPLORER_KV.put(key, String(current));
        try { await env.CODE_EXPLORER_KV.delete('cache:likes'); } catch {}
        try { await env.CODE_EXPLORER_KV.delete('cache:project-meta-v2'); } catch {}
        try { await env.CODE_EXPLORER_KV.delete('cache:home-page-v3'); } catch {}
        return jsonResponse({ project, likes: current });
      } catch {
        return errorResponse('点赞失败', 500);
      }
    }
  }

  // ---- 管理员后台 ----
  if (path === '/api/admin/dashboard') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('管理员未登录', 401);

    let totalComments = 0, commentProjects = 0, totalLikes = 0, likeProjects = 0;
    try {
      const commentsList = await env.CODE_EXPLORER_KV.list({ prefix: 'comments:' });
      commentProjects = commentsList.keys.length;
      for (const key of commentsList.keys) {
        const data = await env.CODE_EXPLORER_KV.get(key.name);
        if (data) {
          try {
            const parsed = JSON.parse(data);
            if (parsed.comments && Array.isArray(parsed.comments)) {
              totalComments += parsed.comments.length;
            }
          } catch {}
        }
      }
    } catch {}
    try {
      const likesList = await env.CODE_EXPLORER_KV.list({ prefix: 'likes:' });
      likeProjects = likesList.keys.length;
      for (const key of likesList.keys) {
        const count = await env.CODE_EXPLORER_KV.get(key.name);
        if (count) totalLikes += parseInt(count, 10) || 0;
      }
    } catch {}

    return jsonResponse({
      server: { uptime: 'Cloudflare Worker (无状态)', uptime_seconds: 0, base_dir: 'GitHub Repository', port: 443, total_files: 0 },
      auth: { active_sessions: '无状态', admin_sessions: '无状态', password_set: Boolean(env.USER_PASSWORD), admin_password_set: Boolean(env.ADMIN_PASSWORD) },
      data: {
        likes_count: likeProjects,
        total_likes: totalLikes,
        likes_label: '个项目有点赞',
        comment_files: commentProjects,
        total_comments: totalComments,
        comments_label: '个项目有评论',
        uploaded_files_count: 0,
        uploads_label: '暂未启用上传功能'
      }
    });
  }

  // ---- AI 对话 API ----
  if (path === '/api/recommend' && request.method === 'POST') {
    try {
      const data = await request.json() as { messages?: { role: string; content: string }[]; input?: string; preferences?: string; context?: { folder?: string }; model?: string; needsProjects?: boolean };
      let messages = data.messages;

      if (!messages && (data.input || data.preferences)) {
        const userInput = (data.input || data.preferences || '').trim();
        if (!userInput) return errorResponse('请输入你的兴趣或需求', 400);
        messages = [{ role: 'user', content: `我的兴趣：${userInput}` }];
      }

      if (!messages || messages.length === 0) {
        return errorResponse('请输入消息', 400);
      }

      const projects = await loadProjectsForRecommend(env);
      let aiResponse: { text: string; recommendations: any[]; reasoning?: string };
      let source = 'workers';

      // AI 优先级链: Ollama (本地 ECS via Tunnel) → Workers AI (Cloudflare) → Zhipu AI
      const tunnelUrl = env.OLLAMA_TUNNEL_URL || '';
      let ollamaDebug = '';

      // 1. 尝试 Ollama (本地 qwen2.5:1.5b)
      if (tunnelUrl && tunnelUrl.includes('ollama')) {
        try {
          const started = Date.now();
          aiResponse = await callOllamaAI(messages, tunnelUrl, projects, data.context);
          source = 'ollama';
          ollamaDebug = `ok(${Date.now() - started}ms)`;
          if (!aiResponse.text && aiResponse.recommendations.length === 0) {
            throw new Error('Ollama 空响应');
          }
          console.log('[AI] Ollama OK:', ollamaDebug);
          // Ollama 成功，直接返回
          return jsonResponse({
            success: true,
            response: aiResponse.text,
            recommendations: aiResponse.recommendations || [],
            reasoning: aiResponse.reasoning || '',
            source,
          });
        } catch (e: any) {
          ollamaDebug = `fail: ${e.message || e}`;
          console.warn('[AI] Ollama failed:', ollamaDebug, '→ 降级');
        }
      } else {
        ollamaDebug = 'skipped(no tunnel url)';
      }

      // 2. 降级到 Workers AI (Cloudflare 内置 Llama 3.1)
      try {
        aiResponse = await getConversationalAI(messages, projects, env, data.context);
        source = 'workers';
        if (!aiResponse.text && aiResponse.recommendations.length === 0) {
          throw new Error('Workers AI 空响应');
        }
      } catch {
        // 3. 最后降级到 Zhipu AI
        try {
          aiResponse = await getConversationalAI(messages, projects, env, data.context, 'glm-4.7-flash');
          source = 'zhipu';
        } catch {
          return errorResponse('AI 服务暂不可用（本地模型 + Workers AI + 智谱 AI 全部失败）', 503);
        }
      }

      return jsonResponse({
        success: true,
        response: aiResponse.text,
        recommendations: aiResponse.recommendations || [],
        reasoning: aiResponse.reasoning || '',
        source,
        _ollama_debug: ollamaDebug,
      });
    } catch (e: any) {
      return errorResponse(`请求失败: ${e.message || e}`, 500);
    }
  }

  if (path === '/api/recommend' && request.method === 'OPTIONS') {
    return optionsResponse();
  }

  if (path === '/api/ai-quota') {
    try {
      const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165.nip.io';
      const resp = await fetchFromEcs('/api/ai-quota', env, request);
      if (resp.ok) {
        return new Response(await resp.text(), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      // 回退到 KV 统计
      const today = new Date().toISOString().slice(0, 10);
      const usageKey = `ai-usage:${today}`;
      const usage = parseInt(await env.CODE_EXPLORER_KV.get(usageKey) || '0', 10);
      const DAILY_LIMIT = 10000;
      const neuronsPerRequest = 100;
      const remaining = Math.max(0, DAILY_LIMIT - usage * neuronsPerRequest);
      return jsonResponse({ usage, remaining, limit: DAILY_LIMIT, neuronsPerRequest });
    } catch (e: any) {
      return jsonResponse({ usage: 0, remaining: 10000, limit: 10000, neuronsPerRequest: 100 });
    }
  }

  // ---- 资源下载 API ----
  if (path === '/api/resources/list') {
    try {
      const resp = await fetchAsset('/resource/resources.json', env);
      if (resp.ok) {
        const resources = await resp.json();
        const result = jsonResponse({ resources });
        addCacheHeader(result.headers, 300);
        return result;
      }
    } catch {}
    // 兜底：从 GitHub 获取
    try {
      const ghResp = await fetchFromGitHub('public/resource/resources.json', env);
      if (ghResp.ok) {
        const resources = await ghResp.json();
        const result = jsonResponse({ resources });
        addCacheHeader(result.headers, 300);
        return result;
      }
    } catch {}
    return jsonResponse({ resources: [] });
  }

  if (path === '/api/resources/download') {
    const resourceName = url.searchParams.get('path') || '';
    if (!resourceName) return errorResponse('缺少 path 参数');
    if (resourceName.includes('..')) return errorResponse('访问被拒绝', 403);

    // 安全检查：只允许下载 resource 目录下的文件
    const safePath = 'resource/' + resourceName;
    const assetResp = await fetchAsset('/' + safePath, env);
    if (assetResp.ok) {
      const ext = getExt(resourceName);
      const contentType = CONTENT_TYPE_MAP[ext] || 'application/octet-stream';
      const headers = new Headers(assetResp.headers);
      headers.set('Content-Type', contentType);
      const encodedName = encodeURIComponent(resourceName);
      headers.set('Content-Disposition', `attachment; filename="${encodedName}"; filename*=UTF-8''${encodedName}`);
      return new Response(assetResp.body, { status: 200, headers });
    }

    // 尝试作为目录（列表子文件）
    try {
      const listResp = await fetchAsset('/resource/' + resourceName + '/index.html', env);
      if (listResp.ok) {
        // 是目录，返回目录内容列表
        return jsonResponse({ type: 'directory', name: resourceName, message: '这是一个文件夹，请逐个下载文件' });
      }
    } catch {}

    return errorResponse('资源不存在', 404);
  }

  if (path === '/api/proxy-download') {
    const targetUrl = url.searchParams.get('url') || '';
    if (!targetUrl) return errorResponse('缺少 url 参数', 400);

    // 安全检查：只允许下载特定域名
    const allowedDomains = ['github.com', 'ollama.com', 'objects.githubusercontent.com', 'codeload.github.com'];
    let target: URL;
    try {
      target = new URL(targetUrl);
    } catch {
      return errorResponse('无效的 URL', 400);
    }
    if (!allowedDomains.some(d => target.hostname.includes(d))) {
      return errorResponse('域名不被允许', 403);
    }

    try {
      const resp = await fetch(targetUrl, {
        headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' },
        redirect: 'follow'
      });
      if (!resp.ok) return errorResponse(`下载失败: HTTP ${resp.status}`, 502);

      const headers = new Headers();
      const contentType = resp.headers.get('content-type') || 'application/octet-stream';
      headers.set('Content-Type', contentType);
      const contentLength = resp.headers.get('content-length');
      if (contentLength) headers.set('Content-Length', contentLength);

      return new Response(resp.body, { status: 200, headers });
    } catch (err: any) {
      return errorResponse(`代理下载失败: ${err.message}`, 502);
    }
  }

  if (path === '/api/proxy-download-status') {
    return jsonResponse({ status: 'ok', feature: 'proxy-download-available' });
  }

  // ---- API Key 管理 API（使用 KV 存储）----
  if (path.startsWith('/api/api-keys')) {
    const kv = env.CODE_EXPLORER_KV;

    if (path === '/api/api-keys') {
      if (request.method === 'GET') {
        try {
          const token = getTokenFromRequest(request);
          if (!token) return errorResponse('请先登录', 401);
          const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
          if (!payload) return errorResponse('请先登录', 401);
          const showAll = url.searchParams.get('all') === '1';
          const username = payload.sub || payload.username || 'user';
          const isAdmin = payload.role === 'admin';
          if (showAll && !isAdmin) return errorResponse('无权限查看全部 Key', 403);
          const keysListStr = await kv.get('api-keys:list');
          let keys = keysListStr ? JSON.parse(keysListStr) : [];
          if (!showAll) keys = keys.filter((k: any) => k.username === username);
          keys.sort((a: any, b: any) => (b.created_at || 0) - (a.created_at || 0));
          return jsonResponse({ keys }, 200);
        } catch (e: any) {
          return errorResponse('加载失败: ' + (e.message || '未知错误'), 500);
        }
      }
      if (request.method === 'POST') {
        try {
          const token = getTokenFromRequest(request);
          if (!token) return errorResponse('请先登录', 401);
          const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
          if (!payload) return errorResponse('请先登录', 401);
          const username = payload.sub || payload.username || 'user';
          const userRole = payload.role || 'user';
          const bodyText = await request.text();
          const body = bodyText ? JSON.parse(bodyText) : {};
          const name = (body.name || '').trim() || `Key-${Date.now()}`;
          const desc = (body.desc || '').trim().slice(0, 100);
          const dailyLimit = Math.max(0, parseInt(body.daily_limit) || 0);
          const expiresAt = Math.max(0, parseInt(body.expires_at) || 0);
          const keyId = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
          const apiKey = 'sk-' + keyId;
          const newKey = {
            id: Date.now(), user_id: 0, username, key: apiKey, name, desc,
            daily_limit: dailyLimit, expires_at: expiresAt,
            created_at: Math.floor(Date.now() / 1000), last_used_at: 0,
            is_active: 1, calls: 0, role: userRole
          };
          const keysListStr = await kv.get('api-keys:list');
          const keys = keysListStr ? JSON.parse(keysListStr) : [];
          keys.push(newKey);
          await kv.put('api-keys:list', JSON.stringify(keys));
          return jsonResponse({ success: true, key: apiKey, name }, 200);
        } catch (e: any) {
          return errorResponse('创建失败: ' + (e.message || '未知错误'), 500);
        }
      }
    }

    if (path === '/api/api-keys/delete' || path === '/api/api-keys/toggle') {
      try {
        const token = getTokenFromRequest(request);
        if (!token) return errorResponse('请先登录', 401);
        const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
        if (!payload) return errorResponse('请先登录', 401);
        const username = payload.sub || payload.username || 'user';
        const isAdmin = payload.role === 'admin';
        let keyId: number;
        if (request.method === 'GET') {
          keyId = parseInt(url.searchParams.get('id') || '0');
        } else {
          const bodyText = await request.text();
          const body = bodyText ? JSON.parse(bodyText) : {};
          keyId = parseInt(body.id || '0');
        }
        if (!keyId) return errorResponse('缺少 id 参数', 400);
        const keysListStr = await kv.get('api-keys:list');
        let keys = keysListStr ? JSON.parse(keysListStr) : [];
        if (path === '/api/api-keys/delete') {
          if (isAdmin) {
            keys = keys.filter((k: any) => k.id !== keyId);
          } else {
            keys = keys.filter((k: any) => !(k.id === keyId && k.username === username));
          }
          await kv.put('api-keys:list', JSON.stringify(keys));
          return jsonResponse({ success: true }, 200);
        }
        if (path === '/api/api-keys/toggle') {
          let found = false;
          for (const k of keys) {
            if (k.id === keyId) {
              if (!isAdmin && k.username !== username) return errorResponse('无权限操作', 403);
              k.is_active = k.is_active ? 0 : 1;
              found = true;
              break;
            }
          }
          if (!found) return errorResponse('未找到 Key', 404);
          await kv.put('api-keys:list', JSON.stringify(keys));
          return jsonResponse({ success: true }, 200);
        }
      } catch (e: any) {
        return errorResponse('操作失败: ' + (e.message || '未知错误'), 500);
      }
    }

    return errorResponse('接口不存在', 404);
  }

  // ---- 文件上传 API（KV 存储 + 子域名访问）----
  if (path === '/api/upload') {
    if (request.method !== 'POST') return errorResponse('方法不允许', 405);
    try {
      const token = getTokenFromRequest(request);
      if (!token) return errorResponse('请先登录', 401);
      const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
      if (!payload) return errorResponse('请先登录', 401);

      const formData = await request.formData();
      const file = formData.get('file') as File;
      if (!file || !(file instanceof File)) return errorResponse('未选择文件', 400);

      // 限制文件大小 20MB（KV 单 value 最大 25MB）
      if (file.size > 20 * 1024 * 1024) return errorResponse('文件大小不能超过 20MB', 400);

      // 生成 8 位随机子域名标识
      const id = Math.random().toString(36).slice(2, 10);
      const filename = file.name;
      const contentType = file.type || 'application/octet-stream';

      // 文件内容存 KV（ArrayBuffer），元数据通过 metadata 附加
      const buf = await file.arrayBuffer();
      await env.CODE_EXPLORER_KV.put(`upload:file:${id}`, buf, {
        metadata: {
          id, filename, contentType,
          size: file.size,
          uploader: payload.sub || payload.username || 'unknown',
          created_at: Math.floor(Date.now() / 1000),
        },
      });

      const subdomainUrl = `https://${id}.codingzhou.top`;
      return jsonResponse({
        success: true,
        id,
        filename,
        url: subdomainUrl,
        size: file.size,
        contentType,
      }, 200);
    } catch (e: any) {
      return errorResponse('上传失败: ' + (e.message || '未知错误'), 500);
    }
  }

  return errorResponse('未找到接口', 404);
}

// ------------------------------------------------------------
// AI 对话辅助函数
// ------------------------------------------------------------

const AI_MODEL = '@cf/meta/llama-3.1-8b-instruct-fp8';
const ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
const ZHIPU_MODEL = 'glm-4.7-flash';
const OLLAMA_MODEL = 'qwen2.5:1.5b';
const AI_CACHE_TTL = 3600;

function simpleHashForAI(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return hash.toString(36);
}

async function loadProjectsForRecommend(env: Env): Promise<any[]> {
  const CACHE_KEY = 'cache:project-meta-v2';
  try {
    const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: 'json' });
    if (cached && cached.projects) return cached.projects;
  } catch {}
  const listResp = await fetchAsset('/project-list.json', env);
  if (!listResp.ok) return [];
  try { return await listResp.json(); } catch { return []; }
}

function buildConversationalPrompt(projects: any[], contextInfo?: { folder?: string }): string {
  let projectSection = '';
  if (projects && projects.length > 0) {
    const projectList = projects.map((p: any) =>
      `- ${p.name} (path: ${p.path}, type: ${p.type || 'unknown'}, desc: ${p.description || 'none'})`
    ).join('\n');
    projectSection = `\n可用的项目列表：\n${projectList}\n`;
  }

  let contextNote = '';
  if (contextInfo?.folder) {
    contextNote = `\n用户当前关注的文件夹：${contextInfo.folder}\n`;
  }

  // 如果有项目列表，包含推荐指令；否则只是普通聊天
  const recommendInstruction = projects && projects.length > 0
    ? `\n当用户表达兴趣或需求时，推荐 3-5 个最相关的项目。推荐时在回复末尾附上 JSON 格式：
---RECOMMEND---
[{"path": "项目路径", "reason": "推荐理由", "name": "项目名称"}]
---END---
没有推荐需求时正常聊天，不要强行推荐。`
    : '';

  return `你是一个热情友好的编程助手，名叫"小码"。你可以和用户自然地聊天、解答编程问题，也可以推荐项目。

你的性格：
- 说话语气像朋友一样自然，不要太正式
- 推荐项目时要说明推荐理由，让人觉得有说服力
- 如果用户问了具体需求，就帮他匹配最合适的项目
- 如果只是聊天，就轻松愉快地聊，不用每次都推荐项目
${projectSection}${contextNote}${recommendInstruction}`;
}

async function callOllamaAI(messages: { role: string; content: string }[], tunnelUrl: string, projects: any[], contextInfo?: { folder?: string }): Promise<{ text: string; recommendations: any[]; reasoning?: string }> {
  const systemPrompt = buildConversationalPrompt(projects, contextInfo);
  const payload = {
    model: OLLAMA_MODEL,
    messages: [
      { role: 'system', content: systemPrompt },
      ...messages
    ],
    stream: false,
    options: { num_predict: 100, temperature: 0.7 }
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 85000);

  try {
    const resp = await fetch(`${tunnelUrl.replace(/\/$/, '')}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
      cf: { connectTimeout: 85 }
    });

    if (!resp.ok) {
      const err = await resp.text();
      throw new Error(`Ollama HTTP ${resp.status}: ${err.substring(0, 200)}`);
    }

    const data: any = await resp.json();
    let text = data.message?.content || '';

    // 解析推荐 JSON
    const recMatch = text.match(/---RECOMMEND---\n?([\s\S]*?)\n?---END---/);
    let recommendations: any[] = [];
    if (recMatch) {
      try {
        const parsed = JSON.parse(recMatch[1]);
        if (Array.isArray(parsed)) {
          recommendations = parsed.filter((r: any) => r.path && r.reason).map((r: any) => ({
            path: r.path, reason: r.reason, name: r.name || r.path
          })).slice(0, 5);
        }
      } catch {}
      text = text.replace(/---RECOMMEND---[\s\S]*?---END---/, '').trim();
    }

    if (!text && recommendations.length > 0) {
      text = '为你推荐以下项目：';
    } else if (!text) {
      text = '抱歉，AI 暂时无法生成回复，请稍后再试。';
    }
    return { text, recommendations };
  } finally {
    clearTimeout(timeoutId);
  }
}

async function callZhipuAI(messages: { role: string; content: string }[], apiKey: string, projects: any[], contextInfo?: { folder?: string }, model: string = ZHIPU_MODEL): Promise<{ text: string; recommendations: any[]; reasoning?: string }> {
  const systemPrompt = buildConversationalPrompt(projects, contextInfo);
  const payload = {
    model,
    messages: [
      { role: 'system', content: systemPrompt },
      ...messages
    ],
    temperature: 0.7,
    max_tokens: 800,
    stream: false,
    thinking: { type: 'enabled' }
  };

  const resp = await fetch(ZHIPU_API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Zhipu API error: ${resp.status} ${err}`);
  }

  const data = await resp.json();
  let text = data.choices?.[0]?.message?.content || '';
  const reasoning = data.choices?.[0]?.message?.reasoning_content || '';

  const recMatch = text.match(/---RECOMMEND---\n?([\s\S]*?)\n?---END---/);
  let recommendations: any[] = [];
  if (recMatch) {
    try {
      const parsed = JSON.parse(recMatch[1]);
      if (Array.isArray(parsed)) {
        recommendations = parsed.filter((r: any) => r.path && r.reason).map((r: any) => ({
          path: r.path, reason: r.reason, name: r.name || r.path
        })).slice(0, 5);
      }
    } catch {}
    text = text.replace(/---RECOMMEND---[\s\S]*?---END---/, '').trim();
  }

  if (!text && recommendations.length > 0) {
    text = '为你推荐以下项目：';
  } else if (!text) {
    text = '抱歉，AI 暂时无法生成回复，请稍后再试。';
  }
  return { text, recommendations, reasoning };
}

async function getConversationalAI(messages: { role: string; content: string }[], projects: any[], env: Env, contextInfo?: { folder?: string }, model?: string): Promise<{ text: string; recommendations: any[]; reasoning?: string }> {
  // Zhipu AI (glm-4.7-flash)
  if (model === 'glm-4.7-flash') {
    const apiKey = env.ZHIPU_API_KEY;
    if (apiKey) {
      try {
        return await callZhipuAI(messages, apiKey, projects, contextInfo);
      } catch (e: any) {
        console.error('Zhipu AI call failed:', e);
      }
    }
  }

  // 默认使用 Cloudflare Workers AI (Llama 3.1)
  const ai = (env as any).AI;
  if (ai) {
    try {
      const systemPrompt = buildConversationalPrompt(projects, contextInfo);
      const response = await ai.run(AI_MODEL, {
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages
        ],
        max_tokens: 800,
        temperature: 0.7
      });

      let text = '';
      if (typeof response === 'string') text = response;
      else if (response.response) text = response.response;
      else if (response.content) text = typeof response.content === 'string' ? response.content : JSON.stringify(response.content);

      const recMatch = text.match(/---RECOMMEND---\n?([\s\S]*?)\n?---END---/);
      let recommendations: any[] = [];
      if (recMatch) {
        try {
          const parsed = JSON.parse(recMatch[1]);
          if (Array.isArray(parsed)) {
            recommendations = parsed.filter((r: any) => r.path && r.reason).map((r: any) => ({
              path: r.path, reason: r.reason, name: r.name || r.path
            })).slice(0, 5);
          }
        } catch {}
        text = text.replace(/---RECOMMEND---[\s\S]*?---END---/, '').trim();
      }

      if (!text && recommendations.length > 0) {
        text = '为你推荐以下项目：';
      } else if (!text) {
        text = '抱歉，AI 暂时无法生成回复，请稍后再试。';
      }
      return { text, recommendations };
    } catch (e: any) {
      console.error('AI call failed:', e);
    }
  }
  return { text: '', recommendations: [] };
}

// ------------------------------------------------------------
// 首页服务（内联项目数据 + KV 缓存）
// ------------------------------------------------------------
async function serveHomePage(request: Request, env: Env): Promise<Response> {
  const CACHE_KEY = 'cache:home-page-v3';
  const CACHE_TTL = 1800;

  try {
    const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: 'text' });
    if (cached) {
      return new Response(cached, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=60, stale-while-revalidate=300' }
      });
    }
  } catch {}

  const [htmlResp, listResp] = await Promise.all([
    fetchAsset('/index.html', env),
    fetchAsset('/project-list.json', env),
  ]);

  if (!htmlResp.ok) return new Response('首页加载失败', { status: 500 });
  let html = await htmlResp.text();

  let projects: any[] = [];
  if (listResp.ok) {
    try { projects = await listResp.json(); } catch {}
  }

  const likesMap: Record<string, number> = {};
  const commentsMap: Record<string, number> = {};
  try {
    const cachedLikes = await env.CODE_EXPLORER_KV.get('cache:likes', { type: 'json' });
    if (cachedLikes) {
      Object.assign(likesMap, cachedLikes);
    } else {
      const likesList = await env.CODE_EXPLORER_KV.list({ prefix: 'likes:' });
      for (const key of likesList.keys) {
        const project = key.name.substring('likes:'.length);
        const value = await env.CODE_EXPLORER_KV.get(key.name);
        likesMap[project] = parseInt(value || '0', 10) || 0;
      }
      try {
        await env.CODE_EXPLORER_KV.put('cache:likes', JSON.stringify(likesMap), {
          expirationTtl: 1800
        });
      } catch {}
    }
  } catch {}
  try {
    const cachedComments = await env.CODE_EXPLORER_KV.get('cache:comment-counts', { type: 'json' });
    if (cachedComments) {
      Object.assign(commentsMap, cachedComments);
    } else {
      const commentsList = await env.CODE_EXPLORER_KV.list({ prefix: 'comments:' });
      for (const key of commentsList.keys) {
        const project = key.name.substring('comments:'.length);
        const value = await env.CODE_EXPLORER_KV.get(key.name);
        try {
          const parsed = JSON.parse(value || '{}');
          commentsMap[project] = (parsed.comments || []).length;
        } catch { commentsMap[project] = 0; }
      }
      try {
        await env.CODE_EXPLORER_KV.put('cache:comment-counts', JSON.stringify(commentsMap), {
          expirationTtl: 1800
        });
      } catch {}
    }
  } catch {}

  const projectsWithMeta = projects.map(p => ({
    ...p,
    likes: likesMap[p.path] || 0,
    comments: commentsMap[p.path] || 0
  }));

  const injectScript = `<script>window.__INITIAL_PROJECTS__ = ${JSON.stringify(projectsWithMeta)};</script>`;
  html = html.replace('</head>', injectScript + '</head>');

  try {
    await env.CODE_EXPLORER_KV.put(CACHE_KEY, html, { expirationTtl: CACHE_TTL });
  } catch {}

  return new Response(html, {
    status: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=60, stale-while-revalidate=300' }
  });
}

// ------------------------------------------------------------
// 静态文件代理
// ------------------------------------------------------------

async function handleStatic(request: Request, env: Env, path: string): Promise<Response> {
  // 首页
  if (path === '/' || path === '') {
    return serveHomePage(request, env);
  }

  // web-games 页面保护
  if (path.startsWith('/web-games/') || path === '/web-games') {
    if (isBrowserRequest(request)) {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) return redirectResponse('/');
    }
  }

  // fathers-day 页面保护
  if (path.startsWith('/fathers-day/') || path === '/fathers-day') {
    if (isBrowserRequest(request)) {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) return redirectResponse('/');
    }
  }

  // resource 页面保护
  if (path.startsWith('/resource/') || path === '/resource') {
    if (isBrowserRequest(request)) {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) return redirectResponse('/');
    }
  }

  // Scratch 页面保护（静态文件从 public/scratch/ 提供）
  if (path.startsWith('/scratch/') || path === '/scratch') {
    if (isBrowserRequest(request)) {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) return redirectResponse('/');
    }
  }

  const ext = getExt(path);
  const isStatic = isStaticAsset(ext);
  const isHtml = ext === '.html' || ext === '.htm';
  const isChangelog = path === '/changelog.json';

  // 静态资源尝试 KV 缓存（changelog.json 除外，动态内容不缓存）
  if (isStatic && !isHtml && !isChangelog) {
    const cacheKey = `cache:static:${path}`;
    try {
      const cached = await env.CODE_EXPLORER_KV.get(cacheKey, { type: 'arrayBuffer' });
      if (cached) {
        const ctype = CONTENT_TYPE_MAP[ext] || 'application/octet-stream';
        return new Response(cached, {
          status: 200,
          headers: {
            'Content-Type': ctype,
            'Cache-Control': `public, max-age=${86400 * 30}`
          }
        });
      }
    } catch {}
  }

  // 优先从 Worker Assets 获取静态文件
  let assetResp = await fetchAsset(path, env);
  if (assetResp.ok) {
    const ctype = CONTENT_TYPE_MAP[ext] || assetResp.headers.get('Content-Type') || 'application/octet-stream';
    const body = ctype.startsWith('text/') || ctype.startsWith('application/')
      ? await assetResp.text()
      : await assetResp.arrayBuffer();
    const headers = new Headers({ 'Content-Type': ctype });
    if (isHtml) {
      headers.set('Cache-Control', 'no-cache');
    } else if (isChangelog) {
      headers.set('Cache-Control', 'no-cache, must-revalidate');
    } else if (isStatic) {
      headers.set('Cache-Control', `public, max-age=${86400 * 30}`);
      try {
        const cacheKey = `cache:static:${path}`;
        const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body as string).buffer;
        await env.CODE_EXPLORER_KV.put(cacheKey, buf as any, {
          expirationTtl: 86400 * 7
        });
      } catch {}
    }
    return new Response(body, { status: 200, headers });
  }

  // 目录 fallback: 尝试路径 + /index.html
  const indexPath = path.endsWith('/') ? path + 'index.html' : path + '/index.html';
  let dirAssetResp = await fetchAsset(indexPath, env);
  if (dirAssetResp.ok) {
    const ctype = CONTENT_TYPE_MAP['.html'] || dirAssetResp.headers.get('Content-Type') || 'text/html';
    const body = await dirAssetResp.text();
    return new Response(body, { status: 200, headers: { 'Content-Type': ctype, 'Cache-Control': 'no-cache' } });
  }

  // Fallback: 从 GitHub 代理静态文件（code-explorer/public 下的资源）
  const rootGhPath = 'code-explorer/public/' + path.substring(1);
  const rootGhResp = await fetchFromGitHub(rootGhPath, env);
  if (rootGhResp.ok) {
    const ctype = CONTENT_TYPE_MAP[ext] || rootGhResp.headers.get('Content-Type') || 'application/octet-stream';
    const body = ctype.startsWith('text/') || ctype.startsWith('application/')
      ? await rootGhResp.text()
      : await rootGhResp.arrayBuffer();
    const headers = new Headers({ 'Content-Type': ctype });
    if (isHtml) {
      headers.set('Cache-Control', 'no-cache');
    } else if (isChangelog) {
      headers.set('Cache-Control', 'no-cache, must-revalidate');
    } else if (isStatic) {
      headers.set('Cache-Control', `public, max-age=${86400 * 30}`);
      try {
        const cacheKey = `cache:static:${path}`;
        const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body as string).buffer;
        await env.CODE_EXPLORER_KV.put(cacheKey, buf as any, {
          expirationTtl: 86400 * 7
        });
      } catch {}
    }
    return new Response(body, { status: 200, headers });
  }

  return new Response('Not Found', { status: 404 });
}

// ------------------------------------------------------------
// 子域名文件访问（KV 存储）
// ------------------------------------------------------------
async function handleFileSubdomain(request: Request, env: Env, hostname: string): Promise<Response> {
  // 子域名部分作为文件标识，如 abc123.codingzhou.top → id = abc123
  const id = hostname.split('.')[0];
  if (!id) return errorResponse('无效的访问地址', 400);

  // 从 KV 读取文件内容（ArrayBuffer）和元数据
  const obj = await env.CODE_EXPLORER_KV.getWithMetadata(`upload:file:${id}`, { type: 'arrayBuffer' });
  if (!obj || !obj.value) return errorResponse('文件不存在或已过期', 404);

  const meta = (obj.metadata as any) || {};
  const headers = new Headers();
  headers.set('Content-Type', meta.contentType || 'application/octet-stream');
  headers.set('Cache-Control', 'public, max-age=31536000');
  headers.set('Content-Disposition', `inline; filename="${encodeURIComponent(meta.filename || id)}"`);
  headers.set('Access-Control-Allow-Origin', '*');

  return new Response(obj.value, { headers });
}

// ------------------------------------------------------------
// Worker 入口
// ------------------------------------------------------------

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const hostname = url.hostname;

    // 子域名文件访问：xxx.codingzhou.top 从 R2 读取文件
    if (hostname.endsWith('.codingzhou.top') && hostname !== 'codingzhou.top' && hostname !== 'www.codingzhou.top') {
      return handleFileSubdomain(request, env, hostname);
    }

    // API 请求
    if (path.startsWith('/api/')) {
      return handleApi(request, env, path);
    }

    // 静态文件 / 页面
    return handleStatic(request, env, path);
  }
};
