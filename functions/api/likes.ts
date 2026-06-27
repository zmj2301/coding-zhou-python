// GET /api/likes  POST /api/likes
import { checkAuth, jsonResponse, errorResponse } from '../_utils';

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  const kv = env.CODE_EXPLORER_KV;
  const likes: Record<string, number> = {};

  try {
    const list = await kv.list({ prefix: 'likes:' });
    for (const key of list.keys) {
      const project = key.name.substring('likes:'.length);
      const value = await kv.get(key.name);
      likes[project] = parseInt(value || '0', 10) || 0;
    }
    return jsonResponse(likes);
  } catch (e) {
    return errorResponse(`加载点赞数据失败: ${e}`, 500);
  }
}

export async function onRequestPost(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  try {
    const data = await request.json();
    const project = data.project || '';

    if (!project) {
      return errorResponse('缺少 project 参数');
    }

    const kv = env.CODE_EXPLORER_KV;
    const key = `likes:${project}`;

    let current = 0;
    const existing = await kv.get(key);
    if (existing) {
      current = parseInt(existing, 10) || 0;
    }
    current += 1;

    await kv.put(key, String(current));
    return jsonResponse({ project, likes: current });
  } catch (e) {
    return errorResponse('点赞失败', 500);
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
