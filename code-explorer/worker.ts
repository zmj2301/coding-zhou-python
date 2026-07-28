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
  const url = `https://raw.githubusercontent.com/${repo}/${branch}/${encodeURI(cleanPath)}`;
  return fetch(url);
}

// ------------------------------------------------------------
// 工具：ECS 服务器代理
// ------------------------------------------------------------

async function fetchFromEcs(path: string, env: Env, request: Request): Promise<Response> {
  const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165';
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

async function fetchAsset(path: string, env: Env): Promise<Response> {
  try {
    if (env.ASSETS && typeof env.ASSETS.fetch === 'function') {
      const cleanPath = path.startsWith('/') ? path.substring(1) : path;
      const resp = await env.ASSETS.fetch(new Request('/' + cleanPath));
      if (resp.ok) return resp;
    }
  } catch {}
  return fetchFromGitHub('code-explorer/public' + path, env);
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