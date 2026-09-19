import { Env } from '../lib/types';
import { jsonResponse, errorResponse, addCacheHeader } from '../lib/http';
import { checkAuth } from '../lib/auth';
import { fetchFromGitHub, searchInTree } from '../lib/github';
import { fetchFromEcs } from '../lib/ecs';
import { fetchAsset, getFileTree, getExt, getLanguage, CONTENT_TYPE_MAP, rewriteHtmlResourcePaths, isStaticAsset } from '../lib/assets';

export const match = (path: string, method: string): boolean =>
  path.startsWith('/api/files/') || path.startsWith('/api/projects/');

export async function handle(request: Request, env: Env, path: string): Promise<Response> {
  const url = new URL(request.url);

  // 需要认证
  const authenticated = await checkAuth(request, env);
  if (!authenticated) return errorResponse('请先登录', 401);

  if (path === '/api/files/tree') {
    const tree = await getFileTree(env);
    const resp = jsonResponse(tree);
    addCacheHeader(resp.headers, 300);
    return resp;
  }

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

  if (path === '/api/projects/tree') {
    const projPath = url.searchParams.get('path') || '';
    if (!projPath) return errorResponse('缺少 path 参数');
    if (projPath.includes('..') || projPath.startsWith('/')) return errorResponse('访问被拒绝', 403);
    try {
      const ecsResp = await fetchFromEcs(`/api/projects/tree${url.search}`, env, request);
      if (ecsResp.ok) {
        const treeData = await ecsResp.json();
        const resp = jsonResponse(treeData);
        addCacheHeader(resp.headers, 300);
        return resp;
      }
    } catch {}
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

    const ecsResp = await fetchFromEcs(`/api/files/content${url.search}`, env, request);
    if (ecsResp.ok) {
      const data = await ecsResp.json();
      const resp = jsonResponse(data);
      addCacheHeader(resp.headers, 3600);
      return resp;
    }

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
      await env.CODE_EXPLORER_KV.put(cacheKey, JSON.stringify(result), { expirationTtl: 3600 });
    } catch {}
    const resp = jsonResponse(result);
    addCacheHeader(resp.headers, 3600);
    return resp;
  }

  if (path === '/api/files/preview') {
    const filePath = url.searchParams.get('path') || '';
    if (!filePath) return errorResponse('缺少 path 参数');
    if (filePath.includes('..') || filePath.startsWith('/')) return errorResponse('访问被拒绝：路径越界', 403);

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
        headers: { 'Content-Type': contentType, 'Cache-Control': 'no-store' }
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
            headers: { 'Content-Type': contentType, 'Cache-Control': `public, max-age=${86400 * 30}` }
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
        await env.CODE_EXPLORER_KV.put(cacheKey, buf as any, { expirationTtl: 86400 * 7 });
      } catch {}
      return new Response(body, {
        status: 200,
        headers: { 'Content-Type': contentType, 'Cache-Control': `public, max-age=${86400 * 30}` }
      });
    }

    return new Response(body, {
      status: 200,
      headers: { 'Content-Type': contentType, 'Cache-Control': 'no-store' }
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

  return errorResponse('未找到接口', 404);
}
