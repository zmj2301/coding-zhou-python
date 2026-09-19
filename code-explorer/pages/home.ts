// 首页 SSR：内联项目数据 + KV 缓存

import { Env } from '../lib/types';
import { fetchAsset } from '../lib/assets';

export async function serveHomePage(request: Request, env: Env): Promise<Response> {
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
        await env.CODE_EXPLORER_KV.put('cache:likes', JSON.stringify(likesMap), { expirationTtl: 1800 });
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
        await env.CODE_EXPLORER_KV.put('cache:comment-counts', JSON.stringify(commentsMap), { expirationTtl: 1800 });
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
