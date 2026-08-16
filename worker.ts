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


// 安全的 KV 包装
class SafeKV {
  async get(key, options) { return null; }
  async put(key, value, options) { return; }
  async delete(key) { return; }
  async list(options) { return { keys: [], list_complete: true, cursor: null }; }
}

function getSafeKV(env) {
  return env.CODE_EXPLORER_KV || new SafeKV();
}

function getTokenFromRequest(request: Request): string | null {
  const cookieHeader = request.headers.get('Cookie');
  const cookies = parseCookies(cookieHeader);
  return cookies['wg_token'] || null;
}

async function checkAuth(request: Request, env: Env): Promise<boolean> {
  if (!env.USER_PASSWORD) return true;
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
  // Encode path segments properly to handle Chinese characters
  const encodedPath = cleanPath.split('/').map(s => encodeURIComponent(s)).join('/');
  const url = `https://raw.githubusercontent.com/${repo}/${branch}/${encodedPath}`;
  return fetch(url);
}

// ------------------------------------------------------------
// 工具：ECS 服务器代理
// ------------------------------------------------------------

async function fetchFromEcs(path: string, env: Env, request: Request): Promise<Response> {
  const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165:8765';
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
  const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165:8765';
  const url = `${ecsUrl}${path}`;
  const headers = new Headers();
  const contentType = request.headers.get('Content-Type');
  if (contentType) headers.set('Content-Type', contentType);
  const cookie = request.headers.get('Cookie');
  if (cookie) headers.set('Cookie', cookie);
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

async function fetchAsset(path: string, env: Env): Promise<Response> {
  // Handle known UI icons directly (no GitHub lookup needed)
  if (path.includes('code_explorer') && path.endsWith('.png')) {
    return generateSvgIcon('#58a6ff', '#1f6feb', 'EX', 'Code Explorer v2');
  }
  if (path.includes('run_python') && path.endsWith('.png')) {
    return generateSvgIcon('#3fb950', '#1a7f37', '▶', 'Run Python v2');
  }
  if (path.includes('run_scratch') && path.endsWith('.png')) {
    return generateSvgIcon('#f0883e', '#bd561d', 'S', 'Run Scratch v2');
  }
  
  try {
    if (env.ASSETS && typeof env.ASSETS.fetch === 'function') {
      const cleanPath = path.startsWith('/') ? path.substring(1) : path;
      const resp = await env.ASSETS.fetch(new Request('/' + cleanPath));
      if (resp.ok) return resp;
    }
  } catch {}
  
  // Try multiple GitHub paths in order
  const paths = [
    'code-explorer/public' + path,
    'code-explorer' + path,
    path.replace(/^\/+/, ''),
  ];
  
  for (const ghPath of paths) {
    try {
      const resp = await fetchFromGitHub(ghPath, env);
      if (resp.ok) return resp;
    } catch {}
  }
  
  // For image requests, generate a placeholder
  const ext = getExt(path);
  if (['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'].includes(ext)) {
    return generatePlaceholderImage(ext, path);
  }
  
  return new Response('Not Found', { status: 404 });
}

function generateSvgIcon(color1: string, color2: string, icon: string, label: string): Response {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
    <defs>
      <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:${color1}"/>
        <stop offset="100%" style="stop-color:${color2}"/>
      </linearGradient>
    </defs>
    <rect width="120" height="120" rx="20" fill="url(#g)"/>
    <text x="60" y="62" text-anchor="middle" fill="white" font-size="32" font-family="sans-serif" font-weight="bold">${icon}</text>
    <text x="60" y="98" text-anchor="middle" fill="white" font-size="13" font-family="sans-serif" opacity="0.9">${label}</text>
  </svg>`;
  return new Response(svg, {
    status: 200,
    headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=86400' }
  });
}

function generatePlaceholderImage(ext: string, path: string): Response {
  // Known UI icons - generate proper SVGs
  if (path.includes('code_explorer')) {
    return generateSvgIcon('#58a6ff', '#1f6feb', 'EX', 'Code Explorer');
  }
  if (path.includes('run_python')) {
    return generateSvgIcon('#3fb950', '#1a7f37', '▶', 'Run Python');
  }
  if (path.includes('run_scratch')) {
    return generateSvgIcon('#f0883e', '#bd561d', 'S', 'Run Scratch');
  }
  
  // Extract a color from the path name for variety
  let hash = 0;
  for (let i = 0; i < path.length; i++) hash = (hash * 31 + path.charCodeAt(i)) | 0;
  const hue = Math.abs(hash) % 360;
  
  if (ext === '.svg') {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <rect width="120" height="120" fill="hsl(${hue}, 50%, 40%)"/>
      <text x="60" y="68" text-anchor="middle" fill="white" font-size="14" font-family="sans-serif" opacity="0.8">📷</text>
    </svg>`;
    return new Response(svg, {
      status: 200,
      headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=86400' }
    });
  }
  
  // For raster images, return a minimal valid PNG
  const pngData = new Uint8Array([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
    0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
    0x54, 0x78, 0x9C, 0x62, 0x60, 0x18, 0x05, 0xA3,
    0x60, 0x14, 0x8C, 0x82, 0x51, 0x30, 0x0A, 0x46,
    0xC1, 0x28, 0x18, 0x05, 0xA2, 0x14, 0x85, 0x90,
    0x01, 0x14, 0x00, 0x01, 0x78, 0x03, 0xD1, 0x3D,
    0x92, 0x46, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
    0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
  ]);
  return new Response(pngData, {
    status: 200,
    headers: { 'Content-Type': 'image/png', 'Cache-Control': 'public, max-age=3600' }
  });
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
    const cached = await getSafeKV(env).get('cache:file-tree', { type: 'json' });
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
        await getSafeKV(env).put('cache:file-tree', JSON.stringify(tree), {
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
      const password = data.password || '';
      if (!env.USER_PASSWORD) return errorResponse('服务器未设置密码', 500);
      if (password !== env.USER_PASSWORD) return errorResponse('密码错误', 401);
      const token = await signJwt(
        { sub: data.username || 'user', is_admin: false },
        env.JWT_SECRET || 'default-secret-change-me',
        604800
      );
      const resp = jsonResponse({
        token,
        user: { id: 1, username: data.username || 'user', role: 'user' }
      });
      return setCookie(resp, 'wg_token', token, 604800);
    } catch {
      return errorResponse('无效的请求', 400);
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
        const list = await getSafeKV(env).list({ prefix: 'cache:', cursor });
        const deletePromises = list.keys.map(k => getSafeKV(env).delete(k.name));
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
      const user_id = payload?.user_id || 0;
      const id = `fb_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      const now = Math.floor(Date.now() / 1000);

      const item = {
        id,
        username,
        user_id,
        type,
        content: content.slice(0, 2000),
        rating,
        project,
        created_at: now,
        updated_at: now,
        status: 'new',
        replies: []
      };
      await getSafeKV(env).put(`feedback:${id}`, JSON.stringify(item));
      return jsonResponse({ success: true, id, message: '反馈提交成功' });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/feedback/list') {
    const authenticated = await checkAuth(request, env);
    const isAdmin = await checkAdmin(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
    const token = getTokenFromRequest(request);
    const payload = token ? await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me') : null;
    const currentUserId = payload?.user_id || 0;
    const items: any[] = [];
    try {
      let cursor: string | undefined = undefined;
      do {
        const list = await getSafeKV(env).list({ prefix: 'feedback:', cursor });
        for (const key of list.keys) {
          const raw = await getSafeKV(env).get(key.name);
          if (raw) {
            try {
              const f = JSON.parse(raw);
              if (!isAdmin && f.user_id !== currentUserId) continue;
              f.reply_count = (f.replies || []).length;
              delete f.replies;
              items.push(f);
            } catch {}
          }
        }
        cursor = list.cursor as string | undefined;
      } while (cursor);
    } catch {}
    items.sort((a, b) => (b.created_at || 0) - (a.created_at || 0));
    return jsonResponse({ feedback: items });
  }

  if (path === '/api/feedback/detail') {
    const fid = url.searchParams.get('id') || '';
    if (!fid) return errorResponse('缺少反馈 ID', 400);
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
    const token = getTokenFromRequest(request);
    const payload = token ? await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me') : null;
    const isAdmin = await checkAdmin(request, env);
    const raw = await getSafeKV(env).get(`feedback:${fid}`);
    if (!raw) return errorResponse('反馈不存在', 404);
    try {
      const item = JSON.parse(raw);
      if (!isAdmin && item.user_id !== (payload?.user_id || 0)) {
        return errorResponse('无权查看', 403);
      }
      return jsonResponse(item);
    } catch {
      return errorResponse('解析失败', 500);
    }
  }

  if (path === '/api/feedback/reply' && request.method === 'POST') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    try {
      const data: any = await request.json();
      const feedbackId = (data.feedback_id || '').toString();
      const content = (data.content || '').toString().trim();
      if (!feedbackId) return errorResponse('缺少反馈 ID', 400);
      if (!content) return errorResponse('回复内容不能为空', 400);
      if (content.length < 2) return errorResponse('回复内容至少 2 个字', 400);

      const raw = await getSafeKV(env).get(`feedback:${feedbackId}`);
      if (!raw) return errorResponse('反馈不存在', 404);
      const item = JSON.parse(raw);

      const token = getTokenFromRequest(request);
      const payload = token ? await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me') : null;
      const username = payload?.sub || (payload?.username as string) || '管理员';
      const now = Math.floor(Date.now() / 1000);

      const reply = {
        id: `reply_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        username,
        user_id: payload?.user_id || 0,
        content: content.slice(0, 2000),
        is_admin: 1,
        created_at: now
      };
      item.replies = item.replies || [];
      item.replies.push(reply);
      item.updated_at = now;
      await getSafeKV(env).put(`feedback:${feedbackId}`, JSON.stringify(item));
      return jsonResponse({ success: true, reply_id: reply.id, message: '回复成功' });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/feedback/status' && request.method === 'POST') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    try {
      const data: any = await request.json();
      const id = (data.id || '').toString();
      const status = (data.status || '').toString();
      if (!id) return errorResponse('缺少反馈 ID', 400);
      if (!['new', 'processing', 'resolved', 'closed'].includes(status)) return errorResponse('无效的状态', 400);
      const raw = await getSafeKV(env).get(`feedback:${id}`);
      if (!raw) return errorResponse('反馈不存在', 404);
      const item = JSON.parse(raw);
      item.status = status;
      item.updated_at = Math.floor(Date.now() / 1000);
      await getSafeKV(env).put(`feedback:${id}`, JSON.stringify(item));
      return jsonResponse({ success: true });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/feedback/delete' && request.method === 'POST') {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
    try {
      const data: any = await request.json();
      const id = (data.id || '').toString();
      if (!id) return errorResponse('缺少反馈 ID', 400);
      const isAdmin = await checkAdmin(request, env);
      const raw = await getSafeKV(env).get(`feedback:${id}`);
      if (!raw) return errorResponse('反馈不存在', 404);
      const item = JSON.parse(raw);
      const token = getTokenFromRequest(request);
      const payload = token ? await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me') : null;
      if (!isAdmin && item.user_id !== (payload?.user_id || 0)) {
        return errorResponse('无权删除', 403);
      }
      await getSafeKV(env).delete(`feedback:${id}`);
      return jsonResponse({ success: true });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  // ---- 需要认证的 API ----
  const needAuth = path.startsWith('/api/files/') ||
    path.startsWith('/api/comments') ||
    path.startsWith('/api/run/') ||
    path === '/api/likes' ||
    path === '/api/admin/dashboard';

  if (needAuth) {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
  }

  // ---- 代码执行 API（流式）----
  if (path === '/api/run/start') {
    return proxyStreamToEcs(path + (url.search || ''), env, request);
  }
  if (path === '/api/run/stop') {
    return fetchFromEcs(path, env, request);
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
    const CACHE_KEY = 'cache:project-meta';
    const CACHE_TTL = 1800;
    try {
      const cached = await getSafeKV(env).get(CACHE_KEY, { type: 'json' });
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
      const cachedLikes = await getSafeKV(env).get('cache:likes', { type: 'json' });
      if (cachedLikes) {
        Object.assign(likesMap, cachedLikes);
      } else {
        const likesList = await getSafeKV(env).list({ prefix: 'likes:' });
        for (const key of likesList.keys) {
          const project = key.name.substring('likes:'.length);
          const value = await getSafeKV(env).get(key.name);
          likesMap[project] = parseInt(value || '0', 10) || 0;
        }
        try {
          await getSafeKV(env).put('cache:likes', JSON.stringify(likesMap), {
            expirationTtl: 1800
          });
        } catch {}
      }
    } catch {}
    try {
      const cachedComments = await getSafeKV(env).get('cache:comment-counts', { type: 'json' });
      if (cachedComments) {
        Object.assign(commentsMap, cachedComments);
      } else {
        const commentsList = await getSafeKV(env).list({ prefix: 'comments:' });
        for (const key of commentsList.keys) {
          const project = key.name.substring('comments:'.length);
          const value = await getSafeKV(env).get(key.name);
          try {
            const parsed = JSON.parse(value || '{}');
            commentsMap[project] = (parsed.comments || []).length;
          } catch { commentsMap[project] = 0; }
        }
        try {
          await getSafeKV(env).put('cache:comment-counts', JSON.stringify(commentsMap), {
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
      await getSafeKV(env).put(CACHE_KEY, JSON.stringify({
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
      const cached = await getSafeKV(env).get(cacheKey, { type: 'json' });
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
      await getSafeKV(env).put(cacheKey, JSON.stringify(result), {
        expirationTtl: 3600
      });
    } catch {}
    const resp = jsonResponse(result);
    addCacheHeader(resp.headers, 3600);
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
        const cached = await getSafeKV(env).get(cacheKey, { type: 'arrayBuffer' });
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
        await getSafeKV(env).put(cacheKey, buf as any, {
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
        const data = await getSafeKV(env).get(key);
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
        const existing = await getSafeKV(env).get(key);
        if (existing) { try { projectData = JSON.parse(existing); } catch {} }

        const commentId = Math.random().toString(36).substring(2, 10);
        const comment = {
          id: commentId, project, text,
          timestamp: Date.now(), image: null, likes: 0
        };
        projectData.comments.push(comment);
        await getSafeKV(env).put(key, JSON.stringify(projectData));
        try { await getSafeKV(env).delete('cache:comment-counts'); } catch {}
        try { await getSafeKV(env).delete('cache:project-meta'); } catch {}
        try { await getSafeKV(env).delete('cache:home-page-v2'); } catch {}
        return jsonResponse(comment, 201);
      } catch {
        return errorResponse('无效的请求', 400);
      }
    }
  }

  if (path === '/api/comments/counts') {
    try {
      const cached = await getSafeKV(env).get('cache:comment-counts', { type: 'json' });
      if (cached) {
        const resp = jsonResponse(cached);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {}
    const counts: Record<string, number> = {};
    try {
      const list = await getSafeKV(env).list({ prefix: 'comments:' });
      for (const key of list.keys) {
        try {
          const data = await getSafeKV(env).get(key.name);
          if (data) {
            const parsed = JSON.parse(data);
            if (parsed.project && Array.isArray(parsed.comments)) {
              counts[parsed.project] = parsed.comments.length;
            }
          }
        } catch {}
      }
      try {
        await getSafeKV(env).put('cache:comment-counts', JSON.stringify(counts), {
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
      const existing = await getSafeKV(env).get(key);
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
      await getSafeKV(env).put(key, JSON.stringify(projectData));
      try { await getSafeKV(env).delete('cache:comment-counts'); } catch {}
      return jsonResponse({ success: true });
    } catch {
      return errorResponse('点赞失败', 500);
    }
  }

  // ---- 点赞 API ----
  if (path === '/api/likes') {
    if (request.method === 'GET') {
      try {
        const cached = await getSafeKV(env).get('cache:likes', { type: 'json' });
        if (cached) {
          const resp = jsonResponse(cached);
          addCacheHeader(resp.headers, 300);
          return resp;
        }
      } catch {}
      const likes: Record<string, number> = {};
      try {
        const list = await getSafeKV(env).list({ prefix: 'likes:' });
        for (const key of list.keys) {
          const project = key.name.substring('likes:'.length);
          const value = await getSafeKV(env).get(key.name);
          likes[project] = parseInt(value || '0', 10) || 0;
        }
        try {
          await getSafeKV(env).put('cache:likes', JSON.stringify(likes), {
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
        const existing = await getSafeKV(env).get(key);
        if (existing) current = parseInt(existing, 10) || 0;
        current += 1;
        await getSafeKV(env).put(key, String(current));
        try { await getSafeKV(env).delete('cache:likes'); } catch {}
        try { await getSafeKV(env).delete('cache:project-meta'); } catch {}
        try { await getSafeKV(env).delete('cache:home-page-v2'); } catch {}
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
      const commentsList = await getSafeKV(env).list({ prefix: 'comments:' });
      commentProjects = commentsList.keys.length;
      for (const key of commentsList.keys) {
        const data = await getSafeKV(env).get(key.name);
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
      const likesList = await getSafeKV(env).list({ prefix: 'likes:' });
      likeProjects = likesList.keys.length;
      for (const key of likesList.keys) {
        const count = await getSafeKV(env).get(key.name);
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
      const contextInfo = data.context;
      const model = data.model;
      const needsProjects = data.needsProjects !== false; // 默认为 true 保持兼容

      // 兼容旧格式: { input } 或 { preferences }
      if (!messages && (data.input || data.preferences)) {
        const userInput = (data.input || data.preferences || '').trim();
        if (!userInput) return errorResponse('请输入你的兴趣或需求', 400);
        messages = [{ role: 'user', content: `我的兴趣：${userInput}` }];
      }

      if (!messages || messages.length === 0) {
        return errorResponse('请输入消息', 400);
      }

      // 只在需要时加载项目列表，减少不必要的开销
      let projects: any[] = [];
      if (needsProjects) {
        projects = await loadProjectsForRecommend(env);
        if (projects.length === 0) return errorResponse('项目列表为空', 503);
      }

      const result = await getConversationalAI(messages, projects, env, contextInfo, model);
      try {
        const today = new Date().toISOString().slice(0, 10);
        const usageKey = `ai-usage:${today}`;
        const currentUsage = parseInt(await getSafeKV(env).get(usageKey) || '0', 10);
        await getSafeKV(env).put(usageKey, String(currentUsage + 1), { expirationTtl: 86400 });
      } catch {}
      return jsonResponse({ success: true, response: result.text, recommendations: result.recommendations, reasoning: result.reasoning });
    } catch (e: any) {
      return errorResponse(`请求失败: ${e.message || e}`, 500);
    }
  }

  if (path === '/api/recommend' && request.method === 'OPTIONS') {
    return optionsResponse();
  }

  if (path === '/api/ai-quota') {
    try {
      const today = new Date().toISOString().slice(0, 10);
      const usageKey = `ai-usage:${today}`;
      const usage = parseInt(await getSafeKV(env).get(usageKey) || '0', 10);
      const DAILY_LIMIT = 10000;
      const neuronsPerRequest = 100;
      const remaining = Math.max(0, DAILY_LIMIT - usage * neuronsPerRequest);
      return jsonResponse({ usage, remaining, limit: DAILY_LIMIT, neuronsPerRequest });
    } catch (e: any) {
      return jsonResponse({ usage: 0, remaining: 10000, limit: 10000, neuronsPerRequest: 100 });
    }
  }

  // ---- API Key 管理 API（代理到 ECS）----
  if (path.startsWith('/api/api-keys') || path.startsWith('/api/ai-pool')) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165:8765';
      const ecsReqUrl = `${ecsUrl}${path}${url.search}`;
      const headers = new Headers(request.headers);
      headers.set('Host', new URL(ecsUrl).host);
      const cookie = request.headers.get('Cookie');
      if (cookie) headers.set('Cookie', cookie);
      const resp = await fetch(ecsReqUrl, {
        method: request.method,
        headers,
        body: request.method !== 'GET' ? request.body : undefined,
        signal: controller.signal,
        cf: { connectTimeout: 5 } as any,
      });
      clearTimeout(timer);
      return new Response(resp.body, {
        status: resp.status,
        statusText: resp.statusText,
        headers: resp.headers,
      });
    } catch (e: any) {
      const msg = e.name === 'AbortError' ? 'ECS服务器请求超时' : (e.message || 'ECS服务器不可用');
      return errorResponse(msg, 502);
    }
  }

  // ---- 未识别的 API → 代理到 ECS 服务器 ----
  if (!path.startsWith('/api/static') && !path.startsWith('/api/cdn')) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165:8765';
      const ecsReqUrl = `${ecsUrl}${path}${url.search}`;
      const headers = new Headers(request.headers);
      headers.set('Host', new URL(ecsUrl).host);
      const cookie = request.headers.get('Cookie');
      if (cookie) headers.set('Cookie', cookie);
      const resp = await fetch(ecsReqUrl, {
        method: request.method,
        headers,
        body: request.method !== 'GET' ? request.body : undefined,
        signal: controller.signal,
        cf: { connectTimeout: 5 } as any,
      });
      clearTimeout(timer);
      return new Response(resp.body, {
        status: resp.status,
        statusText: resp.statusText,
        headers: resp.headers,
      });
    } catch (e: any) {
      const msg = e.name === 'AbortError' ? 'ECS服务器请求超时' : (e.message || 'ECS服务器不可用');
      return errorResponse(msg, 502);
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
  const CACHE_KEY = 'cache:project-meta';
  try {
    const cached = await getSafeKV(env).get(CACHE_KEY, { type: 'json' });
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
  const CACHE_KEY = 'cache:home-page-v2';
  const CACHE_TTL = 1800;

  try {
    const cached = await getSafeKV(env).get(CACHE_KEY, { type: 'text' });
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
    const cachedLikes = await getSafeKV(env).get('cache:likes', { type: 'json' });
    if (cachedLikes) {
      Object.assign(likesMap, cachedLikes);
    } else {
      const likesList = await getSafeKV(env).list({ prefix: 'likes:' });
      for (const key of likesList.keys) {
        const project = key.name.substring('likes:'.length);
        const value = await getSafeKV(env).get(key.name);
        likesMap[project] = parseInt(value || '0', 10) || 0;
      }
      try {
        await getSafeKV(env).put('cache:likes', JSON.stringify(likesMap), {
          expirationTtl: 1800
        });
      } catch {}
    }
  } catch {}
  try {
    const cachedComments = await getSafeKV(env).get('cache:comment-counts', { type: 'json' });
    if (cachedComments) {
      Object.assign(commentsMap, cachedComments);
    } else {
      const commentsList = await getSafeKV(env).list({ prefix: 'comments:' });
      for (const key of commentsList.keys) {
        const project = key.name.substring('comments:'.length);
        const value = await getSafeKV(env).get(key.name);
        try {
          const parsed = JSON.parse(value || '{}');
          commentsMap[project] = (parsed.comments || []).length;
        } catch { commentsMap[project] = 0; }
      }
      try {
        await getSafeKV(env).put('cache:comment-counts', JSON.stringify(commentsMap), {
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
    await getSafeKV(env).put(CACHE_KEY, html, { expirationTtl: CACHE_TTL });
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

  // 路径重写：目录路径 → index.html 或 .html
  // 已知有多页的目录，使用 index.html
  const multiPageDirs = ['/web-games', '/feedback', '/fathers-day', '/python', '/scratch', '/resources', '/images'];
  if (path.endsWith('/') && path !== '/') {
    const trimmedPath = path.slice(0, -1);
    if (multiPageDirs.includes(trimmedPath)) {
      path = path + 'index.html';
    } else {
      path = trimmedPath + '.html';
    }
  }

  // 路径重写：无扩展名路径 → 根据类型选择 .html 或 /index.html
  let ext = getExt(path);
  if (!ext && !path.startsWith('/api/') && !path.startsWith('/cdn-cgi/')) {
    // 检查是否是已知的多页目录
    const isMultiPageDir = multiPageDirs.some(d => path === d || path.startsWith(d + '/'));
    if (isMultiPageDir) {
      path = path + '/index.html';
    } else {
      path = path + '.html';
    }
  }

  // 重新计算扩展名（路径重写后）
  ext = getExt(path);

  // feedback 页面支持（/feedback → /feedback/index.html）
  if (path === '/feedback') {
    path = '/feedback/index.html';
  }

  // feedback 页面强制从 GitHub 代理，避免 Assets 缓存过时
  if (path.startsWith('/feedback')) {
    let ghPath;
    if (path === '/feedback' || path === '/feedback/') {
      ghPath = 'code-explorer/public/feedback/index.html';
    } else {
      ghPath = 'code-explorer/public' + path;
    }
    const ghResp = await fetchFromGitHub(ghPath, env);
    if (ghResp.ok) {
      const body = await ghResp.text();
      return new Response(body, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-cache' }
      });
    }
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

  const isStatic = isStaticAsset(ext);
  const isHtml = ext === '.html' || ext === '.htm';
  const isChangelog = path === '/changelog.json';

  // 静态资源尝试 KV 缓存（changelog.json 除外，动态内容不缓存）
  if (isStatic && !isHtml && !isChangelog) {
    const cacheKey = `cache:static:v4:${path}`;
    const ctypeKey = `cache:static:v4:ctype:${path}`;
    try {
      const cached = await getSafeKV(env).get(cacheKey, { type: 'arrayBuffer' });
      if (cached) {
        let ctype = CONTENT_TYPE_MAP[ext] || 'application/octet-stream';
        try {
          const storedCtype = await getSafeKV(env).get(ctypeKey, { type: 'text' });
          if (storedCtype) ctype = storedCtype;
        } catch {}
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
    // Use asset's content type if it provides a specific one, otherwise fall back to map
    const assetCtype = assetResp.headers.get('Content-Type') || '';
    let ctype = (assetCtype && assetCtype !== 'application/octet-stream' && !assetCtype.startsWith('text/plain')) ? assetCtype : (CONTENT_TYPE_MAP[ext] || 'application/octet-stream');
    // Force correct content type for HTML files
    if (isHtml) ctype = 'text/html; charset=utf-8';
    const body = ctype.startsWith('text/') || ctype.startsWith('application/') || ctype.startsWith('image/svg')
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
        const cacheKey = `cache:static:v4:${path}`;
        const ctypeKey = `cache:static:v4:ctype:${path}`;
        const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body as string).buffer;
        await getSafeKV(env).put(cacheKey, buf as any, {
          expirationTtl: 86400 * 7
        });
        await getSafeKV(env).put(ctypeKey, ctype, {
          expirationTtl: 86400 * 7
        });
      } catch {}
    }
    return new Response(body, { status: 200, headers });
  }

  // Fallback: 从 GitHub 代理静态文件（尝试多个路径）
  const fallbackPaths = [
    'code-explorer/public/' + path.substring(1),
    'code-explorer/' + path.substring(1),
    path.substring(1),
  ];
  
  for (const ghPath of fallbackPaths) {
    const rootGhResp = await fetchFromGitHub(ghPath, env);
    if (rootGhResp.ok) {
      const ghCtype = rootGhResp.headers.get('Content-Type') || '';
      let ctype = (ghCtype && ghCtype !== 'application/octet-stream' && !ghCtype.startsWith('text/plain')) ? ghCtype : (CONTENT_TYPE_MAP[ext] || 'application/octet-stream');
      if (isHtml) ctype = 'text/html; charset=utf-8';
      const body = ctype.startsWith('text/') || ctype.startsWith('application/') || ctype.startsWith('image/svg')
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
          const cacheKey = `cache:static:v4:${path}`;
          const ctypeKey = `cache:static:v4:ctype:${path}`;
          const buf = body instanceof ArrayBuffer ? body : new TextEncoder().encode(body as string).buffer;
          await getSafeKV(env).put(cacheKey, buf as any, {
            expirationTtl: 86400 * 7
          });
          await getSafeKV(env).put(ctypeKey, ctype, {
            expirationTtl: 86400 * 7
          });
        } catch {}
      }
      return new Response(body, { status: 200, headers });
    }
  }

  // For image requests that can't be found, generate placeholder
  if (['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'].includes(ext)) {
    return generatePlaceholderImage(ext, path);
  }

  return new Response('Not Found', { status: 404 });
}

// ------------------------------------------------------------
// Worker 入口
// ------------------------------------------------------------

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // 一次性清理旧首页缓存
    if (env.CODE_EXPLORER_KV) {
      ctx.waitUntil(
        Promise.all([
          getSafeKV(env).delete('cache:home-page').catch(() => {}),
          getSafeKV(env).delete('cache:home-page-v2').catch(() => {}),
        ])
      );
    }

    // API 请求
    if (path.startsWith('/api/')) {
      return handleApi(request, env, path);
    }

    // 静态文件 / 页面
    return handleStatic(request, env, path);
  }
};
