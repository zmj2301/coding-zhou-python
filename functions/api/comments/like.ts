// POST /api/comments/like
import { checkAuth, jsonResponse, errorResponse } from '../../_utils';

function safeProjectName(project: string): string {
  return project
    .replace(/\//g, '_')
    .replace(/\\/g, '_')
    .replace(/[:*?"<>|]/g, '_');
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
    const commentId = data.id || '';

    if (!project || !commentId) {
      return errorResponse('缺少 project 或 id 参数');
    }

    const kv = env.CODE_EXPLORER_KV;
    const key = `comments:${safeProjectName(project)}`;

    const existing = await kv.get(key);
    if (!existing) {
      return errorResponse('评论不存在', 404);
    }

    let projectData: any;
    try {
      projectData = JSON.parse(existing);
    } catch {
      return errorResponse('评论不存在', 404);
    }

    let found = false;
    for (const c of projectData.comments || []) {
      if (c.id === commentId) {
        c.likes = (c.likes || 0) + 1;
        found = true;
        break;
      }
    }

    if (!found) {
      return errorResponse('评论不存在', 404);
    }

    await kv.put(key, JSON.stringify(projectData));
    return jsonResponse({ success: true });
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
