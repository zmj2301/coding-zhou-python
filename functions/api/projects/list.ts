// GET /api/projects/list
import { checkAuth, jsonResponse, errorResponse } from '../../_utils';

const CACHE_KEY = 'cache:project-meta';
const CACHE_TTL = 300;

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  const kv = env.CODE_EXPLORER_KV;

  try {
    const cached = await kv.get(CACHE_KEY, { type: 'json' });
    if (cached && cached.projects && cached.timestamp) {
      const age = Date.now() - cached.timestamp;
      if (age < CACHE_TTL * 1000) {
        return jsonResponse(cached.projects);
      }
    }

    const listResponse = await env.ASSETS.fetch(new Request('/project-list.json', request));
    if (!listResponse.ok) {
      return jsonResponse([]);
    }
    const projects = await listResponse.json();

    const likeList = await kv.list({ prefix: 'likes:' });
    const commentList = await kv.list({ prefix: 'comments:' });

    const likePromises = likeList.keys.map(async (key: any) => {
      const project = key.name.substring('likes:'.length);
      const value = await kv.get(key.name);
      return { project, likes: parseInt(value || '0', 10) || 0 };
    });
    const likeResults = await Promise.all(likePromises);
    const likesMap: Record<string, number> = {};
    likeResults.forEach(({ project, likes }) => {
      likesMap[project] = likes;
    });

    const commentPromises = commentList.keys.map(async (key: any) => {
      try {
        const data = await kv.get(key.name);
        if (data) {
          const parsed = JSON.parse(data);
          if (parsed.project && Array.isArray(parsed.comments)) {
            return { project: parsed.project, comments: parsed.comments.length };
          }
        }
      } catch {}
      return { project: '', comments: 0 };
    });
    const commentResults = await Promise.all(commentPromises);
    const commentsMap: Record<string, number> = {};
    commentResults.forEach(({ project, comments }) => {
      if (project) commentsMap[project] = comments;
    });

    const projectsWithMeta = projects.map((p: any) => ({
      ...p,
      likes: likesMap[p.path] || 0,
      comments: commentsMap[p.path] || 0
    }));

    await kv.put(CACHE_KEY, JSON.stringify({
      projects: projectsWithMeta,
      timestamp: Date.now()
    }), { expirationTtl: CACHE_TTL });

    return jsonResponse(projectsWithMeta);
  } catch (e: any) {
    return errorResponse(`加载项目列表失败: ${e.message || e}`, 500);
  }
}

export async function onRequestOptions(): Promise<Response> {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
