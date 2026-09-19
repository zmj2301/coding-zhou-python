// 静态文件代理：首页、页面保护、静态资源、目录 fallback

import { Env } from '../lib/types';
import { isBrowserRequest, redirectResponse } from '../lib/http';
import { checkAuth } from '../lib/auth';
import { fetchFromGitHub } from '../lib/github';
import { fetchAsset, getExt, isStaticAsset, CONTENT_TYPE_MAP, ensureUtf8Charset } from '../lib/assets';
import { serveHomePage } from './home';

export async function handleStatic(request: Request, env: Env, path: string): Promise<Response> {
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

  // Scratch 页面保护
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

  // 静态资源尝试 KV 缓存
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

  // Fallback: 从 GitHub 代理静态文件
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
