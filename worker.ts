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
    const resp = await fetchFromGitHub('public/file-tree.json', env);
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
    return jsonResponse({ authenticated, passwordSet: Boolean(env.USER_PASSWORD) });
  }

  if (path === '/api/login' && request.method === 'POST') {
    try {
      const data = await request.json();
      const password = data.password || '';
      if (!env.USER_PASSWORD) return errorResponse('服务器未设置密码', 500);
      if (password !== env.USER_PASSWORD) return errorResponse('密码错误', 401);
      const token = await signJwt(
        { sub: 'user', is_admin: false },
        env.JWT_SECRET || 'default-secret-change-me',
        604800
      );
      const resp = jsonResponse({ token });
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
      const resp = jsonResponse({ token });
      return setCookie(resp, 'wg_token', token, 604800);
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/admin/clear-cache' && request.method === 'POST') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    try {
      await env.CODE_EXPLORER_KV.delete('cache:project-meta');
      await env.CODE_EXPLORER_KV.delete('cache:home-page');
    } catch {}
    return jsonResponse({ success: true, message: '缓存已清除' });
  }

  // ---- 需要认证的 API ----
  const needAuth = path.startsWith('/api/files/') ||
    path.startsWith('/api/comments') ||
    path === '/api/likes' ||
    path === '/api/admin/dashboard';

  if (needAuth) {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
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
      const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: 'json' });
      if (cached && (Date.now() - cached.timestamp) < CACHE_TTL * 1000) {
        const resp = jsonResponse(cached.projects);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {}

    const listResp = await fetchFromGitHub('public/project-list.json', env);
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

  // ---- 项目文件树 API（按需加载）----
  if (path === '/api/projects/tree') {
    const projPath = url.searchParams.get('path') || '';
    if (!projPath) return errorResponse('缺少 path 参数');
    if (projPath.includes('..') || projPath.startsWith('/')) return errorResponse('访问被拒绝', 403);
    const safeName = projPath.replace(/\//g, '__').replace(/\\/g, '__');
    const treeGhPath = `public/project-trees/${safeName}.json`;
    const treeResp = await fetchFromGitHub(treeGhPath, env);
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

  if (path === '/api/files/preview') {
    const filePath = url.searchParams.get('path') || '';
    if (!filePath) return errorResponse('缺少 path 参数');
    if (filePath.includes('..') || filePath.startsWith('/')) return errorResponse('访问被拒绝：路径越界', 403);

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
        try { await env.CODE_EXPLORER_KV.delete('cache:project-meta'); } catch {}
        try { await env.CODE_EXPLORER_KV.delete('cache:home-page'); } catch {}
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
        try { await env.CODE_EXPLORER_KV.delete('cache:project-meta'); } catch {}
        try { await env.CODE_EXPLORER_KV.delete('cache:home-page'); } catch {}
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
      auth: { active_sessions: -1, admin_sessions: -1, password_set: Boolean(env.USER_PASSWORD), admin_password_set: Boolean(env.ADMIN_PASSWORD) },
      data: { likes_count: likeProjects, total_likes: totalLikes, comment_files: commentProjects, total_comments: totalComments }
    });
  }

  return errorResponse('未找到接口', 404);
}

// ------------------------------------------------------------
// 首页服务（内联项目数据 + KV 缓存）
// ------------------------------------------------------------
async function serveHomePage(request: Request, env: Env): Promise<Response> {
  const CACHE_KEY = 'cache:home-page';
  const CACHE_TTL = 1800;

  try {
    const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: 'text' });
    if (cached) {
      return new Response(cached, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=60' }
      });
    }
  } catch {}

  const [htmlResp, listResp] = await Promise.all([
    fetchFromGitHub('code-explorer/index.html', env),
    fetchFromGitHub('public/project-list.json', env)
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
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=60' }
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

  const ext = getExt(path);
  const isStatic = isStaticAsset(ext);
  const isHtml = ext === '.html' || ext === '.htm';

  // 静态资源尝试 KV 缓存
  if (isStatic && !isHtml) {
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

  // 从 GitHub 代理静态文件
  // 优先从 public/ 目录找，否则从根目录找
  let ghPath = 'public' + path;
  let ghResp = await fetchFromGitHub(ghPath, env);
  if (ghResp.ok) {
    const ctype = CONTENT_TYPE_MAP[ext] || ghResp.headers.get('Content-Type') || 'application/octet-stream';
    const body = ctype.startsWith('text/') || ctype.startsWith('application/')
      ? await ghResp.text()
      : await ghResp.arrayBuffer();
    const headers = new Headers({ 'Content-Type': ctype });
    if (isHtml) {
      headers.set('Cache-Control', 'no-cache');
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

  // 试试直接从根路径（web-games/fathers-day 等）
  ghPath = path.substring(1);
  ghResp = await fetchFromGitHub(ghPath, env);
  if (ghResp.ok) {
    const ctype = CONTENT_TYPE_MAP[ext] || ghResp.headers.get('Content-Type') || 'application/octet-stream';
    const body = ctype.startsWith('text/') || ctype.startsWith('application/')
      ? await ghResp.text()
      : await ghResp.arrayBuffer();
    const headers = new Headers({ 'Content-Type': ctype });
    if (isHtml) {
      headers.set('Cache-Control', 'no-cache');
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
// Worker 入口
// ------------------------------------------------------------

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // API 请求
    if (path.startsWith('/api/')) {
      return handleApi(request, env, path);
    }

    // 静态文件 / 页面
    return handleStatic(request, env, path);
  }
};
