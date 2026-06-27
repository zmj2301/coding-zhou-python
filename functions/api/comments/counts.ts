// GET /api/comments/counts
import { checkAuth, jsonResponse, errorResponse } from '../../_utils';

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  const kv = env.CODE_EXPLORER_KV;
  const counts: Record<string, number> = {};

  try {
    const list = await kv.list({ prefix: 'comments:' });
    for (const key of list.keys) {
      try {
        const data = await kv.get(key.name);
        if (data) {
          const parsed = JSON.parse(data);
          if (parsed.project && Array.isArray(parsed.comments)) {
            counts[parsed.project] = parsed.comments.length;
          }
        }
      } catch {}
    }
    return jsonResponse(counts);
  } catch (e) {
    return errorResponse(`加载评论数失败: ${e}`, 500);
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
