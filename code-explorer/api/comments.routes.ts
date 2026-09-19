import { Env } from '../lib/types';
import { jsonResponse, errorResponse, addCacheHeader } from '../lib/http';
import { checkAuth } from '../lib/auth';
import { safeProjectName } from '../lib/github';

export const match = (path: string, method: string): boolean =>
  path.startsWith('/api/comments') || path === '/api/likes';

export async function handle(request: Request, env: Env, path: string): Promise<Response> {
  const url = new URL(request.url);

  const authenticated = await checkAuth(request, env);
  if (!authenticated) return errorResponse('请先登录', 401);

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
        try { await env.CODE_EXPLORER_KV.delete('cache:home-page-v2'); } catch {}
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
        await env.CODE_EXPLORER_KV.put('cache:comment-counts', JSON.stringify(counts), { expirationTtl: 300 });
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
          await env.CODE_EXPLORER_KV.put('cache:likes', JSON.stringify(likes), { expirationTtl: 300 });
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
        try { await env.CODE_EXPLORER_KV.delete('cache:home-page-v2'); } catch {}
        return jsonResponse({ project, likes: current });
      } catch {
        return errorResponse('点赞失败', 500);
      }
    }
  }

  return errorResponse('未找到接口', 404);
}
